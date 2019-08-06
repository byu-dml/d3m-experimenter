import os, sys, json, subprocess, time, threading
import numpy as np
import pandas as pd 
from d3mds import D3MDataset, D3MProblem, D3MDS
import networkx as nx
import d3m.metrics as metrics
from d3m.metrics import AverageMeanReciprocalRank as average_mrr
# from sklearn.metrics import accuracy_score
# from sklearn.metrics.cluster import normalized_mutual_info_score
# from sklearn.svm import SVC

here = os.path.dirname(os.path.abspath(__file__))
dspath = os.path.join(here, '..', '..', 'DS01876_dataset')
prpath = os.path.join(here, '..', '..', 'DS01876_problem')
solpath = os.path.join(here, '..')
graphpath = os.path.join(dspath, 'graphs')
assert os.path.exists(dspath)
assert os.path.exists(prpath)

G1 = nx.read_gml(os.path.join(graphpath, 'G1.gml'))
#d3mds = D3MDataset(dspath)
d3mds = D3MDS(dspath, prpath)

nodeIDs = nx.get_node_attributes(G1, 'nodeID')
nodeIDs = np.array(list(nodeIDs))

X_test = d3mds.get_test_data()
sources = X_test['sourceNodeID'].astype(str)
n = len(np.unique(sources))
id_map = dict(zip(nodeIDs, range(n)))

targets = X_test['targetNodeID'].astype(str)
unique_targets, indices = np.unique(targets, return_index=True)
unique_targets = [targets[index + 1] for index in sorted(indices)]
n_voi = len(unique_targets)

# Convert G to an adjacency matrix
A = nx.to_numpy_array(G1) > 0
A = A + A.T

ranks = np.zeros(n*n_voi)
for i, voi in enumerate(unique_targets):
    edges = np.sum(A[id_map[voi], :])
    
    if A[id_map[voi], id_map[voi]]:
        edges -= 1
    
    in_rank = np.mean(range(1, edges + 1))
    out_rank = np.mean(range(edges + 1, n))
        
    for j, id_ in enumerate(nodeIDs):
        if voi != id_:
            if A[id_map[voi],id_map[id_]]:
                ranks[i*n + j] = in_rank
            else:
                ranks[i*n + j] = out_rank
        else:
            ranks[i*n + j] = 0
            
X_test['rank'] = ranks
predictions = X_test[['rank']]

predictions.to_csv(os.path.join(solpath, 'predictions.csv'))

metric = d3mds.problem.get_performance_metrics()[0]['metric']
assert metric == 'average_mrr'
score = 0.0
truth = d3mds.get_data_all()
average_mrr_object = average_mrr()
score = average_mrr_object.score(truth, predictions)
print('average_mrr:', score)

# save the predictions and the score
targetCols = [col['colName'] for col in d3mds.problem.get_targets()]
y_pred_df = pd.DataFrame(index=X_test.index, data=predictions, columns=targetCols)
y_pred_df.to_csv(os.path.join(solpath, 'predictions.csv'))

scoresdf = pd.DataFrame(columns=['metric','value'])
scoresdf.loc[len(scoresdf)]=['average_mrr', score]
scoresdf.to_csv(os.path.join(solpath,'scores.csv'))