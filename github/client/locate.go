package client

import (
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/bytedance/sonic"
)

// Location represents a geographical location.
type Location struct {
	Addr       string `json:"addr,omitempty"`
	C1         string `json:"c1,omitempty"`
	C2         string `json:"c2,omitempty"`
	C3         string `json:"c3,omitempty"`
	Confidence string `json:"confidence,omitempty"`
}

// Locate is responsible for geocoding addresses.
type Locate struct {
	BingMapKey string
	Save       string
	cache      sync.Map
	mu         sync.Mutex
}

func (l *Locate) init() {
	if l.Save != "" {
		if _, err := os.Stat(l.Save); os.IsNotExist(err) {
			file, _ := os.Create(l.Save)
			defer file.Close()
		}
		data, _ := os.ReadFile(l.Save)
		lines := strings.Split(string(data), "\n")
		for _, line := range lines {
			loc := &Location{}
			_ = sonic.UnmarshalString(line, loc)
			l.cache.Store(loc.Addr, loc)
		}
	}
}

type LocationResponse struct {
	ResourceSets []struct {
		EstimatedTotal int `json:"estimatedTotal"`
		Resources      []struct {
			Address struct {
				CountryRegion, AdminDistrict, AdminDistrict2 string `json:",omitempty"`
			} `json:"address"`
			Confidence string `json:"confidence"`
		} `json:"resources"`
	} `json:"resourceSets"`
}

// Geocode performs a geocode operation on the given address.
func (l *Locate) Geocode(address string) *Location {
	address = strings.TrimSpace(address)
	if loc, ok := l.cache.Load(address); ok {
		return loc.(*Location)
	}

	params := url.Values{}
	params.Set("query", address)
	params.Set("key", l.BingMapKey)
	params.Set("maxResults", "1")

	reqURL := fmt.Sprintf("http://dev.virtualearth.net/REST/v1/Locations?%s", params.Encode())
	var httpErr error
	var resp *http.Response
	for {
		resp, httpErr = http.Get(reqURL)
		if httpErr == nil {
			break
		}
		fmt.Println("Error making request:", httpErr)
		time.Sleep(time.Second)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	locResp := LocationResponse{}
	_ = sonic.Unmarshal(body, &locResp)
	res := &Location{
		Addr: address,
	}
	if len(locResp.ResourceSets) == 0 {
		msg, _ := sonic.MarshalString(body)
		fmt.Println("fail to locate", address, msg)
		return res
	}
	if locResp.ResourceSets[0].EstimatedTotal >= 1 {
		res.C1 = locResp.ResourceSets[0].Resources[0].Address.CountryRegion
		res.C2 = locResp.ResourceSets[0].Resources[0].Address.AdminDistrict
		res.C3 = locResp.ResourceSets[0].Resources[0].Address.AdminDistrict2
		res.Confidence = locResp.ResourceSets[0].Resources[0].Confidence
		l.cache.Store(address, res)
		l.asyncSave(res)
	}
	return res
}

func (l *Locate) asyncSave(loc *Location) {
	if l.Save == "" {
		return
	}
	go func() {
		l.mu.Lock()
		fileName := l.Save
		file, _ := os.OpenFile(fileName, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
		defer file.Close()
		line, _ := sonic.MarshalString(loc)
		_, _ = file.WriteString(line + "\n")
		l.mu.Unlock()
	}()
}
