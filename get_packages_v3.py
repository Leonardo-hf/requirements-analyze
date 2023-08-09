import os
import tarfile
from multiprocessing import Queue, Process

import smart_open
from lxml import etree

from requirements_detector.methods import from_setup_cfg, from_setup_py, from_requirements_txt, from_pyproject_toml
from util import spider, ensure_dir

office_url = 'https://pypi.org/simple'
tsinghua_url = 'https://pypi.tuna.tsinghua.edu.cn/simple'
aliyun_url = 'https://mirrors.aliyun.com/pypi/simple/'
base_url = office_url


def produce_all_url(namelist, urlist):
    while not namelist.empty():
        try:
            name = namelist.get()
            repo = etree.HTML(spider('{}/{}'.format(base_url, name)).text)
            file_url = repo.xpath('/html/body/a')
            for a in file_url:
                desc = str(a.text).lower().replace('_', '-')
                if (not is_zip(desc)) and (not is_tar(desc)):
                    continue
                edition = desc
                for suffix in [name + '-', '.zip', '.egg', '.tar.gz', '.tar.bz2']:
                    edition = edition.replace(suffix, '')
                file_url = a.attrib.get('href')
                file_url = file_url[:file_url.rfind('#')]
                if is_tar(file_url):
                    urlist.put(('tar', file_url, name, edition))
                # elif is_zip(file_url):
                #     urlist.put(('zip', file_url, name, edition))
        except Exception as e:
            print(e)


FILE_SETUP_PY = 'setup.py'
FILE_SETUP_CFG = 'setup.cfg'
FILE_REQUIRES = 'requires.txt'
FILE_PYPROJECT = 'pyproject.toml'
PARSE_MAP = {
    FILE_SETUP_PY: from_setup_py,
    FILE_SETUP_CFG: from_setup_cfg,
    FILE_REQUIRES: from_requirements_txt,
    FILE_PYPROJECT: from_pyproject_toml,
}


def consume_url(urlist, output):
    while True:
        (t, url, package, edition) = urlist.get(block=True)
        reqs = set()
        if t == 'tar':
            with smart_open.open(url, mode='rb') as tar:
                tar = tarfile.open(fileobj=tar)
                f = tar.next()
                while f:
                    name = f.name
                    if FILE_SETUP_PY in name:
                        parse = PARSE_MAP[FILE_SETUP_PY]
                    elif FILE_SETUP_CFG in name:
                        parse = PARSE_MAP[FILE_SETUP_CFG]
                    elif FILE_REQUIRES in name:
                        parse = PARSE_MAP[FILE_REQUIRES]
                    elif FILE_PYPROJECT in name:
                        parse = PARSE_MAP[FILE_PYPROJECT]
                    else:
                        f = tar.next()
                        continue
                    reqs = reqs.union(parse(tar.extractfile(f).read().decode('UTF-8')))
                    f = tar.next()
        print(package, edition)
        output.put((package, edition, reqs))


def handle_reqs(output):
    ensure_dir('files')
    while True:
        (package, edition, reqs) = output.get(block=True)
        with open('files/pypi++_v1.csv', 'a') as f:
            if len(reqs) == 0:
                f.write('{},{},,,\n'.format(package, edition))
                continue
            for req in reqs:
                for v in req.version_specs:
                    f.write('{},{},{},{},{}\n'.format(package, edition, req.name, v[1], v[0]))


def is_zip(s):
    return s.endswith('zip') or s.endswith('egg')


def is_tar(s):
    return s.endswith('tar.gz') or s.endswith('tar.bz2')


def get_packages_list():
    p = 'files/packages.txt'
    if os.path.exists(p):
        with open(p, 'r') as f:
            return list(map(lambda x: x.strip(), f.readlines()))
    ensure_dir('files')
    html = spider(base_url).text
    content = etree.HTML(html)
    packages = content.xpath('/html/body/a/text()')
    with open(p, "w") as f:
        for p in packages:
            f.write('{}\n'.format(p))
    return packages


if __name__ == '__main__':
    packages = get_packages_list()
    n, q, o = Queue(), Queue(), Queue()
    for pi in packages:
        n.put(pi)
    p_num, q_num, o_num = 2, 8, 1
    p_list, q_list, o_list = [], [], []
    for i in range(p_num):
        p = Process(target=produce_all_url, args=(n, q))
        p.start()
        p_list.append(p)
    for i in range(q_num):
        p = Process(target=consume_url, args=(q, o))
        p.start()
        q_list.append(p)
    for i in range(o_num):
        p = Process(target=handle_reqs, args=(o,))
        p.start()
        o_list.append(p)
