import os
import queue
from collections import defaultdict

import networkx as nx
from matplotlib import pyplot as plt

# get a tree of dependencies about target package.
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
        return 0, 0, 0  # , sub_graph
    return width / cnt, width, cnt  # , sub_graph


def degree(target, graph):
    return nx.degree(graph, target)


# get shortest path in Graph about target package.
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
