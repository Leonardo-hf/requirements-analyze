
import networkx as nx
import numpy as np
import pandas as pd


def getGraphDensity(graph):
    edge_num = graph.number_of_edges()
    node_num = graph.number_of_nodes()
    if node_num == 0:
        return -1
    return 2 * edge_num / (node_num * (node_num - 1))


def getAverageClusteringCoefficient(graph):
    if graph.number_of_nodes() == 0:
        return -1
    return nx.average_clustering(graph)


def getLocalGraphy(graph, node):
    global_edges = []
    out = list(graph.out_edges(node))
    in_ = list(graph.in_edges(node))

    global_edges.extend(out)
    for node1 in out:
        temp = list(graph.in_edges(node1[1]))
        for ha in temp:
            if ha[0] != node:
                global_edges.append(ha)

    global_edges.extend(in_)
    for node1 in in_:
        temp = list(graph.out_edges(node1[0]))
        for ha in temp:
            if ha[1] != node:
                global_edges.append(ha)

    return global_edges


if __name__ == '__main__':
    df = pd.read_csv('files/d_requirements_pypi.csv', usecols=['package', 'requirement'])
    edges = list(map(lambda x: (x[1], x[0]), (filter(lambda e: not pd.isna(e[1]), np.array(df).tolist()))))
    # 根据边获取节点的集合
    G = nx.DiGraph(name="analyze")
    G.add_edges_from(edges)
    G.remove_nodes_from(['.', 'nan', np.nan])
    deg = G.degree()
    to_remove = [n[0] for n in deg if n[1] <= 5]
    G.remove_nodes_from(to_remove)
    G.remove_nodes_from(list(nx.isolates(G)))
    nodes = G.nodes
    i = 0
    # sizes = {}
    for node in nodes:
        print(i)
        i = i + 1
        edges = getLocalGraphy(G, node)
        localGraph = nx.Graph()
        localGraph.add_edges_from(edges)
        size = localGraph.number_of_nodes()
        # if size not in sizes:
        #     sizes[size] = 0
        # sizes[size] += 1
        # str = '{} {} {} {}\n'.format(node, getGraphDensity(localGraph), getAverageClusteringCoefficient(localGraph),
        #                              size)
        str = '{} {}\n'.format(node, size)
        with open("subgraph2.txt", "a") as file:
            file.write(str)
    # with open('subgraph_size.txt', 'w') as file:
    #     size_list = list(map(lambda it: '{} {}\n'.format(it[0], it[1]), sorted(sizes.items(), key=lambda it: it[0])))
    #     file.writelines(size_list)
