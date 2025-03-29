import pygame
import os
from cyra_ai.env.environment import Environment
from cyra_ai.agent.agent import Agent
from config.trainer_config import *
from config.general_config import BEST_MODEL_PATH, FPS
from graphics_and_data.training_graphics import TrainGraphics

class Train:
    def __init__(self, view):
        
        # Inicializa los graficos de entrenamiento
        self.train_graphics = TrainGraphics()
        
        # Obtiene la vista
        self.view = view
        
        # Variables para almacenar recompensas
        self.best_reward = -float('inf') # Mejor recompensa
        self.best_agent_index = None
        
        # Inicializacion del entorno y agentes
        self.env = Environment(self.view.screen, num_cyras=NUM_AGENTS)
        self.env.get_random_rewards_and_penalty() # Generan valores random para las recompensas y penalizaciones
        self.agents = [Agent() for _ in range(NUM_AGENTS)]
        
        # Carga el modelo guardado y este existe y evalua para obtener una recompensa base
        self.load_model_if_exist()
    
    # --------------------------
    # FUNCIONES DE ENTRENAMIENTO Y EVALUACION
    # --------------------------
    def run_generation_multi_agent(self):
        """
        Ejecuta un ciclo de entrenamiento (generación) en el entorno.
        Se reutiliza el objeto Environment y se acumulan recompensas de cada episodio.
        Retorna la recompensa promedio por agente para la generación.
        """
        total_rewards = [0.0 for _ in range(NUM_AGENTS)]
        for episode in range(NUM_EPISODES):
            self.view.process_events()
            
            states = self.env.reset() # Reposiciona a todos los cyras y actualiza la comida
            episode_rewards = [0.0 for _ in range(NUM_AGENTS)]
            
            # Actualiza la pantalla al inicio de cada episodio
            pygame.display.flip()
            
            for step in range(MAX_STEPS):
                self.view.process_events()
                
                # Selecciona una accion para cada agente usando su estado actual
                actions = [agent.select_action(states[i]) for i, agent in enumerate(self.agents)]

                # Actualiza el entorno con las acciones y obtiene nuevos estados y recompensas
                next_states, rewards, done = self.env.step(actions)
                
                # Almacena la recompensa de cada agente
                for i in range(NUM_AGENTS):
                    #agent.store_reward(rewards[i])
                    self.agents[i].store_reward(rewards[i])
                    episode_rewards[i] += rewards[i]
                states = next_states

                if step % 1 == 0:
                    pygame.display.flip()
                    self.view.clock.tick(FPS)
                
                # Actualiza los valores de las graficas
                healths, energys, hungers = self.get_cyras_status()
                self.train_graphics.update_graph_data(episode_rewards, healths, energys, hungers, self.view.generation, episode, step)
                
                if done:
                    break
            
            
            # Al final de cada episodio, cada agente actualiza su politica
            for agent in self.agents:
                agent.learn()
            
            # Acumula las recompensas de este episodio para cada agente
            for i in range(NUM_AGENTS):
                total_rewards[i] += episode_rewards[i]
            
        avg_reward = [total / NUM_EPISODES for total in total_rewards]
        return avg_reward
    
    def evaluate_agents(self):
        """
        Evalúa a los agentes en modo de prueba (sin aprendizaje) usando el entorno.
        Retorna una lista con la recompensa promedio de cada agente.
        """
        total_rewards = [0.0 for _ in range(NUM_AGENTS)]
        
        # Poner a todos los agentes en modo evaluacion
        for agent in self.agents:
            agent.actor.eval()
            agent.critic.eval()
        
        for episode in range(NUM_EPISODES):
            states = self.env.reset()
            for step in range(MAX_STEPS):
                actions = [agent.select_action(states[i]) for i, agent in enumerate(self.agents)]
                next_states, rewards, done = self.env.step(actions)
                for i in range(NUM_AGENTS):
                    total_rewards[i] += rewards[i]
                states = next_states
                if done:
                    break
        
        # Volver al modo entrenamiento
        for agent in self.agents:
            agent.actor.train()
            agent.critic.train()
            
            # Limpiar los buffers para evitar acumulaciones de datos de evaluación
            agent.log_probs = []
            agent.values = []
            agent.rewards = []
        
        avg_rewards = [total / NUM_EPISODES for total in total_rewards]
        return avg_rewards
    
    # -------------------
    # FUNCIONES DE GUARDADO/CARGA DEL MODELO
    # -------------------
    def load_model_if_exist(self):
        """Si existe un modelo guardado, lo carga en todos los agentes y actualiza la mejor recompensa."""
        if os.path.exists(BEST_MODEL_PATH):
            for agent in self.agents:
                agent.load_model(BEST_MODEL_PATH)
            # Evalua a los agentes para actualizar la mejor recompensa base
            eval_avg_rewards = self.evaluate_agents()
            self.best_reward = max(eval_avg_rewards)
            print(f"Modelo cargado desde disco. Recompensa base: {self.best_reward:.2f}")
        
    def save_best_model(self, avg_rewards):
        """
        Selecciona el agente con la mayor recompensa promedio y, si mejora la recompensa,
        guarda su modelo.
        """
        # Seleccionamos el agente con la mejor recompensa de evaluación
        best_index = max(range(NUM_AGENTS), key=lambda i: avg_rewards[i])
        best_reward = avg_rewards[best_index]
        print(f"Mejor agente: {best_index} con recompensa: {best_reward:.2f}")
        
        
        # Guardamos el modelo solo si la recompensa actual supera la mejor recompensa
        
        if best_reward > self.best_reward:
            self.best_reward = best_reward
            self.agents[best_index].save_model(BEST_MODEL_PATH)
            print("Se guardo un mejor modelo")
        self.best_agent_index = best_index
    
    # -------------------------------------------------------------
    # FUNCIONES PARA OBTENER INFORMACION DE LOS CYRAS Y LOS AGENTES
    # -------------------------------------------------------------
    def get_cyras_status(self):
        """
        Obtiene la salud, energia y hambre de todos los cyras.
        """
        health_list = []
        energy_list = []
        hunger_list = []
        for cyra in self.env.cyras:
            health_list.append(cyra.health)
            energy_list.append(cyra.energy)
            hunger_list.append(cyra.hunger)
        return health_list, energy_list, hunger_list