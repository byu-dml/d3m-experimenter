
# coding: utf-8

# In[17]:


import os, json, glob, csv
import pandas as pd
import numpy as np
os.environ['GLOG_minloglevel'] = '2' # Tell caffe to not be so verbose; this must be before caffe import
import caffe
from   caffe.proto import caffe_pb2
import numpy as np
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error as mse
import sys
from sklearn.linear_model import Ridge
import codecs, io
import warnings
warnings.filterwarnings('ignore')
from math import sqrt
from sklearn.model_selection import cross_val_score, ShuffleSplit, KFold
from d3mds import *
from collections import OrderedDict


# In[4]:

here = os.path.dirname(os.path.abspath(__file__))
rootDir = os.path.join(here, '..', '..')
dataDir = os.path.join(rootDir, '22_handgeometry_dataset')
assert os.path.exists(dataDir)
problemDir = os.path.join(rootDir, '22_handgeometry_problem')
assert os.path.exists(problemDir)
rawDir = os.path.join(dataDir, 'media')
assert os.path.exists(rawDir)

use_gpu = False
find_image_mean = True
exp_dim = 1024
debug = False


# In[5]:


def load_caffe_deephand_model():
	mean_blob = caffe_pb2.BlobProto()
	
	encoding = 'utf8'
	model_dir = os.path.join(here, '1miohands-modelzoo-v2')
	mFile = os.path.join(model_dir, '227x227-TRAIN-allImages-forFeatures-0label-227x227handpatch.mean')
	with io.open(mFile, 'r', encoding=encoding, newline='\n') as fin:
		mean_blob.ParseFromString(fin.read())
	mean_array = np.asarray(mean_blob.data, dtype=np.float32).reshape(
		(mean_blob.channels, mean_blob.height, mean_blob.width))

	# Initialize network from file
	net = caffe.Net(os.path.join(model_dir, 'submit-net.prototxt.v3'), 
					os.path.join(model_dir, '1miohands-v2.caffemodel'),
					caffe.TEST)

	# Initialize data transformer
	transformer = caffe.io.Transformer({'data': net.blobs['data'].data.shape})
	# transformer.set_mean('data', mean_array)
	transformer.set_transpose('data', (2,0,1)) # move image channels to outermost dimension
	transformer.set_channel_swap('data', (2,1,0)) # swap channels from RGB to BGR
	transformer.set_raw_scale('data', 255.0)
	net.blobs['data'].reshape(1,3,227,227)

	return net, transformer


# In[6]:


def find_mean_image(trainData):
	first_time = True
	s = 0.0
	for row in trainData.iterrows():
		im = caffe.io.load_image(os.path.join(rawDir, row[1].image_file))
		im_xform = transformer.preprocess('data', im)
		if first_time:
			s = im_xform
		else:
			s += im_xform
	s = (1.0/len(trainData))*s
	return s


# In[7]:


def image2vec (image_fn, net, transformer):
	# Load the image in the data layer
	im = caffe.io.load_image(image_fn)
	net.blobs['data'].data[...] = transformer.preprocess('data', im)
	out = net.forward()
	layer_vec = net.blobs['pool5/7x7_s1'].data  # get layer output at final stage before classification layer
	fv = layer_vec[0,:,0,0]
	return fv


# ## Build model on train data

# In[8]:


print('initiating pipeline ...')
d3mds = D3MDS(dataDir, problemDir) # this checks that the problem and dataset correspond


print('loading train data ...')
trainData = d3mds.get_train_data()
trainTargets = d3mds.get_train_targets()
# trainData = pd.read_csv(os.path.join(dataDir, 'trainData.csv'), index_col=0)
# trainTargets = pd.read_csv(os.path.join(dataDir, 'trainTargets.csv'), index_col=0)


# # In[10]:


# Set up GPU
if use_gpu:
	caffe.set_device(0)
	caffe.set_mode_gpu()


# In[11]:


# Initialize the cafe model and transformer
print('initializing the cafe model and transformer...')
net, transformer = load_caffe_deephand_model()


# In[12]:


print('finding mean image from training images...') 
if find_image_mean:
	mean_arr = find_mean_image(trainData)
	transformer.set_mean('data', mean_arr)


# In[23]:


print('featurizing train images...')
X_train = np.zeros([len(trainData), exp_dim])

for i1, row in enumerate(trainData.iterrows()):
	image_fn = os.path.join(rawDir, row[1].image_file)
	vec = image2vec(image_fn, net, transformer)
	X_train[i1,:] = vec


# In[25]:


y_train = trainTargets


# In[26]:


# Setup and perform regression
print('builidng model ...')
clf = SVR()


# In[38]:


print('performing 10-fold CV of the model on the training data...')
# splitpoint = int(len(X_train)*0.75)
# clf.fit(X_train[:splitpoint], y_train[:splitpoint])
# y_pred = clf.predict(X_train[splitpoint:])
# score = mse(y_train[splitpoint:], clf.predict(X_train[splitpoint:]))
# print('\tperformance on train/validation split:', score)
# testSize = int(len(X_train)*0.25)
cv = KFold(n_splits=10, shuffle=True, random_state=0)
scores = cross_val_score(clf, X_train, y_train, cv=cv, scoring='mean_squared_error')*-1


# In[39]:


print('performance (mean mse)', scores.mean())
print('performance OK, model selected ....')
train_performance = OrderedDict([
	('train', OrderedDict([
		('split', OrderedDict([
				('type', 'KFold'),
				('n_splits', 10),
				('shuffle', True),
				('random_state', 0)])
		),
		('score', OrderedDict([
				('metric', 'meanSquaredError'),
				('average', 'mean'),
				('value', scores.mean())])
		)
	]))
])


# In[40]:


print('training the model on the entire train data...')
clf.fit(X_train, y_train)


## Make predictions on test data

# In[41]:


print('making predictions on testData (assuming that testData is available) ...')
try:
	print('reading testData ...')
	testData = d3mds.get_test_data()
	
	print('featurizing test images ...')
	X_test = np.zeros([len(testData), exp_dim])

	for i1, row in enumerate(testData.iterrows()):
		image_fn = os.path.join(rawDir, row[1].image_file)
		vec = image2vec(image_fn, net, transformer)
		X_test[i1,:] = vec
		
	print('predicting target values ...')
	y_pred = clf.predict(X_test)
	
	targetCols = []
	targets = d3mds.problem.get_targets()
	for target in targets: targetCols.append(target['colName'])
	y_pred_df = pd.DataFrame(index=testData.index, data=y_pred, columns=targetCols)
	
	y_pred_df.to_csv(os.path.join(here, '..', 'predictions.csv'))
except:
	print('Looks like this is a redacted dataset. testData is unavailable. Cannot complete this step ...')


## Compute performance  on test data

# In[42]:


print('computing performance on testData (assuming the predictions is available) ...')
try:
	print('reading the truth...')
	testTargets = d3mds.get_test_targets()
	y_truth = testTargets
	err = mse(y_truth, y_pred)
	
	y_mean = y_train.mean()*np.ones(y_pred.shape)
	err_mean = mse(y_truth, y_mean)
	
	print('performance on test data...')
	print('regression mse:',err)
	print('predict mean mse:',err_mean)
	
	print('saving the performance score...')
	test_performance = OrderedDict([
		('test', OrderedDict([
			('score', OrderedDict([
					('metric', 'meanSquaredError'),
					('value', err)])
			)
		]))
	])
except:
	print('Looks like this is a redacted dataset. predictions is unavailable. cannot complete this step ...')


# In[43]:


overall_performance = OrderedDict()
overall_performance.update(train_performance)
overall_performance.update(test_performance)

with open(os.path.join(here, '..', 'scores.json'), 'w', encoding='utf-8') as f:
	json.dump(overall_performance, f, indent=2)
print(json.dumps(overall_performance, indent=2))


# In[ ]:



