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
    # G.remove_nodes_from(['.', 'nan', np.nan])
    G.add_edges_from(edges)
    pos = nx.spring_layout(G)
    # pos = nx.shell_layout(G)
    plt.figure(1)
    pr = nx.pagerank(G, alpha=0.85)
    rank = pr.items()
    rank = sorted(rank, key=lambda r: r[1], reverse=True)
    # 对pagerank值进行排序
    print(rank)
    nx.draw(G, pos=pos, node_size=[x * 6000 for x in pr.values()], node_color='m', connectionstyle='arc3, rad = 0.3')
    plt.show()
    # 获得闭包
    closure = set()
    q = Queue()
    for item in rank[:1]:
        q.put(item[0])
    while not q.empty():
        package = q.get()
        if package not in closure:
            for p in np.array(df.loc[df['requirement'] == package]['package']).tolist():
                q.put(p)
            closure.add(package)
    with open('closure.csv', 'w') as cl:
        for p in closure:
            cl.write(str(p) + '\n')
