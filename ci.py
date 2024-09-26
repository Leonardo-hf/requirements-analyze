import heapq
import math
from functools import reduce
from typing import List

import networkx as nx
import tqdm

from util import bfs


class CINode(object):
    def __init__(self, name, score):
        self.name = name
        self.score = score

    def __gt__(self, other):
        return self.score < other.score

    def __lt__(self, other):
        return not self.__gt__(other)

    def __eq__(self, other):
        return self.score == other.score


def heapify(scores: dict) -> List[CINode]:
    ci_nodes = []
    for k, v in scores.items():
        ci_nodes.append(CINode(k, v))
    heapq.heapify(ci_nodes)
    return ci_nodes


def ci(graph: nx.Graph, r: int = 3) -> []:
    scores = _ci_scores(graph, list(graph), r)
    heap = heapify(scores)
    modified = set()
    res = []
    sum_scores = sum(scores.values())
    sum_degree = sum(map(lambda x: x[1], graph.degree))
    # 判断图是否被破坏
    while sum_degree != 0 and math.pow(sum_scores / sum_degree, 1 / (r + 1)) > 1:
        top = heapq.heappop(heap)
        # 删除节点对其他节点的 CI 值造成影响，此处做延迟修改
        if top.name in modified:
            new_score = _ci_score(graph, top.name, r)
            sum_scores -= top.score - new_score
            heapq.heappush(heap, CINode(top.name, new_score))
            modified.remove(top.name)
            continue
        print(sum_scores, sum_degree, top.name, top.score)
        res.append((top.name, top.score))
        sum_scores -= top.score

        # 删除节点，对距离在 r 之内的节点的 CI 值造成影响，将之标记
        sub = bfs(top.name, graph, r)
        for s in sub:
            modified.add(s)
        # 删除节点
        graph.remove_node(top.name)
        # 重新计算 sum_degree
        sum_degree = sum(map(lambda x: x[1], graph.degree))
    return res


def _ci_score(graph: nx.Graph, node: str, r: int) -> int:
    return _ci_scores(graph, [node], r)[node]


def _ci_scores(graph: nx.Graph, nodes, r) -> dict:
    deg = graph.degree
    scores = {}
    node_iter = nodes
    if len(nodes) > 1:
        node_iter = tqdm.tqdm(nodes)
    for node in node_iter:
        # 查看与目标节点距离为 r 的所有节点
        s = list(filter(
            lambda i: i[1] == 3, nx.single_target_shortest_path_length(graph, node, cutoff=r)))
        if len(s) == 0:
            scores[node] = 0
            continue
        score = reduce(lambda a, b: a + b, map(lambda t: deg[t[0]] - 1, s))
        scores[node] = (deg[node] - 1) * score
    return scores
