# -*- coding: utf-8 -*-
"""tcc_pedro_castro.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1PE5d4WCfE1-lq6QUe-zamdJ2rfaPZlO1
"""

from numpy import array,mean
import torch
import gc
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import seaborn as sns
import sklearn.metrics as skl 
from torch.utils.data import TensorDataset
import sys
import getopt
import logging, argparse, time
from typing import List

"""# Arquiteturas

## NetRegression
"""


class NetRegression(nn.Module):
    def __init__(self, in_channels):
        super(NetRegression,self).__init__()
        
        self.conv1d_1 = nn.Conv1d(in_channels = in_channels, out_channels = 32, kernel_size = 3, padding=2)
        self.gn_1 = nn.GroupNorm(1, 32)

        self.conv1d_2 = nn.Conv1d(in_channels = 32, out_channels = 64, kernel_size = 3, padding=2)
        self.gn_2 = nn.GroupNorm(1, 64)

        self.conv1d_3 = nn.Conv1d(in_channels = 64, out_channels = 64, kernel_size = 3, padding=2)
        self.gn_3 = nn.GroupNorm(1, 64)

        self.conv1d_4 = nn.Conv1d(in_channels = 64, out_channels = 128, kernel_size = 3, padding=2)
        self.gn_4 = nn.GroupNorm(1, 128)

        # self.conv1d_5 = nn.Conv1d(in_channels = 64, out_channels = 64, kernel_size = 3, padding=2)
        # self.conv1d_6 = nn.Conv1d(in_channels = 64, out_channels = 128, kernel_size = 3, padding=2)
        # self.conv1d_7 = nn.Conv1d(in_channels = 128, out_channels = 128, kernel_size = 3, padding=2)
        # self.conv1d_8 = nn.Conv1d(in_channels = 128, out_channels = 256, kernel_size = 3, padding=2)

        self.max_pooling1d_1 = nn.MaxPool1d(2)
        # self.max_pooling1d_2 = nn.MaxPool1d(2)

        # self.relu = nn.ReLU()
        self.relu = nn.GELU()
        
        self.fc1 = nn.Linear(1280,50)

        self.fc2 = nn.Linear(50,1)
        self.fc2.bias.data.fill_(y_mean_value)

        # self.dropout = nn.Dropout(0.25)

    def forward(self,x):
        x = self.conv1d_1(x)
        x = self.gn_1(x)
        x = self.relu(x)

        # print('conv1d_1')

        x = self.max_pooling1d_1(x)

        x = self.conv1d_2(x)
        x = self.gn_2(x)
        x = self.relu(x)

        # print('conv1d_2')

        x = self.conv1d_3(x)
        x = self.gn_3(x)
        x = self.relu(x)

        # print('conv1d_3')

        x = self.conv1d_4(x)
        x = self.gn_4(x)
        x = self.relu(x)

        # print('conv1d_4')

        # x = self.conv1d_5(x)
        # x = self.relu(x)

        # # print('conv1d_5')

        # x = self.max_pooling1d_1(x)

        # x = self.conv1d_6(x)
        # x = self.relu(x)

        # x = self.conv1d_7(x)
        # x = self.relu(x)

        # x = self.conv1d_8(x)
        # x = self.relu(x)

        # # print('conv1d_8')

        x = x.view(x.shape[0], -1)
        # x = self.dropout(x)
        
        x = self.fc1(x)
        x = self.relu(x)
        # x = self.dropout(x)
        
        x = self.fc2(x)
        x = self.relu(x)

        return x
  
    def validation_step(self, batch):
        X_train, y_train = batch 
        out = self(X_train)                    # Generate predictions
        loss = F.cross_entropy(out, y_train)   # Calculate loss
        acc = accuracy(out, y_train)           # Calculate accuracy
        return {'val_loss': loss, 'val_acc': acc}
        
    def validation_epoch_end(self, outputs):
        batch_losses = [x['val_loss'] for x in outputs]
        epoch_loss = torch.stack(batch_losses).mean()   # Combine losses
        batch_accs = [x['val_acc'] for x in outputs]
        epoch_acc = torch.stack(batch_accs).mean()      # Combine accuracies
        return {'val_loss': epoch_loss.item(), 'val_acc': epoch_acc.item()}

    def evaluate(self, X_test, y_test):
      self.eval()

      test_x_tensor = torch.from_numpy(X_test.astype('float64'))
      test_x_tensor = torch.permute(test_x_tensor, (0, 2, 1))
      test_y_tensor = torch.from_numpy(y_test.astype('float64'))  

      test_ds = TensorDataset(test_x_tensor, test_y_tensor)
      test_loader = torch.utils.data.DataLoader(test_ds, batch_size = 32, shuffle = False)
      test_loader = DeviceDataLoader(test_loader, get_default_device())
          
      test_losses = []
      outputs = []
      with torch.no_grad():
        for xb, yb in test_loader:
          output = self(xb.float())
          outputs.append(output)
          
      y_pred = torch.vstack(outputs).squeeze(1)
      y_pred = y_pred.cpu().numpy().reshape(-1,1)
      test_error = skl.mean_squared_error(y_test, y_pred)
      print('MSE on the entire test set: %f' % test_error)

      export_results_to_latex(y_test, y_pred)

"""## NetOrdinalClassification

https://stats.stackexchange.com/questions/209290/deep-learning-for-ordinal-classification

https://towardsdatascience.com/simple-trick-to-train-an-ordinal-regression-with-any-classifier-6911183d2a3c

https://towardsdatascience.com/how-to-perform-ordinal-regression-classification-in-pytorch-361a2a095a99

https://arxiv.org/pdf/0704.1028.pdf

https://datascience.stackexchange.com/questions/44354/ordinal-classification-with-xgboost

https://towardsdatascience.com/building-rnn-lstm-and-gru-for-time-series-using-pytorch-a46e5b094e7b

https://neptune.ai/blog/how-to-deal-with-imbalanced-classification-and-regression-data

https://colab.research.google.com/github/YyzHarry/imbalanced-regression/blob/master/tutorial/tutorial.ipynb#scrollTo=tSrzhog1gxyY
"""

NO_RAIN = 0
WEAK_RAIN = 1
MODERATE_RAIN = 2
STRONG_RAIN = 3
EXTREME_RAIN = 4

import numpy as np
def f(x):
  if x == NO_RAIN:
    return np.array([1,0,0,0,0])
  elif x == WEAK_RAIN:
    return np.array([1,1,0,0,0])
  elif x == MODERATE_RAIN:
    return np.array([1,1,1,0,0])
  elif x == STRONG_RAIN:
    return np.array([1,1,1,1,0])
  elif x == EXTREME_RAIN:
    return np.array([1,1,1,1,1])

# teste
# y = np.array([0,1,2,3,4])
# y_encoded = np.array(list(map(f, y)))
# y_encoded

def label2ordinalencoding(y_train, y_val):
  no_rain_train, weak_rain_train, moderate_rain_train, strong_rain_train, extreme_rain_train = get_events_per_precipitation_level(y_train)
  no_rain_val, weak_rain_val, moderate_rain_val, strong_rain_val, extreme_rain_val = get_events_per_precipitation_level(y_val)

  y_train_class = np.zeros_like(y_train)
  y_val_class = np.zeros_like(y_val)

  y_train_class[no_rain_train] = NO_RAIN
  y_train_class[weak_rain_train] = WEAK_RAIN
  y_train_class[moderate_rain_train] = MODERATE_RAIN
  y_train_class[strong_rain_train] = STRONG_RAIN
  y_train_class[extreme_rain_train] = EXTREME_RAIN

  y_val_class[no_rain_val] = NO_RAIN
  y_val_class[weak_rain_val] = WEAK_RAIN
  y_val_class[moderate_rain_val] = MODERATE_RAIN
  y_val_class[strong_rain_val] = STRONG_RAIN
  y_val_class[extreme_rain_val] = EXTREME_RAIN

  y_train = np.array(list(map(f, y_train_class)))
  y_val = np.array(list(map(f, y_val_class)))

  return y_train, y_val

def ordinalencoding2labels(pred: np.ndarray):
    """Convert ordinal predictions to class labels, e.g.
    
    [0.9, 0.1, 0.1, 0.1] -> 0
    [0.9, 0.9, 0.1, 0.1] -> 1
    [0.9, 0.9, 0.9, 0.1] -> 2
    etc.
    """
    return (pred > 0.5).cumprod(axis=1).sum(axis=1) - 1

# teste
# ordinalencoding2labels(y_encoded)

import torch.nn.functional as F
from typing import List

def accuracy(outputs, labels):
    _, preds = torch.max(outputs, dim=1)
    return torch.tensor(torch.sum(preds == labels).item() / len(preds))

class NetOrdinalClassification(nn.Module):
    def __init__(self, in_channels, num_classes):
        super(NetOrdinalClassification,self).__init__()
        self.conv1d_1 = nn.Conv1d(in_channels = in_channels, out_channels = 32, kernel_size = 3, padding=2)
        self.conv1d_2 = nn.Conv1d(in_channels = 32, out_channels = 32, kernel_size = 3, padding=2)
        self.conv1d_3 = nn.Conv1d(in_channels = 32, out_channels = 32, kernel_size = 3, padding=2)
        self.conv1d_4 = nn.Conv1d(in_channels = 32, out_channels = 64, kernel_size = 3, padding=2)

        # self.relu = nn.ReLU()
        self.relu = nn.GELU()
        
        self.sigmoid = nn.Sigmoid()

        self.fc1 = nn.Linear(896,50)

        self.fc2 = nn.Linear(50, num_classes)


    def forward(self,x):
        x = self.conv1d_1(x)
        x = self.relu(x)

        # x = self.max_pooling1d_1(x)

        x = self.conv1d_2(x)
        x = self.relu(x)

        x = self.conv1d_3(x)
        x = self.relu(x)

        x = self.conv1d_4(x)
        
        x = self.relu(x)

        x = x.view(x.shape[0], -1)
        
        x = self.fc1(x)
        x = self.relu(x)
        
        x = self.fc2(x)
        x = self.sigmoid(x)

        return x

    def prediction2label(pred: np.ndarray):
      """Convert ordinal predictions to class labels, e.g.
      
      [0.9, 0.1, 0.1, 0.1] -> 0
      [0.9, 0.9, 0.1, 0.1] -> 1
      [0.9, 0.9, 0.9, 0.1] -> 2
      etc.
      """
      return (pred > 0.5).cumprod(axis=1).sum(axis=1) - 1

    def training_step(self, batch):
        X_train, y_train = batch 
        out = self(X_train)                  # Generate predictions
        loss = F.cross_entropy(out, y_train) # Calculate loss
        return loss

    def validation_step(self, batch):
        X_train, y_train = batch 
        out = self(X_train)                    # Generate predictions
        loss = F.cross_entropy(out, y_train)   # Calculate loss
        acc = accuracy(out, y_train)           # Calculate accuracy
        return {'val_loss': loss, 'val_acc': acc}
        
    def validation_epoch_end(self, outputs):
        batch_losses = [x['val_loss'] for x in outputs]
        epoch_loss = torch.stack(batch_losses).mean()   # Combine losses
        batch_accs = [x['val_acc'] for x in outputs]
        epoch_acc = torch.stack(batch_accs).mean()      # Combine accuracies
        return {'val_loss': epoch_loss.item(), 'val_acc': epoch_acc.item()}
    
    def epoch_end(self, epoch, result):
        print("Epoch [{}], val_loss: {:.4f}, val_acc: {:.4f}".format(epoch, result['val_loss'], result['val_acc']))

    def evaluate(self, X_test, y_test):
      print('Evaluating ordinal regression model...')
      self.eval()

      test_x_tensor = torch.from_numpy(X_test.astype('float64'))
      test_x_tensor = torch.permute(test_x_tensor, (0, 2, 1))
      test_y_tensor = torch.from_numpy(y_test.astype('float64'))  

      test_ds = TensorDataset(test_x_tensor, test_y_tensor)
      test_loader = torch.utils.data.DataLoader(test_ds, batch_size = 32, shuffle = False)
      test_loader = DeviceDataLoader(test_loader, get_default_device())

      test_losses = []
      outputs = []
      with torch.no_grad():
        for xb, yb in test_loader:
          output = self(xb.float())
          yb_pred_encoded = output.detach().cpu().numpy()
          yb_pred_decoded = ordinalencoding2labels(yb_pred_encoded)
          outputs.append(yb_pred_decoded.reshape(-1,1))

      y_pred = np.vstack(outputs)

      export_confusion_matrix_to_latex(y_test, y_pred)

"""# Janelamento"""

import pandas as pd
import numpy as np

def apply_windowing(X, 
                    initial_time_step, 
                    max_time_step, 
                    window_size, 
                    idx_target,
                    only_y_not_nan = False,
                    only_y_gt_zero = False,
                    only_X_not_nan = False):

  assert idx_target >= 0 and idx_target < X.shape[1]
  assert initial_time_step >= 0
  assert max_time_step >= initial_time_step

  start = initial_time_step
    
  sub_windows = (
        start +
        # expand_dims converts a 1D array to 2D array.
        np.expand_dims(np.arange(window_size), 0) +
        np.expand_dims(np.arange(max_time_step + 1), 0).T
  )

  X_temp, y_temp = X[sub_windows], X[window_size:(max_time_step+window_size+1):1, idx_target]

  if only_y_not_nan and only_y_gt_zero and only_X_not_nan:
    y_train_not_nan_idx = np.where(~np.isnan(y_temp))[0]
    y_train_gt_zero_idx = np.where(y_temp>0)[0]
    x_train_is_nan_idx = np.unique(np.where(np.isnan(X_temp)))
    idxs = np.intersect1d(y_train_not_nan_idx, y_train_gt_zero_idx)
    idxs = np.setdiff1d(idxs, x_train_is_nan_idx)
    X_temp, y_temp = X_temp[idxs], y_temp[idxs]

  return X_temp, y_temp

def generate_windowed_split(df, id_target = 'CHUVA', window_size = 6):
  n = len(df)
  train_df = df[0:int(n*0.7)]
  val_df = df[int(n*0.7):int(n*0.9)]
  test_df = df[int(n*0.9):]

  train_arr = np.array(train_df)
  val_arr = np.array(val_df)
  test_arr = np.array(test_df)

  idx_target = train_df.columns.get_loc(id_target)
  print(idx_target)

  TIME_WINDOW_SIZE = window_size
  IDX_TARGET = id_target
      
  X_train, y_train = apply_windowing(train_arr, 
                                    initial_time_step=0, 
                                    max_time_step=len(train_arr)-TIME_WINDOW_SIZE-1, 
                                    window_size = TIME_WINDOW_SIZE, 
                                    idx_target = idx_target)
  y_train = y_train.reshape(-1,1)

  X_val, y_val = apply_windowing(val_arr, 
                                initial_time_step=0, 
                                max_time_step=len(val_arr)-TIME_WINDOW_SIZE-1, 
                                window_size = TIME_WINDOW_SIZE, 
                                idx_target = idx_target)
  y_val = y_val.reshape(-1,1)

  X_test, y_test = apply_windowing(test_arr, 
                                  initial_time_step=0, 
                                  max_time_step=len(test_arr)-TIME_WINDOW_SIZE-1, 
                                  window_size = TIME_WINDOW_SIZE, 
                                  idx_target = idx_target)
  y_test = y_test.reshape(-1,1)

  return X_train, y_train, X_val, y_val, X_test, y_test

"""# Treinamento"""

import random

def initialize_weights(m):
  if isinstance(m, nn.Conv1d):
      nn.init.kaiming_uniform_(m.weight.data, nonlinearity='relu')
      if m.bias is not None:
          nn.init.constant_(m.bias.data, 0)
  elif isinstance(m, nn.BatchNorm2d):
      nn.init.constant_(m.weight.data, 1)
      nn.init.constant_(m.bias.data, 0)
  elif isinstance(m, nn.Linear):
      nn.init.kaiming_uniform_(m.weight.data)
      nn.init.constant_(m.bias.data, 0)

def seed_everything(seed=1234):
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.backends.cudnn.deterministic = True

def get_default_device():
    """Pick GPU if available, else CPU"""
    if torch.cuda.is_available():
        return torch.device('cuda')
    else:
        return torch.device('cpu')

def to_device(data, device):
    """Move tensor(s) to chosen device"""
    if isinstance(data, (list,tuple)):
        return [to_device(x, device) for x in data]
    return data.to(device, non_blocking=True)

class DeviceDataLoader():
    """Wrap a dataloader to move data to a device"""
    def __init__(self, dl, device):
        self.dl = dl
        self.device = device
        
    def __iter__(self):
        """Yield a batch of data after moving it to device"""
        for b in self.dl: 
            yield to_device(b, self.device)

    def __len__(self):
        """Number of batches"""
        return len(self.dl)

class EarlyStopping:
    """Early stops the training if validation loss doesn't improve after a given patience."""
    def __init__(self, patience=7, verbose=False, delta=0):
        """
        Args:
            patience (int): How long to wait after last time validation loss improved.
                            Default: 7
            verbose (bool): If True, prints a message for each validation loss improvement. 
                            Default: False
            delta (float): Minimum change in the monitored quantity to qualify as an improvement.
                            Default: 0
        """
        self.patience = patience
        self.verbose = verbose
        self.counter = 0
        self.best_score = None
        self.early_stop = False
        self.val_loss_min = np.Inf
        self.delta = delta

    def __call__(self, val_loss, model):

        score = -val_loss

        if self.best_score is None:
            self.best_score = score
            self.save_checkpoint(val_loss, model)
        elif score < self.best_score + self.delta:
            self.counter += 1
            print(f'EarlyStopping counter: {self.counter} out of {self.patience}')
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_score = score
            self.save_checkpoint(val_loss, model)
            self.counter = 0

    def save_checkpoint(self, val_loss, model):
        '''Saves model when validation loss decrease.'''
        if self.verbose:
            print(f'Validation loss decreased ({self.val_loss_min:.6f} --> {val_loss:.6f}).  Saving model ...')
        torch.save(model.state_dict(), 'Modelo_'+ aux_nome +'.pt')
        self.val_loss_min = val_loss

def fit(model, n_epochs, optimizer, train_loader, val_loader, patience, criterion):    
    # to track the training loss as the model trains
    train_losses = []
    # to track the validation loss as the model trains
    valid_losses = []
    # to track the average training loss per epoch as the model trains
    avg_train_losses = []
    # to track the average validation loss per epoch as the model trains
    avg_valid_losses = [] 
    
    # initialize the early_stopping object
    early_stopping = EarlyStopping(patience=patience, verbose=True)

    for epoch in range(n_epochs):

        ###################
        # train the model #
        ###################
        model.train() # prep model for training
        for data, target in train_loader:
            # clear the gradients of all optimized variables
            optimizer.zero_grad()
            
            # forward pass: compute predicted outputs by passing inputs to the model
            output = model(data.float())

            # calculate the loss
            loss = criterion(output, target.float())
            assert not (np.isnan(loss.item()) or loss.item() > 1e6), f"Loss explosion: {loss.item()}"

            loss.backward()

            # perform a single optimization step (parameter update)
            optimizer.step()

            # record training loss
            train_losses.append(loss.item())

        ######################    
        # validate the model #
        ######################
        model.eval() # prep model for evaluation
        for data, target in val_loader:
            # forward pass: compute predicted outputs by passing inputs to the model
            output = model(data.float())
            # calculate the loss
            loss = criterion(output, target.float())
            # record validation loss
            valid_losses.append(loss.item())

        # print training/validation statistics 
        # calculate average loss over an epoch
        train_loss = np.average(train_losses)
        valid_loss = np.average(valid_losses)
        avg_train_losses.append(train_loss)
        avg_valid_losses.append(valid_loss)
        
        epoch_len = len(str(n_epochs))
        
        print_msg = (f'[{(epoch+1):>{epoch_len}}/{n_epochs:>{epoch_len}}] ' +
                     f'train_loss: {train_loss:.5f} ' +
                     f'valid_loss: {valid_loss:.5f}')
        
        print(print_msg)
        
        # clear lists to track next epoch
        train_losses = []
        valid_losses = []

        early_stopping(valid_loss, model)
        
        if early_stopping.early_stop:
            print("Early stopping")
            break

    return  avg_train_losses, avg_valid_losses

def create_train_n_val_loaders(train_x, train_y, val_x, val_y, batch_size):
    train_x = torch.from_numpy(train_x.astype('float64'))
    train_x = torch.permute(train_x, (0, 2, 1))
    train_y = torch.from_numpy(train_y.astype('float64'))

    val_x = torch.from_numpy(val_x.astype('float64'))
    val_x = torch.permute(val_x, (0, 2, 1))
    val_y = torch.from_numpy(val_y.astype('float64'))

    train_ds = TensorDataset(train_x, train_y)
    val_ds = TensorDataset(val_x, val_y)

    train_loader = torch.utils.data.DataLoader(train_ds, batch_size = batch_size, shuffle = True)
    val_loader = torch.utils.data.DataLoader(val_ds, batch_size = batch_size, shuffle = True)
    
    return train_loader, val_loader

def gen_learning_curve(train_loss, val_loss):
  fig = plt.figure(figsize=(10,8))
  plt.plot(range(1, len(train_loss)+1), train_loss, label='Training Loss')
  plt.plot(range(1, len(val_loss)+1), val_loss, label='Validation Loss')
  plt.xlabel('epochs')
  plt.ylabel('loss')
  plt.xlim(0, len(train_loss)+1)
  plt.grid(True)
  plt.legend()
  plt.tight_layout()
  fig.savefig('loss_plot_' + aux_nome + '.png', bbox_inches='tight')

"""# Avaliação"""

import numpy as np
from sklearn.metrics import confusion_matrix
import pandas as pd

'''
  https://stackoverflow.com/questions/59935155/how-to-calculate-mean-bias-errormbe-in-python
'''
def mean_bias_error(y_true, y_pred):
  MBE = np.mean(y_pred - y_true)
  return MBE

def get_events_per_precipitation_level(y):
  no_rain = np.where(np.any(y<=0., axis=1))
  weak_rain = np.where(np.any((y>0.) & (y<=5.), axis=1))
  moderate_rain = np.where(np.any((y>5.) & (y<=25.), axis=1))
  strong_rain = np.where(np.any((y>25.) & (y<=50.), axis=1))
  extreme_rain = np.where(np.any(y>50., axis=1))
  return no_rain, weak_rain, moderate_rain, strong_rain, extreme_rain

def export_confusion_matrix_to_latex(y_true, y_pred):
  no_rain_true, weak_rain_true, moderate_rain_true, strong_rain_true, extreme_rain_true = get_events_per_precipitation_level(y_true)
  no_rain_pred, weak_rain_pred, moderate_rain_pred, strong_rain_pred, extreme_rain_pred = get_events_per_precipitation_level(y_pred)

  y_true_class = np.zeros_like(y_true)
  y_pred_class = np.zeros_like(y_pred)
  y_true_class[no_rain_true] = NO_RAIN
  y_pred_class[no_rain_pred] = NO_RAIN
  y_true_class[weak_rain_true] = WEAK_RAIN
  y_pred_class[weak_rain_pred] = WEAK_RAIN
  y_true_class[moderate_rain_true] = MODERATE_RAIN
  y_pred_class[moderate_rain_pred] = MODERATE_RAIN
  y_true_class[strong_rain_true] = STRONG_RAIN
  y_pred_class[strong_rain_pred] = STRONG_RAIN
  y_true_class[extreme_rain_true] = EXTREME_RAIN
  y_pred_class[extreme_rain_pred] = EXTREME_RAIN
  
  # target_names = ['No Rain', 'Weak Rain', 'Moderate Rain', 'Strong Rain']
  df = pd.DataFrame(
      confusion_matrix(y_true_class, y_pred_class, labels=[0,1,2,3,4]), 
      index=['true:No Rain', 'true:Weak Rain', 'true:Moderate Rain', 'true:Strong Rain', 'true:Extreme Rain', ], 
      columns=['pred:No Rain', 'pred:Weak Rain', 'pred:Moderate Rain', 'pred:Strong Rain', 'pred:Extreme Rain', ], 
  )
  print(df.to_latex())
  print()

'''
  MAE (mean absolute error) and MBE (mean bias error) values are computed for each precipitation level.
'''
def export_results_to_latex(y_true, y_pred):
  export_confusion_matrix_to_latex(y_true, y_pred)

  no_rain_true, weak_rain_true, moderate_rain_true, strong_rain_true, extreme_rain_true = get_events_per_precipitation_level(y_true)
  no_rain_pred, weak_rain_pred, moderate_rain_pred, strong_rain_pred, extreme_rain_pred = get_events_per_precipitation_level(y_pred)

  if no_rain_pred[0].size > 0:
    mse_no_rain = skl.mean_absolute_error(y_true[no_rain_true], y_pred[no_rain_true])
    mbe_no_rain = mean_bias_error(y_true[no_rain_true], y_pred[no_rain_true])
  else:
    mse_no_rain = mbe_no_rain = 'n/a'

  if weak_rain_pred[0].size > 0:
    mse_weak_rain = skl.mean_absolute_error(y_true[weak_rain_true], y_pred[weak_rain_true])
    mbe_weak_rain = mean_bias_error(y_true[weak_rain_true], y_pred[weak_rain_true])
  else:
    mse_weak_rain = mbe_weak_rain = 'n/a'

  if moderate_rain_pred[0].size > 0:
    mse_moderate_rain = skl.mean_absolute_error(y_true[moderate_rain_true], y_pred[moderate_rain_true])
    mbe_moderate_rain = mean_bias_error(y_true[moderate_rain_true], y_pred[moderate_rain_true])
  else:
    mse_moderate_rain = mbe_moderate_rain = 'n/a'

  if strong_rain_pred[0].size > 0:
    mse_strong_rain = skl.mean_absolute_error(y_true[strong_rain_true], y_pred[strong_rain_true])
    mbe_strong_rain = mean_bias_error(y_true[strong_rain_true], y_pred[strong_rain_true])
  else:
    mse_strong_rain = mbe_strong_rain = 'n/a'

  if extreme_rain_pred[0].size > 0:
    mse_extreme_rain = skl.mean_absolute_error(y_true[extreme_rain_true], y_pred[extreme_rain_true])
    mbe_extreme_rain = mean_bias_error(y_true[extreme_rain_true], y_pred[extreme_rain_true])
  else:
    mse_extreme_rain = mbe_extreme_rain = 'n/a'
  
  df = pd.DataFrame()
  df['level'] = ['No rain', 'Weak', 'Moderate', 'Strong', 'Extreme']
  df['qty_true'] = [no_rain_true[0].shape[0], weak_rain_true[0].shape[0], moderate_rain_true[0].shape[0], strong_rain_true[0].shape[0], extreme_rain_true[0].shape[0]]
  df['qty_pred'] = [no_rain_pred[0].shape[0], weak_rain_pred[0].shape[0], moderate_rain_pred[0].shape[0], strong_rain_pred[0].shape[0], extreme_rain_pred[0].shape[0]]
  df['mae'] = [mse_no_rain, mse_weak_rain, mse_moderate_rain, mse_strong_rain, mse_extreme_rain]
  df['mbe'] = [mbe_no_rain, mbe_weak_rain, mbe_moderate_rain, mbe_strong_rain, mbe_extreme_rain]
  print(df.to_latex())

"""# Main"""

def apply_subsampling(X, y, percentage = 0.1):
  print('*BEGIN*')
  print(X.shape)
  print(y.shape)
  y_eq_zero_idxs = np.where(y==0)[0]
  print('# original samples  eq zero:', y_eq_zero_idxs.shape)
  y_gt_zero_idxs = np.where(y>0)[0]
  print('# original samples gt zero:', y_gt_zero_idxs.shape)
  mask = np.random.choice([True, False], size=y.shape[0], p=[percentage, 1.0-percentage])
  y_train_subsample_idxs = np.where(mask==True)[0]
  print('# subsample:', y_train_subsample_idxs.shape)
  idxs = np.intersect1d(y_eq_zero_idxs, y_train_subsample_idxs)
  print('# subsample that are eq zero:', idxs.shape)
  idxs = np.union1d(idxs, y_gt_zero_idxs)
  print('# subsample final:', idxs.shape)
  X, y = X[idxs], y[idxs]
  print(X.shape)
  print(y.shape)
  print('*END*')
  return X, y

import time
import pandas as pd
import numpy as np
import torch

def train(X_train, y_train, X_val, y_val, ordinal_regression):
  N_EPOCHS = 5000
  PATIENCE = 500
  LEARNING_RATE = .3e-6
  NUM_FEATURES = X_train.shape[2]
  BATCH_SIZE = 512
  weight_decay = 1e-6

  if ordinal_regression:
    NUM_CLASSES = 5
    model = NetOrdinalClassification(in_channels = NUM_FEATURES,
                                    num_classes = NUM_CLASSES)
    y_train, y_val = label2ordinalencoding(y_train, y_val)
  else:
    global y_mean_value
    y_mean_value = np.mean(y_train)
    print(y_mean_value)
    model = NetRegression(in_channels = NUM_FEATURES)

  # model.apply(initialize_weights)

  criterion = nn.MSELoss()

  print(model)

  train_loader, val_loader = create_train_n_val_loaders(X_train, y_train, X_val, y_val, batch_size = BATCH_SIZE)

  optimizer = torch.optim.Adam(model.parameters(), 
                               lr=LEARNING_RATE, 
                               weight_decay=weight_decay)

  device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
  train_loader = DeviceDataLoader(train_loader, device)
  val_loader = DeviceDataLoader(val_loader, device)    
  to_device(model, device)
    
  train_loss, val_loss = fit(model, 
                             n_epochs = N_EPOCHS, 
                             optimizer = optimizer, 
                             train_loader = train_loader, 
                             val_loader = val_loader, 
                             patience = PATIENCE, 
                             criterion = criterion)

  gen_learning_curve(train_loss, val_loss)

  return model

def main(ordinal_regression = True, file = ''):
  seed_everything()

  arquivo = '../data/' + file + '.csv'

  cor_est = ['alto_da_boa_vista','guaratiba','iraja','jardim_botanico','riocentro','santa_cruz','sao_cristovao','vidigal']
  df = pd.read_csv(arquivo)
  df = df.fillna(0)

  if arquivo in cor_est:
    df1 = df.drop(columns=['Unnamed: 0', 'Dia','Hora','estacao','HBV', 'showalter'])
    col_target = 'Chuva'
  else:
    df1 = df.drop(columns=['Unnamed: 0', 'DC_NOME','UF','DT_MEDICAO','CD_ESTACAO','VL_LATITUDE','VL_LONGITUDE','HR_MEDICAO'])
    col_target = 'CHUVA'


  assert df1.isnull().values.any() == False

  target = df1[col_target].copy()

  df2 = ((df1-df1.min())/(df1.max()-df1.min()))

  df2[col_target] = target

  df2 = df2.fillna(0)

  assert df2.isnull().values.any() == False

  X_train, y_train, X_val, y_val, X_test, y_test = generate_windowed_split(df2, id_target = col_target, window_size = 6)

  print('***Before subsampling***')
  print('Max precipitation values (train/val/test): %d, %d, %d' % (np.max(y_train), np.max(y_val), np.max(y_test)))
  print('Mean precipitation values (train/val/test): %.4f, %.4f, %.4f' % (np.mean(y_train), np.mean(y_val), np.mean(y_test)))

  # ### Subsampling
  X_train, y_train = apply_subsampling(X_train, y_train)
  X_val, y_val = apply_subsampling(X_val, y_val)
  X_test, y_test = apply_subsampling(X_test, y_test)
  # ### Subsampling

  print('***After subsampling***')
  print('Max precipitation values (train/val/test): %d, %d, %d' % (np.max(y_train), np.max(y_val), np.max(y_test)))
  print('Mean precipitation values (train/val/test): %.4f, %.4f, %.4f' % (np.mean(y_train), np.mean(y_val), np.mean(y_test)))

  model = train(X_train, y_train, X_val, y_val, ordinal_regression)
  
  # load the best model
  model.load_state_dict(torch.load('Modelo_'+ aux_nome +'.pt'))

  model.evaluate(X_test, y_test)


def myfunc(argv):
    arg_file = ""
    arg_help = "{0} -f <file>".format(argv[0])
    
    try:
        opts, args = getopt.getopt(argv[1:], "hf:", ["help", "file="])
    except:
        print(arg_help)
        sys.exit(2)
    
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(arg_help)  # print the help message
            sys.exit(2)
        elif opt in ("-f", "--file"):
            arg_file = arg
    
        
    global aux_nome
    aux_nome = 'teste'
    aux_nome = arg_file
    start_time = time.time()
    main(ordinal_regression = False, file = arg_file)
    print("--- %s seconds ---" % (time.time() - start_time))



if __name__ == "__main__":
    myfunc(sys.argv)



"""# Análise exploratória"""

# import seaborn as sns
# import matplotlib.pyplot as plt

# sns.distplot(train_y, hist=False)
# sns.distplot(val_y, hist=False)
# sns.distplot(test_y, hist=False)

# plt.show()

"""# TODO

- iniciar parâmetros explicitamente (nn.init.kaiming_normal_(_conv.weight)): https://adityassrana.github.io/blog/theory/2020/08/26/Weight-Init.html; https://www.kaggle.com/code/mlwhiz/initializing-pytorch-layers-weight-with-kaiming

- depurar gradient flow: https://discuss.pytorch.org/t/how-to-check-for-vanishing-exploding-gradients/9019

- Testar CyclicLR: https://github.com/anandsaha/pytorch.cyclic.learning.rate/blob/master/cls.py

- WeightWatcher (https://youtu.be/xEuBwBj_Ov4)


# Refs

- https://arxiv.org/ftp/arxiv/papers/1810/1810.10485.pdf
- https://github.com/sonawanemaitreya/Precipitation-Nowcasting-1

"""