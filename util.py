import math
import os
import queue
import time
from collections import defaultdict
from queue import Queue

import networkx as nx
import numpy as np
import pandas as pd
import requests
import urllib3


def get_all_50_nodes():
    names = set()
    for f in os.listdir('rank'):
        if f in filter:
            continue
        names = names.union(get_50_nodes(f[:f.find('.')]))
    return names


# get the top few of the sorted results.
def get_nodes(target, number=50):
    names = []
    with open('rank/{}.txt'.format(target), 'r') as rank:
        i = 0
        for line in rank:
            if ':' in line:
                package = line.strip()[:line.find(':')]
            else:
                package = line.strip()
            if i == number:
                break
            i += 1
            names.append(package)
    return names


def get_50_nodes(target):
    return get_nodes(target)


def get_rank(target):
    rank = {}
    with open('rank/{}.txt'.format(target), 'r') as f:
        i = 0
        for line in f:
            if ':' in line:
                package = line.strip()[:line.find(':')]
            else:
                package = line.strip()
            rank[package] = i
            i += 1
    return rank


# get graph of dependencies.
def get_graph(source='files/pypi_v8.csv', min=6):
    graph = nx.DiGraph()
    csv = pd.read_csv(source)
    edges = set(
        map(lambda x: (x[0], x[1]), (filter(lambda e: not pd.isna(e[1]) and e[0] != e[1], np.array(csv).tolist()))))
    graph.add_edges_from(edges)
    graph.remove_nodes_from(['.', 'nan', np.nan])
    deg = graph.in_degree()
    to_remove = [n[0] for n in deg if n[1] < min]
    graph.remove_nodes_from(to_remove)
    # graph.remove_nodes_from(list(nx.isolates(graph)))
    return graph


# get reversed graph of dependencies.
def get_r_graph(source='files/pypi_v8.csv', min=6):
    return get_graph(source, min).reverse()


# get depth of each package in graph.
def get_depth(graph):
    gnodes = defaultdict(dict)
    finish = Queue()
    layer = defaultdict(int)
    for node in list(filter(lambda l: l[1] == 0, graph.out_degree)):
        node = node[0]
        gnodes[node]['layer'] = 1
        gnodes[node]['cnt'] = 0
        gnodes[node]['finished'] = True
        finish.put(node)
    while not finish.empty():
        node = finish.get()
        for s in graph.in_edges(node):
            s = s[0]
            if s not in gnodes:
                gnodes[s]['layer'] = 0
                gnodes[s]['cnt'] = 0
                gnodes[s]['finished'] = False
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
                # print(len(gnodes))
    for node, attr in gnodes.items():
        layer[node] = attr['layer']
    return layer


def get_classify():
    classify = {}
    with open('files/classfiy.csv', 'r') as f:
        for line in f:
            line = line.strip().split(',')
            classify[line[0]] = line[1].strip()
    return classify


def get_classify_cnt(target, num=100):
    nodes = get_nodes(target, number=num)
    c = get_classify()
    cnt = defaultdict(int)
    for node in nodes:
        cnt[c[node]] += 1
    p = cnt.items()
    p = sorted(p, key=lambda i: i[1], reverse=True)
    x = []
    y = []
    for pi in p:
        x.append(pi[0])
        y.append(pi[1])
    return x, y


# get a tree of dependencies about target package.
def tree(target, graph, limit=None) -> (int, int, nx.DiGraph):
    sub_graph = nx.DiGraph()
    q = queue.Queue()
    q.put(target)
    edges = []
    node_distance = {target: 0}
    cnt = 0
    while not q.empty():
        t = q.get()
        sons = graph.in_edges(t)
        for son in sons:
            son = son[0]
            if son in node_distance:
                continue
            cnt += 1
            node_distance[son] = node_distance[t] + 1
            if limit is None or node_distance[son] <= limit:
                q.put(son)
            edges.append((son, t))
    sub_graph.add_edges_from(edges)
    width = len(graph.in_edges(target))
    if width == 0:
        return 0, 0, sub_graph
    return width, cnt, sub_graph


headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 '
                  'Safari/537.36',
}

proxies = {
    'http': 'http://127.0.0.1:7890/',
    'https': 'http://127.0.0.1:7890/'
}

s = requests.Session()
s.keep_alive = False
s.verify = False
urllib3.disable_warnings()


def spider(url):
    while True:
        try:
            html = requests.get(url, headers=headers, proxies=proxies)
            return html
        except Exception as e:
            print(e)
            # time.sleep(3)


def download(url, path, chunk_s=1024):
    while True:
        try:
            req = requests.get(url, stream=True, headers=headers)
            with open(path, 'wb') as fh:
                for chunk in req.iter_content(chunk_size=chunk_s):
                    if chunk:
                        fh.write(chunk)
            return
        except:
            time.sleep(3)
            pass


def ensure_dir(dirs):
    if not os.path.exists(dirs):
        os.makedirs(dirs)
        return False
    return True


# get the intersection of multiple sorted results.
def get_intersection(items):
    sets = []
    for item in items:
        sets.append(set(get_50_nodes(item)))
    inter = sets[0]
    for i in range(1, len(sets)):
        inter = inter.intersection(sets[i])
    return inter


# get the difference between two sorted results.
def get_2_diff(first, second):
    f = set(get_50_nodes(first))
    s = set(get_50_nodes(second))
    a = f.difference(s)
    b = s.difference(f)
    print('diff {} from {}, {}'.format(first, second, a))
    print('diff {} from {}, {}'.format(second, first, b))
    return a, b
