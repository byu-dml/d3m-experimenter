from __future__ import print_function, division

import pickle, random
import argparse
import os, sys
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
import node2vec
from gensim.models import Word2Vec
from sklearn import metrics, model_selection, pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

random.seed(42)
np.random.RandomState(seed=42)

# Default parameters from node2vec paper (and for DeepWalk)
default_params = {
    'log2p': 0,                     # Parameter p, p = 2**log2p
    'log2q': 0,                     # Parameter q, q = 2**log2q
    'log2d': 7,                     # Feature size, dimensions = 2**log2d
    'num_walks': 10,                # Number of walks from each node
    'walk_length': 80,              # Walk length
    'window_size': 10,              # Context size for word2vec
    'edge_function': "hadamard",    # Default edge function to use
    "prop_pos": 0.5,                # Proportion of edges to remove nad use as positive samples
    "prop_neg": 0.5,                # Number of non-edges to use as negative samples
                                    #  (as a proportion of existing edges, same as prop_pos)
}

edge_functions = {
    "hadamard": lambda a, b: a * b,
    "average": lambda a, b: 0.5 * (a + b),
    "l1": lambda a, b: np.abs(a - b),
    "l2": lambda a, b: np.abs(a - b) ** 2,
}

class GraphN2V(node2vec.Graph):
    def __init__(self,
                 nx_G=None, is_directed=False,
                 prop_pos=0.5, prop_neg=0.5,
                 workers=1,
                 random_seed=None):
        self.G = nx_G
        self.is_directed = is_directed
        self.prop_pos = prop_neg
        self.prop_neg = prop_pos
        self.wvecs = None
        self.workers = workers
        self._rnd = np.random.RandomState(seed=random_seed)

    def read_graph_edgelist(self, edgelist, enforce_connectivity=True, weighted=False, directed=False):
        '''
        Reads the input network in networkx.
        '''
        input = edgelist
        if weighted:
            G = nx.read_edgelist(input, nodetype=int, data=(('weight', float),), create_using=nx.DiGraph())
        else:
            G = nx.read_edgelist(input, nodetype=int, create_using=nx.DiGraph())
            for edge in G.edges():
                G.edges[edge[0],edge[1]]['weight'] = 1

        if not directed:
            G = G.to_undirected()

        # Take largest connected subgraph
        if enforce_connectivity and not nx.is_connected(G):
            G = max(nx.connected_component_subgraphs(G), key=len)
            print("Input graph not connected: using largest connected subgraph")

        # Remove nodes with self-edges
        # I'm not sure what these imply in the dataset
        for se in G.nodes_with_selfloops():
            G.remove_edge(se, se)

        print("Read graph, nodes: %d, edges: %d" % (G.number_of_nodes(), G.number_of_edges()))
        self.G = G

    def read_graph_gml(self, gml, enforce_connectivity=True, weighted=False, directed=False):
        '''
        Reads the input network in networkx from gml file.
        '''
        G = nx.read_gml(gml)

        if not directed:
            G = G.to_undirected()

        # Take largest connected subgraph
        if enforce_connectivity and not nx.is_connected(G):
            G = max(nx.connected_component_subgraphs(G), key=len)
            print("Input graph not connected: using largest connected subgraph")

        # Remove nodes with self-edges
        # I'm not sure what these imply in the dataset
        for se in G.nodes_with_selfloops():
            G.remove_edge(se, se)

        print("Read graph, nodes: %d, edges: %d" % (G.number_of_nodes(), G.number_of_edges()))
        self.G = G        

    def learn_embeddings(self, walks, dimensions, window_size=10, niter=5):
        '''
        Learn embeddings by optimizing the Skipgram objective using SGD.
        '''
        # TODO: Python27 only
        walks = [list(map(str, walk)) for walk in walks]
        model = Word2Vec(walks,
                         size=dimensions,
                         window=window_size,
                         min_count=0,
                         sg=1,
                         workers=self.workers,
                         iter=niter)
        self.wvecs = model.wv

    def get_selected_edges(self):
        edges = self._pos_edge_list + self._neg_edge_list
        labels = np.zeros(len(edges))
        labels[:len(self._pos_edge_list)] = 1
        return edges, labels

    def train_embeddings(self, p, q, dimensions, num_walks, walk_length, window_size):
        """
        Calculate nodde embedding with specified parameters
        :param p:
        :param q:
        :param dimensions:
        :param num_walks:
        :param walk_length:
        :param window_size:
        :return:
        """
        self.p = p
        self.q = q
        self.preprocess_transition_probs()
        walks = self.simulate_walks(num_walks, walk_length)
        self.learn_embeddings(
            walks, dimensions, window_size
        )

    def edges_to_features(self, edge_list, edge_function, dimensions):
        """
        Given a list of edge lists and a list of labels, create
        an edge feature array using binary_edge_function and
        create a label array matching the label in the list to all
        edges in the corresponding edge list

        :param edge_function:
            Function of two arguments taking the node features and returning
            an edge feature of given dimension
        :param dimension:
            Size of returned edge feature vector, if None defaults to
            node feature size.
        :param k:
            Partition number. If None use all positive & negative edges
        :return:
            feature_vec (n, dimensions), label_vec (n)
        """
        n_tot = len(edge_list)
        feature_vec = np.empty((n_tot, dimensions), dtype='f')

        # Iterate over edges
        for ii in range(n_tot):
            v1, v2 = edge_list[ii]

            # Edge-node features
            emb1 = np.asarray(self.wvecs[str(v1)])
            emb2 = np.asarray(self.wvecs[str(v2)])

            # Calculate edge feature
            feature_vec[ii] = edge_function(emb1, emb2)

        return feature_vec


here = os.path.dirname(os.path.abspath(__file__))
ddir = os.path.join(here, '..','..','59_LP_karate_dataset')
lddfpath = os.path.join(ddir, 'tables', 'learningData.csv')
assert os.path.exists(lddfpath)
graphpath = os.path.join(ddir, 'graphs', 'G.gml')
assert os.path.exists(graphpath)
pdir = os.path.join(here, '..','..','59_LP_karate_problem')
spdfpath = os.path.join(pdir, 'dataSplits.csv')
assert os.path.exists(spdfpath)

# Get the train edges, both positive and negative examples
lddf = pd.read_csv(lddfpath, index_col='d3mIndex')
spdf = pd.read_csv(spdfpath, index_col='d3mIndex')
spdf.drop(columns=['fold','repeat'], inplace=True)
lddf=pd.merge(left=lddf, right=spdf, left_index=True, right_index=True)
pos_edges = (lddf[
        (lddf['type']=='TRAIN') &
        (lddf['linkExists'] == 1)][['sourceNode','targetNode']])
pos_edges = ([tuple(i) for i in pos_edges.values.tolist()])
neg_edges = (lddf[
        (lddf['type']=='TRAIN') &
        (lddf['linkExists'] == 0)][['sourceNode','targetNode']])
neg_edges = ([tuple(i) for i in neg_edges.values.tolist()])

# create GraphN2V class instance from train gml
G = GraphN2V(random_seed=42)
G.read_graph_gml(graphpath)

# assign the positive and negative edges
G._pos_edge_list=pos_edges
G._neg_edge_list=neg_edges

p = 2.0**default_params['log2p']
q = 2.0**default_params['log2q']
dimensions = 2**default_params['log2d']
num_walks = default_params['num_walks']
walk_length = default_params['walk_length']
window_size = default_params['window_size']

# embed and get edge features
edges_train, labels_train = G.get_selected_edges()
G.train_embeddings(p, q, dimensions, num_walks, walk_length, window_size)
edge_features_train = G.edges_to_features(edges_train, lambda a, b: a * b, dimensions)
edges_test = (lddf[lddf['type']=='TEST'][['sourceNode','targetNode']])
test_index = edges_test.index
edges_test = ([tuple(i) for i in edges_test.values.tolist()])
edge_features_test = G.edges_to_features(edges_test, edge_functions['hadamard'], dimensions)

# Linear classifier
scaler = StandardScaler()
lin_clf = LogisticRegression(C=1, random_state=42)
clf = pipeline.make_pipeline(scaler, lin_clf)

# Train classifier
clf.fit(edge_features_train, labels_train)
y_pred=clf.predict(edge_features_test).astype(int)
print(y_pred)
print(y_pred.shape)
y_true = (lddf[lddf['type']=='TEST'][['linkExists']]).values.ravel()
accuracy = accuracy_score(y_true, y_pred)
print('accuracy on test data:', accuracy)

# saving the predictions.csv file
y_pred_df = pd.DataFrame(y_pred, index=test_index, columns=['linkExists'])
y_pred_df.to_csv(os.path.join(here, '..', 'predictions.csv'))

# saving the scores.csv file
df = pd.DataFrame(columns=['metric', 'value', 'randomState','fold'])
df.loc[len(df)] = ['accuracy', accuracy, 42, 0]
df.to_csv(os.path.join(here, '..', 'scores.csv'), index=None)
