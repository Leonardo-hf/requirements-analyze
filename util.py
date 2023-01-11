import os
from collections import defaultdict
from queue import Queue

import networkx as nx
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt


def get_targets():
    return ['betweenness', 'closeness', 'degree', 'local-centrality', 'pagerank', 'voterank']


def get_all_50_nodes():
    filter = ['iks2', 'paths', 'eigenvector']
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
def get_graph(source='files/pypi_v2.csv', min=6):
    graph = nx.DiGraph()
    csv = pd.read_csv(source)
    edges = list(
        map(lambda x: (x[0], x[1]), (filter(lambda e: not pd.isna(e[1]) and e[0] != e[1], np.array(csv).tolist()))))
    graph.add_edges_from(edges)
    graph.remove_nodes_from(['.', 'nan', np.nan])
    deg = graph.degree()
    to_remove = [n[0] for n in deg if n[1] < min]
    graph.remove_nodes_from(to_remove)
    # graph.remove_nodes_from(list(nx.isolates(graph)))
    return graph


# get reversed graph of dependencies.
def get_r_graph(source='files/pypi_v2.csv', min=6):
    return get_graph(source, min).reverse()


# get depth of each package in graph.
def get_depth():
    graph = get_graph(min=0)
    gnodes = defaultdict(dict)
    finish = Queue()
    for node in list(filter(lambda l: l[1] == 0, graph.out_degree)):
        node = node[0]
        gnodes[node]['layer'] = 1
        gnodes[node]['cnt'] = 0
        finish.put(node)
    while not finish.empty():
        node = finish.get()
        for s in graph.in_edges(node):
            s = s[0]
            if s in gnodes:
                gnodes[s]['layer'] += gnodes[node]['layer'] + 1
                gnodes[s]['cnt'] += 1
            else:
                gnodes[s]['layer'] = gnodes[node]['layer'] + 1
                gnodes[s]['cnt'] = 1

            if gnodes[s]['cnt'] == len(graph.out_edges(s)):
                gnodes[s]['layer'] /= gnodes[s]['cnt']
                gnodes[s]['cnt'] = 0
                finish.put(s)
    layer = {}
    for node in gnodes.keys():
        if gnodes[node]['cnt'] != 0:
            gnodes[node]['layer'] /= gnodes[node]['cnt']
        layer[node] = gnodes[node]['layer']
    return layer


def get_classify():
    classify = {}
    with open('files/classfiy.csv', 'r') as f:
        for line in f:
            line = line.strip().split(',')
            classify[line[0]] = line[1].strip()
    return classify


def get_classify_cnt(target):
    nodes = get_50_nodes(target)
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


def draw_classify_diff(a, b):
    x1, y1 = get_classify_cnt(a)
    x2, y2 = get_classify_cnt(b)
    x = list(set(x1).union(set(x2)))
    ny1 = []
    ny2 = []
    for xi in x:
        flag = False
        for i in range(0, len(x2)):
            if x2[i] == xi:
                ny2.append(y2[i])
                flag = True
                break
        if not flag:
            ny2.append(0)
        flag = False
        for i in range(0, len(x1)):
            if x1[i] == xi:
                ny1.append(y1[i])
                flag = True
                break
        if not flag:
            ny1.append(0)
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    fig, ax = plt.subplots(figsize=(40, 7))
    ax.bar(x, ny1, color='blue', label=a)
    ax.bar(x, ny2, color='green', label=b, bottom=ny1)
    ax.legend()
    plt.show()
