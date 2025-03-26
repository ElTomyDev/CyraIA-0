import pygame
from config.general_config import WINDOWS_WIDTH, WINDOWS_HEIGHT

class Run:
    def __init__(self):
        
        # Inicializacion de Pygame y la ventana
        pygame.init()
        pygame.display.set_caption("Cyras: La Civilización")
        self.screen = pygame.display.set_mode((WINDOWS_WIDTH, WINDOWS_HEIGHT))
        
        # Configuracion del clock y bandera de ejecucion
        self.clock = pygame.time.Clock()
        self.running = True
    
    def process_events(self):
        """Procesa eventos de Pygame (cierre de ventana y tecla G para entrenamiento, etc)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.can_next_gen = True
                if event.key == pygame.K_s:
                    self.can_next_gen = False