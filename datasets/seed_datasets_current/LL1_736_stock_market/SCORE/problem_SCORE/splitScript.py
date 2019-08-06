import os, sys
import pandas as pd 

ldfpath = sys.argv[1] # path to learningData.csv
dsfpath = sys.argv[2] # path to dataSplits.csv
assert os.path.exists(ldfpath)
ldf = pd.read_csv(ldfpath)
# print(ldf.head())
# print(ldf.tail())
ldf['month']=ldf['Date'].apply(lambda x: x.split('-')[1])
ldf['type']=['TRAIN']*len(ldf)
test_idx=(ldf[(ldf['month']=='12') | (ldf['month']=='11')].index)
ldf.loc[test_idx, 'type'] = 'TEST'
print(ldf[ldf['type']=='TRAIN'].shape, ldf[ldf['type']=='TEST'].shape)
ldf = ldf.drop(['Company', 'Year', 'Date', 'Close', 'month'], axis=1)
ldf['fold']=[0]*len(ldf)
ldf['repeat']=[0]*len(ldf)
ldf = ldf.set_index('d3mIndex')
print(ldf.head())
print(ldf.tail())
ldf.to_csv(dsfpath)
