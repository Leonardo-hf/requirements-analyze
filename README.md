# requirements-analyze
Code to analyze requirements relations between packages of different program language.

# structure

* get_packages_v3.py, get dependencies for all the different versions of python packages on the PYPI platform.
* get_packages_java.py, get dependencies for all the different versions of java packages on the MAVEN platform.
* get_packages_go.py, get dependencies for all the different versions of go packages on the GO PROXY.
* rank.py, build a directed graph using dependencies between packages and apply some centrality algorithm to rank packages.
* util.py, some utility functions to help build graphs, get the depth of packages, and get sorting results.
* ci.py, implements for collective centrality algorithm.