import networkx as nx
import numpy as np


def read_node(node):
    nodes = {}
    with open(node, 'r') as f:
        i = 0
        for l in f:
            if i != 0:
                try:
                    l = l.strip().split(',')
                    nodes[l[0]] = l[1]
                except:
                    pass
            i = 1
    return nodes


def read_edge(edge):
    edges = []
    with open(edge, 'r') as f:
        i = 0
        for l in f:
            if i != 0:
                try:
                    l = l.strip().split(',')
                    edges.append((l[1], l[2]))
                except:
                    pass
            i = 1
    return edges


def create_graph(edge, limit=1):
    G = nx.DiGraph()
    edges = read_edge(edge)
    G.add_edges_from(edges)
    G.remove_nodes_from(['.', 'nan', np.nan])
    deg = G.degree()
    to_remove = [n[0] for n in deg if n[1] <= limit]
    G.remove_nodes_from(to_remove)
    return G


def rank_by_pagerank(node, edge):
    nodes = read_node(node)
    G = create_graph(edge)
    pr = nx.pagerank(G, alpha=0.85)
    rank = pr.items()
    rank = sorted(rank, key=lambda r: r[1], reverse=True)
    rank = list(map(lambda r: '{}: {:.5f}'.format(nodes[r[0]], r[1]), rank))
    return rank


def rank_by_degree(node, edge):
    nodes = read_node(node)
    G = create_graph(edge, limit=10)
    pr = nx.degree_centrality(G)
    rank = pr.items()
    rank = sorted(rank, key=lambda r: r[1], reverse=True)
    rank = list(map(lambda r: '{}: {:.5f}'.format(nodes[r[0]], r[1]), rank))
    return rank


if __name__ == '__main__':
    print(rank_by_degree('node.csv', 'edge.csv'))
