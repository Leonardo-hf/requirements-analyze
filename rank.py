import math
import os.path
import sys
from collections import defaultdict
from functools import reduce

import networkx as nx
import pandas
import pandas as pd
import tqdm

from ci import ci
from util import get_graph, get_depth, bfs, get_nodes


# warning! this algo will change G
def voterank(G: nx.DiGraph, num: int):
    res = []
    scores = {}
    if len(G) == 0:
        return res
    if num is None or num > len(G):
        num = len(G)
    # attenuation factor
    f = sum(deg for _, deg in G.in_degree) / len(G)
    # step 1 - initiate all nodes to (0,1) (score, voting ability)
    for n in G.nodes():
        scores[n] = [0, 1]
    # Repeat steps 1b to 4 until num_seeds are elected.
    for _ in tqdm.tqdm(range(num)):
        # step 1b - reset rank
        for n in G.nodes():
            scores[n][0] = 0
        # step 2 - vote
        for n, nbr in G.out_edges:
            # In directed graphs nodes only vote for their in-neighbors
            scores[n][0] += scores[nbr][1]
        # step 3 - select top node
        top = max(G.nodes, key=lambda x: scores[x][0])
        if scores[top][0] == 0:
            return res
        res.append((top, scores[top][0]))
        # step 4 - update voterank properties
        for nbr, _ in G.in_edges(top):
            scores[nbr][1] = max(scores[nbr][1] - 1 / f, 0)
        # step 5 - remove the top node
        G.remove_node(top)
    return res


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


def write_rank(res, name, dir):
    with open('{}/{}.csv'.format(dir, name), 'w') as f:
        if isinstance(res, pandas.DataFrame):
            for v in res.itertuples(index=False):
                f.write('{}\n'.format(','.join(map(lambda i: str(i), v))))
        elif isinstance(res, dict):
            rank = res.items()
            rank = sorted(rank, key=lambda r: r[1], reverse=True)
            for item in rank:
                f.write('{},{}\n'.format(item[0], item[1]))
        elif isinstance(res, (list, set)):
            for item in res:
                if isinstance(item, (list, tuple)):
                    f.write('{}\n'.format(','.join(map(lambda i: str(i), item))))
                else:
                    f.write('{}\n'.format(item))
        else:
            print('aa')
    # print('{} fin!'.format(name))


def between_vote(G: nx.DiGraph, num=sys.maxsize):
    def get_bv_score(it, scores, blacklist):
        score = 0
        for i in it:
            if i[0] in blacklist or i[1] in blacklist:
                continue
            score += scores[i[0]][i[1]]
        return score

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
        best = max(between.items(), key=lambda it: get_bv_score(it[1], scores, blacklist))
        score = get_bv_score(best[1], scores, blacklist)
        for s, t in best[1]:
            scores[s][t] = max(0, scores[s][t] - f)
        between.pop(best[0])
        res[best[0]] = score
        pro.update(1)
        blacklist.add(best[0])
        cnt += 1
    return res


def depth(G: nx.DiGraph):
    a_level = get_depth(G)
    res = []
    for k, v in tqdm.tqdm(a_level.items()):
        sub = bfs(k, G)
        score = reduce(lambda a, b: a + b, list(map(lambda n: a_level[n] - v, sub.nodes)))
        res.append((k, score))
    res = sorted(res, key=lambda i: -i[1])
    return res


def stable(G: nx.DiGraph, radius: int = 3):
    res = []
    for node in tqdm.tqdm(G.nodes, desc='stable'):
        sub = G.subgraph(bfs(node, G).nodes).copy().to_undirected()
        # print(node, len(sub.edges))
        res.append((node, len(ci(sub, r=radius)), len(sub.nodes)))

    def maxin(g):
        n_max = g.max()
        n_min = g.min()
        if n_max == n_min:
            n_max += 1
        return g.map(lambda i: (i - n_min) / (n_max - n_min))

    df = pd.DataFrame(res, columns=['node', 'ci', 'cnt'])
    df['score'] = df.groupby(['ci'])['cnt'].transform(maxin) + df['ci']
    return df.sort_values(by='score', ascending=False)[['node', 'score']]


def replace_id_2_name(file_rank, file_package):
    idmap = {}
    with open(file_package, 'r') as p:
        p.readline()
        for l in p:
            l = list(map(lambda i: i.strip(), l.split(',')))
            idmap[l[0]] = l[1]
    res = []
    with open(file_rank, 'r') as r:
        for l in r:
            l = list(map(lambda i: i.strip(), l.split(',')))
            l[0] = idmap[l[0]]
            res.append(l)
    write_rank(res, os.path.basename(file_rank).split('.')[0], os.path.dirname(file_rank))


def get_score(file_in):
    res = {}
    with open(file_in, 'r') as f:
        for line in f.readlines()[:2000]:
            line = line.strip().split(',')
            # res[line[0].strip()] = float(line[1].strip())
            res[line[0].strip()] = math.log(float(line[1].strip()))
    # u = sum(res.values()) / len(res.values())
    n_max = max(res.values())
    n_min = min(res.values())
    # fc = math.sqrt(sum(map(lambda x: math.pow(x - u, 2), res.values())) / len(res.values()))
    for k in res.keys():
        # res[k] = (res[k] - u) / fc
        res[k] = (res[k] - n_min) / (n_max - n_min)
        # res[k] /= u
    return res


def comprehensive(dir_in):
    size = 1000
    algos = ['breadth', 'depth', 'proxy', 'stable']
    scores = list(map(lambda a: get_score('{}/{}.csv'.format(dir_in, a)), algos))
    q = [52.887, 21.942, 9.656, 15.515]
    # q = np.random.dirichlet(np.ones(4), size=1)[0]
    nodes = reduce(lambda a, b: a.union(b),
                   list(map(lambda a: set(get_nodes('{}/{}.csv'.format(dir_in, a), number=size)), algos)))
    r = {}
    for node in nodes:
        score = 0
        for i in range(len(algos)):
            try:
                score += q[i] / 100 * scores[i][node]
            except:
                pass
                # score += q[i] / 100 * -1
        r[node] = score
    return r


ALGO_BREADTH = 'breadth'
ALGO_DEPTH = 'depth'
ALGO_PROXY = 'proxy'
ALGO_STABLE = 'stable'
ALGO_COMP = 'comprehensive'


def ranks_all(file_in, dir_out):
    # step1: breadth
    G = get_graph(file=file_in, k=0).reverse()
    r = voterank(G, num=2000)
    write_rank(r, ALGO_BREADTH, dir=dir_out)
    # step2: depth
    G = get_graph(file=file_in, k=0)
    r = depth(G)
    write_rank(r, ALGO_DEPTH, dir=dir_out)
    # step3: proxy
    G = get_graph(file=file_in, k=0)
    r = nx.betweenness_centrality(G)
    write_rank(r, ALGO_PROXY, dir=dir_out)
    # step4: ecology
    G = get_graph(file=file_in, k=0)
    r = stable(G)
    write_rank(r, ALGO_STABLE, dir=dir_out)
    # step5: comprehensive
    r = comprehensive(dir_in=dir_out)
    write_rank(r, ALGO_COMP, dir=dir_out)