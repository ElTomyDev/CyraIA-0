import math
import pygame
import random
from trainer.entities.cyras import Cyra
from trainer.entities.foods import Food
from enums.health_actions import HealthActions
from enums.health_states import HealthStates
from enums.hunger_states import HungerStates
from enums.energy_states import EnergyStates

class Environment:
    def __init__(self, screen, num_cyras=5):
        
        self.screen = screen
        self.screen_width, self.screen_height = self.screen.get_size()
        self.num_cyras = num_cyras  # Cantidad de cyras
        
        self.random_pos = (random.randint(0, self.screen_width), random.randint(0, self.screen_height)) # Direccion random
        
        # Lista de agentes (cyras) y la comida
        self.cyras = [Cyra(pygame.math.Vector2(self.random_pos)) for _ in range(self.num_cyras)]
        self.food = [Food() for _ in range(10)]
        self.all_objects = []
        
        self.reward = 0
        self.cant_deads = 0 # Cantidad de cyras muertos
        
       # ---------- Umbrales ----------
        self.eat_threshold = 25.0                  # Umbral para considerar que se "come" la comida
        self.angle_threshold = math.radians(15.0)  # Umbral para considerar bonus por girar
        self.corner_threshold = 20.0               # Umbral de esquina para otorgar penalizacion
        self.max_repeat_position = 3               # Maximas posiciones repetidas permitidas; si aumenta, se penaliza
        
        # ---------- Parámetros de recompensa/penalización ----------
        
        # Recompensas y Penalizaciones de la Comida y el Hambre
        self.enable_food_and_hunger_rewards = True # Habilita o desabilita las recompensas y penalizaciones de la comida y el hambre
        
        self.upgrade_food_dist_bonus = 0.0         # Bonus si mejora la distancia hacia la comida
        self.food_eat_bonus = 0.0                  # Bonus extra cuando se come la comida
        self.food_found_bonus = 0.0                # Bonus por encontrar comida en el rango de vision
        self.hunger_good_bonus = 0.0               # Bonus por tener el hambre en buen estado
        
        self.no_upgrade_food_dist_penalty = 0.0    # Penalizacion si no mejora la distancia a la comida
        self.no_food_in_range_penalty = 0.0        # Penalizacion si tiene hambre y no se encuentra comida en el rango de vision
        self.hunger_hungry_penalty = 0.0           # Penalización si el estado es hambriento
        self.hunger_critic_penalty = 0.0           # Penalizacion si el del hambre estado es critico
        
        # Recompensas y Penalizaciones de la Energia
        self.enable_energy_rewards = True   # Habilita o desabilita las recompensas y penalizaciones de la energia
        
        self.energy_recharge_bonus = 0.0    # Bonus por recargar energia
        self.energy_good_bonus = 0.0        # Bonus por tener la energia en buen estado
        
        self.energy_weary_penalty = 0.0     # Penalizacion si esta en estado de cansancio
        self.energy_critic_penalty = 0.0    # Penalizacion si la energia esta en estado critico
        
        # Recompensas y Penalizaciones de la Salud
        self.enable_health_rewards = True    # Habilita o desabilita las recompensas y penalizaciones de la salud
        
        self.health_recove_bonus = 0.0       # Bonus si recupera salud
        self.health_any_bonus = 0.0          # Bonus si la salud esta en un valor fijo
        self.health_good_bonus = 0.0         # Bonus si la salud esta en buen estado
        
        self.health_loss_penalty = 0.0       # Penalizacion si pierde salud
        self.health_wounded_penalty = 0.0    # Penalizacion si el estado de la salud es herido
        self.health_critic_penalty = 0.0     # Penalizacion si la salud esta en estado critico
        self.dead_penalty = 0.0              # Penalizacion si muere
        
        # Recompensas y Penalizaciones de la Pocicion y Direccion
        self.enable_pos_and_dir_rewards = True   # Habilita o desabilita las recompensas y penalizaciones de las direcciones y posiciones
        
        self.change_direction_bonus = 0.0        # Bonus por cambiar de direccion
        self.away_border_bonus = 0.0             # Bonus por alejarse de la pared
        
        self.border_penalty = 0.0                # Penalizacion por llegar al borde de la pantalla
        self.corner_penalty = 0.0                # Penalizacion por estar en la esquina
        self.repeat_position_penalty = 0.0       # Penalizacion si repite posiciones en el mapa 
    
    def reset(self):
        """
        Reinicia el entorno: reposiciona al cyras en el centro y reubica la comida
        """
        states = []
        self.cant_deads = 0
        for food in self.food:
            food.reset()
        for cyra in self.cyras:
            cyra.reset()
            states.append(cyra.get_state() + [0.0 for _ in range(15)])

        return states
    
    def draw(self):
        """
        Borra y redibuja la pantalla con la comida y los cyras.
        """
        self.screen.fill((0, 0, 0))
        for food in self.food:
            food.draw(self.screen)
        for cyra in self.cyras:
            if cyra.health_state != HealthStates.DEAD:
                cyra.draw(self.screen)
    
    def step(self, actions):
        """
        Procesa las acciones de los cyras, actualiza su estado (incluyendo hambre),
        calcula la recompensa en función de varias señales (acercarse a la comida,
        evitar paredes, esquinas, cambio de dirección y manejo del hambre),
        y actualiza el entorno.
        """
        rewards = []
        states = []
        self.all_objects = self.food
           
        for i, cyra in enumerate(self.cyras):
            self.reward = 0
            action = actions[i]
            
            # ** Actualiza al cyra y obtiene toda la informacion **
            old_dist_food, new_dist_food, old_dist_border, new_dist_border, old_pos, old_dir, new_dir, move_speed, cant_objects, cant_food, nearest_food = cyra.update_all(action[0], action[1], action[2], self.all_objects)

            # ** Habilita o no las recompensas y penalizaciones de la comida y el hambre **
            if self.enable_food_and_hunger_rewards:
                self.rewards_and_penalty_food_hunger(cyra, cant_food, old_dist_food, new_dist_food)
            
            # ** Habilita o no las recompensas y penalizaciones de la energia **
            if self.enable_energy_rewards:
                self.rewards_and_penalty_energy(cyra)
            
            # ** Habilita o no las recompensas y penalizaciones de la salud **
            if self.enable_health_rewards:
                self.rewards_and_penalty_health(cyra)
            
            # ** Habilita o no las recompensas y penalizaciones de las posiciones y direcciones **
            if self.enable_pos_and_dir_rewards:
                self.rewards_and_penalty_direction_position(cyra, old_dist_border, new_dist_border, old_dir, new_dir)
        
            states.append(self.get_enriched_states(cyra, 
                    [old_dist_food, new_dist_food, old_dist_border, new_dist_border, 
                    old_pos.x, old_pos.y, old_dir.x, old_dir.y, new_dir.x, new_dir.y,
                    move_speed, cant_objects, cant_food, nearest_food.x, nearest_food.y]))
            rewards.append(self.reward)
        
        self.draw()
        for cyra in self.cyras:
            if cyra.health_state == HealthStates.DEAD:
                self.cant_deads += 1
        done = self.cant_deads >= len(self.cyras)
        return states, rewards, done
    
    # -------------------------------------
    # FUNCIONES PARA RECOMPENSAS Y CASTIGOS
    #--------------------------------------
    def rewards_and_penalty_food_hunger(self, cyra : Cyra, cant_food, old_dist_food, new_dist_food):
        """
        Se encarga de manejar las rempensas y castigos con respecto a la comida
        """
        # ** Si detecta comida **
        if cant_food > 0:
            # ** Si se detecta comida dentro de el rango de vision recompensar por cantidad vista **
            self.reward += self.food_found_bonus * (cant_food / 2.0)
            
            # ** Recompensa por acercarse a la comida **
            if old_dist_food > new_dist_food:
                self.reward += ((old_dist_food - new_dist_food) / old_dist_food if old_dist_food != 0 else 1.0) * self.upgrade_food_dist_bonus
            
            # ** Penalizacion por alejarse de la comida **
            if old_dist_food < new_dist_food:
                self.reward -= self.no_upgrade_food_dist_penalty

            # ** Recompenza por comer **
            for food in cyra.food_objects:
                near_food = cyra.pos.distance_to(food.pos)
                if near_food < self.eat_threshold:
                    self.reward += self.food_eat_bonus + self.energy_recharge_bonus # se agrega tambien el bonus por recargar energia
                    food.reset()
                    cyra.eat(food.nutrition) # Disminuye el hambre al comer
        else:
            # ** Penalizacion si el cyra tiene hambre y no encuentra comida **
            if cyra.hunger_state == HungerStates.HUNGRY:
                self.reward -= self.no_food_in_range_penalty
            
        # ** Penalizaciones o Recompensas dependiendo del estado del hambre **
        if cyra.hunger_state == HungerStates.HUNGRY:
            self.reward -= self.hunger_hungry_penalty
        elif cyra.hunger_state == HungerStates.CRITIC:
            self.reward -= self.hunger_critic_penalty
        else:
            self.reward += self.hunger_good_bonus
        
    def rewards_and_penalty_energy(self, cyra : Cyra):
        """
        Se encarga de manejar las recompensas y penalizaciones con 
        respecto a la energia del cyra
        """
        # ** Penalizaciones o Recompensas dependiendo del estado de la energia **
        if cyra.energy_state == EnergyStates.WEARY:
            self.reward -= self.energy_weary_penalty
        elif cyra.energy_state == EnergyStates.CRITIC:
            self.reward -= self.energy_critic_penalty
        else:
            self.reward += self.energy_good_bonus
        
    def rewards_and_penalty_health(self, cyra : Cyra):
        """
        Se encarga de manejar las recompensas y penalizaciones
        con respecto a la salud.
        """
        # ** Recompensas y penalizaciones en base al accion de la salud ** 
        if cyra.health_action == HealthActions.LOSS:
            self.reward -= self.health_loss_penalty
        elif cyra.health_action == HealthActions.RECOVE:
            self.reward += self.health_recove_bonus
        else:
            self.reward += self.health_any_bonus
            
        # ** Recompensas y penalizaciones en base al estado de la salud **
        if cyra.health_state == HealthStates.DEAD:
            self.reward -= self.dead_penalty
        elif cyra.health_state == HealthStates.CRITIC:
            self.reward -= self.health_critic_penalty
        elif cyra.health_state == HealthStates.WOUNDED:
            self.reward -= self.health_wounded_penalty
        else:
            self.reward += self.health_good_bonus
    
    def rewards_and_penalty_direction_position(self, cyra : Cyra, old_dist_border, new_dist_border, old_dir, new_dir):
        """
        Se encarga de manejar las Recompensas y Penalizaciones 
        en con respecto a las posiciones y direcciones.
        """
        # ** Recompensa por alejarse de la pared **
        if new_dist_border > old_dist_border:
            self.reward += (new_dist_border - old_dist_border) * self.away_border_bonus
        
        # ** Recompensa por cambiar de direccion **
        if old_dir is not None:
            ang = self.angle_between(old_dir, new_dir)
            if ang > self.angle_threshold:
                self.reward += self.change_direction_bonus
        
        # ** Penalizacion por chocar con los bordes **
        if (cyra.pos.x <= 0 or cyra.pos.x >= self.screen_width) or (cyra.pos.y <= 0 or cyra.pos.y >= self.screen_height):
            self.reward -= self.border_penalty
        
        # ** Obtiene una lista con la posicion de cada esquina **
        corners = [pygame.math.Vector2(0, 0), # Esquina superior izquierda
                   pygame.math.Vector2(self.screen_width, 0), # Esquina superior derecha
                   pygame.math.Vector2(0, self.screen_height), # Esquina inferior izquierda
                   pygame.math.Vector2(self.screen_width, self.screen_height)] # Esquina inferior derecha
        
        # ** Penalización por estar en una esquina **
        if min(cyra.pos.distance_to(corner) for corner in corners) < self.corner_threshold:
            self.reward -= self.corner_penalty
        
        # ** Penalizacion si repite posiciones anteriores **
        rounded_dir = (round(new_dir.x, 1), round(new_dir.y, 1)) # Redondeamos la posicion antes de comparar
        if cyra.prev_positions.count(rounded_dir) > self.max_repeat_position:
            self.reward -= self.repeat_position_penalty
    
    #--------------------
    # FUNCIONES AUXILIARES
    #--------------------
    def get_random_rewards_and_penalty(self):
        """
        Actualiza todos los valores de las recompensas y castigos
        fomar random con un rango del 0.0 a 1.0
        """
        x = 0.0
        y = 1.0
        random_value = random.uniform(x, y)
        
        # Recompensas y Penalizaciones de la Comida y el Hambre
        self.upgrade_food_dist_bonus = random_value         
        self.food_eat_bonus = random_value
        self.food_found_bonus = random_value         
        self.hunger_good_bonus = random_value       
        
        self.no_upgrade_food_dist_penalty = random_value    
        self.no_food_in_range_penalty = random_value
        self.hunger_hungry_penalty = random_value
        self.hunger_critic_penalty = random_value  
        
        # Recompensas y Penalizaciones de la Energia
        self.energy_recharge_bonus = random_value
        self.energy_good_bonus = random_value
        
        self.energy_weary_penalty = random_value
        self.energy_critic_penalty = random_value
        
        # Recompensas y Penalizaciones de la Salud
        self.health_recove_bonus = random_value
        self.health_any_bonus = random_value
        self.health_good_bonus = random_value 
        
        self.health_loss_penalty = random_value
        self.health_wounded_penalty = random_value
        self.health_critic_penalty = random_value
        self.dead_penalty = random_value
        
        # Recompensas y Penalizaciones de la Pocicion y Direccion
        self.change_direction_bonus = random_value        
        self.away_border_bonus = random_value
        
        self.border_penalty = random_value    
        self.corner_penalty = random_value       
        self.repeat_position_penalty = random_value       
        
    def get_enriched_states(self, cyra: Cyra, enriched_list : list):
        """
        Devuelve una lista con los estados por defecto de un (cyra) dado, sumada con otra lista
        de (enriched_list) con mas estados.
        """
        
        return cyra.get_state() + enriched_list

    def angle_between(self, v1, v2):
        """Calcula el ángulo en radianes entre los vectores v1 y v2."""
        if v1.length() == 0 or v2.length() == 0:
            return 0.0
        return v1.angle_to(v2)