# requirements-analyze
Code to analyze requirements relations between packages of python from pypi.

# structure

* get_packages_v2.py, get the latest edition of each python package on Pypi.
* parse_v2.py, use requirements_detector to get all necessary dependencies of each package.
* rank.py, build a directed graph using dependencies between packages and apply some centrality algorithm to rank packages.
* sir.py, apply SIR model and linear_threshold in the graph mentioned above.
* tree.py, build a tree using the package's dependencies.
* venn.py, use Venn diagram to analyze the difference of sorting results of different algorithms.
* util.py, some utility functions to help build graphs, get the depth of packages, and get sorting results.