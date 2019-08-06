import pyflux as pf
from scipy.stats import randint as sp_randint
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np
import pandas as pd

class MultiIndexARIMA:
    """
    An implementation of multi-index version of ARIMA which operates on timeseries indexed by multiple levels.
    """
    
    def __init__(self, multiIndexCols, timecol, valuecol, ar_values=[1], ma_values=[1], integ_values=[0]):
        self.multiIndexCols = multiIndexCols
        self.timecol = timecol
        self.valuecol = valuecol
        self.ar_values = ar_values
        self.ma_values = ma_values
        self.integ_values = integ_values
        self.train_time_min = None
        self.train_time_max = None
        self.timecolType = None
        self.valuecolType = None
        self.model = {}
    
    def _timeSeries_integerTime_fillFrame(self, series, indexcols, timecol, valuecol, start, end):
        assert series[timecol].dtype==int
        assert type(start)==int and type(end)==int

        S_given = series.reset_index().set_index(timecol)
        valuecolType = S_given[valuecol].dtype
        S_std = pd.DataFrame(list(range(start, end-1)), columns=[timecol])
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

    def _timeSeries_dateTime_fillFrame(self, series, indexcols, timecol, valuecol, start, end):
        raise RuntimeError("This is not implemented yet!!")
        
    
    def _evaluate_arima_model(self, X, ar, ma, integ):
        train, test = X[:len(X)-65], X[len(X)-65:]
        history = train        
        model = pf.ARIMA(history, ar, ma, integ, family=pf.Normal())
        model_fit = model.fit('MLE')
        pred = model.predict(h=len(test))
        error = mean_squared_error(test, pred)
        return error
    
    def _search_arima_models(self, dataset):
        best_score, best_cfg = float("inf"), None
        for ar in self.ar_values:
            for ma in self.ma_values:
                for integ in self.integ_values:
                    mse = self._evaluate_arima_model(dataset, ar, ma, integ)
                    if mse < best_score:
                        best_score, best_cfg = mse, (ar, ma, integ)
        return best_cfg
        
    def fit (self, X_train, y_train, verbose=False):
        trainData = X_train.copy()
        trainData[self.valuecol] = y_train
        trainData.set_index(self.multiIndexCols, drop=True, inplace=True)
        
        # inferred information from train data
        self.train_time_min = int(trainData[self.timecol].min())
        self.train_time_max = int(trainData[self.timecol].max())
        self.timecolType = X_train[self.timecol].dtype
        self.valuecolType = y_train.dtype
        
        for i, (idx, df) in enumerate(trainData.groupby(level=[0,1])):
            cutoff = df[self.timecol].max()
            if self.timecolType == int:
                series = self._timeSeries_integerTime_fillFrame(df, 
                                                      self.multiIndexCols, 
                                                      self.timecol, 
                                                      self.valuecol, 
                                                      self.train_time_min, 
                                                      self.train_time_max)
            elif self.timecolType == pd.datetime:
                series = self._timeSeries_dateTime_fillFrame(df, 
                                                      self.multiIndexCols, 
                                                      self.timecol, 
                                                      self.valuecol, 
                                                      self.train_time_min, 
                                                      self.train_time_max)
            # plt.figure(figsize=(15,5))
            # plt.plot(series.index,series[self.valuecol])
            (ar, ma, integ) = self._search_arima_models(series)
            if verbose:
                print("series: %s, best_config: %s"%(i, (ar, ma, integ)))
            model = pf.ARIMA(series, ar, ma, integ, family=pf.Normal())
            self.model[idx] = (model, cutoff)
            model_fit = model.fit('MLE')
            
    def predict(self, X_test):
        testData = X_test.copy()
        testData.set_index(self.multiIndexCols, drop=True, inplace=True)
        predictions = []
        for i, (idx, df) in enumerate(testData.groupby(level=[0,1])):
            (M, cutoff) = self.model[idx]
            h = (df[self.timecol].max() - cutoff)+5
            predictions_df = pd.DataFrame(M.predict(h))
            predictions_df[self.valuecol] = predictions_df[self.valuecol].astype(self.valuecolType)
            predictions_df = pd.merge(left=df, right=predictions_df, left_on=self.timecol, right_index=True)
            try:
                assert len(df) == len(predictions_df)
            except:
                print(len(df), len(predictions_df))
                print(df)
                print(predictions_df)
                raise
            predictions.append(predictions_df)
        return pd.concat(predictions, axis=0)[self.valuecol].values
        