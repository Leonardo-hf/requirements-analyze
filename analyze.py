from __future__ import print_function, division

import pandas as pd
import networkx as nx
from networkx.drawing.nx_pydot import write_dot

import numpy as np


# %matplotlib inline

def draw():
    requirements = pd.read_csv('requirements.csv')
    DG = make_graph(requirements, min_edges=10)
    write_dot(DG, 'requirements_graph.dot')
    # dep_graph = make_graph(requirements, min_edges=0)
    # print(len(dep_graph.node))


def make_graph(df, min_edges=0):
    DG = nx.DiGraph()
    DG.add_nodes_from(df.package_name.unique())
    edges = df.loc[df.requirement.notnull(), ['package_name', 'requirement']].values
    DG.add_edges_from(edges)

    # Remove bad nodes
    DG.remove_nodes_from(['.', 'nan', np.nan])

    deg = DG.degree()
    to_remove = {key: value for key, value in deg if value <= min_edges}
    # to_remove = [n for n in deg if deg[n] <= min_edges]
    DG.remove_nodes_from(to_remove)
    return DG
