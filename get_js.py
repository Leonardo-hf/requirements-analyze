import os
import random
import re
from multiprocessing import Process, Queue

import requests
import tqdm
import urllib3

from util import ensure_dir

central_url = 'https://registry.npmjs.org'
cnpm_url = 'https://r.cnpmjs.org'
taobao_url = 'https://registry.npm.taobao.org'
mirror_url = 'https://registry.npmmirror.com'
ulist = [taobao_url, mirror_url]


def query(q: Queue):
    while not q.empty():
        n = q.get()
        name = n[0]
        key = n[1]
        urls = list(map(lambda u: '{}/{}'.format(u, key), ulist))
        r = spiders(urls)
        if r.status_code == 200:
            print(n)
            with open('/usr/local/src/datasets/npm/{}'.format(name), 'w') as f:
                f.write(r.text)


headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 '
                  'Safari/537.36',
}

s = requests.Session()
s.keep_alive = False
s.verify = False
urllib3.disable_warnings()


def spiders(urls):
    while True:
        try:
            url = urls[int(random.random() * len(urls))]
            resp = requests.get(url, headers=headers, timeout=3.05)
            return resp
        except Exception as e:
            print(e)


if __name__ == '__main__':
    with open('npm_all_json.txt', 'w') as nj:
        for n in tqdm.tqdm(range(2613548)):
            p = '/usr/local/src/datasets/npm/{}'.format(n)
            if os.path.exists(p):
                with open(p, 'r') as o:
                    nj.write(o.read())
                    nj.write('\n')
    ensure_dir('/usr/local/src/datasets/npm')
    ids = Queue()
    i = 0
    e = max(map(lambda n: int(n), os.listdir('/usr/local/src/datasets/npm')))
    with open('npm_all.json', 'r') as na:
        for l in na:
            keys = re.findall('\"key\":\".*?\"', l)
            if keys:
                for k in keys:
                    i += 1
                    if i > e:
                        ids.put((i, k[7:-1]))
    q_num = 20
    q_list = []
    for i in range(q_num):
        p = Process(target=query, args=(ids,))
        p.daemon = True
        p.start()
        q_list.append(p)
    for p in q_list:
        p.join()
