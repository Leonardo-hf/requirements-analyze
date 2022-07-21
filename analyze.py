import os.path
from queue import Queue

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

if __name__ == '__main__':
    if os.path.exists('d_requirements.csv'):
        df = pd.read_csv('d_requirements.csv', usecols=['package', 'requirement'])
    else:
        df = pd.read_csv('requirements.csv', usecols=['package', 'requirement'])
        # 读入有向图，存储边
        df = df.drop_duplicates(subset=['package', 'requirement'])
        df.to_csv('d_requirements.csv', index=False)
    edges = list(map(lambda x: (x[0], x[1]), (filter(lambda e: not pd.isna(e[1]), np.array(df).tolist()))))
    # print(edges)
    # 根据边获取节点的集合
    G = nx.DiGraph(name="analyze")
    G.remove_nodes_from(['.', 'nan', np.nan])
    G.add_edges_from(edges)
    # pos = nx.spring_layout(G)
    # pos = nx.shell_layout(G)
    # plt.figure(1)

    # 对pagerank值进行排序
    # pr = nx.pagerank(G, alpha=0.85)
    # rank = pr.items()
    # rank = sorted(rank, key=lambda r: r[1], reverse=True)
    # with open("rank/pagerank.txt", 'w') as pagerank:
    #     for item in rank:
    #         pagerank.write('{}: {}\n'.format(item[0], item[1]))
    # betweenness = nx.betweenness_centrality(G, normalized=False)
    # # 对betweenness值进行排序
    # rank = betweenness.items()
    # rank = sorted(rank, key=lambda r: r[1], reverse=True)
    # with open("rank/betweenness.txt", 'w') as pagerank:
    #     for item in rank:
    #         pagerank.write('{}: {}\n'.format(item[0], item[1]))
    # 对clustering值进行排序
    # clustering = nx.clustering(G)
    # rank = clustering.items()
    # rank = sorted(rank, key=lambda r: r[1], reverse=True)
    # with open("rank/clustering.txt", 'w') as pagerank:
    #     for item in rank:
    #         pagerank.write('{}: {}\n'.format(item[0], item[1]))
    # 对voterank值进行排序
    voterank = nx.voterank(G)
    print(voterank)
    # rank = sorted(rank, key=lambda r: r[1], reverse=True)
    # with open("rank/voterank.txt",'w') as pagerank:
    #     for item in rank:
    #         pagerank.write('{}: {}\n'.format(item[0], item[1]))
    # 对closeness值进行排序
    closeness = nx.closeness_centrality(G)
    rank = closeness.items()
    rank = sorted(rank, key=lambda r: r[1], reverse=True)
    with open("rank/closeness.txt", 'w') as pagerank:
        for item in rank:
            pagerank.write('{}: {}\n'.format(item[0], item[1]))
    # 对percolation值进行排序
    percolation = nx.percolation_centrality(G)
    rank = percolation.items()
    rank = sorted(rank, key=lambda r: r[1], reverse=True)
    with open("rank/percolation.txt", 'w') as pagerank:
        for item in rank:
            pagerank.write('{}: {}\n'.format(item[0], item[1]))
    # 对katz值进行排序
    katz = nx.katz_centrality(G)
    rank = katz.items()
    rank = sorted(rank, key=lambda r: r[1], reverse=True)
    with open("rank/katz.txt", 'w') as pagerank:
        for item in rank:
            pagerank.write('{}: {}\n'.format(item[0], item[1]))
    # 对degree值进行排序
    degree = nx.degree_centrality(G)
    rank = degree.items()
    rank = sorted(rank, key=lambda r: r[1], reverse=True)
    with open("rank/degree.txt", 'w') as pagerank:
        for item in rank:
            pagerank.write('{}: {}\n'.format(item[0], item[1]))
    # 对degree值进行排序
    load = nx.load_centrality(G)
    rank = load.items()
    rank = sorted(rank, key=lambda r: r[1], reverse=True)
    with open("rank/load.txt", 'w') as pagerank:
        for item in rank:
            pagerank.write('{}: {}\n'.format(item[0], item[1]))
    # 对communicability值进行排序
    communicability = nx.communicability_betweenness_centrality(G)
    rank = communicability.items()
    rank = sorted(rank, key=lambda r: r[1], reverse=True)
    with open("rank/communicability.txt", 'w') as pagerank:
        for item in rank:
            pagerank.write('{}: {}\n'.format(item[0], item[1]))
# nx.draw(G, pos=pos, node_size=[x * 6000 for x in pr.values()], node_color='m', connectionstyle='arc3, rad = 0.3')
# plt.show()
# 获得闭包
# closure = set()
# q = Queue()
# for item in rank[:100]:
#     q.put(item[0])
# while not q.empty():
#     package = q.get()
#     if package not in closure:
#         for p in np.array(df.loc[df['requirement'] == package]['package']).tolist():
#             q.put(p)
#         closure.add(package)
# with open('closure.csv', 'w') as cl:
#     for p in closure:
#         cl.write(str(p) + '\n')
