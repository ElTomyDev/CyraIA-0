import pygame
import random
from enums.object_types import ObjectTypes
from config.general_config import WINDOWS_WIDTH, WINDOWS_HEIGHT, FIRST_FOOD_COLOR, TWO_FOOD_COLOR

class Food:
    def __init__(self) -> None:
        # --- Configuracion de la comida
        self.obj_type = ObjectTypes.FOOD
        self.nutrition = 0.0

        self.random_figure = random.randint(0,1)
        
        self.reset()
        
        self.pos = pygame.Vector2(random.randint(0, WINDOWS_WIDTH), random.randint(0, WINDOWS_HEIGHT))
        
        
    
    def reset(self) -> None:
        """Reposiciona la comida y asigna un valor nutricional aleatorio."""
        self.pos = pygame.Vector2(random.randint(0, WINDOWS_WIDTH), random.randint(0, WINDOWS_HEIGHT))
        self.nutrition = random.uniform(0.0, 1.0)
        self.random = random.randint(0,1)
    
    def draw(self, screen) -> None:
        """
        Dibuja la comida en pantalla como un cuadrado verde.
        """
        if self.random_figure == 0:
            pygame.draw.rect(screen, TWO_FOOD_COLOR, (int(self.pos.x), int(self.pos.y), 15, 15))
            pygame.draw.rect(screen, FIRST_FOOD_COLOR, (self.pos.x+(15-10)/2, self.pos.y+(15-10)/2, 10, 10)) # centrar esto al rect de arriba
        else:
            pygame.draw.circle(screen, TWO_FOOD_COLOR, (int(self.pos.x), int(self.pos.y)), 8)
            pygame.draw.circle(screen, FIRST_FOOD_COLOR, (int(self.pos.x), int(self.pos.y)), 5)