from collections import defaultdict

import networkx as nx

from pypi.util import get_graph


def local_centrality(G):
    n = {}
    for node in G.nodes():
        cnt = set()
        for n1 in G.in_edges(node):
            n1 = n1[0]
            cnt.add(n1)
            for n2 in G.in_edges(n1):
                n2 = n2[0]
                cnt.add(n2)
        if node in cnt:
            cnt.remove(node)
        n[node] = len(cnt)
    q = defaultdict(int)
    for node in G.nodes():
        for n1 in G.in_edges(node):
            n1 = n1[0]
            q[node] += n[n1]
    cl = defaultdict(int)
    for node in G.nodes():
        for n1 in G.in_edges(node):
            n1 = n1[0]
            cl[node] += q[n1]
    return cl


def write_rank(res, name):
    with open("rank2/{}.txt".format(name), 'w') as f:
        if isinstance(res, dict):
            rank = res.items()
            rank = sorted(rank, key=lambda r: r[1], reverse=True)
            for item in rank:
                f.write('{}: {}\n'.format(item[0], item[1]))
        elif isinstance(res, list) or isinstance(res, set):
            for item in res:
                f.write('{}\n'.format(item))
        else:
            print('aa')
    print('{} fin!'.format(name))


def rank():
    G = get_graph(source='files/f_requirements_pypi.csv', min=0)
    print(len(G.nodes))
    print(len(G.edges))
    write_rank(nx.degree_centrality(G), 'degree')
    write_rank(nx.pagerank(G, alpha=0.85), 'pagerank')
    write_rank(local_centrality(G), 'local_centrality')
    return
    write_rank(nx.betweenness_centrality(G, normalized=False), 'betweenness')
    write_rank(nx.closeness_centrality(G), 'closeness')

    G = G.reverse()
    write_rank(nx.voterank(G), 'voterank')


rank()
