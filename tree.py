import math
import os
import queue
import sys
from collections import defaultdict
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from networkx import DiGraph
from networkx.drawing.nx_agraph import graphviz_layout

from pypi.util import get_all_50_nodes, get_graph


def tree(target, graph):
    # sub_graph = nx.DiGraph()
    q = queue.Queue()
    q.put(target)
    edges = []
    node_set = set()
    cnt = 0
    while not q.empty():
        t = q.get()
        sons = graph.in_edges(t)
        for son in sons:
            son = son[0]
            if son in node_set:
                continue
            cnt += 1
            node_set.add(son)
            q.put(son)
            edges.append((son, t))
            # graph.add_edge(t, son)
    # sub_graph.add_edges_from(edges)
    # ap = nx.average_shortest_path_length(sub_graph)
    # print(len(sub_graph.edges))
    # pos = graphviz_layout(sub_graph, prog='dot')
    # nx.draw(sub_graph, pos, with_labels=False, arrows=True)
    # plt.savefig('tree/{}.png'.format(target))
    width = len(graph.in_edges(target))
    # print(width)
    # print(cnt)
    # print(sub_graph.nodes)
    if width == 0:
        return 0, 0, 0#, sub_graph
    return width / cnt, width, cnt#, sub_graph


def pre_tree(target, graph):
    # sub_graph = nx.Graph()
    q = queue.Queue()
    q.put(target)
    # edges = []
    node_set = set()
    cnt = 0
    while not q.empty():
        t = q.get()
        sons = graph.out_edges(t)
        for son in sons:
            son = son[1]
            if son in node_set:
                continue
            cnt += 1
            node_set.add(son)
            q.put(son)
            # edges.append((t, son))
            # graph.add_edge(t, son)
    # sub_graph.add_edges_from(edges)
    # ap = nx.average_shortest_path_length(sub_graph)
    # print(len(sub_graph.edges))
    # pos = graphviz_layout(sub_graph, prog='dot')
    # nx.draw(sub_graph, pos, with_labels=False, arrows=True)
    # plt.savefig('tree/{}.png'.format(target))
    width = len(graph.out_edges(target))
    # print(width)
    # print(cnt)
    # print(sub_graph.nodes)
    if width == 0:
        return 0, 0, 0
    return width / cnt, width, cnt


def degree(target, graph):
    return nx.degree(graph, target)


def shortest_about(target, G):
    if not os.path.exists('short'):
        os.mkdir('short')
    if not os.path.exists('short-me'):
        os.mkdir('short-me')
    all_paths = nx.all_pairs_shortest_path(G)
    left = set()
    right = set()
    with open('short/{}.txt'.format(target), 'w'):
        pass
    with open('short-me/{}.txt'.format(target), 'w'):
        pass
    for start, tos in all_paths:
        if start != target:
            for k, v in tos.items():
                if k != target and target in v:
                    i = list(v).index(target)
                    left.add(tuple(v[:i]))
                    right.add(tuple(v[i + 1:]))
                    with open('short/{}.txt'.format(target), 'a') as f:
                        f.write('{}\n'.format(v))
    with open('short-me/{}.txt'.format(target), 'a') as f:
        f.write('left: {}\nright: {}\n'.format(len(left), len(right)))
        k, r = to_dict(left)
        for i in range(0, len(k)):
            f.write('left-{}: {}\n'.format(k[i], r[i]))
        k, r = to_dict(right)
        for i in range(0, len(k)):
            f.write('right-{}: {}\n'.format(k[i], r[i]))


def to_dict(s):
    sdict = defaultdict(int)
    rk = []
    rv = []
    for item in list(map(lambda l: (len(l), 1), s)):
        sdict[item[0]] += item[1]
    for k in list(sorted(sdict.keys())):
        rk.append(k)
        rv.append(sdict[k])
    return rk, rv


def to_degraph(x, y, split=10, name=''):
    l = min(x)
    r = max(x)
    size = r - l
    nx = []
    ny = []
    while l < r:
        next = l + size / split
        ty = 0
        for i in range(0, len(x)):
            if l <= x[i] < next:
                ty += y[i]
        nx.append(next)
        ny.append(ty)
        l = next
    plt.plot(nx, ny, 'ro-', alpha=0.8, linewidth=1, label=name)
    for a, b in zip(nx, ny):
        plt.text(a, b, b, ha='center', va='bottom')
    plt.legend(loc="upper right")
    plt.xlabel('degree')
    plt.ylabel('number')
    plt.show()


def each_layer(target, graph):
    q = queue.Queue()
    q.put((target, 0))
    # edges = []
    node_set = set()
    layer_cnt = defaultdict(int)
    while not q.empty():
        t, layer = q.get()
        sons = graph.in_edges(t)
        layer_cnt[layer + 1] += len(sons)
        for son in sons:
            son = son[0]
            if son in node_set:
                continue
            node_set.add(son)
            q.put((son, layer + 1))
    with open('files/layer_cnt.csv', 'a') as f:
        f.write('{},'.format(target))
        for l in range(1, 7):
            f.write('{},'.format(layer_cnt[l]))
        f.write('{}\n'.format(layer_cnt[3] + layer_cnt[4]))


# requests 0.628813997586623
# sphinx 3.5723357847152295
if __name__ == '__main__':
    G = get_graph()
    nodes = get_all_50_nodes()
    l = []
    for n in nodes:
        a, b, c, _ = tree(n, G)
        l.append((n, a, b, c))
    l.sort(key=lambda i: i[1])
    with open('files/wd.csv', 'w') as f:
        for li in l:
            f.write('{}, {}, {}, {}\n'.format(li[0], li[1], li[2], li[3]))
