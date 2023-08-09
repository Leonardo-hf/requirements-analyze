import heapq
import math
from collections import defaultdict
from typing import List

import networkx as nx
import tqdm

from util import tree


def _ci_score(graph: nx.DiGraph, node: str, r: int) -> int:
    return _ci_scores(graph, [node], r)[node]


def _ci_scores(graph, nodes, r) -> dict:
    deg = graph.in_degree
    scores = defaultdict(int)
    for node in nodes:
        score = 0
        borders = _borders(graph, node, r)
        for b in borders:
            score += deg[b] - 1
        scores[node] = score * (deg[node] - 1)
    return scores


def _borders(graph: nx.DiGraph, node: str, r: int) -> set:
    borders = set()
    _, _, sub = tree(node, graph, limit=r - 1)
    for s in sub.nodes:
        if graph.in_degree(s):
            borders.update(list(map(lambda n: n[1], graph.in_edges(s))))
    return borders


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


def ci(graph: nx.DiGraph, r: int = 3) -> dict:
    r_graph = graph.reverse()
    nodes = graph.nodes
    scores = _ci_scores(graph, nodes, r)
    heap = heapify(scores)
    modified = set()
    res = {}
    sum_scores = sum(scores.values())
    sum_degree = sum(map(lambda x: x[1], graph.in_degree))
    # proc = tqdm.tqdm(desc='ci_nodes')
    while math.pow(sum_scores / sum_degree, 1 / (r + 1)) > 1:
        top = heapq.heappop(heap)
        if top.name in modified:
            new_score = _ci_score(graph, top.name, r)
            sum_scores -= top.score - new_score
            heapq.heappush(heap, CINode(top.name, new_score))
            modified.remove(top.name)
            continue
        res[top.name] = top.score
        sum_scores -= top.score
        _, _, sub = tree(top.name, r_graph, r)
        # borders = _borders(r_graph, top.name, r)
        for s in sub:
            modified.add(s)
        graph.remove_node(top.name)
        r_graph.remove_node(top.name)
        # proc.update(1)
    return res
