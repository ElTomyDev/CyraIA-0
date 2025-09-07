from typing import Any
import torch
import torch.optim as optim
import numpy as np
from torch.optim import lr_scheduler
from cyra_ai.models.actor import Actor
from cyra_ai.models.critic import Critic

class Agent:
    def __init__(self, input_size=31, output_size=5, gamma=0.99) -> None:
        # Inicializamos el actor (política) y el crítico (valor), usando las clases Actor y Critic
        self.actor = Actor(input_size, output_size) # Actor toma el tamaño de la entrada y el número de acciones posibles
        self.critic = Critic(input_size) # Critic toma solo el tamaño de la entrada (estado)
        
        # Optimizadores para las redes Actor y Critic
        self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=0.001)
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=0.001)
        
        # Scheduler para disminuir la tasa de aprendizaje de manera gradual
        self.scheduler = lr_scheduler.StepLR(self.actor_optimizer, step_size=10, gamma=0.95)
        
        # factor de descuento para recompensas futuras
        self.gamma = gamma
        
        # Buffers para almacenar logaritmos de probabilidad, entropía, valores y recompensas
        self.log_probs = [] # Almacena los log_probs de las acciones
        self.entropies = [] # Almacena la entropía de las acciones
        self.values = [] # Almacena los valores estimados por el crítico
        self.rewards = [] # Almacena las recompensas obtenidas
        self.exploration_rate = 1.0 # Tasa de exploración inicial, controla la aleatoriedad de las acciones
    
    def select_action(self, state) -> list:
        """
        Recibe un estado y devuelve la acción.
        También almacena el log_prob y la entropía de la distribución para regular la exploración.
        """
        # Converte el estado a un tensor de tipo float32 y lo preparamos para pasar al modelo
        state = np.asarray(state, dtype=np.float32)
        state = torch.from_numpy(state).unsqueeze(0) # Añade una dimensión extra para lotes de tamaño 1
        
        action_mean = self.actor(state) # El actor genera una media para la distribución de las acciones
        std = torch.ones_like(action_mean) * self.exploration_rate # Desviación estándar para la distribución (controla exploración)
        
        # Creamos una distribución normal con la media y la desviación estándar
        dist = torch.distributions.Normal(action_mean.squeeze(0), std)
        action = dist.sample() # Muestra una acción de la distribución normal
        
        log_prob = dist.log_prob(action).sum() # Calcula el logaritmo de la probabilidad de la acción seleccionada
        entropy = dist.entropy().sum() # Calcula la entropía de la distribución para incentivar la exploración
        
        # Almacenamos el log_prob y la entropía en sus respectivos buffers
        self.log_probs.append(log_prob)
        self.entropies.append(entropy)
        
        # El valor estimado del estado (por el Critic)
        value = self.critic(state)
        self.values.append(value)
        
        action_np = action.detach().numpy().flatten()
        
        directions = [1 if d > 0 else 0 for d in action_np[:4]] # Obtiene direcciones redondeadas
        
        speed = max(0.0, min(abs(action_np[4]), 5.0))

        return [directions, speed]
    
    def store_reward(self, reward) -> None:
        """
        Guarda la recompensa obtenida en un paso.
        """
        self.rewards.append(reward)

    def learn(self) -> None:
        """
        Actualiza la política y el critic usando Actor-Critic.
        Calcula retornos y ventajas, normaliza, y aplica regularización por entropía.
        """
        # Calcular retornos
        returns = self.discount_rewards(self.rewards, self.gamma)
        returns = torch.tensor(returns, dtype=torch.float32)

        # Convertir buffers a tensores
        log_probs = torch.stack(self.log_probs)
        values = torch.stack(self.values).squeeze()

        # Calcular ventajas
        advantages = returns - values.detach()
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        # Entropía
        entropy_bonus = torch.stack(self.entropies).mean()
        beta = 0.01

        # Pérdidas
        actor_loss = -(log_probs * advantages).mean() - beta * entropy_bonus
        critic_loss = (returns - values).pow(2).mean()
        total_loss = actor_loss + critic_loss

        # Optimización
        self.actor_optimizer.zero_grad()
        self.critic_optimizer.zero_grad()
        total_loss.backward()
        self.actor_optimizer.step()
        self.critic_optimizer.step()

        # Limpiar buffers
        self.log_probs.clear()
        self.entropies.clear()
        self.values.clear()
        self.rewards.clear()

        # Ajustes dinámicos
        self.scheduler.step()
        self.decay_exploration()

    def discount_rewards(self, rewards, gamma) -> np.ndarray:
        rewards = np.array(rewards, dtype=np.float32)
        discounted = np.zeros_like(rewards)
        running_add = 0
        for t in reversed(range(len(rewards))):
            running_add = rewards[t] + gamma * running_add
            discounted[t] = running_add
        return discounted
    
    def decay_exploration(self, decay_rate=0.995, min_rate=0.1) -> None:
        """
        Disminuye la tasa de exploración de forma multiplicativa hasta un valor mínimo.
        """
        self.exploration_rate = max(self.exploration_rate * decay_rate, min_rate) # Disminuimos la exploración multiplicativamente
    
    def save_model(self, path) -> None:
        """Guarda el modelo en el path dado."""
        torch.save({
        'actor_state_dict': self.actor.state_dict(),
        'critic_state_dict': self.critic.state_dict()
        }, path)

    def load_model(self, path) -> None:
        """Carga el modelo desde el path dado."""
        checkpoint = torch.load(path)
        self.actor.load_state_dict(checkpoint['actor_state_dict']) # Carga el estado del actor
        self.critic.load_state_dict(checkpoint['critic_state_dict']) # Cargamos el estado del crítico