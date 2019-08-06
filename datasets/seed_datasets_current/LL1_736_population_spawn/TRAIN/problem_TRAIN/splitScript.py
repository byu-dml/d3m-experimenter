import os, sys
import pandas as pd 

ldfpath = sys.argv[1] # path to learningData.csv
dsfpath = sys.argv[2] # path to dataSplits.csv

# here = os.path.dirname(os.path.abspath(__file__))
# ldfpath = os.path.join(here, '..','LL1_736_population_spawn_dataset','tables','learningData.csv')
# dsfpath = os.path.join(here, 'dataSplits.csv')
assert os.path.exists(ldfpath)
assert os.path.exists(dsfpath)

ldf = pd.read_csv(ldfpath)

# print(ldf.head())
# print(ldf.tail())
test_index = []
for grp in ldf.groupby(['species','sector']):
	days_original = (grp[1]['day']).copy()
	days_sorted = days_original.sort_values(ascending=True)
	assert (days_original.equals(days_sorted))
	test_index.extend(grp[1].tail()[-2:].d3mIndex.values)

ldf['type']=['TRAIN']*len(ldf)
ldf.loc[test_index, 'type'] = 'TEST'

print(ldf[ldf['type']=='TRAIN'].shape, ldf[ldf['type']=='TEST'].shape)
ldf = ldf.drop(columns=['species', 'sector', 'day', 'count'], axis=1)
ldf['fold']=[0]*len(ldf)
ldf['repeat']=[0]*len(ldf)
ldf = ldf.set_index('d3mIndex')
print(ldf.head())
print(ldf.tail())
ldf.to_csv(dsfpath)
