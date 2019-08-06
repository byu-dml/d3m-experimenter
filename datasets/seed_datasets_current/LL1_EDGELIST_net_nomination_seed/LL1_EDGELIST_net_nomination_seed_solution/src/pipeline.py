
# coding: utf-8

# In[1]:


import os, sys, json, subprocess, time, threading
import pandas as pd 
from d3mds import D3MDataset, D3MProblem, D3MDS
import networkx as nx
from sklearn.metrics import accuracy_score
from sklearn.metrics.cluster import normalized_mutual_info_score
from sklearn.svm import SVC


# In[2]:


here = os.path.dirname(os.path.abspath(__file__))
dspath = os.path.join(here, '..', '..', 'LL1_EDGELIST_net_nomination_seed_dataset')
prpath = os.path.join(here, '..', '..', 'LL1_EDGELIST_net_nomination_seed_problem')
solpath = os.path.join(here, '..')
graphpath = os.path.join(dspath, 'graphs')
assert os.path.exists(dspath)
assert os.path.exists(prpath)


# In[44]:


# convert edgeList to graph
G1 = nx.Graph()
edf = pd.read_csv(os.path.join(graphpath, 'edgeList.csv'), index_col=0)
for i, row in edf.iterrows():
    v1 = int(row.V1_nodeID)
    v2 = int(row.V2_nodeID)
    G1.add_edge(v1, v2)

# add attributes to nodes of G1 
ldf = pd.read_csv(os.path.join(dspath, 'tables', 'learningData.csv'), index_col=0)
attr1_dict = {}
attr2_dict = {}
nodeid_dict = {}
for i, row in ldf.iterrows():
    nodeID = int(row.nodeID)
    attr1 = row.attr1
    attr2 = row.attr2
    attr1_dict[nodeID]=attr1
    attr2_dict[nodeID]=attr2
    nodeid_dict[nodeID]=nodeID
nx.set_node_attributes(G1, attr1_dict, 'attr1')
nx.set_node_attributes(G1, attr2_dict, 'attr2')
nx.set_node_attributes(G1, nodeid_dict, 'nodeID')
nx.write_gml(G1, 'G1.gml')


# In[45]:


G1 = nx.read_gml('G1.gml')
d3mds = D3MDS(dspath, prpath)


# In[58]:


# get the train data
X_train = d3mds.get_train_data()
X_train.pop('nodeID')
print('X_train.shape', X_train.shape)
y_train = d3mds.get_train_targets().ravel()
print('y_train.shape', y_train.shape)


# In[59]:


# train a simple baseline classifier that only considers the node attributes
# We are ignoring the relational data (connections between the nodes)
clf = SVC()
clf.fit(X_train, y_train)


# In[62]:


# get the test data
X_test = d3mds.get_test_data()
X_test.pop('nodeID')
print('X_test.shape', X_test.shape)
# make a prediction on the test data
y_pred = clf.predict(X_test)


# In[63]:


# get the true test targets
y_truth = d3mds.get_test_targets().ravel()


# In[64]:


# compute the performance score on test data
metric = d3mds.problem.get_performance_metrics()[0]['metric']
assert metric == 'accuracy'
score = 0.0
score = accuracy_score(y_truth, y_pred)
print('accuracy score:', accuracy_score(y_truth, y_pred))

