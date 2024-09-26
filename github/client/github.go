package client

import (
	"fmt"
	"io"
	"math/rand"
	"net/http"
	"sync"
	"time"
	"toolkits/github/util"

	"github.com/bytedance/sonic"
	"github.com/hashicorp/golang-lru"
	"github.com/panjf2000/ants/v2"
)

const (
	defaultMaxUsagePerHour = 5000      // 每个Token每小时的最大使用次数
	coolDownTime           = time.Hour // 冷却时间为一小时
)

// GithubApi manages a pool of GitHub tokenStates and distributes them for use.
type GithubApi struct {
	tokens      []string               // List of tokens
	tokenStates map[string]*tokenState // Stores the state of each token
	mu          sync.Mutex             // Mutex for thread-safe access
	cache       *lru.Cache
	loc         *Locate
}

// tokenState holds the state of a token, including its usage count and last used time.
type tokenState struct {
	accessCounts map[time.Time]int // 记录每分钟的访问次数
	maxUsage     int               // 区间内最大使用次数
}

// NewGithubAPI creates a new token pool with a list of tokenStates.
func NewGithubAPI(tokens ...string) *GithubApi {
	if len(tokens) == 0 {
		panic("No tokenStates provided")
	}
	cache, _ := lru.New(10000)
	pool := &GithubApi{
		tokens:      tokens,
		tokenStates: make(map[string]*tokenState),
		cache:       cache,
		loc: &Locate{BingMapKey: "ArQyEcbz07bFaAja48jANcfhxlZ1tX_lfPhVsU_fYd7yQwEwr9N-syeEnGp_x9t5",
			Save: "resources/locations.txt"},
	}
	pool.loc.init()
	for _, token := range tokens {
		pool.tokenStates[token] = &tokenState{
			accessCounts: make(map[time.Time]int),
			maxUsage:     defaultMaxUsagePerHour,
		}
	}
	return pool
}

// getToken returns a usable token from the pool or blocks until one becomes available.
func (tp *GithubApi) getToken() string {
	for {
		tp.mu.Lock()
		// shuffle tokenStates
		rand.NewSource(time.Now().UnixNano())
		rand.Shuffle(len(tp.tokens), func(i, j int) {
			tp.tokens[i], tp.tokens[j] = tp.tokens[j], tp.tokens[i]
		})
		for _, token := range tp.tokens {
			state := tp.tokenStates[token]
			if tp.isTokenUsable(state) {
				now := time.Now().UTC().Truncate(time.Minute)
				state.accessCounts[now]++
				tp.mu.Unlock()
				return token
			}
		}
		tp.mu.Unlock()
		fmt.Println("All tokens are exhausted, sleeping...")
		for token, state := range tp.tokenStates {
			count := 0
			for _, c := range state.accessCounts {
				count += c
			}
			fmt.Printf("Token %s usage %v, count %v\n", token, state.accessCounts, count)
		}
		// Sleep for a minute before retrying
		time.Sleep(time.Minute)
	}
}

// isTokenUsable checks if a token can be used based on its usage count within the last hour.
func (tp *GithubApi) isTokenUsable(state *tokenState) bool {
	now := time.Now().UTC()
	totalAccess := 0
	for t, count := range state.accessCounts {
		if now.Add(-coolDownTime).Before(t) {
			totalAccess += count
		} else {
			// Remove old access counts
			delete(state.accessCounts, t)
		}
	}
	return totalAccess < state.maxUsage
}

// Query makes a request to the GitHub API using a token from the pool.
func (tp *GithubApi) Query(url string) ([]byte, error) {
	if item, ok := tp.cache.Get(url); ok {
		if result, ok := item.([]byte); ok {
			return result, nil
		}
	}
	token := tp.getToken()
	req, _ := http.NewRequest("GET", url, nil)
	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("X-GitHub-Api-Version", "2022-11-28")

	client := &http.Client{}
	var resp *http.Response
	var httpErr error
	for {
		resp, httpErr = client.Do(req)
		if httpErr == nil {
			break
		}
		fmt.Println("Error making request:", httpErr)
		time.Sleep(time.Second)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	if resp.StatusCode == 403 {
		fmt.Println("Token rate limit exceeded, sleeping...")
		return tp.Query(url) // Retry
	}

	if resp.StatusCode != 200 {
		fmt.Println("Unexpected status code:", resp.StatusCode, url)
		return nil, fmt.Errorf("unexpected status code %d", resp.StatusCode)
	}
	tp.cache.Add(url, body)
	return body, nil
}

func (tp *GithubApi) GetUser(usr string) (*PersonInfo, error) {
	url := fmt.Sprintf("https://api.github.com/users/%s", usr)
	body, err := tp.Query(url)
	if err != nil {
		return nil, err
	}
	res := &PersonInfo{
		Usr: usr,
	}
	_ = sonic.Unmarshal(body, &res)
	addr, _ := sonic.Get(body, "location")
	addrStr, _ := addr.String()
	res.Location = tp.loc.Geocode(addrStr)
	return res, nil
}

func (tp *GithubApi) GetProject(owner, project string) (*Project, error) {
	url := fmt.Sprintf("https://api.github.com/repos/%s/%s", owner, project)
	body, err := tp.Query(url)
	if err != nil {
		return nil, err
	}
	var repo struct {
		Owner struct {
			Login string `json:"login"`
			Type  string `json:"type"`
		} `json:"owner"`
		Lisense struct {
			Name string `json:"name"`
		}
	}

	res := &Project{}
	_ = sonic.Unmarshal(body, &res)
	_ = sonic.Unmarshal(body, &repo)
	res.Org = nil
	res.Owner = nil

	if repo.Owner.Type == "Organization" {
		org, err := tp.GetOrg(repo.Owner.Login)
		if err != nil {
			return nil, err
		}
		res.Org = org
	} else {
		maintainer, err := tp.GetUser(repo.Owner.Login)
		if err != nil {
			return nil, err
		}
		res.Owner = maintainer
	}

	contributorsURL := fmt.Sprintf("https://api.github.com/repos/%s/%s/contributors", repo.Owner.Login, res.Name)
	contribResp, err := tp.Query(contributorsURL)
	if err != nil {
		return nil, err
	}

	var contributors []struct {
		Login         string `json:"login"`
		Contributions int    `json:"contributions"`
	}
	_ = sonic.Unmarshal(contribResp, &contributors)
	names := make([]string, 0, len(contributors))
	for _, member := range contributors {
		names = append(names, member.Login)
	}
	users := tp.BatchGetUser(names...)

	var cons []*Contributor
	for i, contrib := range users {
		if contrib == nil {
			continue
		}
		cons = append(cons, &Contributor{Info: contrib, Contributions: contributors[i].Contributions})
	}
	res.Contributors = cons
	return res, nil
}

// GetOrg creates an Organize instance from an organization name.
func (tp *GithubApi) GetOrg(org string) (*Organize, error) {
	orgURL := fmt.Sprintf("https://api.github.com/orgs/%s", org)
	resp, err := tp.Query(orgURL)
	if err != nil {
		return nil, err
	}
	var orgInfo struct {
		Name string `json:"name"`
		Blog string `json:"blog"`
	}

	_ = sonic.Unmarshal(resp, &orgInfo)

	membersURL := fmt.Sprintf("https://api.github.com/orgs/%s/members", org)
	membersResp, err := tp.Query(membersURL)
	if err != nil {
		return nil, err
	}

	var members []struct {
		Login string `json:"login"`
	}

	_ = sonic.Unmarshal(membersResp, &members)

	names := make([]string, 0, len(members))
	for _, member := range members {
		names = append(names, member.Login)
	}
	maintainers := tp.BatchGetUser(names...)
	return &Organize{
		IDF:         org,
		Name:        orgInfo.Name,
		Blog:        orgInfo.Blog,
		Maintainers: util.FilterNil(maintainers),
	}, nil
}

func (tp *GithubApi) BatchGetUser(names ...string) []*PersonInfo {
	users := make([]*PersonInfo, len(names))
	wait := sync.WaitGroup{}
	limitedGetUser, _ := ants.NewPoolWithFunc(10, func(i interface{}) {
		name := names[i.(int)]
		person, err := tp.GetUser(name)
		if err != nil {
			return
		}
		users[i.(int)] = person
		wait.Done()
	})
	for i := range names {
		wait.Add(1)
		_ = limitedGetUser.Invoke(i)
	}
	wait.Wait()
	return users
}
