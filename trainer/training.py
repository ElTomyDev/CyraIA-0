from typing import Any
import pygame
import os
import numpy as np
from trainer.env.environment import Environment
from trainer.env.rewards_and_penalty import RewardsAndPenalty
from cyra_ai.agent.agent import Agent
from config.trainer_config import *
from config.general_config import BEST_MODEL_PATH, FPS
from graphics_and_data.training_data import TrainCsvData
import copy
import torch

class Train:
    def __init__(self, view, is_new_train: bool=True, age:int=3) -> None:
        self.is_new_train = is_new_train
        
        # Obtiene la vista
        self.view = view
        
        self.init_train_values(age)
        
        # Inicializacion del entorno y agentes
        self.env = Environment(self.view.screen, num_cyras=NUM_AGENTS)
        self.cyras = [Agent() for _ in range(NUM_AGENTS)]
        
        # Carga el modelo guardado y este existe y evalua para obtener una recompensa base
        self.load_model_if_exist()

    def init_train_values(self, age:int) -> None:
        if self.is_new_train: # Si es un nuevo entrenamiento
            RewardsAndPenalty.get_random_rewards_and_penalty() # Suministra recompenzas y penalizaciones aleatorias
            TrainCsvData.add_new_train_data_row() # Agrega una nueva fina con los datos del nuevo entrenamiento al csv
            self.generation = 0
            self.best_reward = -float('inf')
            self.current_age = TrainCsvData.get_current_age()
            return
        self.current_age = age
        RewardsAndPenalty.set_rewards_and_penalty_values(self.current_age)
        self.best_reward = float(TrainCsvData.get_train_data_by_age(self.current_age)['best_reward'])
        self.generation = int(TrainCsvData.get_train_data_by_age(self.current_age)['generations'])
        
    # --------------------------
    # FUNCIONES DE ENTRENAMIENTO Y EVALUACION
    # --------------------------
    def run_generation(self) -> float:
        """
        Ejecuta un ciclo de entrenamiento (generación) en el entorno.
        Se reutiliza el objeto Environment y se acumulan recompensas de cada episodio.
        Retorna la recompensa promedio por agente para la generación.
        """
        self.generation += 1
        states = self.env.reset() # Reposiciona a todos los cyras y actualiza la comida
        generation_rewards = np.zeros(NUM_AGENTS)
        
        for step in range(MAX_STEPS):
            # Selecciona una accion para cada agente usando su estado actual
            actions = [agent.select_action(states[i]) for i, agent in enumerate(self.cyras)]

            # Actualiza el entorno con las acciones y obtiene nuevos estados y recompensas
            next_states, rewards, done = self.env.step(actions)
            
            # Almacena la recompensa de cada agente
            for i in range(NUM_AGENTS):
                #agent.store_reward(rewards[i])
                self.cyras[i].store_reward(rewards[i])
                generation_rewards[i] += rewards[i]
            
            states = next_states
            # Actializa la pantalla en cada paso
            pygame.display.flip()
            self.view.clock.tick(FPS)
            
            # Verifica eventos de teclado y si puede seguir con con la generacion
            self.view.process_events()
            if done or not self.view.train_running:
                break
            
        # Al final de cada generacion, cada agente actualiza su politica
        for agent in self.cyras:
            agent.learn()
            
        
        
        return generation_rewards
    
    def evolve_population(self, avg_rewards) -> None:
        """
        Selecciona al mejor agente y genera una nueva población
        copiando sus parámetros con pequeñas mutaciones.
        """
        best_index = int(np.argmax(avg_rewards))
        best_agent = self.cyras[best_index]
        best_reward = avg_rewards[best_index]

        new_cyras = []
        for i in range(len(self.cyras)):
            if i == best_index:
                # mantenemos el mejor sin cambios
                new_cyras.append(best_agent)
            else:
                # clon del mejor + mutación
                clone = copy.deepcopy(best_agent)
                self._mutate_agent(clone, mutation_rate=0.05, mutation_std=0.02)
                new_cyras.append(clone)
        
        if best_reward > self.best_reward:
            self.best_reward = best_reward
            self.cyras[best_index].save_model(BEST_MODEL_PATH)
            print("Se guardo un mejor modelo")
        TrainCsvData.update_gen_and_rewards_data(self.current_age, self.generation, self.best_reward)
        
        self.cyras = new_cyras
        

    def _mutate_agent(self, cyra, mutation_rate: float=0.05, mutation_std: float=0.02) -> None:
        """
        Aplica mutaciones gaussianas pequeñas a los parámetros del actor y crítico.
        """
        for param in cyra.actor.parameters():
            if torch.rand(1).item() < mutation_rate:
                noise = torch.randn_like(param) * mutation_std
                param.data.add_(noise)
        for param in cyra.critic.parameters():
            if torch.rand(1).item() < mutation_rate:
                noise = torch.randn_like(param) * mutation_std
                param.data.add_(noise)
    
    def evaluate_agents(self):
        """
        Evalúa a los agentes en modo de prueba (sin aprendizaje) usando el entorno.
        Retorna una lista con la recompensa promedio de cada agente.
        """
        total_rewards = np.zeros(NUM_AGENTS)
        
        # Poner a todos los agentes en modo evaluacion
        for agent in self.agents:
            agent.actor.eval()
            agent.critic.eval()
        
        for episode in range(NUM_EPISODES):
            states = self.env.reset()
            for step in range(MAX_STEPS):
                actions = [agent.select_action(states[i]) for i, agent in enumerate(self.agents)]
                next_states, rewards, done = self.env.step(actions)
                total_rewards += rewards
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
        
        avg_rewards = total_rewards / NUM_EPISODES 
        return total_rewards / NUM_EPISODES 
    
    # -------------------
    # FUNCIONES DE GUARDADO/CARGA DEL MODELO
    # -------------------
    def load_model_if_exist(self) -> None:
        """Si existe un modelo guardado, lo carga en todos los agentes y actualiza la mejor recompensa."""
        if os.path.exists(BEST_MODEL_PATH) and self.is_new_train == False:
            for agent in self.cyras:
                agent.load_model(BEST_MODEL_PATH)
            TrainCsvData.update_gen_and_rewards_data(self.current_age, self.generation, self.best_reward)
            #TrainCsvData.recove_best_reward_and_gen()
            print("Mejor modelo cargado")
    