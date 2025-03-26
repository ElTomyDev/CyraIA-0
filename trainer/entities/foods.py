import pygame
import random

class Food:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.nutrition = 0.0
        self.respawn()
        
        self.pos = pygame.Vector2(random.randint(0, self.screen_width), random.randint(0, self.screen_height))
    
    def respawn(self):
        """Reposiciona la comida y asigna un valor nutricional aleatorio."""
        self.pos = pygame.Vector2(random.randint(0, self.screen_width), random.randint(0, self.screen_height))
        self.nutrition = random.uniform(0.0, 1.0)
    
    def draw(self, screen):
        """
        Dibuja la comida en pantalla como un cuadrado verde.
        """
        pygame.draw.rect(screen, (0, 255, 0), (int(self.pos.x), int(self.pos.y), 10, 10))