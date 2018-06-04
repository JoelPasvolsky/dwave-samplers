import networkx as nx
import numpy as np
import scipy

from savanna.io.dimod import bqm_to_multigraph
from savanna.kasteleyn import kasteleyn
from savanna.planar import rotation_from_coordinates, plane_triangulate, odd_edge_orientation


def logsqrtdet(K):
    # now let's factor K
    PL, U = scipy.linalg.lu(K, permute_l=True)

    # assert np.linalg.det(PL) in (-1, 1), 'The contribution to the determinent of PL should be 1'
    # assert np.all(np.triu(U) == U), 'U should be upper triangular'

    return .5 * np.sum(np.log(np.absolute(np.diag(U))))


def log_partition_bqm(bqm, pos):

    if len(bqm) < 3:
        raise ValueError("bqm must have at least three variables")

    G, off = bqm_to_multigraph(bqm)

    # apply the rotation system
    r = rotation_from_coordinates(G, pos)
    nx.set_node_attributes(G, name='rotation', values=r)

    # triangulation
    plane_triangulate(G)

    # get the odd edge orientation
    orientation = odd_edge_orientation(G)
    nx.set_edge_attributes(G, name='oriented', values=orientation)

    # create an edge indexing scheme
    indices = {edge: idx for idx, edge in enumerate(G.edges(keys=True))}
    nx.set_edge_attributes(G, name='index', values=indices)

    # now build the Kasteleyn
    K = kasteleyn(G)

    return logsqrtdet(K) - sum(G.edges[e].get('weight', 0.0) for e in G.edges(keys=True)) - off
