import pyflux as pf
from scipy.stats import randint as sp_randint
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np
import pandas as pd
import sys
from datetime import datetime

class MultiIndexARIMA:
    """
    An implementation of multi-index version of ARIMA which operates on timeseries indexed by multiple levels.
    """
    
    def __init__(self, 
        multiIndexCols, # required
        timecol, # required
        timecolType, # required (currently only 'integer' or 'dateTime' are supported)
        timecolFormat, # required only if timecolType is 'dateTime'
        timedelta, # required only if timecolType is 'dateTime'
        valuecol, # required
        ar_values=[1], 
        ma_values=[1], 
        integ_values=[0]):
        
        self.multiIndexCols = multiIndexCols
        self.timecol = timecol
        self.timecolType = timecolType
        self.timecolFormat = timecolFormat
        self.timedelta = timedelta
        self.valuecol = valuecol
        self.ar_values = ar_values
        self.ma_values = ma_values
        self.integ_values = integ_values
        
        self.train_time_min = None
        self.train_time_max = None
        self.valuecolType = None
        self.model = {}
    
    def _timeSeries_fillFrame(self, series, indexcols, timecol, timecolType, valuecol, start, end):
        """
        Standardization of the input time series by filling in the missing values
        """
        S_given = series.reset_index().set_index(timecol)
        valuecolType = S_given[valuecol].dtype

        if timecolType == 'integer':
            S_std = pd.DataFrame(list(range(start, end-1)), columns=[timecol])
        elif timecolType == 'dateTime':
            S_std = pd.DataFrame(pd.date_range(start, end), columns=[timecol])
        
        S_std = S_std.join(S_given, on=timecol)
        
        for col in S_std.columns:
            if col != valuecol:
                S_std[col] = S_std[col].fillna(method='bfill')
                S_std[col] = S_std[col].fillna(method='ffill')
            else:
                S_std[valuecol] = S_std[valuecol].interpolate(method='linear', limit_direction='both')
                S_std[valuecol] = S_std[valuecol].astype(valuecolType)
        
        series = S_std[[self.timecol, self.valuecol]]
        series.set_index(self.timecol, drop=True, inplace=True)
        return series
    
    def _evaluate_arima_model(self, X, ar, ma, integ):
        """
        Evaluate ARIMA model using MAE. Used for grid search of ARIMA models.
        """
        train, test = X[:len(X)-65], X[len(X)-65:]
        history = train        
        model = pf.ARIMA(history, ar, ma, integ, family=pf.Normal())
        model_fit = model.fit('MLE')
        pred = model.predict(h=len(test))
        error = mean_squared_error(test, pred)
        return error
    
    def _search_arima_models(self, dataset):
        """
        Simple grid search of ARIMA models
        """
        best_score, best_cfg = float("inf"), None
        for ar in self.ar_values:
            for ma in self.ma_values:
                for integ in self.integ_values:
                    mse = self._evaluate_arima_model(dataset, ar, ma, integ)
                    if mse < best_score:
                        best_score, best_cfg = mse, (ar, ma, integ)
        return best_cfg

    def _to_time(self, d):
        """
        Convert string to time format
        """
        try:
            return datetime.strptime(d, self.timecolFormat)
        except:
            return np.nan

        
    def fit (self, X_train, y_train, verbose=False):
        """
        Fit a multiIndexARIMA model to the input training data.
        """
        trainData = X_train.copy()       
        trainData[self.valuecol] = y_train
        trainData.set_index(self.multiIndexCols, drop=True, inplace=True)

        ## column type adjustments ###############
        if self.timecolType == 'dateTime':
            trainData[self.timecol] = trainData[self.timecol].apply(lambda d: self._to_time(d))
        elif self.timecolType == 'integer':
            trainData[self.timecol] = trainData[self.timecol].astype(int)
        else:
            raise RuntimeError("time column type not recognized. Only integer and dateTime types are currently supported!")
        self.valuecolType = y_train.dtype
        ## end column type adjustments ###############

        ## drop rows with missing values in time col
        trainData.dropna(subset=[self.timecol], inplace=True)

        # inferred min and max information from train data
        self.train_time_min = trainData[self.timecol].min()
        self.train_time_max = trainData[self.timecol].max()
                
        # for each sub-group series develop models
        for i, (idx, df) in enumerate(trainData.groupby(level=[0,1])):
            cutoff = df[self.timecol].max() # determine cutoff for that sub-group series
            
            series = self._timeSeries_fillFrame( # standardization and fill in missing values
                df,
                self.multiIndexCols,
                self.timecol,
                self.timecolType,
                self.valuecol,
                self.train_time_min,
                self.train_time_max) 
            
            (ar, ma, integ) = self._search_arima_models(series) # grid search ARMIMA models to find best config
            if verbose: print("series: %s, best_config: %s"%(i, (ar, ma, integ)))
            
            # train the model with best config and store the model along with the cutoff
            model = pf.ARIMA(series, ar, ma, integ, family=pf.Normal())
            self.model[idx] = (model, cutoff)
            model_fit = model.fit('MLE')
            
    def predict(self, X_test):
        """
        Make a prediciton on test data using the trained multiIndexARIMA model
        """
        testData = X_test.copy()
        testData.set_index(self.multiIndexCols, drop=True, inplace=True)

        ## column type adjustments ###############
        if self.timecolType == 'dateTime':
            testData[self.timecol] = testData[self.timecol].apply(lambda d: self._to_time(d))
        elif self.timecolType == 'integer':
            testData[self.timecol] = testData[self.timecol].astype(int)
        else:
            raise RuntimeError("time column type not recognized. Only integer and dateTime types are currently supported!")
        ## end column type adjustments ###############

        predictions = [] # collection of predictions for each sub-group series
        
        # for each sub-group series, retrieve the respective model and make predictions
        for i, (idx, df) in enumerate(testData.groupby(level=[0,1])):
            (M, cutoff) = self.model[idx] # retrieve the model and cutoff point
            
            ### determine h - the number of steps in future to predict for this sub-group series
            h = None
            if self.timecolType == 'integer':
                h = (df[self.timecol].max() - cutoff)+5
            elif self.timecolType == 'dateTime':
                diff = df[self.timecol].max()-cutoff 
                h = (eval('diff.%s'%self.timedelta))+5
            if h is None:
                raise RuntimeError('could not determine h (how many steps to predict in future)!')

            # make predictions
            predictions_df = pd.DataFrame(M.predict(h))
            # set the correct type for the predicted column
            predictions_df[self.valuecol] = predictions_df[self.valuecol].astype(self.valuecolType)
            # join the df and predictions to obtain only the resuired predicion points
            predictions_df = pd.merge(left=df, right=predictions_df, left_on=self.timecol, right_index=True)
            
            #### sanity check ###
            try:
                assert len(df) == len(predictions_df)
            except:
                print(len(df), len(predictions_df))
                print(df)
                print(predictions_df)
                raise
            #### end sanity check ###

            predictions.append(predictions_df) # add predictions of this series to the collection of predicitons
        
        return pd.concat(predictions, axis=0)[self.valuecol].values # concat all the predictions and return
        