import math
import pygame
from simulation.entities.cyras import Cyra
from simulation.entities.foods import Food

class Environment:
    def __init__(self, screen, num_cyras=5):
        self.screen = screen
        self.screen_width, self.screen_height = self.screen.get_size()
        self.num_cyras = num_cyras  # Cantidad de cyras
        
        # Lista de agentes (cyras) y la comida
        self.cyras = [Cyra(pygame.math.Vector2(self.screen_width//2, self.screen_height//2)) for _ in range(self.num_cyras)]  # Por ahora, un cyras en el centro
        self.food = [Food(self.screen_width, self.screen_height) for _ in range(10)]
        self.all_objects = []
    
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