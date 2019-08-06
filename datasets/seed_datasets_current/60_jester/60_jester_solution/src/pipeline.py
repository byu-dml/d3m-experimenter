
# coding: utf-8

# In[1]:


import pandas as pd
from surprise import Dataset, Reader, SVD, evaluate, SVDpp, NMF, SlopeOne, CoClustering
import os,sys, json, tempfile, io
from sklearn.metrics import mean_absolute_error
import numpy as np
from collections import OrderedDict


# In[2]:

here = os.path.dirname(os.path.abspath(__file__))

from d3mds import D3MDataset, D3MProblem, D3MDS

dspath = os.path.join(here, '..', '..', '60_jester_dataset')
prpath = os.path.join(here, '..', '..', '60_jester_problem')
solpath = os.path.join(here, '..')

assert os.path.exists(dspath)
assert os.path.exists(prpath)

d3mds = D3MDS(dspath, prpath) # this checks that the problem and dataset correspond

print('reading training data ...')
# trainData = pd.read_csv(os.path.join(dataDir, 'trainData.csv'), index_col=0)
# trainTargets = pd.read_csv(os.path.join(dataDir, 'trainTargets.csv'), index_col=0)
# traindf = pd.concat([trainData, trainTargets], axis=1)
# traindf.to_csv('mergedTrainDataTargets.csv', header=None, index=None)

trainData = d3mds.get_train_data()
trainTargets = pd.DataFrame(d3mds.get_train_targets(), index=trainData.index)
traindf = pd.concat([trainData, trainTargets], axis=1)
traindf.to_csv(os.path.join(here, 'mergedTrainDataTargets.csv'), header=None, index=None)

reader = Reader(line_format='user item rating', sep=',')

dataset = Dataset.load_from_file(os.path.join(here, 'mergedTrainDataTargets.csv'), reader=reader)


## Explore models on training data
print('exploring different algos on training data using 2-Fold CV...')

dataset.split(n_folds=2)
result1 = result2 = result3 = result4 = result5 = None

print('trying algo: SVD ...')
try:
    algo1 = SVD()
    result1 = evaluate(algo1, dataset, measures=['MAE'])
    # result1 = {'mae': [3.773, 3.777]}
    print(result1)
except:
    pass


print('trying algo: SVDpp ...')
try:
    algo2 = SVDpp()
    result2 = evaluate(algo2, dataset, measures=['MAE'])
#     result2 = {'mae': [3.880, 3.889]}
    print(result2)
except:
    pass


print('trying algo: NMF ...')
try:
    algo3 = NMF()
    result3 = evaluate(algo3, dataset, measures=['MAE'])
#     result3 = {'mae': [3.892, 3.886]}
    print(result3)
except:
    pass


print('trying algo: SlopeOne ...')
try:
    algo4 = SlopeOne()
    result4 = evaluate(algo4, dataset, measures=['MAE'])
#     result4 = {'mae': [3.756, 3.758]}
    print(result4)
except:
    pass


print('trying algo: CoClustering ...')
try:
    algo5 = CoClustering()
    result5 = evaluate(algo5, dataset, measures=['MAE'])
#     result5 = {'mae': [3.795, 3.797]}
    print(result5)
except:
    pass


results = [result1, result2, result3, result4, result5]
algos = [SVD(),SVDpp(),NMF(),SlopeOne(),CoClustering()]

scores = []
for s in results: 
    if s:
        scores.append(np.mean(s['mae']))
    else:
        scores.append(1000000.0)

print('choosing the best model for baseline...')
baseline = algos[np.argmin(scores)]
baselineScore = scores[np.argmin(scores)]
print('baseline model:', str(baseline))
print('baseline performance on 10-fold CV (mean MAE):', baselineScore)

print('training the baseline model on full training set ...')
# use the full dataset to train the model
trainset = dataset.build_full_trainset()
algo = baseline
algo.train(trainset)


## Make predictions on testData
print('===============================================================================')

def make_prediction(row, algo):
    user_id = str(row.user_id)
    item_id = str(row.item_id)
    # print(user_id, item_id)
    prediction = (algo.predict(user_id, item_id, r_ui=3.756))
    return prediction.est

print('making predictions on testData (assuming that testData is available) ...')

testData = d3mds.get_test_data()
testData['predicted_rating'] = testData.apply(make_prediction, algo=algo, axis=1)
y_pred = testData['predicted_rating'].tolist()

y_truth = d3mds.get_test_targets().ravel()
mae = mean_absolute_error(y_truth, y_pred)
print('MAE on test data:', mae)

# saving the predictions.csv file
y_pred_df = pd.DataFrame(index=testData.index, data=y_pred, columns=[target['colName'] for target in d3mds.problem.get_targets()])
y_pred_df.to_csv(os.path.join(solpath, 'predictions.csv'))

# saving the scores.csv file
df = pd.DataFrame(columns=['metric', 'value'])
df.loc[len(df)] = ['meanAbsoluteError', mae]
df.to_csv(os.path.join(solpath, 'scores.csv'))