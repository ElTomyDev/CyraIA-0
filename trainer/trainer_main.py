import pygame
from config.general_config import WINDOWS_WIDTH, WINDOWS_HEIGHT, FPS
from trainer.training import Train

class TrainerView:
    def __init__(self) -> None:
        
        # Inicializacion de Pygame y la ventana
        pygame.init()
        pygame.display.set_caption("Cyras: La Civilización")
        self.screen = pygame.display.set_mode((WINDOWS_WIDTH, WINDOWS_HEIGHT))
        
        # Variable que determina si puede o no pasar a la siguiente generacion
        self.train_running = False
        
        # Inicializacion del training
        self.train = Train(self)
        
        # Configuracion del clock y bandera de ejecucion
        self.clock = pygame.time.Clock()
        self.running = True
    
    def run(self) -> None:
        """Bucle principal del juego. Procesa eventos y ejecuta generaciones de entrenamiento."""
        while self.running:
            self.process_events()
            
            # Si la generacion anterior termino, se inicia la siguiente
            if self.train_running == True:
                self.run_next_generation()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
    
    def run_next_generation(self) -> None:
        """
        Ejecuta una nueva generación:
            - Incrementa el contador de generación.
            - Ejecuta el entrenamiento (varios episodios).
            - Guarda el mejor modelo si se mejora la recompensa promedio.
            - Guarda el número de generación.
        """
        # Ejecuta entrenamiento y obtiene la recompensa promedio del mismo
        train_rewards = self.train.run_generation()
        self.train.evolve_population(avg_rewards=train_rewards)
    
    def process_events(self) -> None:
        """Procesa eventos de Pygame (cierre de ventana y tecla G para entrenamiento, etc)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.train_running = True
                if event.key == pygame.K_s:
                    self.train_running = False