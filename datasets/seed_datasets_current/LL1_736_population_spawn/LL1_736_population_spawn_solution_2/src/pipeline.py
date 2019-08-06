
import argparse
import glob
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import sys
import pickle
import numpy as np
import pandas as pd

from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import MinMaxScaler

import keras
from keras.models import Model, Sequential, load_model
from keras.layers import Dense, LSTM, InputLayer
from keras import backend as K

from d3mds import D3MDS


class LSTMTimeSeriesPredictor(object):
    def __init__(self, multi_index_cols, time_col, value_col, save_dir, num_epochs=20):
        self.multi_index_cols = multi_index_cols
        self.time_col = time_col
        self.value_col = value_col
        self.num_epochs = num_epochs
        self.model = None
        self.save_dir = save_dir
        self.model_dir = os.path.join(self.save_dir, 'models')
            
    def fit(self, X_train, y_train):
        data_train = self._pivot_train_data(X_train, y_train)
        last_day_info = self._compute_last_day_info(data_train)
        
        # Interpolate values
        data_train_interp = data_train.interpolate('index', axis=1, limit_direction='both', inplace=False)
        # Take the differences
        data_train_diff = self._diff_df(data_train_interp)
        # Build supervised dataset
        data_train_diff_shift = self._shift_df(data_train_diff)
        data_train_diff_full = pd.concat([data_train_diff_shift, data_train_diff], axis=1)

        # Scale data to [-1,1]
        scalers = self._build_scalers(data_train_diff_full)
        data_train_scaled = self._apply_scalers(data_train_diff_full, scalers)
        
        # Build lstm model
        self.model = self._build_lstm_model()
        
        # Train lstm model
        model_file = os.path.join(self.model_dir, 'lstm_model_%d_epochs.h5' % self.num_epochs)
        if os.path.exists(model_file):
            print('Pretrained model exists')
            print('Loading model %s' % model_file)
            self._load_prev_model(model_file)
        else:
            print('Training LSTM model')
            for e in range(self.num_epochs):
                print('On Epoch %d' % e)
                
                for i, (idx, df) in enumerate(data_train_scaled.groupby(level=[0,1])):
                    print('Processing series: ', idx)
                    print(last_day_info[idx])
                    last_ind = last_day_info[idx]['last_ind']
                    self._train_lstm(self.model, data_train_scaled.loc[idx][:, None],
                                     batch_size=1, nb_epoch=1, last_ind=last_ind)
                    
                self.model.save(model_file)

        # Save training data + (last_day_info, scalers) to .pkl file
        train_data_dict = {'data_train': data_train, 'data_train_scaled': data_train_scaled,
                           'scalers': scalers, 'last_day_info': last_day_info}        
        with open(os.path.join(self.save_dir, 'train_data.pkl'), 'wb') as f:
            pickle.dump(train_data_dict, f)
        
    def predict(self, X_test):
        data_test = X_test.copy()
        data_test.set_index(self.multi_index_cols, drop=True, inplace=True)

        preds_test = []
        for i, (idx, df) in enumerate(data_test.groupby(level=[0,1], sort=False)):
            for day in df['day']:
                #print(idx, day)
                pred = self.predict_single_ts(idx, day)
                #print(pred)
                preds_test.append(pred)                
      
        data_test.reset_index(inplace=True)
        
        return preds_test

    def predict_single_ts(self, idx, target_day):
        # Load training data + (last_day_info, scalers) from .pkl file
        data_train, data_train_scaled, scalers, last_day_info = self._load_train_dict(os.path.join(self.save_dir, 'train_data.pkl'))
        
        # forecast the entire training dataset to build up state for forecasting
        last_ind, last_day = last_day_info[idx]['last_ind'], last_day_info[idx]['last_day']

        df = data_train.loc[idx][0:last_ind+1]
        df_scaled = data_train_scaled.loc[idx][0:last_ind+1]
        #print(df_scaled)
        scaler = scalers[idx]

        self.model.reset_states()
        res = self.model.predict(df_scaled[:, None, None], batch_size=1)   

        if target_day <= last_day:        
            print('target_day less than last_day')
            target_ind = np.where(data_train.columns == target_day)[0]
            return res[target_ind]

        target_ind = last_ind+(target_day-last_day)
        #print(target_ind)
        for i in range(last_ind+1, target_ind+1):
            #print(res[-1])
            val = self.model.predict(res[-1][:, None, None], batch_size=1)
            #print(val)
            res = np.append(res, val[0])[:, None]

        res_inv_scale = scaler.inverse_transform(res)
        pred_train = df[:, None] + res_inv_scale[0:last_ind+1]
        remainder = (df.values[-1] + np.cumsum(res_inv_scale[last_ind+1:]))[:,None]
        return remainder[-1]
        
    def _load_train_dict(self, pkl_file):
        with open(pkl_file, 'rb') as f:
            d = pickle.load(f)
        return d['data_train'], d['data_train_scaled'], d['scalers'], d['last_day_info']
    
    def _load_prev_model(self, model_file):
        self.model.load_weights(model_file)
   
    def _pivot_train_data(self, X_train, y_train):
        data_train = X_train.copy()
        data_train[self.value_col] = y_train
        data_train = data_train.pivot_table(index=self.multi_index_cols,
                                            columns=self.time_col,
                                            values=self.value_col)
        return data_train
    
    def _compute_last_day_info(self, X_train):
        last_day_info = {}

        for i, (idx, df) in enumerate(X_train.groupby(level=[0,1])):
            #print(i, (idx, df))
            last_ind = np.where(X_train.notnull().iloc[i,:]==True)[0][-1]
            last_day =  X_train.columns[last_ind]

            last_day_info[idx] = {}
            last_day_info[idx]['last_ind'] = last_ind
            last_day_info[idx]['last_day'] = last_day
            
        return last_day_info
    
    # Create shifted form of each timeseries - (creates supervised version of timeseries problem)
    def _shift_df(self, df, lag=1):    
        shifted_df = df.shift(lag, axis=1)
        shifted_df.fillna(0, inplace=True)
        return shifted_df
    
    def _diff_df(self, df):
        df_diff = df.diff(periods=-1, axis=1)
        df_diff.fillna(0, inplace=True)
        return df_diff
    
    def _build_scalers(self, train_df):
        scalers = {}
        for i, (idx, df) in enumerate(train_df.groupby(level=[0,1])):
            #print(i, (idx, df))
            scaler = MinMaxScaler(feature_range=(-1, 1))
            scaler = scaler.fit(df.T)
            scalers[idx] = scaler

        return scalers
    
    def _apply_scalers(self, df_in, scalers):
        df_out = df_in.copy()
        for i, (idx, df) in enumerate(df_in.groupby(level=[0,1])):
            #print('before scale', df_in.loc[idx])
            df_out.loc[idx] = scalers[idx].transform(df_in.loc[idx].reshape(1,-1))
            #print('after scale', df_out.loc[idx])

        return df_out
    
    def _build_lstm_model(self, batch_size=1, num_time_steps=1, num_feat=1, neurons=5):
        model = Sequential()
        model.add(LSTM(neurons, batch_input_shape=(batch_size, num_time_steps, num_feat), stateful=True))
        model.add(Dense(1))
        opt = keras.optimizers.Adam(lr=1e-4)
        model.compile(loss='mae', optimizer=opt)
        return model

    def _train_lstm(self, model, train, batch_size, nb_epoch, last_ind):
        #TODO: hard-coded 304 (needs to be addressed)
        X, y = train[0:last_ind+1, 0:1], train[304:(304+last_ind+1), 0:1]
        print(X.shape, y.shape)
        X = X.reshape(X.shape[0], 1, X.shape[1])
        #print(X.shape)
        for i in range(nb_epoch):
            model.fit(X, y, epochs=1, batch_size=batch_size, verbose=1, shuffle=False)
            model.reset_states()
        return model


def write_predictions_csv_file(inds, preds, prediction_filename):
    df = pd.DataFrame(preds, index=inds, columns=['count'])
    df.to_csv(prediction_filename, index_label='d3mIndex')
    
def write_scores_csv_file(metric_dict, score_filename):
    metric_names = []
    metric_values = []
    for metric_name, metric_value in metric_dict.items():
        metric_names.append(metric_name)
        metric_values.append(metric_value)
    metric_names = np.array(metric_names)
    metric_values = np.array(metric_values)

    df = pd.DataFrame(np.concatenate((metric_names[:, None], metric_values[:, None]), axis=1), columns=['metric', 'value'])
    df.to_csv(score_filename, index=None)

def parse_args():
    parser = argparse.ArgumentParser(
        description='Script to train LSTM time series prediction pipeline on population_spawn dataset.')
    parser.add_argument('--dataset_root', dest='dataset_root',
                        help='Folder containing dataset to run pipeline.')
    parser.add_argument('--save_dir', dest='save_dir', default='./models/',
                        help='Location to load and save model files and training data.')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()

    # Fix random seed for reproducibility
    np.random.seed(42)
    #dataset_root = '../../'
    #model_dir = './models'
    dataset_root = args.dataset_root
    save_dir = args.save_dir

    data_path = glob.glob(os.path.join(dataset_root, "*_dataset"))[0]
    problem_path = glob.glob(os.path.join(dataset_root, "*_problem"))[0]
    d3mds = D3MDS(data_path, problem_path)

    print('Load train data')
    df_train = d3mds.get_train_data()
    targets_train = d3mds.get_train_targets()

    lstm_ts_predictor = LSTMTimeSeriesPredictor(multi_index_cols=['species', 'sector'], 
                                                time_col='day',
                                                value_col='count', 
                                                save_dir=save_dir)

    lstm_ts_predictor.fit(df_train, targets_train)

    print('Load test data')
    df_test = d3mds.get_test_data()
    targets_test = d3mds.get_test_targets()

    print('Generating predictions')
    preds_test = lstm_ts_predictor.predict(df_test)
    mae_test = mean_absolute_error(targets_test, preds_test)
    print('MAE test: ', mae_test)

    output_dir = './'
    print('Writing predictions to .csv file.')
    predictions_file = os.path.join(output_dir, 'predictions.csv')
    write_predictions_csv_file(df_test.index, preds_test, predictions_file)    

    print('Writing scores to .csv file.')
    metric_dict = {'meanAbsoluteError': mae_test}
    scores_file = os.path.join(output_dir, 'scores.csv')
    write_scores_csv_file(metric_dict, scores_file)
   