import math
import pygame
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
        
        # Lista de agentes (cyras) y la comida
        self.cyras = [Cyra(pygame.math.Vector2(self.screen_width//2, self.screen_height//2)) for _ in range(self.num_cyras)]  # Por ahora, un cyras en el centro
        self.food = [Food(self.screen_width, self.screen_height) for _ in range(10)]
        self.all_objects = []
        
        self.reward = 0
        
       # ---------- Umbrales ----------
        self.eat_threshold = 35.0                  # umbral para considerar que se "come" la comida
        self.angle_threshold = math.radians(15.0)  # Umbral para considerar bonus por girar
        self.corner_threshold = 60.0               # Umbral de esquina para otorgar penalizacion
        self.hunger_threshold = 0.3                # Umbral de hambre para otorgar bonus
        self.low_energy_threshold = 0.2            # Umbral de energía baja; si cae por debajo, se penaliza
        self.low_health_threshold = 45.0           # Umbral de salud baja; si cae por debajo, se penaliza
        self.max_repeat_position = 3               # Maximas posiciones repetidas permitidas; si aumenta, se penaliza
        self.optimal_hunger_min = 0.6              # Nivel de hambre; si aumenta, se penaliza.
        
        # ---------- Parámetros de recompensa/penalización ----------
        
        # Recompensas y Penalizaciones de la Comida y el Hambre
        self.enable_food_and_hunger_rewards = True # Habilita o desabilita las recompensas y penalizaciones de la comida y el hambre
        
        self.upgrade_food_dist_bonus = 10.5        # Bonus si mejora la distancia hacia la comida
        self.food_eat_bonus = 30.5                 # Bonus extra cuando se come la comida
        self.food_found_bonus = 4.0                # Bonus por encontrar comida en el rango de vision
        self.hunger_good_bonus = 0.0               # Bonus por tener el hambre en buen estado
        
        self.no_upgrade_food_dist_penalty = 3.0    # Penalizacion si no mejora la distancia a la comida
        self.no_food_in_range_penalty = 6.2        # Penalizacion si tiene hambre y no se encuentra comida en el rango de vision
        self.hunger_hungry_penalty = 4.5           # Penalización si el estado es hambriento
        self.hunger_critic_penalty = 4.5           # Penalizacion si el del hambre estado es critico
        
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
        self.repeat_position_penalty = 0.05      # Penalizacion si repite posiciones en el mapa 
    
    def reset(self):
        """
        Reinicia el entorno: reposiciona al cyras en el centro y reubica la comida
        """
        self.cyras = [Cyra(pygame.math.Vector2(self.screen_width//2, self.screen_height//2)) for _ in range(self.num_cyras)]
        for food in self.food:
            food.respawn()
        for cyra in self.cyras:
            cyra.reset(self.screen_width, self.screen_height)
        return self.get_enriched_states()
    
    def draw(self):
        """
        Borra y redibuja la pantalla con la comida y los cyras.
        """
        self.screen.fill((0, 0, 0))
        for food in self.food:
            food.draw(self.screen)
        for cyra in self.cyras:
            cyra.draw(self.screen)
    
    def step(self, actions):
        """
        Procesa las acciones de los cyras, actualiza su estado (incluyendo hambre),
        calcula la recompensa en función de varias señales (acercarse a la comida,
        evitar paredes, esquinas, cambio de dirección y manejo del hambre),
        y actualiza el entorno.
        """
        rewards = []
        self.all_objects = self.food
           
        for i, cyra in enumerate(self.cyras):
            self.reward = 0
            action = actions[i]
            
            # ** Actualiza al cyra y obtiene toda la informacion **
            old_dist_food, new_dist_food, old_dist_border, new_dist_border, old_pos, old_dir, new_dir, move_speed, cant_objects, cant_food, nearest_food = cyra.update_all(actions[0], actions[1], actions[2], self.all_objects)

            # ** Habilita o no las recompensas y penalizaciones de la comida y el hambre **
            if self.enable_food_and_hunger_rewards:
                self.rewards_and_penalty_food_hunger(cyra, nearest_food, cant_food, old_dist_food, new_dist_food)
            
            # ** Habilita o no las recompensas y penalizaciones de la energia **
            if self.enable_energy_rewards:
                self.rewards_and_penalty_energy(cyra)
            
            # ** Habilita o no las recompensas y penalizaciones de la salud **
            if self.enable_health_rewards:
                self.rewards_and_penalty_health(cyra)
            
            # ** Habilita o no las recompensas y penalizaciones de las posiciones y direcciones **
            if self.enable_pos_and_dir_rewards:
                self.rewards_and_penalty_direction_position(cyra, old_dist_border, new_dist_border, old_dir, new_dir)

            rewards.append(self.reward)
        self.draw()
        done = len(self.cyras) == 0
        states = self.get_enriched_states()

        return states, rewards, done
    
    # -------------------------------------
    # FUNCIONES PARA RECOMPENSAS Y CASTIGOS
    #--------------------------------------
    def rewards_and_penalty_food_hunger(self, cyra : Cyra, nearest_food, cant_food, old_dist_food, new_dist_food):
        """
        Se encarga de manejar las rempensas y castigos con respecto a la comida
        """
        # ** Si detecta comida **
        if cant_food > 0:
            # ** Si se detecta comida dentro de el rango de vision recompensar por cantidad vista **
            self.reward += self.food_found_bonus * (float(len(cant_food)) / 2.0)
            
            # ** Recompensa por acercarse a la comida **
            if old_dist_food > new_dist_food:
                self.reward += ((old_dist_food - new_dist_food) / old_dist_food) * self.upgrade_food_dist_bonus
            
            # ** Penalizacion por alejarse de la comida **
            if old_dist_food < new_dist_food:
                reward -= self.no_upgrade_food_dist_penalty

            # ** Recompenza por comer **
            if new_dist_food < self.eat_threshold:
                self.reward += self.food_eat_bonus + self.energy_recharge_bonus # se agrega tambien el bonus por recargar energia
                nearest_food.respawn()
                cyra.eat(nearest_food.nutrition) # Disminuye el hambre al comer
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
        if cyra.health_state == HealthStates.CRITIC:
            self.reward -= self.health_critic_penalty
        elif cyra.health_state == HealthStates.WOUNDED:
            self.reward -= self.health_wounded_penalty
        else:
            self.reward += self.health_good_bonus
        
        # ** Penalizacion si muere **
        if cyra.health <= 0.0:
            reward -= self.dead_penalty
            self.cyras = [cyra for cyra in self.cyras if cyra.health > 0]
    
    def rewards_and_penalty_direction_position(self, cyra : Cyra, old_dist_border, new_dist_border, old_dir, new_dir):
        """
        Se encarga de manejar las Recompensas y Penalizaciones 
        en con respecto a las posiciones y direcciones.
        """
        # ** Recompensa por alejarse de la pared **
        if new_dist_border > old_dist_border:
            reward += (new_dist_border - old_dist_border) * self.away_border_bonus
        
        # ** Recompensa por cambiar de direccion **
        if old_dir is not None:
            ang = self.angle_between(old_dir, new_dir)
            if ang > self.angle_threshold:
                reward += self.change_direction_bonus
        
        # ** Penalizacion por chocar con los bordes **
        if (cyra.pos.x <= 0 or cyra.pos.x >= self.screen_width) or (cyra.pos.y <= 0 or cyra.pos.y >= self.screen_height):
            reward -= self.border_penalty
        
        # ** Obtiene una lista con la posicion de cada esquina **
        corners = [pygame.math.Vector2(0, 0), # Esquina superior izquierda
                   pygame.math.Vector2(self.screen_width, 0), # Esquina superior derecha
                   pygame.math.Vector2(0, self.screen_height), # Esquina inferior izquierda
                   pygame.math.Vector2(self.screen_width, self.screen_height)] # Esquina inferior derecha
        
        # ** Penalización por estar en una esquina **
        if min(cyra.pos.distance_to(corner) for corner in corners) < self.corner_threshold:
            reward -= self.corner_penalty
        
        # ** Penalizacion si repite posiciones anteriores **
        rounded_dir = (round(new_dir.x, 1), round(new_dir.y, 1)) # Redondeamos la posicion antes de comparar
        if cyra.prev_positions.count(rounded_dir) > self.max_repeat_position:
            reward -= self.repeat_position_penalty
    
    #--------------------
    # FUNCIONES AUXILIARES
    #--------------------
    def get_enriched_states(self):
        """
        Recorre todos los cyras y genera un vector de estado enriquecido para cada uno.
        El estado enriquecido incluye:
        [x, y, hunger, last_speed, distancia_al_alimento, distancia_al_borde]
        """
        enriched_states = []
        for cyra in self.cyras: 
            closest_food, dist_food = self.get_closest_food(cyra.pos)
            
            # Vector de direccion hacia la comida
            food_direction = (closest_food.pos - cyra.pos).normalize() if dist_food > 0 else pygame.math.Vector2(0, 0)
            if dist_food > cyra.detect_radio:
                food_direction = pygame.math.Vector2(0, 0)
            
            # Calcular la distancia a los bordes
            dist_to_border_x = min(cyra.pos.x, self.screen_width - cyra.pos.x)
            dist_to_border_y = min(cyra.pos.y, self.screen_height - cyra.pos.y)
            
            # Normalizamos posiciones pasadas
            flattened_positions = []
            for pos in cyra.prev_positions:
                flattened_positions.extend([pos[0], pos[1]])  # Normalizamos

            # Si hay menos posiciones, rellenamos con ceros
            while len(flattened_positions) < 10 * 2:  # 10 posiciones * 2 coordenadas (x, y)
                flattened_positions.append(0.0)
            
            
            # Armar el estado enriquecido: estado base, distancia a la comida y dirección
            enriched_state = cyra.get_state() + [dist_food, food_direction.x, food_direction.y, dist_to_border_x, dist_to_border_y]
            enriched_states.append(enriched_state)
        return enriched_states

    def angle_between(self, v1, v2):
        """Calcula el ángulo en radianes entre los vectores v1 y v2."""
        if v1.length() == 0 or v2.length() == 0:
            return 0.0
        return v1.angle_to(v2)