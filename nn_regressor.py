import matplotlib.pyplot as plt
import torch.nn as nn
import torch.nn.functional as F
import tqdm

from scipy.stats import zscore
from sklearn.model_selection import train_test_split
from torch.autograd import Variable
from sklearn import preprocessing
from torch.utils.data import DataLoader, TensorDataset

class EarlyStopping():
  def __init__(self, patience=5, min_delta=1e-2, restore_best_weights=True):
    self.patience = patience
    self.min_delta = min_delta
    self.restore_best_weights = restore_best_weights
    self.best_model = None
    self.best_loss = None
    self.counter = 0
    self.status = ""
    
  def __call__(self, model, val_loss):
    if self.best_loss == None:
      self.best_loss = val_loss
      self.best_model = copy.deepcopy(model)
    elif self.best_loss - val_loss > self.min_delta:
      self.best_loss = val_loss
      self.counter = 0
      self.best_model.load_state_dict(model.state_dict())
    elif self.best_loss - val_loss < self.min_delta:
      self.counter += 1
      if self.counter >= self.patience:
        self.status = f"Stopped on {self.counter}"
        if self.restore_best_weights:
          model.load_state_dict(self.best_model.state_dict())
        return True
    self.status = f"{self.counter}/{self.patience}"
    return False

class Net(nn.Module):
  def __init__(self, in_count, out_count):
    super(Net, self).__init__()
    self.fc1 = nn.Linear(in_count, 50)
    self.fc2 = nn.Linear(50, 25)
    self.fc3 = nn.Linear(25, out_count)
	

  def forward(self, x):
    x = F.relu(self.fc1(x))
    x = F.relu(self.fc2(x))
    return self.fc3(x)