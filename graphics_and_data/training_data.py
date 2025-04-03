import pandas as pd
import os

CSV_PATH = "graphics_and_data/data/data.csv"

"""
< Recompensas y Penalizaciones de la Comida y el Hambre >
    upgrade_food_dist_bonus = UFDB
    food_eat_bonus = FEB
    food_found_bonus = FFB   
    hunger_good_bonus = HGB

    no_upgrade_food_dist_penalty   
    no_food_in_range_penalty
    hunger_hungry_penalty
    hunger_critic_penalty

< Recompensas y Penalizaciones de la Energia >
    energy_recharge_bonus
    energy_good_bonus

    energy_weary_penalty
    energy_critic_penalty

< Recompensas y Penalizaciones de la Salud >
    health_recove_bonus
    health_any_bonus
    health_good_bonus 

    health_loss_penalty
    health_wounded_penalty
    health_critic_penalty
    dead_penalty

< Recompensas y Penalizaciones de la Pocicion y Direccion >
    change_direction_bonus        
    away_border_bonus

    border_penalty    
    corner_penalty       
    repeat_position_penalty   
"""

def create_csv_if_not_exist():
    """
    Crea un archivo CSV con los datos necesarios si es que este no existe.
    """
    if not os.path.exists(CSV_PATH):
        data = {
            'Best Reward' :   [],
            'Generations' :     [],
            'UFDB' :            [],
            'FEB' :             [],
            'FFB' :             [],
            'HGB' :             [],
            'NUFDP' :           [],
            'NFIRP' :           [],
            'HHP' :             [],
            'HCP' :             [],
            '-' :               [],
            'ERB' :             [],
            'EGB' :             [],
            'EWP' :             [],
            'ECP' :             [],
            '--' :              [],
            'HRB' :             [],
            'HAB' :             [],
            'HGB2' :            [],
            'HLP' :             [],
            'HWP' :             [],
            'HCP2' :            [],
            'DP' :              [],
            '---' :             [],
            'CDB' :             [],
            'ABB' :             [],
            'BP' :              [],
            'CP' :              [],
            'RPP' :             []
        }
        df = pd.DataFrame(data)
        df.to_csv(CSV_PATH)

create_csv_if_not_exist()

def create_new_rows(ufdb,feb,ffb,hgb,nufdp,nfirp,hhp,hcp,erb,egb,ewp,ecp,hrb,hab,hgb2,hlp,hwp,hcp2,dp,cdb,abb,bp,cp,rpp):
    """
    Crea una nueva fila en el csv con nuevos datos.
    """
    data = {
            'Best Reward' :   [0.0],
            'Generations' :     [0],
            'UFDB' :            [f"{ufdb:.2f}"],
            'FEB' :             [f"{feb:.2f}"],
            'FFB' :             [f"{ffb:.2f}"],
            'HGB' :             [f"{hgb:.2f}"],
            'NUFDP' :           [f"{nufdp:.2f}"],
            'NFIRP' :           [f"{nfirp:.2f}"],
            'HHP' :             [f"{hhp:.2f}"],
            'HCP' :             [f"{hcp:.2f}"],
            '-' :               ["-"],
            'ERB' :             [f"{erb:.2f}"],
            'EGB' :             [f"{egb:.2f}"],
            'EWP' :             [f"{ewp:.2f}"],
            'ECP' :             [f"{ecp:.2f}"],
            '--' :              ["-"],
            'HRB' :             [f"{hrb:.2f}"],
            'HAB' :             [f"{hab:.2f}"],
            'HGB2' :            [f"{hgb2:.2f}"],
            'HLP' :             [f"{hlp:.2f}"],
            'HWP' :             [f"{hwp:.2f}"],
            'HCP2' :            [f"{hcp2:.2f}"],
            'DP' :              [f"{dp:.2f}"],
            '---' :             ["-"],
            'CDB' :             [f"{cdb:.2f}"],
            'ABB' :             [f"{abb:.2f}"],
            'BP' :              [f"{bp:.2f}"],
            'CP' :              [f"{cp:.2f}"],
            'RPP' :             [f"{rpp:.2f}"]
        }
    df = pd.DataFrame(data)
    df.to_csv(CSV_PATH, mode="a", header=False)

def update_gen_and_rewards_data(genetation, best_reward):
    """
    Actualiza la generacion y la mejor recompensa del ultimo indice del data frame.
    """
    df = pd.read_csv(CSV_PATH)

    df.at[df.index[-1], "Best Reward"] = f"{best_reward:.2f}"
    df.at[df.index[-1], "Generations"] = genetation
    
    df.to_csv(CSV_PATH, index= False)
