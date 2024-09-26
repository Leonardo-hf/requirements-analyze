import csv
import os
import time
import urllib.parse
from functools import lru_cache
from typing import Optional, List, Union

import util


class PersonInfo:

    def __init__(self, usr: str,
                 name: str = None,
                 image: str = None,
                 location: str = None,
                 email: str = None,
                 company: str = None,
                 blog: str = None):
        self.usr = usr
        self.name = name
        self.image = image
        self.location = location
        self.email = email
        self.company = company
        self.blog = blog

    @classmethod
    @lru_cache(maxsize=10240, typed=False)
    def from_username(cls, usr):
        res = api('https://api.github.com/users/{}'.format(usr))
        return PersonInfo(usr=usr, name=res['name'], company=res['company'], email=res['email'],
                          location=res['location'], image=res['avatar_url'], blog=res['blog'])


class Contributor:

    def __init__(self, info: PersonInfo, contributions: int):
        self.info = info
        self.contributions = contributions


class Organize:
    def __init__(self, idf: str, name: str, blog: Optional[str], maintainers: List[PersonInfo]):
        self.maintainers = maintainers
        self.name = name
        self.blog = blog
        self.idf = idf

    @classmethod
    @lru_cache(maxsize=16, typed=False)
    def from_org(cls, org):
        res = api('https://api.github.com/orgs/{}'.format(org))
        name, blog = None, None
        if 'name' in res:
            name = res['name']
        if 'blog' in res:
            blog = res['blog']
        res = api('https://api.github.com/orgs/{}/members'.format(org))
        maintainers = []
        for r in res:
            maintainers.append(PersonInfo.from_username(r['login']))
        return Organize(idf=org, maintainers=maintainers, name=name, blog=blog)


class Project:
    def __init__(self, name: str, desc: Optional[str], owner: Optional[PersonInfo], org: Optional[Organize],
                 cons: List[Contributor]):
        self.org = org
        self.contributors = cons
        self.owner = owner
        self.desc = desc
        self.name = name

    @classmethod
    def from_project_name(cls, owner: str, project: str):
        res = api('https://api.github.com/repos/{}/{}'.format(owner, project))
        if res is None:
            return None
        desc = res['description']
        org, maintainer = None, None
        owner = res.get('owner').get('login')
        project = res.get('name')
        if res['owner']['type'] == 'Organization':
            org = Organize.from_org(owner)
        else:
            maintainer = PersonInfo.from_username(owner)
        res = api('https://api.github.com/repos/{}/{}/contributors'.format(owner, project))
        contributors = []
        for r in res:
            contributors.append(Contributor(PersonInfo.from_username(r['login']), r['contributions']))
        return Project(name=project, desc=desc, owner=maintainer, org=org, cons=contributors)


def api(url, author):
    headers = {
        'Authorization': author,
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    res = util.spider(url, headers=headers, proxies=util.USER_PROXIES)
    if res.status_code == 403:
        time.sleep(3600)
    if res.status_code == 404:
        return None
    if res.status_code != 200:
        # raise Exception(res.status_code, res.text)
        print(res.status_code, res.text)
        return None
    return res.json()


class Locate:
    class Location:
        def __init__(self, c1=None, c2=None, c3=None, confidence='Low'):
            self.c1 = c1
            self.c2 = c2
            self.c3 = c3
            self.confidence = confidence

    def __init__(self, bing_map_key: str,
                 save: Union[str, None] = 'files'):
        self._f = 'geo.csv'
        self._save = save
        self._api = bing_map_key
        cache = {}
        if save:
            util.ensure_dir(save)
            if not os.path.exists('{}/{}'.format(save, self._f)):
                open('{}/{}'.format(save, self._f), 'w').close()
            with open('{}/{}'.format(save, self._f), 'r') as geo:
                lines = csv.reader(geo.readlines()[1:])
                for l in lines:
                    cache[l[0]] = Locate.Location(c1=l[1], c2=l[2], c3=l[3], confidence=l[4])
        self._cache = cache

    def geocode(self, address: str) -> Location:

        def get_or(d: dict, key):
            if key in d:
                return d[key]
            return 'None'

        address = address.strip()
        if address in self._cache:
            return self._cache[address]
        params = {
            'query': address,
            'key': self._api,
            'maxResults': 1
        }
        loc = util.spider(
            '?'.join(('http://dev.virtualearth.net/REST/v1/Locations', urllib.parse.urlencode(params))),
            proxies=util.USER_PROXIES).json()
        resources = loc['resourceSets'][0]
        if resources['estimatedTotal'] >= 1:
            raw = resources['resources'][0]['address']
            confidence = resources['resources'][0]['confidence']
            res = Locate.Location(c1=get_or(raw, 'countryRegion'), c2=get_or(raw, 'adminDistrict'),
                                  c3=get_or(raw, 'adminDistrict2'),
                                  confidence=confidence)
        else:
            res = Locate.Location()
        self._cache[address] = res
        if self._save:
            with open('{}/{}'.format(self._save, self._f), 'a') as f:
                f.write('\"{}\",\"{}\",\"{}\",\"{}\",{}\n'.format(address, res.c1, res.c2, res.c3, res.confidence))
        return res