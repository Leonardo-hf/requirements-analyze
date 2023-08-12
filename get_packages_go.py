import json
from ctypes import *

from util import spider, ensure_dir


def search_all(start='2019-04-10T19:08:52.997264Z'):
    while True:
        url = 'http://index.golang.org/index?since={}'.format(start)
        lines = spider(url).text.split('\n')
        if len(lines) <= 1:
            break
        with open('go/index', 'a') as f:
            for l in lines:
                if len(l.strip()) == 0:
                    continue
                try:
                    l = json.loads(l.strip())
                except Exception as e:
                    print(e)
                    print(l)
                    continue
                artifact = l['Path']
                version = l['Version']
                time = l['Timestamp']
                f.write('{},{},{}\n'.format(artifact, version, time))
            start = time


def get_deps(artifact, version):
    url = 'https://goproxy.cn/{}/@v/{}.mod'.format(artifact, version)
    content = spider(url).content
    lib = CDLL("./lib/libmod.so")
    lib.Parse.restype = c_char_p
    res = lib.Parse(c_char_p(content))
    res = json.loads(res.decode())
    reqs = []
    if 'Require' in res and res['Require']:
        for r in res['Require']:
            reqs.append({'artifact': r['Mod']['Path'], 'version': r['Mod']['Version'],
                         'indirect': r['Indirect'], 'exclude': False})
    if 'Replace' in res and res['Replace']:
        for r in res['Replace']:
            old = {'artifact': r['Old']['Path'], 'version': r['Old'].setdefault('Version', '')}
            new = {'artifact': r['New']['Path'], 'version': r['New'].setdefault('Version', '')}
            index = -1
            for i in range(len(reqs)):
                if reqs[i]['artifact'] == old['artifact']:
                    index = i
                    break
            if index == -1:
                continue
            if new['artifact'] and new['artifact'].startswith('.'):
                del reqs[index]
                continue
            reqs[index]['artifact'] = new['artifact']
            reqs[index]['version'] = new['version']
    if 'Exclude' in res and res['Exclude']:
        for e in res['Exclude']:
            index = -1
            for i in range(len(reqs)):
                if reqs[i]['artifact'] == e['Mod']['Path']:
                    index = i
                    break
            indirect = False
            if index != -1:
                indirect = True
            reqs.append({'artifact': e['Mod']['Path'], 'version': e['Mod']['Version'],
                         'indirect': indirect, 'exclude': True})
    if 'Retract' in res and res['Retract']:
        with open('go/retract', 'a') as f:
            for r in res['Retract']:
                f.write('{},{},{},{}\n'.format(artifact, r['Low'], r['High'], r['Rationale']))
    if 'Go' in res and res['Go']:
        with open('go/go_version', 'a') as f:
            f.write('{},{},{}\n'.format(artifact, version, res['Go']['Version']))
    with open('go/deps', 'a') as f:
        for r in reqs:
            f.write('{},{},{},{},{},{}\n'.format(artifact, version, r['artifact'], r['version'], r['indirect'],
                                                 r['exclude']))


if __name__ == '__main__':
    ensure_dir('go')
    search_all()
    with open('go/index', 'r') as f:
        for l in f.readlines():
            l = l.strip().split(',')
            get_deps(l[0].strip(), l[1].strip())
