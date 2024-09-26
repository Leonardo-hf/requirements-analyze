import asyncio
import json
import logging
import os
import sys
from typing import List, Callable, Dict

import aiofiles
import aiohttp
import packageurl
import psutil
import smart_open
from aiohttp_retry import RetryClient, ExponentialRetry
from lxml import etree

from file_helper import resolve_archive
from requirements_detector.methods import from_setup_cfg, from_setup_py, from_requirements_txt, from_pyproject_toml
from requirements_detector.requirement import DetectedRequirement
from util import spider, ensure_dir, spider_async

office_url = 'https://pypi.org/simple'
tsinghua_url = 'https://pypi.tuna.tsinghua.edu.cn/simple'
aliyun_url = 'https://mirrors.aliyun.com/pypi/simple/'
base_url = tsinghua_url


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

PY_PARSE_MAP: Dict[str, Callable[[str], List[DetectedRequirement]]] = {
    FILE_SETUP_PY: from_setup_py,
    FILE_SETUP_CFG: from_setup_cfg,
    FILE_REQUIRES: from_requirements_txt,
    FILE_PYPROJECT: from_pyproject_toml,
}


def consume_url(urlist, output):
    while True:
        (t, url, package, edition) = urlist.get(block=True)
        reqs = set()
        with smart_open.open(url, mode='rb') as res:
            archive = resolve_archive(res.read())
            if not archive:
                logging.warning('illegal archive: {}'.format(url))
                return
            reqs = {}

            def dep(name: str):
                for k in PY_PARSE_MAP:
                    if name.endswith(k):
                        try:
                            k_reqs = PY_PARSE_MAP[k](archive.get_file_by_name(name).decode())
                            reqs.union(k_reqs)
                        except Exception as e:
                            logging.warning('parse {} failed: {}'.format(name, e))
                        return

            archive.iter(dep)
        output.put((package, edition, reqs))


def handle_reqs(output):
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


def safe_get(j, k, default):
    v = j.get(k, default)
    if v is None:
        return default
    return v


def to_json_without_none(d: Dict) -> str:
    def del_none(d: Dict) -> Dict:
        for key, value in list(d.items()):
            if not value:
                # 删除空值
                del d[key]
            elif value in ('UNKNOWN', 'Unknown'):
                # 删除魔数
                del d[key]
            elif isinstance(value, dict):
                del_none(value)
        return d

    return json.dumps(del_none(d))


# 获得包名索引
def get_packages_list(file: str) -> List[Dict]:
    if os.path.exists(file):
        with open(file, 'r') as f:
            return list(map(lambda x: json.loads(x.strip()), f.readlines()))
    html = spider(base_url).text
    content = etree.HTML(html)
    packages = content.xpath('/html/body/a/text()')
    packages_list = []
    # 增量写入
    for p in packages[:100000]:
        with open(file, 'a') as f:
            res = spider(f'https://pypi.org/pypi/{p}/json',
                         proxies={'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}).json()
            info = res.get('info')
            homepage = ''
            desc = ''
            if info is not None:
                urls = sorted(list(filter(lambda url: url is not None,
                                          {*safe_get(info, 'project_urls', {}).values(), info.get('home_page'),
                                           info.get('project_url'),
                                           info.get('package_url')})),
                              key=lambda url: ('github.com' in url, 'pypi.org' in url, -len(url)), reverse=True)
                if len(urls) > 0:
                    homepage = urls[0]
                desc = info.get('summary', '')
            meta = {
                'artifact': p,
                'home': homepage,
                'desc': desc
            }
            packages_list.append(meta)
            f.write(f'{to_json_without_none(meta)}\n')
    return packages_list


# 从python包名获得github地址
def get_github_by_name(name: str):
    resp = spider('https://pypi.org/project/{}'.format(name))
    if resp.status_code == 404:
        if '-' in name:
            return get_github_by_name(name.replace('-', '_'))
        return None, None
    html = etree.HTML(resp.text)

    def check(urls: List[str]):
        for url in urls:
            # 处理 readthedocs.io
            if 'readthedocs.io' in url:
                resp = spider(url, proxies={'https': '127.0.0.1:7890'})
                if resp.status_code == 404:
                    continue
                html = etree.HTML(resp.text)
                url = list(filter(lambda u: 'github.com' in u, html.xpath('//div[@role="navigation"]//a/@href')))
                if len(url) == 0:
                    continue
                url = url[0]
            # 直接检查 url
            for p in ['https://www.github.com/', 'https://www.github.com/', 'https://github.com/',
                      'http://github.com/']:
                if url.startswith(p) and not url.startswith(p + 'sponsors'):
                    url = url[len(p):]
                    spans = url.split('/')
                    if len(spans) < 2:
                        continue
                    for e in ['#', '.git']:
                        if e in spans[1]:
                            spans[1] = spans[1][:spans[1].find(e)]
                    return spans[0], spans[1]
        return None, None

    # 查找项目的主页是否是 Github
    urls = list(html.xpath('//div[@class="vertical-tabs__tabs"]//h3[text()="Project links"]/../ul/li/a/@href'))
    # 查找项目的描述内容中是否涉及 Github
    urls.extend(html.xpath('//div[@id="description"]//a/@href'))
    print(urls)
    return check(urls)


# 协程方式爬取包主页，收集各版本包url
async def get_releases_by_coroutine(package: str, limit: asyncio.Semaphore, output: str):
    async with limit:
        try:
            meta, _ = await spider_async(f'https://pypi.org/pypi/{package}/json')
            meta = json.loads(meta)
            releases = list(map(lambda kv: '{}\n'.format(
                to_json_without_none(
                    {
                        'purl': packageurl.PackageURL(type='pypi', name=package, version=kv[0]).to_string(),
                        'artifact': package,
                        'version': kv[0],
                        'url': sorted(list(map(lambda x: x.get('url'), kv[1])),
                                      key=lambda url: (
                                          url.endswith('tar.gz'),
                                          url.endswith('tar.bz2'),
                                          url.endswith('zip'),
                                          url.endswith('egg'),
                                      ), reverse=True)[0],
                        'createTime': kv[1][0].get('upload_time_iso_8601'),
                    }
                )
            ), filter(lambda kv: len(kv[1]) > 0, meta.get('releases', {}).items())))
            # 写入文件
            if len(releases) > 0:
                async with aiofiles.open(output, 'a') as f:
                    await f.writelines(releases)
        except Exception as e:
            logging.error(f'[Deps] fail to get releases for package: {package}, err: {e}')


# 协程方式爬取每个包
async def get_archive_by_coroutine(url: str, package: str, edition: str, limit: asyncio.Semaphore, output: str):
    try:
        async with (limit):
            reqs = set()
            async with RetryClient(aiohttp.ClientSession(), retry_options=ExponentialRetry()) as session:
                async with session.get(url) as res:
                    if res.status == 404:
                        return
                    size = res.headers.get('Content-Length')
                    if size is not None and (
                            int(size) > 1024 * 1024 * 100 or
                            psutil.virtual_memory().available - 500 * 1024 * 1024 < int(size)
                    ):
                        logging.warning(
                            f'[Deps] skip huge file, url: {url}, size: {int(size) / 1024 / 1024} MB, available: {psutil.virtual_memory().available / 1024 / 1024} MB')
                        return
                    archive = resolve_archive(await res.read())
                    if not archive:
                        logging.warning(f'[Deps] illegal archive: {url}')
                        return
                    reqs = set()

                    def dep(name: str):
                        for k in PY_PARSE_MAP:
                            if name.endswith(k):
                                try:
                                    k_reqs = PY_PARSE_MAP[k](archive.get_file_by_name(name).decode())
                                    reqs.update(k_reqs)
                                except Exception as e:
                                    logging.warning(
                                        f'[Deps] fail to parse deps file: {package}-{edition}.{name}, url: {url}, err: {e}')
                                return

                    archive.iter(dep)
            async with aiofiles.open(output, 'a') as f:
                content = '{},{},,,\n'.format(package, edition)
                if len(reqs):
                    content = ''
                    for req in reqs:
                        if len(req.version_specs) == 0:
                            content += '{},{},{},,\n'.format(package, edition, req.name)
                        for v in req.version_specs:
                            content += '{},{},{},{},{}\n'.format(package, edition, req.name, v[1], v[0])
                await f.write(content)
    except Exception as e:
        logging.error(f'[Deps] fail to parse deps for release: {package}-{edition}, url: {url}, err: {e}')


def standardize(name: str) -> str:
    return name.lower().replace('_', '-')


if __name__ == '__main__':
    # 准备工作目录
    dir = 'python/pypi'
    ensure_dir(dir)
    # 准备文件
    logging.basicConfig(filename=f'{dir}/python-deps-2024-06-27.log', level=logging.INFO)
    deps_file = f'{dir}/pypi_v10.csv'
    packages_file = f'{dir}/packages-2024-06-27.txt'
    releases_file = f'{dir}/releases-2024-06-27.txt'
    # 设置事件循环
    loop = asyncio.get_event_loop()
    # 设置并发数
    limit = asyncio.Semaphore(100)
    # 获取包名列表
    packages = get_packages_list(packages_file)
    sys.exit()
    logging.info(f'finish fetching packages list, size = {len(packages)}')
    # 协程获取每个包的所有版本
    loop.run_until_complete(asyncio.wait(list(
        map(lambda p: loop.create_task(get_releases_by_coroutine(p.get('artifact'), limit, releases_file)), packages))))
    logging.info(f'finish fetching releases')
    # 协程解析每个版本的依赖
    v = 0
    flag = True
    while flag:
        with open(releases_file, 'r') as f:
            # 跳过已处理的行
            for i in range(0, v):
                f.readline()
            # 每次处理10000行
            tasks = []
            for i in range(0, 10000):
                line = f.readline().strip()
                # 读到文件结尾，提前跳出
                if len(line) == 0:
                    flag = False
                    break
                # 记录处理行数
                v += 1
                release = json.loads(line)
                url = release.get('url')
                if is_tar(url) or is_zip(url):
                    url = url.replace('https://files.pythonhosted.org/', 'https://pypi.tuna.tsinghua.edu.cn/'),
                    tasks.append(loop.create_task(get_archive_by_coroutine(
                        url, release.get('artifact'), release.get('version'), limit, deps_file)))
            loop.run_until_complete(asyncio.wait(tasks))
            logging.info('processed {}'.format(v))
