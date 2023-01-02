import sys

from matplotlib import pyplot as plt
from matplotlib_venn import venn2, venn2_circles, venn3, venn3_circles

from pypi.util import get_50_nodes


def draw_venn(items):
    sets = []
    for item in items:
        sets.append(set(get_50_nodes(item)))
    plt.rcParams['font.family'] = ["Times New Roman"]
    fig, ax = plt.subplots(figsize=(5, 3), dpi=110)
    if len(items) == 2:
        vee = venn2(sets, set_labels=items, alpha=0.8, ax=ax)
        venn2_circles(sets, linestyle="--", linewidth=2, color="black", ax=ax)
    elif len(items) == 3:
        vee = venn3(sets, set_labels=items, alpha=0.8, ax=ax)
        venn3_circles(sets, linestyle="--", linewidth=2, color="black", ax=ax)
    else:
        print('only support 2~3 groups!')
        return
    for text in vee.set_labels:
        text.set_fontsize(15)
    for text in vee.subset_labels:
        text.set_fontsize(16)
        text.set_fontweight("bold")
    plt.title("{}".format(items), size=15, fontweight="bold",
              backgroundcolor="#868686FF", color="black", style="italic")
    plt.show()


def get_intersection(items):
    sets = []
    for item in items:
        sets.append(set(get_50_nodes(item)))
    inter = sets[0]
    for i in range(1, len(sets)):
        inter = inter.intersection(sets[i])
    return inter


def get_2_diff(first, second):
    f = set(get_50_nodes(first))
    s = set(get_50_nodes(second))
    a = f.difference(s)
    b = s.difference(f)
    print('diff {} from {}, {}'.format(first, second, a))
    print('diff {} from {}, {}'.format(second, first, b))
    return a, b


if __name__ == '__main__':
    l = ['pagerank', 'local-centrality']
    all = ['pagerank', 'betweenness', 'degree', 'voterank', 'closeness', 'local-centrality']
    res = []
    draw_venn(l)
    get_2_diff('local-centrality', 'pagerank')
    # print(get_intersection(all))
    sys.exit()
    for i in range(0, len(all)):
        for p in range(i + 1, len(all)):
            t = get_intersection([all[i], all[p]])
            tt = ''
            for q in t:
                tt = tt + q + ' '
            res.append(('{}-{}, {}%, {}, {}'.format(all[i], all[p], len(t) * 2, len(t), tt), len(t)))
    res.sort(key=lambda r: r[1])
    for r in res:
        print(r[0])
# draw_venn(l)
# print(get_intersection(all))
