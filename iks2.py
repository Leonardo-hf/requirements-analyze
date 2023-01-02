from collections import defaultdict

import numpy as np
from networkx import DiGraph


def gDegree(G):
    """
    将G.degree()的返回值变为字典
    """
    node_degrees_dict = {}
    for i in G.degree():
        node_degrees_dict[i[0]] = i[1]
    return node_degrees_dict.copy()


def kshell(G):
    graph = DiGraph(G.copy())
    importance_dict = defaultdict(list)
    while graph.size() != 0:
        level = min(graph.degree, key=lambda x: x[1])[1]
        ok = True
        while ok:
            ok = False
            level_node_list = []
            for item in graph.degree:
                if item[1] <= level:
                    ok = True
                    level_node_list.append(item[0])
            importance_dict[level].extend(level_node_list)
            graph.remove_nodes_from(level_node_list)
    return importance_dict


def sumD(G):
    """
    计算G中度的和
    """
    G_degrees = gDegree(G)
    sum = 0
    for v in G_degrees.values():
        sum += v
    return sum


def getNodeImportIndex(G):
    """
    计算节点的重要性指数
    """
    sum = sumD(G)
    I = {}
    G_degrees = gDegree(G)
    for k, v in G_degrees.items():
        I[k] =v / sum
        if I[k] == 0:
            I[k] = 1
    return I


def Entropy(G):
    """
    Entropy(G) 计算出G中所有节点的熵
    I 为重要性
    e 为节点的熵sum += I[i]*math.log(I[i])
    """
    I = getNodeImportIndex(G)
    e = {}
    for k, v in I.items():
        sum = 0
        for p in G.neighbors(k):
            sum += I[p] * np.math.log(I[p])
        sum = -sum
        e[k] = sum
    return e


def kshellEntropy(G):
    """
    kshellEntropy(G) 是计算所有壳层下，所有节点的熵值
    例：
    {28: {'1430': 0.3787255719932099,
          '646': 0.3754626894107377,
          '1431': 0.3787255719932099,
          '1432': 0.3787255719932099,
          '1433': 0.3754626894107377
          ....
    ks is a dict 显示每个壳中的节点
    e 计算了算有节点的熵
    """
    ks = kshell(G)
    e = Entropy(G)
    ksES = {}
    ksIs = sorted(ks.keys(), reverse=True)
    for ksI in ksIs:
        ksE = {}
        for i in ks[ksI]:
            ksE[i] = e[i]
        ksES[ksI] = ksE
    return ksES


def kshellEntropySort(G):
    ksE = kshellEntropy(G)
    ksES = []
    ksIs = sorted(ksE.keys(), reverse=True)
    for ksI in ksIs:
        with open('iks/iks2_{}.txt'.format(ksI), 'w') as f:
            for k, v in ksE[ksI].items():
                f.writelines('{}: {}\n'.format(k, v))

        t = sorted([(v, k) for k, v in ksE[ksI].items()], reverse=True)

        # 把熵值一样的节点放在一个集合中
        t_new = {}
        for i in t:
            t_new.setdefault(i[0], list()).append(i[1])
        # 按熵值排序变成列表
        t = sorted([(k, v) for k, v in t_new.items()], reverse=True)

        # 把相同熵值的节点列表打乱顺序，相当于随机选择
        sub_ksES = []
        for i in t:
            if len(i[1]) == 1:
                sub_ksES += i[1]
            else:
                np.random.shuffle(i[1])
                sub_ksES += i[1]

        ksES.append(sub_ksES)
    #         ksES.append(list(i[1] for i in t))
    return ksES


def getRank(G):
    rank = []
    rankEntropy = kshellEntropySort(G)
    while (len(rankEntropy) != 0):
        for i in range(len(rankEntropy)):
            rank.append(rankEntropy[i].pop(0))
        while True:
            if [] in rankEntropy:
                rankEntropy.remove([])
            else:
                break
    return rank
