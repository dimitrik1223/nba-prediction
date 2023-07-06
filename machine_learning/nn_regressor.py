import copy
import pickle
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import tqdm

from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, TensorDataset

class EarlyStopping():
	"""
	Early stopping algorithm
	"""
	def __init__(self, patience=5, min_delta=1e-2, restore_best_weights=True):
		self.patience = patience
		self.min_delta = min_delta
		self.restore_best_weights = restore_best_weights
		self.best_model = None
		self.best_loss = None
		self.counter = 0
		self.status = ""

	def __call__(self, model, val_loss):
		if self.best_loss is None:
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
	"""
	Subclass of Pytorch neural network superclass
	"""
	def __init__(self, in_count, out_count):
		super(Net, self).__init__()
		self.fc1 = nn.Linear(in_count, 50)
		self.fc2 = nn.Linear(50, 25)
		self.fc3 = nn.Linear(25, out_count)

	def forward(self, inputs):
		"""
		Forward pass
		"""
		outputs = F.relu(self.fc1(inputs))
		outputs = F.relu(self.fc2(outputs))
		return self.fc3(outputs)

def get_predictors(data):
	"""
	Return dataframe of MinMax scaled predictors.
	"""
	predictors = data[[
		col for col in data.columns if data[col].dtype in ("float64", "int64")
		and col not in ("Pts Won", "Pts Max", "Share")
	]]
	scaler = MinMaxScaler()
	scaled_predictor_arr = scaler.fit_transform(predictors)
	predictors = pd.DataFrame(scaled_predictor_arr)

	return predictors

def train_model(train_set):
	"""
	returns:
	scaled_predictor_arr (array): Numpy array of scaled predictors
	"""
	scaled_predictors = get_predictors(train_set)
	x_full = scaled_predictors.values
	y_full = train_set["Pts Won"].values
	x_train, x_test, y_train, y_test = train_test_split(
	x_full, y_full, test_size=0.25, random_state=0
	)
	# Numpy to Torch Tensor
	x_train = torch.Tensor(x_train).float()
	y_train = torch.Tensor(y_train).float()
	x_test = torch.Tensor(x_test).float().to("cpu")
	y_test = torch.Tensor(y_test).float().to("cpu")
	BATCH_SIZE = 16
	dataset_train = TensorDataset(x_train, y_train)
	dataloader_train = DataLoader(dataset_train, \
	batch_size=BATCH_SIZE, shuffle=True)
	# Initialize model
	model = Net(x_full.shape[1], 1)
	# Define the loss function for regression
	loss_fn = nn.MSELoss()
	# Define the optimizer
	optimizer = torch.optim.Adam(model.parameters())
	early_stopping = EarlyStopping()
	epoch = 0
	done = False
	while epoch < 1000 and not done:
		epoch += 1
		steps = list(enumerate(dataloader_train))
		pbar = tqdm.tqdm(steps)
		model.train()
		for i, (x_batch, y_batch) in pbar:
			y_batch_pred = model(x_batch.to("cpu")).flatten()
			loss = loss_fn(y_batch_pred, y_batch.to("cpu"))
			optimizer.zero_grad()
			loss.backward()
			optimizer.step()
			loss = loss.item()
			if i == len(steps) - 1:
				model.eval()
				pred = model(x_test).flatten()
				vloss = loss_fn(pred, y_test)
				if early_stopping(model,vloss):
					done = True
					pbar.set_description(
						f"Epoch: {epoch}, tloss: {loss}, vloss: {vloss:>7f}, EStop:[{early_stopping.status}]"
					)
			else:
				pbar.set_description(f"Epoch: {epoch}, tloss {loss:}")
	with open("flask_app/mvp_model.pkl", "wb") as file:
		pickle.dump(model, file)

	return scaled_predictors


def predict(model, data):
	"""
	Prediction method
	"""
	tensor = torch.Tensor(data, device="cpu").type(torch.float32)
	preds = model(tensor).detach().numpy()
	# Negative preds to 0
	mvp_preds = np.where(preds < 0, 0, preds)

	return mvp_preds

def get_predicted_mvp(data, preds, year):
	"""
	Prints predicted and actual MVP for a given year.
	"""
	data["Predicted Pts Won"] = preds
	year_stats = data[data["Year"] == year]
	if not year_stats.empty:
		max_pred_pts = year_stats["Predicted Pts Won"].max()
		max_pts = year_stats["Pts Won"].max()
		mvp_pred = year_stats.loc[year_stats["Predicted Pts Won"] == max_pred_pts, "Player"].iloc[0]
		mvp_actual = year_stats.loc[year_stats["Pts Won"] == max_pts, "Player"].iloc[0]
		mvp_results = {
			"mvp_pred": mvp_pred,
			"mvp_actual": mvp_actual
		}
		return mvp_results

	year_start = data["Year"].min()
	year_end = data["Year"].max()
	raise Exception(f"Year must fall within the range from {year_start} to {year_end}")
