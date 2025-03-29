import plotly.graph_objects as go
import plotly.io as pio
import dash
import threading
from dash import dcc, html
from dash.dependencies import Input, Output
from config.trainer_config import NUM_AGENTS, MAX_STEPS, NUM_EPISODES


class TrainGraphics:
    def __init__(self):
        self.rewards_list = [0 for _ in range(NUM_AGENTS)]  # Lista de recompensas de los agentes
        self.health_list = [0 for _ in range(NUM_AGENTS)] # Lista para la salud de los agentes
        self.energy_list = [0 for _ in range(NUM_AGENTS)] # Lista para la energia de los agentes
        self.hunger_list = [0 for _ in range(NUM_AGENTS)] # Lista para el hambre de los agentes
        
        self.generation = 0
        self.episode = 0
        self.step = 0
        
        # Inicializa y configura Dash para actualizacion automatica
        self.app = dash.Dash(__name__)
        self.app.layout = html.Div([
            html.H1("Monitoreo de datos", style={'textAlign': 'center'}),
            
            dcc.Graph(id="rewards_graph"),
            dcc.Graph(id="status_graph"),
            
            html.Div([
                html.P(id="gen_text", style={'fontSize': 20}),
                html.P(id="episode_text", style={'fontSize': 20}),
                html.P(id="step_text", style={'fontSize': 20}),
            ], style={'textAlign': 'center'}),
            
            dcc.Interval(id="interval", interval=1000, n_intervals=0)
        ])
        
        @self.app.callback(
            [Output("rewards_graph", "figure"),
             Output("status_graph", "figure"),
             Output("gen_text", "children"),
             Output("episode_text", "children"),
             Output("step_text", "children")],
            [Input("interval", "n_intervals")]
        )
        def update_graphs(n_intervals):
            return self.draw_graphs()
        
        # Hilo para correr Dash
        self.dash_thread = threading.Thread(target=self.run_dash, daemon=True)
        self.dash_thread.start()
    
    # ------------------------------------------------------------
    # FUNCIONES PARA EL GRAFICO DE RECOMPENSAS TOTALES POR AGENTES
    # ------------------------------------------------------------
    def create_reawrds_agent_graph_bar(self):
        """
        Crea el gráfico actualizado con las recompensas de los agentes
        """
        fig = go.Figure()
        fig.add_trace(go.Bar(x=[f"Agente {i}" for i in range(NUM_AGENTS)], y=self.rewards_list))
        fig.update_layout(
            title="Agentes y sus recompensas totales",
            xaxis_title="Agentes",
            yaxis_title="Recompensa Total (Episodio)"
        )
        return fig

    # ------------------------------------------------------------
    # FUNCIONES PARA EL GRAFICO DE SALUD, ENERGÍA Y HAMBRE
    # ------------------------------------------------------------
    def create_status_graph_bar(self):
        """
        Crea el gráfico de Salud, Energía y Hambre para los agentes.
        """
        fig = go.Figure()

        # Agregar barras para cada estado
        fig.add_trace(go.Bar(name="Salud", x=[f"Agente {i}" for i in range(NUM_AGENTS)], y=self.health_list, marker_color="green"))
        fig.add_trace(go.Bar(name="Energía", x=[f"Agente {i}" for i in range(NUM_AGENTS)], y=self.energy_list, marker_color="blue"))
        fig.add_trace(go.Bar(name="Hambre", x=[f"Agente {i}" for i in range(NUM_AGENTS)], y=self.hunger_list, marker_color="red"))

        fig.update_layout(
            title="Estado de los Agentes",
            xaxis_title="Agentes",
            yaxis_title="Valores",
            barmode="group"
        )
        return fig

    # ------------------------------------------------------------
    # FUNCIONES PARA LA INFORMACION DE ENTRENAMIENTO
    # ------------------------------------------------------------
    def create_training_info(self):
        """
        Devuelve la informacion de la generaciom, episodio y paso.
        """
        return f"Generacion: {self.generation}", f"Episodio: {self.episode}/{NUM_EPISODES}", f"Paso: {self.step}/{MAX_STEPS}"
    
    # ---------------
    # OTRAS FUNCIONES
    # ---------------
    def draw_graphs(self):
        """
        Redibuja los gráficos con los datos actualizados.
        """
        graph_rewards = self.create_reawrds_agent_graph_bar()
        graph_status = self.create_status_graph_bar()
        
        generation, episode, step = self.create_training_info()

        return graph_rewards, graph_status, generation, episode, step
    
    def update_graph_data(self, rewards_list, health_list, energy_list, hunger_list, generation, episode, step):
        """
        Actualiza las recompensas de los agentes en el gráfico
        """
        self.rewards_list = rewards_list  # Se actualiza la lista de recompensas en tiempo real
        
        self.health_list = health_list
        self.energy_list = energy_list
        self.hunger_list = hunger_list
        
        self.generation = generation
        self.episode = episode
        self.step = step
        
    
    def run_dash(self):
        """
        Corre la aplicación Dash en un hilo separado.
        """
        self.app.run(debug=True, use_reloader=False)  # Mantener `use_reloader=False` para evitar recargas automáticas.
        
        
        
    