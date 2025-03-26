import torch.nn as nn
import torch.nn.functional as F
from cyra_ai.utils.init_weights import init_weights

class Actor(nn.Module):
    def __init__(self, input_size, output_size):
        super(Actor, self).__init__()
        
        # Capa 0: de input_size a 128
        self.fc0 = nn.Linear(input_size, 128)
        self.ln0 = nn.LayerNorm(128)
        # Capa 1: de 128 a 64
        self.fc1 = nn.Linear(128, 64)
        self.ln1 = nn.LayerNorm(64)
        
        # Capa de salida: de 64 a output_size
        self.fc2 = nn.Linear(64, output_size)
        
        # Inicicalizacion de pesos
        self.apply(init_weights)
    
    def forward(self, x):
        # Procesamiento atraves de las capas con activacion LeakyReLU
        x = F.leaky_relu(self.ln0(self.fc0(x)), negative_slope=0.01)
        x = F.leaky_relu(self.ln1(self.fc1(x)), negative_slope=0.01)
        x = self.fc2(x)
        return x