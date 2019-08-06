import os, sys, json
import pandas as pd
from collections import OrderedDict
from sklearn.model_selection import train_test_split, StratifiedShuffleSplit, ShuffleSplit
import numpy as np

ldfpath = sys.argv[1] # path to learningData.csv
dsfpath = sys.argv[2] # path to dataSplits.csv
assert os.path.exists(ldfpath)
assert os.path.exists(dsfpath)

# here = os.path.dirname(os.path.abspath(__file__)) # _ignore
# ldfpath = os.path.join(here, '..','LL1_336_MS_Geolife_transport_mode_prediction_dataset','tables','learningData.csv')
# dsfpath = os.path.join(here, 'dataSplits.csv')

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
TEST_SIZE = 0.33
target_col = 'Transportation'
CHUNK_SIZE = 1000

tables = []
for lddf in pd.read_csv(ldfpath, chunksize=CHUNK_SIZE, iterator=True, index_col='d3mIndex'):
	lddf['type'] = ['TRAIN']*len(lddf)
	X = lddf.copy()
	y = pd.DataFrame(lddf.pop(target_col))
	try:
		sss = StratifiedShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=RANDOM_SEED)
		for train_index, test_index in sss.split(X, y):
			for i in test_index:
				lddf.iloc[i, lddf.columns.get_loc('type')] = 'TEST'
	except:
		sss = ShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=RANDOM_SEED)
		for train_index, test_index in sss.split(X, y):
			for i in test_index:
				lddf.iloc[i, lddf.columns.get_loc('type')] = 'TEST'

	for col in lddf.columns:
		if col != 'type':
			lddf.pop(col)
	
	lddf['repeat']=[0]*(len(lddf))
	lddf['fold']=[0]*(len(lddf))
	tables.append(lddf)

splitsdf = pd.concat(tables)
splitsdf.to_csv(dsfpath)