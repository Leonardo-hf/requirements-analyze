import asyncio
import random

import aiohttp
import pybloomer
import tqdm
from aiohttp_retry import ExponentialRetry, RetryClient
from lxml import etree

from util import ensure_dir

central_url = 'https://repo1.maven.org/maven2'
tsinghua_url = 'https://repo.maven.apache.org/maven2'
base_url = tsinghua_url

# bloom 过滤器地址
bloom = pybloomer.BloomFilter(14000000, 0.0001, 'java/java.bloom')

process = tqdm.tqdm()


# 请求
async def fetch(url):
    async with RetryClient(aiohttp.ClientSession(), retry_options=ExponentialRetry(attempts=10)) as session:
        async with session.get(url) as res:
            return await res.text(), res.headers


async def search(sem_req: asyncio.Semaphore, url: str, base_url: str):
    # 如果已经爬取过则直接返回
    if url in bloom:
        return
    # 爬取页面
    async with sem_req:
        text, headers = await fetch(url)
    process.update()
    # index文件记录已经爬取的页面
    with open('java/index', 'a') as f:
        f.write('{}, "{}"\n'.format(url[len(base_url) + 1:], headers.get('Last-Modified', '')))
    tasks = []
    # 如果是pom文件则直接存储
    if url.endswith('.pom'):
        with open('java/pom/{}'.format(url[len(base_url) + 1:].replace('/', '.')), 'w') as f:
            f.write(text)
    else:
        # 否则继续爬取
        page = etree.HTML(text)
        folder = page.xpath('//*[@id="contents"]/a')
        random.shuffle(folder)
        for f in folder:
            f = str(f.text)
            if f == '../':
                continue
            if f.endswith('/') or f.endswith('.pom'):
                tasks.append(asyncio.create_task(
                    search(sem_req, '{}/{}'.format(url, f.replace('/', '')), base_url)))
    # 将已经爬取的页面存储到bloom过滤器
    bloom.add(url)
    # 等待所有子页面爬取完毕
    if len(tasks):
        await asyncio.wait(tasks)


# 将存储的文件名转换回仓库路径
def parse_name(name: str):
    s = name.split('.')
    res = ''
    for i in range(len(s) - 1):
        if i >= 2 and s[i][0].isdigit():
            res = '/'.join(s[:i]) + '/' + '.'.join(s[i:-1])
            break
    return res


# 运行主协程


if __name__ == '__main__':
    # 创建java目录
    ensure_dir('java')
    ensure_dir('java/pom')
    loop = asyncio.get_event_loop()
    # 信号量控制协程数目
    sem = asyncio.Semaphore(100)
    loop.run_until_complete(search(sem, base_url, base_url))
    # 读取已经爬取的页面
    # for f in os.listdir('java'):
    #     n = parse_name(f)
    #     bloom.add(central_url + '/' + n)
    # q_num = 20
    # q_list = []
    # for i in range(q_num):
    #     p = Process(target=search_all, args=(base_url,))
    #     p.daemon = True
    #     p.start()
    #     q_list.append(p)
    # for p in q_list:
    #     p.join()
