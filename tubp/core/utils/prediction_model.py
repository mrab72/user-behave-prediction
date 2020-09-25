import torch
import torch.nn.functional as F
from torch import nn


class PredictionModel(nn.Module):

    def __init__(self):
        super(PredictionModel, self).__init__()
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.dist = GaussianDistribution()

        self.linear1 = nn.Linear(784, 1000)
        self.linear2 = nn.Linear(1000, 500)
        self.linear3 = nn.Linear(500, 100)
        self.linear4 = nn.Linear(100, 18)
        self.sftmx = nn.Softmax()
        self.cent = torch.eye(18).to(device)

    def forward(self, x):
        x = torch.flatten(x, 1)
        x = F.relu(self.linear1(x))
        x = F.relu(self.linear2(x))
        x = F.relu(self.linear3(x))
        x = self.dist(self.linear4(x))
        return x


class GaussianDistribution(nn.Module):

    def __init__(self, mean=0, std=1):
        super(GaussianDistribution, self).__init__()
        self.mean = mean
        self.std = std

    def forward(self, x):
        gauss = torch.exp((-(x - self.mean) ** 2) / (2 * self.std ** 2))
        return gauss
