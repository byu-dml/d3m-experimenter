
# coding: utf-8
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score
from math import sqrt
from d3mds import D3MDataset, D3MProblem, D3MDS
import os, sys
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
import geohash
import category_encoders as ce
from sklearn.externals import joblib
import glob

here = here = os.path.dirname(os.path.abspath(__file__))
dspath = os.path.join(here, '..', '..', 'LL1_336_MS_Geolife_transport_mode_prediction_separate_lat_lon_dataset')
prpath = os.path.join(here, '..', '..', 'LL1_336_MS_Geolife_transport_mode_prediction_separate_lat_lon_problem')
ldfpath = os.path.join(dspath,'tables','learningData.csv')
solpath = os.path.join(here, '..')
assert os.path.exists(dspath)
assert os.path.exists(prpath)
assert os.path.exists(ldfpath)
preddir = os.path.join(here, 'predictions')
if not os.path.exists(preddir):
    os.mkdir(preddir)

d3mds = D3MDS(dspath, prpath)
CHUNK_SIZE = 10000
cat_cols = ['user_id', 'geohash']
category_encoder = ce.HashingEncoder(cols=cat_cols, n_components=8)
target_name='Transportation'
model = GaussianNB()
# all_labels = pd.read_csv(ldfpath, index_col=0)[target_name].unique()
all_labels = ['train','taxi','walk','bus','subway','airplane','car','bike','boat','run','motorcycle'] # obtained from above commented line

# ######## Experiment 1 #################

# if not os.path.exists(os.path.join(here,'trainData.csv')):
#     train_data = d3mds.get_train_data()
#     train_targets = d3mds.get_train_targets().ravel()
#     train_data[target_name] = train_targets
#     train_data.to_csv('trainData.csv')

# if not os.path.exists(os.path.join(here,'testData.csv')):
#     test_data = d3mds.get_test_data()
#     test_targets = d3mds.get_test_targets().ravel()
#     test_data[target_name] = test_targets
#     test_data.to_csv('testData.csv')

# def featurize_geoordinates(X):
#     LAT = X['lat_lon'].apply(lambda x: float(x.split(',')[0]))
#     LON = X['lat_lon'].apply(lambda x: float(x.split(',')[1]))
#     LAT_LON = pd.concat([LAT, LON], axis=1)
#     assert not LAT_LON.isnull().values.any() 
#     return LAT_LON.apply(geohash.encode, axis=1)

# def feature_engineer(df):
#     df.pop('date_time')
#     df.pop('track_id')   
#     df['geohash'] = featurize_geoordinates(df)
#     df.pop('lat_lon')
#     # feature hash the categorical columns
#     # print(df.head())
#     df = category_encoder.fit_transform(df)
#     # print(df.head())
#     return df

# if not os.path.exists(os.path.join(here, 'model.pkl')):
#     print('training a new model...')
#     count=0
#     for train_data in pd.read_csv(os.path.join(here, 'trainData.csv'), chunksize=CHUNK_SIZE, iterator=True, index_col=0):
#         print('train batch %s'%count)
#         train_df = train_data
#         featurized_train_df = feature_engineer(train_df)
#         print(train_data.shape)
#         print(featurized_train_df.shape)
        
#         X_train = featurized_train_df.reindex(columns=[x for x in featurized_train_df.columns.values if x != target_name])
#         y_train = featurized_train_df[target_name].ravel()
#         print(X_train.shape)
#         print(y_train.shape)
#         model.partial_fit(X_train, y_train, classes=np.unique(all_labels))
    
#         count+=1

#     joblib.dump(model, 'model.pkl') 
# else:
#     print('loading trained model...')
#     model = joblib.load(os.path.join(here, 'model.pkl')) 

# if not(os.path.exists(os.path.join(solpath, 'predictions.csv'))):
#     count=0
#     for test_data in pd.read_csv(os.path.join(here, 'testData.csv'), chunksize=CHUNK_SIZE, iterator=True, index_col=0):
#         print('test batch %s'%count)
#         test_df = test_data
#         featurized_test_df = feature_engineer(test_df)
#         print(test_df.shape)
#         print(featurized_test_df.shape)
        
#         X_test = featurized_test_df.reindex(columns=[x for x in featurized_test_df.columns.values if x != target_name])
#         print(X_test.shape)

#         y_truth = pd.DataFrame(featurized_test_df[target_name])
#         y_truth.to_csv(os.path.join(preddir, 'truths%s.csv'%count))
        
#         y_pred = pd.DataFrame(model.predict(X_test))
#         y_pred.index = X_test.index
#         y_pred.columns = [target_name]
#         y_pred.to_csv(os.path.join(preddir, 'predictions%s.csv'%count))
#         count+=1

#     filepaths = glob.glob(os.path.join(preddir, "predictions*.csv"))
#     pd.concat(map(pd.read_csv, filepaths)).to_csv(os.path.join(solpath, "predictions.csv"), index=None)
#     filepaths = glob.glob(os.path.join(preddir, "truths*.csv"))
#     pd.concat(map(pd.read_csv, filepaths)).to_csv(os.path.join(solpath, "truth.csv"), index=None)


# y_pred_df = pd.read_csv(os.path.join(solpath, 'predictions.csv'), index_col=0)
# y_pred = y_pred_df[target_name].ravel()
# y_truth_df = pd.read_csv(os.path.join(solpath, 'truth.csv'), index_col=0)
# y_truth = y_truth_df[target_name].ravel()
# acc = accuracy_score(y_truth, y_pred)
# print('accuracy score:', acc)

# # acc = 0.2268
# ########################################################################


######## Experiment 2 #################
def feature_engineer(df):
    df.pop('date_time')
    df.pop('track_id')
    
    users = df.pop('user_id')
    # one-hot-encode users
    users = pd.get_dummies(users)
    print(df.shape, users.shape)
    df = pd.concat([df, users], axis = 1)
    print(df.shape)
    
    print(df.head())
    return df

train_X = d3mds.get_train_data()
train_X = feature_engineer(train_X)
train_y = d3mds.get_train_targets().ravel()

clf = RandomForestClassifier(max_depth=5, random_state=42)
clf.fit(train_X, train_y)

test_X = d3mds.get_test_data()
test_X = feature_engineer(test_X)
pred_y = clf.predict(test_X)
truth_y = d3mds.get_test_targets().ravel()

accuracy = accuracy_score(truth_y, pred_y)
print('accuracy (model)', accuracy)
print('accuracy (random)', 1/len(set(train_y)))

targetCols = []
targets = d3mds.problem.get_targets()
for target in targets: targetCols.append(target['colName'])
y_pred_df = pd.DataFrame(index=d3mds.get_test_data().index, data=pred_y, columns=targetCols)
print(y_pred_df.head())
y_pred_df.to_csv(os.path.join(solpath, 'predictions.csv'))

df = pd.DataFrame(columns=['metric', 'value'])
df.loc[len(df)] = ['accuracy', accuracy]
df.to_csv(os.path.join(solpath, 'scores.csv'))

# acc = 0.5398
########################################################################