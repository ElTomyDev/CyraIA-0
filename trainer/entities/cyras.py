from typing import Any
import pygame
import random
import numpy as np
from enums.health_actions import HealthActions
from enums.health_states import HealthStates
from enums.hunger_states import HungerStates
from enums.energy_states import EnergyStates
from enums.object_types import ObjectTypes
from config.general_config import WINDOWS_WIDTH, WINDOWS_HEIGHT, FIRST_CYRA_COLOR, TWO_CYRA_COLOR

class Cyra:
    def __init__(self, pos, id) -> None:
        # --- Configuracion de Cyra
        self.obj_type = ObjectTypes.CYRA
        self.cyra_id = id
        
        # --- Posicion
        self.pos = pygame.Vector2(pos)                              # Copia de la posicion inicial
        self.prev_direction = pygame.Vector2(self.pos)              # Direccion previa del movimiento
        self.max_prev_positions = 5                                 # Cantidad de posiciones a guardar en la lista (prev_positions)
        self.prev_positions = np.zeros((self.max_prev_positions,2)) # Ultimas (max_prev_positions) posiciones
        
        # --- Velocidad
        self.max_speed = 5                                  # Velocidad maxima permitida
        self.last_speed = 0.0                               # Magnitud del ultimo movimiento
        
        # --- Hambre
        self.hunger = 1.0                                   # Nivel de hambre inicial
        self.max_hunger = 1.0                               # Maximo nivel de hambre
        self.hunger_decrement = 0.002                       # La cantidad de hambre que se incrementa en cada paso
        self.hunger_state = HungerStates.GOOD               # Estado actual del hambre
        self.hunger_hungry_threshold = 0.5                  # Umbral minimo para considerarse hambriento
        self.hunger_crititc_threshold = 0.2                 # Umbral maximo para estado critico de hambre
        
        # --- Energia
        self.energy = 1.0                                   # Energia inicial
        self.max_energy = 1.0                               # Energia maxima
        self.energy_decrement = 0.001                       # Perdida de energia
        self.energy_increment_idle = 0.0015                  # carga de energia por estar quieto
        self.energy_state = EnergyStates.GOOD               # Estado actual de la energia
        self.energy_weary_threshold = 0.5                   # Umbral minimo para considerarse cansado
        self.energy_critic_threshold = 0.2                  # Umbral maximo para considerarse muy cansado
        
        # --- Salud
        self.health = 1.0                                   # Nivel de salud actual
        self.max_health = 1.0                               # Maximo nivel de salud
        self.health_decrement = 0.01                        # Incremento de la salud
        self.health_increment = 0.015                       # Decremento de la salud
        self.health_action = HealthActions.ANY              # Accion actual de la salud
        self.health_state = HealthStates.GOOD               # Estado actual de la salud
        self.health_wounded_threshold = 0.5                 # Umbral minimo para considerarse herido
        self.health_critic_threshold = 0.2                  # Umbral maximo para considerarse en estado critico
        
        # --- Deteccion de objetos
        self.detect_radio = 150.0                           # Radio de deteccion
        self.detected_objects = []                          # Lista de todos los objetos detectados
        self.food_objects = []                              # Lista de comida detectada
    
    def update_all(self, directions, speed, all_objects) -> Any:
        """
        Se encarga de actualizar todos los parametros y estados del cyra.
        """
        # ** Actualiza las detecciones de los objetos **
        self.update_detection_objects(all_objects)
        self.update_food_objects()
        
        # ** Obtiene la cantidad total de objetos y las cantidades de cada objeto detectado por separado **
        cant_objects = self.cant_detected_objects() # Cantidad total de objetos
        cant_food = self.cant_food_objects() # Cantidad total de comida
        
        # ** Obtiene la comida mas cercana al cyra **
        nearest_food = self.get_nearest_food()
        
        # ** Obtiene la distancia hacia la comida mas cercana antes de moverse **
        old_dist_food = min(self.pos.x, nearest_food.x - self.pos.x,
                            self.pos.y, nearest_food.y - self.pos.y)
        
        # ** Calcular distancias al borde y al alimento antes de moverse **
        old_dist_border = min(self.pos.x, WINDOWS_WIDTH - self.pos.x,
                            self.pos.y, WINDOWS_HEIGHT - self.pos.y)
        
        # ** Actualiza la salud del cyra **
        self.update_health()
        
        # ** Obtiene la antigua posicion del cyra antes de moverse **
        old_pos = self.pos.copy()
        
        # ---- FUNCIONES ANTES DE MOVERSE ---- <
        
        old_dir, new_dir, move_speed = self.move(directions, speed) # Mueve al cyra 
        
        # ---- FUNCIONES DESPUES DE MOVERSE ---- >
        
        # ** Obtiene la distancia hacia la comida mas cercana antes de moverse **
        new_dist_food = min(self.pos.x, nearest_food.x - self.pos.x,
                            self.pos.y, nearest_food.y - self.pos.y)
        
        # ** Calcular distancias al borde y al alimento despues de moverse **
        new_dist_border = min(self.pos.x, WINDOWS_WIDTH - self.pos.x,
                            self.pos.y, WINDOWS_HEIGHT - self.pos.y)
        
        # ** Actualiza el hambre en funcion del movimiento ** 
        self.update_hunger()
        
        # ** Actualiza la energia del cyra en funcion al movimiento **
        self.update_energy(move_speed)
        
        # ** Actualiza la lista de posiciones **
        self.update_prev_positions(old_pos)

        return old_dist_food, new_dist_food, old_dist_border, new_dist_border, old_pos, old_dir, new_dir, move_speed, cant_objects, cant_food, nearest_food
        
    # -----------------------
    # FUNCIONES PARA LA SALUD
    # -----------------------
    def recharge_health(self, cant_recharge) -> None:
        """
        Recarga la salud, en función del valor recarga.
        """
        self.health = min(self.health + cant_recharge, self.max_health)
    
    def reduce_health(self, reduce) -> None:
        """
        Disminuye la cantidad de salud en base a una reduccion 'reduce'.
        """
        self.health = max(self.health - reduce, 0.0)

    def update_health(self) -> None:
        """
        Disminuye la salud si el hambre sobrepasa el umbral.
        """
        if self.hunger_state == HungerStates.CRITIC:
            self.reduce_health(self.health_decrement)
            self.health_action = HealthActions.LOSS
        elif self.hunger_state == HungerStates.GOOD:
            self.recharge_health(self.health_increment)
            self.health_action = HealthActions.RECOVE
        else:
            self.health_action = HealthActions.ANY

        # Actualiza es estado actual de la salud
        if self.health <= 0.0:
            self.health_state = HealthStates.DEAD
        if self.health < self.health_critic_threshold:
            self.health_state = HealthStates.CRITIC
        elif self.health < self.health_wounded_threshold:
            self.health_state = HealthStates.WOUNDED
        else:
            self.health_state = HealthStates.GOOD
    
    # ------------------------
    # FUNCIONES PARA EL HAMBRE
    # ------------------------
    def reduce_hunger(self) -> None:
        """
        Incrementa el hambre, en función del movimiento.
        """
        if not self.energy_state == EnergyStates.CRITIC:
            self.hunger = max(self.hunger - self.hunger_decrement, 0.0)
            return
        self.hunger = max(self.hunger - (self.hunger_decrement * 5), 0.0)
        
    def recharge_hunger(self, cant_recharge) -> None:
        """
        decrementa la cantidad de hambre.
        """
        self.hunger = min(self.hunger + cant_recharge, self.max_hunger)
    
    def update_hunger(self) -> None:
        """
        Actualiza el hambre en funcion del movimiento y tambien actualiza su estado.
        """
        self.reduce_hunger()
        if self.hunger <= self.hunger_crititc_threshold:
            self.hunger_state = HungerStates.CRITIC
        elif self.hunger <= self.hunger_hungry_threshold:
            self.hunger_state = HungerStates.HUNGRY
        else:
            self.hunger_state = HungerStates.GOOD
    
    # -------------------------
    # FUNCIONES PARA LA ENERGIA
    # -------------------------
    def reduce_energy(self, movement_distance, decrement) -> None:
        """
        Disminuye la energía en función de la distancia movida.
        Por ejemplo, consume 0.05 unidades de energía por cada unidad de movimiento.
        """
        move_factor = movement_distance**2
        self.energy = max(self.energy - (decrement * move_factor), 0.0)
    
    def recharge_energy(self, cant_recharge) -> None:
        """
        Recarga la energía, en función del valor recarga.
        """
        self.energy = min(self.energy + cant_recharge, self.max_energy)
    
    def update_energy(self, movement_distance) -> None:
        """
        Actualiza la perdida de energia en funcion al movimiento y el hambre. Acuatilza tambien
        el estado.
        """
        # Actualiza la energia
        if movement_distance <= 0:
            self.recharge_energy(self.energy_increment_idle)
        else:
            self.reduce_energy(movement_distance, self.energy_decrement)
        
        # Actualiza el estado actual de la energia
        if self.energy <= self.energy_critic_threshold:
            self.energy_state = EnergyStates.CRITIC
        elif self.energy <= self.energy_weary_threshold:
            self.energy_state = EnergyStates.WEARY
        else:
            self.energy_state = EnergyStates.GOOD
        
    # --------------------------
    # FUNCIONES PARA LA POSICION
    # --------------------------
    def update_prev_positions(self, position) -> None:
        """
        Actualiza la lista de sus ultimas posiciones
        """
        new_pos = np.array([round(position.x, 1), round(position.y, 1)])
        self.prev_positions = np.roll(self.prev_positions, -1, axis=0)
        self.prev_positions[-1] = new_pos

    # ---------------------------
    # FUNCIONES PARA LAS ACCIONES
    # ---------------------------
    def eat(self, nutrition) -> None:
        """Reduce el hambre y aumenta la energia cuando come."""
        self.recharge_hunger(nutrition)
        self.recharge_energy(nutrition)
    
    def move(self, directions, speed) -> Any:
        """
        Mueve al cyra sumándole dx y dy a su posición, 
        aplicando además un factor de speed para modular la velocidad del movimiento,
        respetando la velocidad máxima y controlando que no se salga de la pantalla.
        
        Retorna:
            old_direction (pygame.Vector2): El vector de movimiento anterior (o None si no existe).
            new_direction (pygame.Vector2): El vector de movimiento actual.
            magnitude (float): La magnitud (velocidad) del movimiento actual.
        """
        up, down, left, right = directions

        dx = right - left   # derecha suma, izquierda resta
        dy = down - up      # abajo suma, arriba resta
        
        # Crea el vector base a partir de dx y dy
        base_direction = pygame.Vector2(dx, dy)
        if base_direction.length_squared() > 0:
            base_direction = base_direction.normalize()
            new_direction = base_direction * min(speed, self.max_speed)
        else:
            new_direction = pygame.Vector2(0, 0)
        
        magnitude = new_direction.length() # Obtiene la magnitud del movimiento

        if not self.health <= 0.0: # Si no esta muerto
            self.pos += new_direction # Actualiza su posicion
        
        # Control de bordes
        self.pos.x = max(0, min(self.pos.x, WINDOWS_WIDTH))
        self.pos.y = max(0, min(self.pos.y, WINDOWS_HEIGHT))

        self.last_speed = magnitude # Guarda la magnitud del movimiento
        # Se guarda y actualiza el vector de direccion anterior
        old_direction = self.prev_direction
        self.prev_direction = new_direction

        return old_direction, new_direction, magnitude
    
    def dead(self) -> None:
        """
        Hace que el cyra muera.
        """
        self.max_speed = 0
        
    # -----------------------------
    # FUNCIONES PARA LAS COLISIONES
    # -----------------------------
    def detect_collision_objects(self, obj) -> bool:
        """
        Detecta si un objeto colisiona con el área de detección del Cyra.
        """
        return self.pos.distance_to(obj.pos) <= self.detect_radio

    def update_detection_objects(self, all_objects) -> None:
        """
        Actualiza la lista de objetos detectados dinámicamente.
        - Si un objeto entra en el área, se agrega.
        - Si un objeto sale del área, se elimina.
        """
        new_detected = []
        for obj in all_objects:
            if self.detect_collision_objects(obj):
                new_detected.append(obj)
        
        # Actualizamos la lista
        self.detected_objects = new_detected
    
    def update_food_objects(self) -> None:
        """
        Actualiza la lista de objetos que son solo comida.
        """
        new_food_objects = []
        for obj in self.detected_objects:
            if obj.obj_type == ObjectTypes.FOOD:
                new_food_objects.append(obj)
        
        self.food_objects = new_food_objects
    
    # ----------------------------------
    # FUNCIONES AUXILIARES E INFORMACION
    # ----------------------------------
    def cant_food_objects(self) -> int:
        """
        Devuelve la cantidad de comida que se detecto
        """
        return len(self.food_objects)
    
    def cant_detected_objects(self) -> int:
        """
        Devuelve la cantidad de objetos que se detecto
        """
        return len(self.detected_objects)
    
    def get_nearest_food(self) -> pygame.Vector2:
        """
        Retorna el objeto comida más cercano a cyra.
        
        Retorna:
            El objeto comida más cercano o None si la lista está vacía.
        """
        if not self.food_objects:
            return pygame.Vector2(0.0, 0.0)
        
        # Convierte las posiciones de comida en arrays de Numpy
        food_positions = np.array([[food.pos.x, food.pos.y] for food in self.food_objects])
        cyra_pos = np.array([self.pos.x, self.pos.y])
        
        distances = np.linalg.norm(food_positions - cyra_pos, axis=1)
        ind = np.argmin(distances)
        nearest_food = food_positions[ind]
        
        return pygame.Vector2(nearest_food[0], nearest_food[1])
    
    # ---------------
    # OTRAS FUNCIONES
    # ---------------
    def reset(self) -> None:
        """ Reinicia a los cyras """
        # Reinicia los estados
        self.hunger_state = HungerStates.GOOD
        self.energy_state = EnergyStates.GOOD
        self.health_state = HealthStates.GOOD
        self.health_action = HealthActions.ANY
        
        # Reinicia los valores (Hambre, Salud, Energia)
        self.health = self.max_health
        self.energy = self.max_energy
        self.hunger = self.max_hunger
        
        # Reinicia valores de movimiento (Posicion, Direcciones, Etc)
        self.last_speed = 0.0
        self.max_speed = 3
        self.pos = pygame.math.Vector2(random.randint(0, WINDOWS_WIDTH), random.randint(0, WINDOWS_HEIGHT))
        self.prev_direction = pygame.Vector2(self.pos)
        
        # Reinicia lista de objetos
        self.detected_objects = []
        self.food_objects = []
    
    def get_state(self) -> list:
        """
        Retorna el estado completo del cyra, que incluye la posición y el nivel de hambre.
        
        Returns:
            list: [x, y, hunger, last_speed, prev_direction, energy, max_energy, max_speed]
        """
        # Normalizacion continua
        hunger_norm = self.hunger / self.max_hunger
        energy_norm = self.energy / self.max_energy
        health_norm = self.health / self.max_health
        
        pos_x_norm = self.pos.x / WINDOWS_WIDTH
        pos_y_norm = self.pos.y / WINDOWS_HEIGHT
        speed_norm = self.last_speed / (self.max_speed if self.max_speed > 0 else 1)
        
        # One-hot para estados discretos
        # Hambre (3 estados)
        hunger_onehot = [0, 0, 0]
        hunger_onehot[self.hunger_state.value] = 1

        # Energía (3 estados)
        energy_onehot = [0, 0, 0]
        energy_onehot[self.energy_state.value] = 1

        # Salud (4 estados: GOOD, WOUNDED, CRITIC, DEAD)
        health_onehot = [0, 0, 0, 0]
        health_onehot[self.health_state.value] = 1
        
        
        return [pos_x_norm,
                pos_y_norm,
                hunger_norm,
                energy_norm,
                health_norm,
                speed_norm] + hunger_onehot + energy_onehot + health_onehot
    
    def draw(self, screen) -> None:
        """
        Dibuja al cyras en pantalla como un círculo azul.
        """
        # -----------------------------
        # --- DIBUJA CUERPO DE CYRA ---
        # -----------------------------
        pygame.draw.circle(screen, TWO_CYRA_COLOR, (int(self.pos.x), int(self.pos.y)), 18)
        pygame.draw.circle(screen, FIRST_CYRA_COLOR, (int(self.pos.x), int(self.pos.y)), 15)
        
        # ------------------------------
        # --- DIBUJA BARRAS DE STATS --- 
        # ------------------------------
        bar_x_pos = int(self.pos.x)-10
        health_bar_y_pos = int(self.pos.y)+27
        hunger_bar_y_pos = int(self.pos.y)+21
        energy_bar_y_pos = int(self.pos.y)+15
        #bar_y_relative_pos = (health_bar_y_pos + energy_bar_y_pos + hunger_bar_y_pos) / 3
        
        bar_background_color = (50, 50, 50)
        health_bar_color = (255, 0, 0)
        hunger_bar_color = (255, 164, 32)
        energy_bar_color = (0, 0, 200)
        
        current_health_bar_width = (self.health / self.max_health) * 20
        current_hunger_bar_width = (self.hunger / self.max_hunger) * 20
        current_energy_bar_width = (self.energy / self.max_energy) * 20
        
        if health_bar_y_pos < WINDOWS_HEIGHT: # Si la barra de vida sale de la pantalla
            # Barra de energia
            pygame.draw.rect(screen, bar_background_color, (bar_x_pos, energy_bar_y_pos, 20, 5))
            pygame.draw.rect(screen, energy_bar_color, (bar_x_pos, energy_bar_y_pos, current_energy_bar_width, 5))
            # Barra de hambre
            pygame.draw.rect(screen, bar_background_color, (bar_x_pos, hunger_bar_y_pos, 20, 5))
            pygame.draw.rect(screen, hunger_bar_color, (bar_x_pos, hunger_bar_y_pos, current_hunger_bar_width, 5))
            # Barra de vida
            pygame.draw.rect(screen, bar_background_color, (bar_x_pos, health_bar_y_pos, 20, 5))
            pygame.draw.rect(screen, health_bar_color, (bar_x_pos, health_bar_y_pos, current_health_bar_width, 5))
        else:
            # Barra de energia
            pygame.draw.rect(screen, bar_background_color, (bar_x_pos, -energy_bar_y_pos, 20, 5))
            pygame.draw.rect(screen, energy_bar_color, (bar_x_pos, -energy_bar_y_pos, current_energy_bar_width, 5))
            # Barra de hambre
            pygame.draw.rect(screen, bar_background_color, (bar_x_pos, -hunger_bar_y_pos, 20, 5))
            pygame.draw.rect(screen, hunger_bar_color, (bar_x_pos, -hunger_bar_y_pos, current_hunger_bar_width, 5))
            # Barra de vida
            pygame.draw.rect(screen, bar_background_color, (bar_x_pos, -health_bar_y_pos, 20, 5))
            pygame.draw.rect(screen, health_bar_color, (bar_x_pos, -health_bar_y_pos, current_health_bar_width, 5))
            
        font = pygame.font.SysFont("comic sans ms", 25)
        label = font.render(f"{self.cyra_id}",10,TWO_CYRA_COLOR)
        
        label_x = self.pos.x  - label.get_width() / 2
        label_y = self.pos.y - label.get_height() / 2
        screen.blit(label, (label_x, label_y))
    