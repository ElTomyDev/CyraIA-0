import torch
import random
import math
import torch.optim as optim
from torch.optim import lr_scheduler
from models.actor import Actor
from models.critic import Critic

class Agent:
    def __init__(self, input_size=0, output_size=0, gamma=0.99):
        # Inicializamos el actor (política) y el crítico (valor), usando las clases Actor y Critic
        self.actor = Actor(input_size, output_size) # Actor toma el tamaño de la entrada y el número de acciones posibles
        self.critic = Critic(input_size) # Critic toma solo el tamaño de la entrada (estado)
        
        # Optimizadores para las redes Actor y Critic
        self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=0.01)
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=0.01)
        
        # Scheduler para disminuir la tasa de aprendizaje de manera gradual
        self.scheduler = lr_scheduler.StepLR(self.actor_optimizer, step_size=10, gamma=0.95)
        
        # factor de descuento para recompensas futuras
        self.gamma = gamma
        
        # Buffers para almacenar logaritmos de probabilidad, entropía, valores y recompensas
        self.log_probs = [] # Almacena los log_probs de las acciones
        self.entropies = [] # Almacena la entropía de las acciones
        self.values = [] # Almacena los valores estimados por el crítico
        self.rewards = [] # Almacena las recompensas obtenidas
        self.exploration_rate = 5.5 # Tasa de exploración inicial, controla la aleatoriedad de las acciones
    
    def select_action(self, state):
        """
        Recibe un estado y devuelve la acción.
        También almacena el log_prob y la entropía de la distribución para regular la exploración.
        """
        # Convertimos el estado a un tensor de tipo float32 y lo preparamos para pasar al modelo
        state = torch.tensor(state, dtype=torch.float32).clone().unsqueeze(0) # Añadimos una dimensión extra para lotes de tamaño 1
        action_mean = self.actor(state) # El actor genera una media para la distribución de las acciones
        std = torch.tensor([self.exploration_rate, self.exploration_rate]) # Desviación estándar para la distribución (controla exploración)
        
        # Creamos una distribución normal con la media y la desviación estándar
        dist = torch.distributions.Normal(action_mean.squeeze(0), std)
        
        # Muestra una acción de la distribución normal y calcula el log_prob y la entropía
        action = dist.sample() # Muestra una acción de la distribución normal
        log_prob = dist.log_prob(action).sum() # Calcula el logaritmo de la probabilidad de la acción seleccionada
        entropy = dist.entropy().sum() # Calcula la entropía de la distribución para incentivar la exploración
        
        # Almacenamos el log_prob y la entropía en sus respectivos buffers
        self.log_probs.append(log_prob)
        self.entropies.append(entropy)
        
        # El valor estimado del estado (por el Critic)
        value = self.critic(state)
        self.values.append(value)
        
        # Devuelve la acción en formato NumPy (desacoplada de PyTorch para interactuar con el entorno)
        return action.detach().numpy().flatten()
    
    def store_reward(self, reward):
        """
        Guarda la recompensa obtenida en un paso.
        """
        self.rewards.append(reward)

    def learn(self):
        """
        Actualiza la política y el critic usando Actor-Critic.
        Calcula retornos y ventajas, normaliza, y aplica regularización por entropía.
        """
        # Calcula las recompensas descontadas (retornos)
        discounted_rewards = [] # Lista para almacenar las recompensas descontadas
        R = 0 # Variable para acumular las recompensas futuras
        for r in self.rewards[::-1]: # Itera desde el final de las recompensass
            R = r + self.gamma * R # Calcula la recompensa descontada
            discounted_rewards.insert(0, R) # Inserta al principio de la lista
        
        # Convierte las recompensas descontadas a un tensor y las normaliza
        discounted_rewards = torch.tensor(discounted_rewards, dtype=torch.float32)
        discounted_rewards = (discounted_rewards - discounted_rewards.mean()) / (discounted_rewards.std() + 1e-8) # Normalización para estabilidad
        
        # Convertimos los buffers a tensores para poder usarlos en las funciones de pérdida
        log_probs = torch.stack(self.log_probs) # Apila las probabilidades logarítmicas de las acciones
        values = torch.stack(self.values).squeeze() # Apila los valores del crítico y eliminamos dimensiones innecesarias
        
        # Calcular ventaja: diferencia entre retorno observado y valor estimado
        advantages = discounted_rewards - values

        # Calculsa la bonificación de entropía para incentivar la exploración
        entropy_bonus = torch.stack(self.entropies).mean() # Promediamos las entropías
        beta = 0.01  # Coeficiente para la penalización de la entropía
        
        # Calcular perdidas
        actor_loss = - (log_probs * advantages.detach()).mean() - beta * entropy_bonus # Pérdida del actor
        critic_loss = advantages.pow(2).mean() # Pérdida del crítico
        total_loss = actor_loss + critic_loss # Pérdida total combinando ambas pérdidas
        
        # Optimizacion del modelo
        self.actor_optimizer.zero_grad() # Resetea los gradientes del optimizador del actor
        self.critic_optimizer.zero_grad() # Resetea los gradientes del optimizador del crítico
        total_loss.backward() # Calcula los gradientes de la pérdida total
        self.actor_optimizer.step() # Actualiza los parámetros del actor
        self.critic_optimizer.step() # Actualiza los parámetros del crítico
        
        # Limpiamos los buffers para preparar para el siguiente paso
        self.log_probs = []
        self.entropies = []
        self.values = []
        self.rewards = []
        
        # Ajustamos la tasa de aprendizaje con el scheduler
        self.scheduler.step()
        # Reducimos la tasa de exploración después de cada paso de entrenamiento
        self.decay_exploration()
    
    def decay_exploration(self, decay_rate=0.99, min_rate=0.1):
        """
        Disminuye la tasa de exploración de forma multiplicativa hasta un valor mínimo.
        """
        self.exploration_rate = max(self.exploration_rate * decay_rate, min_rate) # Disminuimos la exploración multiplicativamente
    
    def save_model(self, path):
        """Guarda el modelo en el path dado."""
        torch.save({
        'actor_state_dict': self.actor.state_dict(),
        'critic_state_dict': self.critic.state_dict()
        }, path)

    def load_model(self, path):
        """Carga el modelo desde el path dado."""
        checkpoint = torch.load(path)
        self.actor.load_state_dict(checkpoint['actor_state_dict']) # Carga el estado del actor
        self.critic.load_state_dict(checkpoint['critic_state_dict']) # Cargamos el estado del crítico