import pygame
from enums.health_states import HealthStates
from enums.hunger_states import HungerStates

class Cyra:
    def __init__(self, pos):
        # --- Posicion
        self.pos = pygame.math.Vector2(pos)                 # Copia de la posicion inicial
        self.prev_direction = pygame.Vector2(self.pos)      # Direccion previa del movimiento
        self.prev_positions = []                            # Ultimas 6 posiciones
        
        # --- Velocidad
        self.max_speed = 3                                  # Velocidad maxima permitida
        self.last_speed = 0.0                               # Magnitud del ultimo movimiento
        
        # --- Hambre
        self.hunger = 0.0                                   # Nivel de hambre inicial
        self.max_hunger = 1.0                               # Maximo nivel de hambre
        self.hunger_increment = 0.001                       # La cantidad de hambre que se incrementa en cada paso
        self.hunger_state = HungerStates.HUNGRY             # Estado actual del hambre
        self.min_hunger_threshold = 0.7                     # Umbral minimo para considerarse hambriento
        self.max_hunger_threshold = 0.9                     # Umbral maximo para estado critico de hambre
        
        # --- Energia
        self.energy = 1.0                                   # Energia inicial
        self.max_energy = 1.0                               # Energia maxima
        
        # --- Salud
        self.health = 100.0                                 # Nivel de salud actual
        self.max_health = 100.0                             # Maximo nivel de salud
        self.min_health_charge = 0.2                        # Candidad minima de aumento de salud
        self.max_health_charge = 0.5                        # Candidad maxima de aumento de salud
        self.min_health_loss = 0.05                         # Cantidad minima de decremento de salud
        self.max_health_loss = 0.1                          # Cantidad maxima de decremento de salud
        self.health_state = HealthStates.ANY                # Estado actual de la salud
        self.min_health_recovery_hunger = 0.6               # Umbral minimo de hambre para recuperar salud
        self.max_health_recovery_hunger = 0.2               # Umbral maximo de hambre para recuperar salud
        self.min_health_loss_hunger = 0.7                   # Umbral minimo de hambre para perder salud
        self.max_health_loss_hunger = 0.95                  # Umbral maximo de hambre para perder salud
        
        # --- Rango de deteccion
        self.detect_radio = 150.0                           # Radio de deteccion
        self.detected_objects = []                          # Lista de objetos detectados
    
    def update_states():
        """
        Se encarga de actualizar todos los parametros y estados del cyra.
        """
        
        
    # -----------------------
    # FUNCIONES PARA LA SALUD
    # -----------------------
    def recharge_health(self, cant_recharge):
        """
        Recarga la salud, en función del valor recarga.
        """
        self.health = min(self.health + cant_recharge, self.max_health)
    
    def reduce_health(self, reduce):
        """
        Disminuye la cantidad de salud en base a una reduccion 'reduce'.
        """
        self.health = max(self.health - reduce, 0.0)

    def update_health(self):
        """
        Disminuye la salud si el hambre sobrepasa el umbral.
        """
        if self.hunger >= self.max_health_loss_hunger:
            self.reduce_health(self.max_health_loss)
            self.health_state = HealthStates.LOSS
        elif self.hunger >= self.min_health_loss_hunger:
            self.reduce_health(self.min_health_loss)
            self.health_state = HealthStates.LOSS
        elif self.hunger <= self.max_health_recovery_hunger:
            self.recharge_health(self.max_health_charge)
            self.health_state = HealthStates.RECOVE
        elif self.hunger <= self.min_health_recovery_hunger:
            self.recharge_health(self.min_health_charge)
            self.health_state = HealthStates.RECOVE
        else:
            self.health_state = HealthStates.ANY
    
    # ------------------------
    # FUNCIONES PARA EL HAMBRE
    # ------------------------
    def increment_hunger(self, movement_distance):
        """
        Incrementa el hambre, en función del movimiento.
        """
        move_factor = movement_distance if movement_distance > 0 else 1.0
        self.hunger = min(self.hunger + (self.hunger_increment * move_factor), self.max_hunger)
    
    def reduce_hunger(self, reduce):
        """
        Disminuye la cantidad de hambre en base a una reduccion 'reduce'.
        """
        self.hunger = max(self.hunger - reduce, 0.0)
    
    def update_hunger(self, movement_distance):
        """
        Actualiza el hambre en funcion del movimiento y tambien actualiza su estado.
        """
        self.increment_hunger(movement_distance)
        if self.hunger >= self.max_hunger_threshold:
            self.hunger_state = HungerStates.CRITIC
        elif self.hunger >= self.min_hunger_threshold:
            self.hunger_state = HungerStates.HUNGRY
        else:
            self.hunger = HungerStates.GOOD
    
    # -------------------------
    # FUNCIONES PARA LA ENERGIA
    # -------------------------
    def update_energy(self, movement_distance):
        """
        Disminuye la energía en función de la distancia movida.
        Por ejemplo, consume 0.05 unidades de energía por cada unidad de movimiento.
        """
        consumption = 0.0001 * movement_distance  # Ajustá este factor según convenga
        self.energy = max(self.energy - consumption, 0.0)
    
    def recharge_energy(self, cant_recharge):
        """
        Recarga la energía, en función del valor recarga.
        """
        self.energy = min(self.energy + cant_recharge, self.max_energy)
    
    def update_positions(self, position):
        """
        Actualiza la lista de sus ultimas posiciones
        """
        rounded_pos = (round(position.x, 1), round(position.y, 1))
        self.prev_positions.append(rounded_pos)
        if len(self.prev_positions) > 10:
            self.prev_positions.pop(0)
        
    def eat(self, nutrition):
        """Resetea la hambre cuando come."""
        self.hunger = max(self.hunger - nutrition, 0.0)
        self.recharge_energy(nutrition)
    
    def move(self, dx, dy, screen_widht, screen_height):
        """
        Mueve al cyra sumándole dx y dy a su posición, 
        respetando la velocidad máxima y controlando que no se salga de la pantalla.
        
        Retorna:
            old_direction (list): El vector de movimiento anterior (o None si no existe).
            new_direction (list): El vector de movimiento actual.
        """
        # Reduce la velocidad maxima si tiene poca energia
        if self.energy <= 0.2:
            self.max_speed = 1
        else:
            self.max_speed = 3
        
        new_direction = pygame.Vector2(dx, dy)
        magnitude = new_direction.length()
        
        # Escala el vector de movimient si supera la velocidad maxima
        if magnitude > self.max_speed:
            new_direction.scale_to_length(self.max_speed)
            magnitude = self.max_speed # Se limita la magnitud a max_speed
        
        # Actualiza la posicion
        self.pos += new_direction
        
        # Control de bordes
        self.pos.x = max(0, min(self.pos.x, screen_widht))
        self.pos.y = max(0, min(self.pos.y, screen_height))
        
        # Guarda la magnitud del movimiento
        self.last_speed = magnitude
        
        # Actualiza la energia en funcion del movimiento
        self.update_energy(magnitude)
        
        old_direction = self.prev_direction
        self.prev_direction = new_direction
        return old_direction, new_direction, magnitude
    
    def reset(self, screen_width, screen_height):
        """ Reinicia a los cyras """
        self.pos = pygame.math.Vector2(screen_width // 2, screen_height // 2)
        self.last_speed = 0.0
        self.prev_direction = pygame.Vector2(self.pos)
        self.max_speed = 3
        self.hunger = self.hunger
        self.energy = self.max_energy
        self.health = self.max_health
        self.detected_objects = []
        self.health_state = 0
    
    def detect_collision(self, obj):
        """
        Detecta si un objeto colisiona con el área de detección del Cyra.
        """
        return self.pos.distance_to(obj.pos) <= self.detect_radio

    def update_detection(self, all_objects):
        """
        Actualiza la lista de objetos detectados dinámicamente.
        - Si un objeto entra en el área, se agrega.
        - Si un objeto sale del área, se elimina.
        """
        new_detected = []
        for obj in all_objects:
            if self.detect_collision(obj):
                new_detected.append(obj)
        
        # Actualizamos la lista
        self.detected_objects = new_detected
    
    def get_state(self):
        """
        Retorna el estado completo del cyra, que incluye la posición y el nivel de hambre.
        
        Returns:
            list: [x, y, hunger, last_speed, prev_direction, energy, max_energy, max_speed]
        """
        return [self.pos.x, self.pos.y, self.hunger, self.last_speed, self.energy, self.health, len(self.detected_objects), self.health_state]
    
    def draw(self, screen):
        """
        Dibuja al cyras en pantalla como un círculo azul.
        """
        pygame.draw.circle(screen, (0, 0, 255), (int(self.pos.x), int(self.pos.y)), 10)