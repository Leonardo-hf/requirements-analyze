import sys
from collections import defaultdict

import networkx as nx
import tqdm


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


def write_rank(res, name, dir='rank'):
    with open("{}/{}.txt".format(dir, name), 'w') as f:
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
    # print('{} fin!'.format(name))


def get_score(it, scores, blacklist):
    score = 0
    for i in it:
        if i[0] in blacklist or i[1] in blacklist:
            continue
        score += scores[i[0]][i[1]]
    return score


def between_vote(G, num=sys.maxsize):
    paths = nx.all_pairs_shortest_path(G)
    scores = {}
    total_score = 0
    total_num = 0
    between = defaultdict(list)
    for s, tp in paths:
        for t, path in tp.items():
            if len(path) <= 2:
                continue
            if s not in scores:
                scores[s] = {t: 1.0}
            else:
                scores[s][t] = 1.0
            total_num += 1
            total_score += len(path) - 2
            for i in range(1, len(path) - 1):
                between[path[i]].append((path[0], path[-1]))
    blacklist = set()
    f = total_num / total_score
    print(f)
    res = {}
    pro = tqdm.tqdm(total=min(num, len(between)), desc='进度')
    cnt = 0
    while len(between) != 0 and cnt < num:
        best = max(between.items(), key=lambda it: get_score(it[1], scores, blacklist))
        score = get_score(best[1], scores, blacklist)
        for s, t in best[1]:
            scores[s][t] = max(0, scores[s][t] - f)
        between.pop(best[0])
        res[best[0]] = score
        pro.update(1)
        blacklist.add(best[0])
        cnt += 1
    return res

# G = get_graph(source='files/pypi_v8.csv', min=0).reverse()
# r = nx.voterank(G, number_of_nodes=2000)
# write_rank(r, 'breadth', dir='rank')
# def get_together(a, b):
#     return len(set(map(lambda e: e[1], G.out_edges(a))).intersection(
#         set(map(lambda e: e[1], G.out_edges(b)))))


# graph = get_graph(source='files/pypi_v8.csv', min=0)
# res = []
# for node in tqdm.tqdm(graph.nodes, total=len(graph.nodes), desc='cal'):
#     _, _, sub = tree(node, graph)
#     if len(sub.nodes):
#         res.append((node, len(ci(sub, r=3)), len(sub.nodes)))
# res = sorted(res, key=lambda x: (-x[1], -x[2]))
# write_rank(res, 'ecosystem2')

