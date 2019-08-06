
# coding: utf-8

import os, glob, json, sys
import pandas as pd 
from sklearn.feature_extraction import DictVectorizer
from sklearn import ensemble
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.model_selection import GridSearchCV
from collections import OrderedDict


here = os.path.dirname(os.path.abspath(__file__))

from d3mds import D3MDataset, D3MProblem, D3MDS

dspath = os.path.join(here, '..', '..', 'LL1_726_TIDY_GPS_carpool_bus_service_rating_prediction_dataset')
prpath = os.path.join(here, '..', '..', 'LL1_726_TIDY_GPS_carpool_bus_service_rating_prediction_problem')
solpath = os.path.join(here, '..')
assert os.path.exists(dspath)
assert os.path.exists(prpath)

d3mds = D3MDS(dspath, prpath) # this checks that the problem and dataset correspond

print('load in train data....')

# Load-in train data
trainData = d3mds.get_train_data()
# print(trainData.head())

# Load-in train target labels
trainTargets = d3mds.get_train_targets()

X_train = trainData.copy()
print('X_train.shape', X_train.shape)

print('performing featurization of train data .............')

non_pred_cols = ['id_trip', 'bus_company']
cat_cols = ['id_android', 'traffic','weather','car_or_bus']

# remove non-predictor cols
for col in non_pred_cols:
	X_train.pop(col)

# one-hot-encode
feats = []
for col in cat_cols:
	feats.append(pd.get_dummies(X_train[col]))

X_train = pd.concat(feats, axis=1)
print('X_train.shape after featurization', X_train.shape)


# Re-assign targets for scikit-learn
y_train = trainTargets.ravel()
print('unique target classes', set(y_train))

print('building Random Forest model on training data ...')

print('10-fold CV ...')

cv = StratifiedKFold(n_splits=2, random_state=42, shuffle=True)
parameters = {'n_estimators':[100]}
rfmodel = GridSearchCV(estimator=ensemble.RandomForestClassifier(class_weight="balanced"), 
					   param_grid=parameters, 
					   scoring='f1_macro', 
					   cv=cv)


rfmodel.fit(X_train,y_train)

rf_score = rfmodel.best_score_
print('RF accuracy score on 10 fold CV on training data:', rf_score)

print('making predicitons on test data ...')

testData = d3mds.get_test_data()
X_test = testData.copy()
print('X_test.shape', X_test.shape)

print('performing featurization of test data .............')

# remove non-predictor cols
for col in non_pred_cols:
	X_test.pop(col)

# one-hot-encode
feats = []
for col in cat_cols:
	feats.append(pd.get_dummies(X_test[col]))

X_test = pd.concat(feats, axis=1)
print('X_test.shape after featurization', X_test.shape)

y_pred = rfmodel.predict(X_test)

targetCols = []
targets = d3mds.problem.get_targets()
for target in targets: targetCols.append(target['colName'])
	
y_pred_df = pd.DataFrame(index=testData.index, data=y_pred, columns=targetCols)
# print(y_pred_df.head())

y_pred_df.to_csv(os.path.join(solpath, 'predictions.csv'))

print('computing performance on test data...')


testTargets =  d3mds.get_test_targets()
y_truth = testTargets.ravel()

# print(len(y_truth))
# print(len(y_pred))

f1_macro = f1_score(y_truth, y_pred, average='macro')
print('f1Macro score on test data', f1_macro)

df = pd.DataFrame(columns=['metric', 'value'])
df.loc[len(df)] = ['f1Macro', f1_macro]
df.to_csv(os.path.join(solpath, 'scores.csv'))
