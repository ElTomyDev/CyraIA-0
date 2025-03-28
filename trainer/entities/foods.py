import pygame
import random
from enums.object_types import ObjectTypes
from config.general_config import WINDOWS_WIDTH, WINDOWS_HEIGHT

class Food:
    def __init__(self):
        # --- Configuracion de la comida
        self.obj_type = ObjectTypes.FOOD
        self.nutrition = 0.0
        
        self.reset()
        
        self.pos = pygame.Vector2(random.randint(0, WINDOWS_WIDTH), random.randint(0, WINDOWS_HEIGHT))
        
        
    
    def reset(self):
        """Reposiciona la comida y asigna un valor nutricional aleatorio."""
        self.pos = pygame.Vector2(random.randint(0, WINDOWS_WIDTH), random.randint(0, WINDOWS_HEIGHT))
        self.nutrition = random.uniform(0.0, 1.0)
    
    def draw(self, screen):
        """
        Dibuja la comida en pantalla como un cuadrado verde.
        """
        pygame.draw.rect(screen, (0, 255, 0), (int(self.pos.x), int(self.pos.y), 10, 10))