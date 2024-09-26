package client

// PersonInfo represents the information of a person.
type PersonInfo struct {
	Usr      string    `json:"usr"`
	Name     string    `json:"name"`
	Image    string    `json:"avatar_url"`
	Location *Location `json:"location,omitempty"`
	Email    string    `json:"email"`
	Company  string    `json:"company"`
	Blog     string    `json:"blog"`
}

// Contributor represents a contributor to a project.
type Contributor struct {
	Info          *PersonInfo `json:"info"`
	Contributions int         `json:"contributions"`
}

// Organize represents an organization.
type Organize struct {
	IDF         string        `json:"id"`
	Name        string        `json:"name"`
	Blog        string        `json:"blog"`
	Maintainers []*PersonInfo `json:"maintainers"`
}

// Project represents a project.
type Project struct {
	PyPI         string         `json:"pypi"`
	Name         string         `json:"name"`
	Desc         string         `json:"description"`
	IsFork       bool           `json:"fork"`
	IsArchived   bool           `json:"archived"`
	Created      string         `json:"created_at"`
	Star         int            `json:"stargazers_count"`
	Watch        int            `json:"watchers_count"`
	Fork         int            `json:"forks_count"`
	Lisense      string         `json:"license"`
	Topics       []string       `json:"topics"`
	Owner        *PersonInfo    `json:"owner,omitempty"`
	Org          *Organize      `json:"org,omitempty"`
	Contributors []*Contributor `json:"contributors"`
}
