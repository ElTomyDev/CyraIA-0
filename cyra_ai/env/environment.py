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