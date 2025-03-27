import math
import pygame
from trainer.entities.cyras import Cyra
from trainer.entities.foods import Food
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
        # Recompensas
        self.reward_factor = 10.5             # Factor para recompensar la mejora en distancia
        self.eat_reward = 30.5               # Recompensa extra cuando se come la comida
        self.direction_bonus = 0.0           # Bonos por cambiar de direccion
        self.away_bonus_factor = 0.0         # Bonus por alejarse de la pared
        self.hunger_bonus_factor = 6.0       # Bonus adicional al comer si el hambre es alta
        self.health_bonus_factor = 4.5       # Bonus adicional por recuperar vida
        self.max_health_bonus = 3.5          # Bonus por tener la salud al maximo
        self.food_found_bonus = 4.0          # Bonus por encontrar comida en el rango de vision
        
        # Penalizacion
        self.corner_penalty = 0.0            # Penalizacion por estar en la esquina
        self.border_penalty = 0.0            # Penalizacion por llegar al borde de la pantalla
        self.hunger_penalty_factor = 4.5     # Factor de penalización si el hambre es demasiado baja
        self.no_upgrade_dist_penalty = 3.0   # Penalizacion si no mejora la distancia a la comida
        self.energy_penalty_factor = 1.2     # Penalización si la energía es baja
        self.low_health_penalty = 4.0        # Penalizacion si la salud es baja
        self.dead_penalty = 40.0             # Penalizacion si muere
        self.no_food_in_range = 6.2          # Penlizacion si no se encuentra comida en el rango de vision
        self.repeat_position_penalty = 0.05  # Penalizacion si repite posiciones en el mapa 
    
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
    
    def update(self):
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
            
            # ------------------- RECOMPENSAS ---------------------
            
            # ** Si detecta comida **
            if cant_food > 0:
                # ** Recompensa por acercarse a la comida **
                if old_dist_food > new_dist_food:
                    reward += ((old_dist_food - new_dist_food) / old_dist_food) * reward_factor

                # ** Recompenza por comer **
                if new_dist_food < eat_threshold:
                    bonus = hunger_bonus_factor if cyra.hunger > hunger_threshold else 0
                    reward += eat_reward + bonus
                    nearest_food.respawn()
                    cyra.eat(nearest_food.nutrition) # Reiniciar el hambre al comer
            
            # ** Si recupera vida se recompensa **
            if cyra.health_state == HealthStates.RECOVE:
                reward += health_bonus_factor
        
            # ** Si se detecta comida dentro de el rango de vision recompensar por cantidad vista **
            if cant_food > 0:
                reward += food_found_bonus * (float(len(cant_food)) / 2.0)
            
            # ** Recompensa por alejarse de la pared **
            if new_dist_border > old_dist_border:
                reward += (new_dist_border - old_dist_border) * away_bonus_factor
            
            # ** Recompensa por cambiar de direccion **
            if old_dir is not None:
                ang = self.angle_between(old_dir, new_dir)
                if ang > angle_threshold:
                    reward += direction_bonus
            
            # ** Recompensa por tener la vida al maximo **
            if cyra.health >= cyra.max_health:
                reward += max_health_bonus
            
            # ------------------ PENALIZACIONES -------------------
            
            # ** Si detecta comida **
            if closest_food:
                # ** Penalizacion si no mejora la distancia a la comida **
                if min_dist_after >= min_dist_before:
                    reward -= no_upgrade_dist_penalty
            
            # ** Si no se detecta comida y tiene hambre se penaliza **
            if len(food_objects) == 0 and cyra.hunger >= optimal_hunger_min:
                reward -= no_food_in_range
            
            # ** Penalización por energía baja **
            if cyra.energy < low_energy_threshold:
                reward -= (low_energy_threshold - cyra.energy) * energy_penalty_factor
            
            
            # ** Penalizacion si el hambre aumenta a un estado critico > 0.9 **
            if cyra.hunger >= 0.9: 
                reward -= (cyra.hunger + 0.9) * 10
            elif cyra.hunger > optimal_hunger_min:# ** Penalizacion si el hambre aumento por ensima del umbral optimo **
                reward -= (optimal_hunger_min + cyra.hunger) * hunger_penalty_factor
            
            
            # ** Penalizacion por chocar con los bordes **
            if cyra.pos.x <= 0 or cyra.pos.x >= self.screen_width:
                reward -= border_penalty 
            if cyra.pos.y <= 0 or cyra.pos.y >= self.screen_height:
                reward -= border_penalty
                
            # ** Penalización por estar en una esquina **
            corners = [pygame.math.Vector2(0, 0),
                       pygame.math.Vector2(self.screen_width, 0),
                       pygame.math.Vector2(0, self.screen_height),
                       pygame.math.Vector2(self.screen_width, self.screen_height)]
            
            if min(cyra.pos.distance_to(corner) for corner in corners) < corner_threshold:
                reward -= corner_penalty

            # ** Penalizacion si repite posiciones anteriores **
            rounded_dir = (round(new_dir.x, 1), round(new_dir.y, 1)) # Redondeamos la posicion antes de comparar
            if cyra.prev_positions.count(rounded_dir) > max_repeat_position:
                reward -= repeat_position_penalty
            
            # ** Penalizacion si la vida disminute **
            if cyra.health <= low_health_threshold:
                reward -= low_health_penalty
                cyra.reduce_health()
            
            # ** Penalizacion si muere **
            if cyra.health <= 0.0:
                reward -= dead_penalty
                self.cyras = [cyra for cyra in self.cyras if cyra.health > 0]

            rewards.append(reward)
        self.update()
        done = len(self.cyras) == 0
        states = self.get_enriched_states()

        return states, rewards, done
    
    # -------------------------------------
    # FUNCIONES PARA RECOMPENSAS Y CASTIGOS
    #--------------------------------------
    def rewards_and_penalty_food(self, cyra : Cyra, nearest_food, cant_food, old_dist_food, new_dist_food):
        """
        Se encarga de manejar las rempensas y castigos con respecto a la comida
        """
        # ** Si detecta comida **
        if cant_food > 0:
            # ** Si se detecta comida dentro de el rango de vision recompensar por cantidad vista **
            self.reward += self.food_found_bonus * (float(len(cant_food)) / 2.0)
            
            # ** Recompensa por acercarse a la comida **
            if old_dist_food > new_dist_food:
                self.reward += ((old_dist_food - new_dist_food) / old_dist_food) * self.reward_factor

            # ** Recompenza por comer **
            if new_dist_food < self.eat_threshold:
                bonus = self.hunger_bonus_factor if cyra.hunger > self.hunger_threshold else 0
                self.reward += self.eat_reward + bonus
                nearest_food.respawn()
                cyra.eat(nearest_food.nutrition) # Reiniciar el hambre al comer
        else:
            # ** Penalizacion si el cyra tiene hambre y no encuentra comida **
            if cyra.hunger_state == HungerStates.HUNGRY:
                self.reward -= self.no_food_in_range
        
    
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
    
    def get_closest_food(self, pos):
        """Encuentra la comida más cercana a la posición dada y retorna (food, distancia)."""
        closest_food = min(self.food, key=lambda food: pos.distance_to(food.pos))
        return closest_food, pos.distance_to(closest_food.pos)
    
    def calc_distance(self, point1, point2):
        """
        Calcula la distancia euclidiana entre dos puntos.

        Args:
            point1 (tuple or list): Coordenadas (x, y) del primer punto.
            point2 (tuple or list): Coordenadas (x, y) del segundo punto.

        Returns:
            float: La distancia entre ambos puntos.
        """
        dx = point2[0] - point1[0]
        dy = point2[1] - point1[1]
        return math.sqrt(dx**2 + dy**2)

    def angle_between(self, v1, v2):
        """Calcula el ángulo en radianes entre los vectores v1 y v2."""
        if v1.length() == 0 or v2.length() == 0:
            return 0.0
        return v1.angle_to(v2)