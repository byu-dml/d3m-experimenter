
# coding: utf-8

# In[1]:


import os, sys, json
import pandas as pd
from d3mds import D3MDataset, D3MProblem, D3MDS
from multiIndexARIMA import MultiIndexARIMA
from sklearn.metrics import mean_absolute_error, mean_squared_error


# In[2]:


def in_jyputer_notebook():
   try:
       assert get_ipython().__class__.__name__=="ZMQInteractiveShell"
       return True
   except:
       return False

if in_jyputer_notebook(): 
   here = os.getcwd()
else:
   here = os.path.dirname(os.path.abspath(__file__))


# In[3]:


dspath = os.path.join(here, '..', '..', 'LL1_736_population_spawn_simpler_dataset')
prpath = os.path.join(here, '..', '..', 'LL1_736_population_spawn_simpler_problem')
solpath = os.path.join(here, '..')
assert os.path.exists(dspath)
assert os.path.exists(prpath)
d3mds = D3MDS(dspath, prpath)

X_train = d3mds.get_train_data()
y_train = d3mds.get_train_targets()
X_test = d3mds.get_test_data()
y_test = d3mds.get_test_targets()

print(X_train.shape, y_train.shape)
print(X_test.shape, y_test.shape)

# In[ ]:


# m = MultiIndexARIMA(multiIndexCols=['species','sector'], timecol='day', valuecol='count', ar_values=[1], ma_values=[1])
m = MultiIndexARIMA(multiIndexCols=['species','sector'], timecol='day', valuecol='count', ar_values=[1,2,3,4], ma_values=[1,2,3,4])
m.fit(X_train, y_train, verbose=True)


# In[5]:


y_pred = pd.DataFrame(m.predict(X_test))
y_pred.index = X_test.index
y_pred.columns = [x['colName'] for x in d3mds.problem.get_targets()]


# In[6]:


scores = pd.DataFrame(columns=['metric','value'], 
                      data=[["meanAbsoluteError", mean_absolute_error(y_test.ravel(), y_pred)]])


# In[7]:


y_pred.to_csv(os.path.join('..', 'predictions.csv'))
scores.to_csv(os.path.join('..', 'scores.csv'), index=None)

