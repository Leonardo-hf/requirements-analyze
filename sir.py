import copy
import random

import networkx as nx
import numpy as np
from pypi.tree import get_graph, tree


def spread(G, beta, target, gamma=0.0):
    # colors = {"R": 'b', "I": 'r', "S": 'g'}

    y = []
    n = len(G.nodes)  # 总人数
    for i in G.nodes:  # 所有人默认为易感染
        G.nodes[i]['state'] = 'S'
    s = n - 1  # 易感染人数

    i_nodes = set()
    ai = set()

    for t in target:
        G.nodes[t]['state'] = 'I'
        i_nodes.add(t)
    y.append((s, (len(i_nodes)), 0))
    ai = ai.union(i_nodes)
    # 开始传播，直到所有人被传染

    r_nodes = nx.Graph()
    while len(i_nodes) != 0:
        # 当前轮被传染的人数
        i_temp = set()
        for i in i_nodes:
            # 按beta概率传染I节点的邻居节点
            for node in G.in_edges(i):
                node = node[0]
                r = random.random()
                if r < beta and G.nodes[node]['state'] == 'S':
                    G.nodes[node]['state'] = 'I'
                    i_temp.add(node)
        for t in i_temp:
            i_nodes.add(t)
        ai = ai.union(i_nodes)
        s = n - len(i_nodes) - len(r_nodes.nodes)
        i = len(i_nodes)
        r = len(r_nodes.nodes)
        y.append((s, i, r))

        # 当前恢复人数 gamma 概率
        to_remove = []
        for i in i_nodes:
            if random.random() < gamma:
                r_nodes.add_node(i)
                to_remove.append(i)
                G.nodes[i]['state'] = 'R'
        for node in to_remove:
            i_nodes.remove(node)
        # states = nx.get_node_attributes(G, 'state')  ############ 获得节点的属性
        # color = [colors[states[i]] for i in range(n)]
        # nx.draw(G, ps, node_color=color, with_labels=True, node_size=300)
        # plt.show()
    return np.array(y), len(y), len(ai)


def linear_threshold(G, target):
    in_degree = G.in_degree()
    # init influence
    for e in G.edges():
        G[e[0]][e[1]]['influence'] = 1 / in_degree[e[1]]
    final_activated = copy.deepcopy([target])
    # init threshold
    # threshold = uniform(size=G.number_of_nodes())
    for n in G.nodes():
        # G.nodes[n]['threshold'] = threshold[0][n]
        G.nodes[n]['threshold'] = 0.5
    activated = []
    while True:
        flag = False
        for v in G.nodes():
            if v in final_activated:
                continue
            activated_u = list(set(G.predecessors(v)).intersection(set(final_activated)))
            total_threshold = 0.0
            for u in activated_u:
                total_threshold += G[u][v]['influence']
            if total_threshold >= G.nodes[v]['threshold']:
                activated.append(v)
                final_activated.append(v)
                flag = True
        if flag:
            continue
        else:
            break

    return activated, final_activated


if __name__ == '__main__':
    G = get_graph()
    # for node in get_nodes():
    target = 'matplotlib'
    score = 0
    _, _, _, sub_graph = tree(target, G)
    for i in range(0, 100):
        ar, times, ai = spread(sub_graph.copy(), 0.35, [target], 0.1)
        print('round: {}, times: {}, number of infected nodes: {}'.format(i, times, ai))
        score += ai
    print('score: {}'.format(score / 100))
    # plt.plot(ar[:, 0], 'g', label='S')
    # plt.plot(ar[:, 1], 'r', label='I')
    # plt.plot(ar[:, 2], 'b', label='R')
    # plt.legend(loc='right')
    # plt.title(target)
    # plt.xlabel('time')
    # plt.ylabel('number of packages')
    # plt.show()

# numpy 28176.7
# sphinx 25115.3
