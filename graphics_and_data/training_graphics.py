import plotly.graph_objects as go
import plotly.io as pio
import dash
import threading
from dash import dcc, html
from dash.dependencies import Input, Output
from config.trainer_config import NUM_AGENTS


class TrainGraphics:
    def __init__(self):
        self.rewards_list = [0 for _ in range(NUM_AGENTS)]  # Lista de recompensas de los agentes
        
        # Inicializa y configura Dash para actualizacion automatica
        self.app = dash.Dash(__name__)
        self.app.layout = html.Div([
            dcc.Graph(id="graph"),
            dcc.Interval(id="interval", interval=2500, n_intervals=0)
        ])
        
        @self.app.callback(
            Output("graph", "figure"),
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
    def update_agents_and_rewards_bar_graph(self, rewards_list):
        """
        Actualiza las recompensas de los agentes en el gráfico
        """
        self.rewards_list = rewards_list  # Se actualiza la lista de recompensas en tiempo real

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

    # ---------------
    # OTRAS FUNCIONES
    # ---------------
    def draw_graphs(self):
        """
        Actualiza y re dibuja todos los graficos.
        """
        graph_reward_agent = self.create_reawrds_agent_graph_bar()
        
        return graph_reward_agent
        
    def run_dash(self):
        """
        Corre la aplicación Dash en un hilo separado.
        """
        self.app.run(debug=True, use_reloader=False)  # Mantener `use_reloader=False` para evitar recargas automáticas.
        
        
        
    