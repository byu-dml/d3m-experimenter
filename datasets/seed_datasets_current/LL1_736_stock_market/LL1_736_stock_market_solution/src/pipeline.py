# coding: utf-8

import os, sys, json
import pandas as pd
from d3mds import D3MDataset, D3MProblem, D3MDS
from multiIndexARIMA import MultiIndexARIMA
from sklearn.metrics import mean_absolute_error, mean_squared_error

# set the path and ensure that paths exist
here = os.path.dirname(os.path.abspath(__file__))
dspath = os.path.join(here, '..', '..', 'LL1_736_stock_market_dataset')
prpath = os.path.join(here, '..', '..', 'LL1_736_stock_market_problem')
solpath = os.path.join(here, '..')
assert os.path.exists(dspath)
assert os.path.exists(prpath)

# get train and test data
d3mds = D3MDS(dspath, prpath)
X_train = d3mds.get_train_data()
y_train = d3mds.get_train_targets()
X_test = d3mds.get_test_data()
y_test = d3mds.get_test_targets()

# initializa a MultiIndexARIMA model
m = MultiIndexARIMA(
  multiIndexCols=['Company','Year'],
  timecol='Date',
  timecolType='dateTime',
  timecolFormat='%m-%d',
  timedelta='days',
  valuecol='Close',
  ar_values=[1],
  ma_values=[1])

# Fit the model on the trian data
m.fit(X_train, y_train, verbose=True)

# Make a prediciton on the test data
y_pred = pd.DataFrame(m.predict(X_test))

# set the index and column headers for the predicted data
y_pred.index = X_test.index
y_pred.columns = [x['colName'] for x in d3mds.problem.get_targets()]

# compute the performance scores
scores = pd.DataFrame(columns=['metric','value'], data=[["meanAbsoluteError", mean_absolute_error(y_test.ravel(), y_pred)]])
print(scores)

# save the predictions and the scores file
y_pred.to_csv(os.path.join(here, '..', 'predictions.csv'))
scores.to_csv(os.path.join(here, '..', 'scores.csv'), index=None)

