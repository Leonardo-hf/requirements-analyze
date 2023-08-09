import json

from util import spider, ensure_dir


def search_all():
    start = '2019-04-10T19:08:52.997264Z'
    while True:
        url = 'https://index.golang.org/index?since={}'.format(start)
        lines = spider(url).text.split('\n')
        if len(lines) == 0:
            break
        with open('go/index', 'a') as f:
            for l in lines:
                if len(l.strip()) == 0:
                    continue
                l = json.loads(l.strip())
                artifact = l['Path']
                version = l['Version']
                time = l['Timestamp']
                f.write('{},{},{}\n'.format(artifact, version, time))
            start = time


def get_deps(artifact, version):
    url = 'https://goproxy.cn/{}/@v/{}.mod'.format(artifact, version)
    content = spider(url).text.split('\n')
    require = False
    exclude = False
    replace = False
    retract = False
    go_version = ''
    deps = {}
    discard = set()

    def handle_require(l, exclude=False):
        l = l.split(' ')
        ta = l[0]
        tv = l[1]
        indirect = len(l) >= 4 and l[3] == 'indirect'
        deps[ta + '@' + tv] = {
            'artifact': ta,
            'version': tv,
            'indirect': indirect,
            'exclude': exclude
        }

    def handle_replace(l):
        l = l.split(' ')
        oa = l[0]
        tod = ''
        if len(l) == 3:
            for key in deps.keys():
                if key.startswith(oa + '@'):
                    tod = key
                    break
        elif len(l) == 4:
            na = l[2]
            nv = l[3]
            for key in deps.keys():
                if key.startswith(oa + '@'):
                    deps[na + '@' + nv] = {
                        'artifact': na,
                        'version': nv,
                        'indirect': deps[key]['indirect'],
                        'exclude': False
                    }
                    tod = key
                    break
        elif len(l) == 5:
            ov = l[1]
            tod = oa + '@' + ov
            na = l[3]
            if not na.startswith('.'):
                nv = l[4]
                deps[na + '@' + nv] = {
                    'artifact': na,
                    'version': nv,
                    'indirect': deps[tod]['indirect'],
                    'exclude': False
                }
        if tod in deps:
            del deps[tod]

    for line in content:
        line = line.strip()
        if len(line) == 0 or (len(line) == 1 and line[0] == ')'):
            require = False
            exclude = False
            replace = False
            retract = False
        elif line.startswith('require ('):
            require = True
        elif line.startswith('require'):
            handle_require(line[8:])
        elif line.startswith('exclude ('):
            exclude = True
        elif line.startswith('exclude'):
            handle_require(line[8:], True)
        elif require or exclude:
            handle_require(line, exclude)
        elif line.startswith('replace ('):
            replace = True
        elif line.startswith('replace'):
            handle_replace(line[8:])
        elif replace:
            handle_replace(line)
        elif line.startswith('retract ('):
            retract = True
        elif line.startswith('retract'):
            discard.add(line[8:])
        elif retract:
            discard.add(line)
        elif line.startswith('go'):
            go_version = line.split(' ')[1]

    with open('go/deps', 'a') as f:
        for d in deps.values():
            f.write('{},{},{},{},{},{}\n'.format(artifact, version, d['artifact'], d['version'], d['indirect'],
                                                 d['exclude']))
    with open('go/extra', 'a') as f:
        if len(discard) > 0:
            for d in discard:
                f.write('discord: {},{}\n'.format(artifact, d))
        if go_version != '':
            f.write('go: {},{},{}\n'.format(artifact, version, go_version))


if __name__ == '__main__':
    ensure_dir('go')
    search_all()
