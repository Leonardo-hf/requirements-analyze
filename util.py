import math
import os
import queue
from collections import defaultdict
from queue import Queue

import aiohttp
import networkx as nx
import numpy as np
import pandas as pd
import requests
from aiohttp_retry import RetryClient, ExponentialRetry
from requests_file import FileAdapter


# get the top few of the sorted results.
def get_nodes(file, number=100):
    names = []
    with open(file, 'r') as rank:
        i = 0
        for line in rank:
            if ',' in line:
                package = line.strip()[:line.find(',')]
            else:
                package = line.strip()
            if i == number:
                break
            i += 1
            names.append(package)
    return names


# get graph of dependencies.
# k note min deg of the graph.
def get_graph(file: str, k=6):
    graph = nx.DiGraph()
    csv = pd.read_csv(file)
    edges = set(
        map(lambda x: (x[0], x[1]), (filter(lambda e: not pd.isna(e[1]) and e[0] != e[1], np.array(csv).tolist()))))
    graph.add_edges_from(edges)
    graph.remove_nodes_from(['.', 'nan', np.nan])
    deg = graph.in_degree()
    to_remove = [n[0] for n in deg if n[1] < k]
    graph.remove_nodes_from(to_remove)
    # graph.remove_nodes_from(list(nx.isolates(graph)))
    return graph


# get reversed graph of dependencies.
def get_r_graph(file, k=6):
    return get_graph(file, k).reverse()


# get depth of each package in graph.
def get_depth(graph):
    gnodes = defaultdict(dict)
    finish = Queue()
    layer = defaultdict(int)
    for node in list(filter(lambda l: l[1] == 0, graph.out_degree)):
        node = node[0]
        gnodes[node] = {
            'layer': 1,
            'cnt': 0,
            'finished': True
        }
        finish.put(node)
    while not finish.empty():
        node = finish.get()
        for s in graph.in_edges(node):
            s = s[0]
            if s not in gnodes:
                gnodes[s] = {
                    'layer': 0,
                    'cnt': 0,
                    'finished': False
                }
            if not gnodes[s]['finished']:
                gnodes[s]['layer'] += math.pow(gnodes[node]['layer'], 2)
                gnodes[s]['cnt'] += 1
                if gnodes[s]['cnt'] == len(graph.out_edges(s)):
                    gnodes[s]['layer'] = math.sqrt(gnodes[s]['layer'] / gnodes[s]['cnt']) + 1
                    gnodes[s]['finished'] = True
                    finish.put(s)
        if finish.empty():
            unfinished = list(filter(lambda n: not gnodes[n]['finished'], gnodes.keys()))
            if len(unfinished):
                shell = min(map(lambda n: len(graph.out_edges(n)) - gnodes[n]['cnt'], unfinished))
                forces = list(filter(lambda n: len(graph.out_edges(n)) - gnodes[n]['cnt'] <= shell, unfinished))
                for f in forces:
                    gnodes[f]['layer'] = math.sqrt(gnodes[f]['layer'] / gnodes[f]['cnt']) + 1
                    gnodes[f]['finished'] = True
                    finish.put(f)
    for node, attr in gnodes.items():
        layer[node] = attr['layer']
    return layer


# get a tree of dependencies about target package.
def bfs(target, graph: nx.Graph, radius=None) -> nx.DiGraph:
    sub = nx.DiGraph()
    q = queue.Queue()
    q.put(target)
    distance = {target: 0}
    sub.add_node(target, d=0)
    while not q.empty():
        v = q.get()
        if graph.is_directed():
            ws = list(map(lambda e: e[0], graph.in_edges(v)))
        else:
            ws = list(map(lambda e: e[1], graph.edges(v)))
        for w in ws:
            if w in distance:
                continue
            distance[w] = distance[v] + 1
            sub.add_node(w, d=distance[w])
            sub.add_edge(w, v)
            if radius is None or distance[w] < radius:
                q.put(w)
    return sub


s = requests.Session()
s.mount('file://', FileAdapter())

USER_PROXIES = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}


def spider(url: str, headers=None, proxies=None) -> requests.Response:
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 '
                          'Safari/537.36',
        }
    while True:
        try:
            resp = requests.get(url, headers=headers, proxies=proxies, timeout=3.05)
            return resp
        except Exception as e:
            print(e)


async def spider_async(url: str, only_head=False):
    async with RetryClient(aiohttp.ClientSession(), retry_options=ExponentialRetry(attempts=10)) as session:
        if only_head:
            async with session.head(url) as res:
                return None, res.headers
        async with session.get(url) as res:
            return await res.text(), res.headers


# async def download_async(url: str, file_out, chunk_s=1024):
#     async with RetryClient(aiohttp.ClientSession(), retry_options=ExponentialRetry(attempts=10)) as session:
#         async with session.post(url) as resp:
#             with open(file_out, 'wb') as f:
#                 async for chunk in resp.content.iter_chunked(chunk_s):
#                     f.write(await chunk)


def download(url, file_out, chunk_s=1024, headers=None, proxies=None):
    resp = spider(url, headers, proxies)
    with open(file_out, 'wb') as fh:
        for chunk in resp.iter_content(chunk_size=chunk_s):
            if chunk:
                fh.write(chunk)


def ensure_dir(dirs):
    if not os.path.exists(dirs):
        os.makedirs(dirs)
        return False
    return True


# get the intersection of multiple sorted results.
def get_intersection(items, number=100):
    sets = []
    for item in items:
        sets.append(set(get_nodes(item, number=number)))
    inter = sets[0]
    for i in range(1, len(sets)):
        inter = inter.intersection(sets[i])
    return inter


# get the difference between two sorted results.
def get_2_diff(first, second, number=100):
    f = set(get_nodes(first, number=number))
    s = set(get_nodes(second, number=number))
    a = f.difference(s)
    b = s.difference(f)
    print('diff {} from {}, {}'.format(first, second, a))
    print('diff {} from {}, {}'.format(second, first, b))
    return a, b
