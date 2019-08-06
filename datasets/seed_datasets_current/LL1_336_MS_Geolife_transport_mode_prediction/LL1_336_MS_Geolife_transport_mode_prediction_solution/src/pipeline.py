
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score
from math import sqrt
from d3mds import D3MDataset, D3MProblem, D3MDS
import os, sys
from sklearn.ensemble import RandomForestClassifier

# In[2]:


here = here = os.path.dirname(os.path.abspath(__file__))
dspath = os.path.join(here, '..', '..', 'LL1_336_MS_Geolife_transport_mode_prediction_dataset')
prpath = os.path.join(here, '..', '..', 'LL1_336_MS_Geolife_transport_mode_prediction_problem')
solpath = os.path.join(here, '..')
assert os.path.exists(dspath)
assert os.path.exists(prpath)
d3mds = D3MDS(dspath, prpath)

def feature_engineer(df):
    df.pop('date_time')
    users = df.pop('user_id')
    # one-hot-encode users
    users = pd.get_dummies(users)
    print(df.shape, users.shape)
    df = pd.concat([df, users], axis = 1)
    print(df.shape)
    df.pop('track_id')
    df['lat'] = df['lat_lon'].apply(lambda x: float(x.split(',')[0]))
    df['lon'] = df['lat_lon'].apply(lambda x: float(x.split(',')[1]))
    df.pop('lat_lon')
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


sys.exit()



# **Process missing values**

# In[4]:


if pd.isnull(df).any().any():
    print('Found NaNs! Replacing NaNs with 0')
    df_nonan = df.fillna(0)
else:
    pass
df_nonan.head()


# **Process outliers**

# In[5]:


if pd.isnull(df_nonan.where(df_nonan>=0)).any().any():
    print('Found outliers! Person counts are less than 0. Replacing negative values with zeros')
    df_nooutliers = df_nonan.where(df>=0, 0)
df_nooutliers.head()


# **Diff the dataframes**
# 
# To check if the values are replaced correctly

# In[6]:


def compare_two_dfs(input_df_1, input_df_2):
    df_1, df_2 = input_df_1.copy(), input_df_2.copy()
    ne_stacked = (df_1 != df_2).stack()
    changed = ne_stacked[ne_stacked]
    changed.index.names = ['id', 'col']
    difference_locations = np.where(df_1 != df_2)
    changed_from = df_1.values[difference_locations]
    changed_to = df_2.values[difference_locations]
    df = pd.DataFrame({'from': changed_from, 'to': changed_to}, index=changed.index)
    return df

changes = compare_two_dfs(df_nonan, df_nooutliers)
print(changes.head())


# In[7]:


df = df_nooutliers


# **Filter data**
# 
# Problem required daily predictions for a particular location 'AQLP01'

# In[8]:


df = df[df['Location']=='AQLP01']
print(df.shape)
df.head()


# **Reindex dataframe in preparation for next step: Melt**

# In[9]:


df = df.set_index(['Reporting Group', 'Location', 'Date_Time'])
df.head()


# **Drop the extra RecordID column**

# In[10]:


_ = df.pop('RecordID')
df.head()


# **Perform Melt operation**

# In[11]:


def time_series_melt(df, index_col):
    col_map = {}
    for i, col in enumerate(df.columns):
        col_map['count_%s'%i]=col.strip()
    df.columns = list(col_map.keys())
    df1 = df.reset_index()
    df2 = pd.wide_to_long(df1, i=index_col, stubnames='count_',j='Category')
    return df2

df_melted = time_series_melt(df, index_col=['Reporting Group', 'Location', 'Date_Time'])


# In[12]:


df_melted


# **Aggregate data across categories**

# In[13]:


# aggregate across  categories
df_category_aggregated = df_melted.groupby(level=[0,1,2]).sum()
df_category_aggregated


# **Aggregate data from minutes to days**
# 
# Using the resample feature of pandas

# In[14]:


# Resample the times series from minutes to days
def resample_days(df, time_index_col, other_index_col, how='sum'):
    df = df.reset_index()
    df = df.set_index(time_index_col)
    
    # drop other index columns
    for col in other_index_col:
        df.pop(col)
        
    df = df.sort_index()
    df = df.resample('1D', how=how)
    return df

df_resampled = resample_days(df_category_aggregated, 'Date_Time', ['Reporting Group','Location'])
df_resampled


# **Train a model on this data**
# 
# This contains data upto 2017. The last entry is for 2016-12-30

# In[15]:


train_data = df_resampled.copy()


# In[16]:


# Initialize a forecasting model
model = pf.ARIMA(data=train_data, ar=4, ma=4, target='count_', family=pf.Normal())


# In[17]:


# fit the model to train data
x = model.fit("MLE")
x.summary()


# ** Make predictions for test data **

# In[18]:


test_targets = y_truth = d3mds.get_test_targets().ravel()
test_targets


# In[19]:


# how many points in the future to predict = len(test_targets)
N = len(test_targets)
# print(N)


# In[20]:


y_pred = model.predict(N).count_.tolist()
# print(y_pred)


# **Compute performance**

# In[21]:


score = sqrt(mean_squared_error(y_truth, y_pred))
print('RMSE', score)

targetCols = []
targets = d3mds.problem.get_targets()
for target in targets: targetCols.append(target['colName'])

y_pred_df = pd.DataFrame(index=d3mds.get_test_data().index, data=y_pred, columns=targetCols)
print(y_pred_df.head())

y_pred_df.to_csv(os.path.join(solpath, 'predictions.csv'))

df = pd.DataFrame(columns=['metric', 'value'])
df.loc[len(df)] = ['rootMeanSquaredError', score]
df.to_csv(os.path.join(solpath, 'scores.csv'))
