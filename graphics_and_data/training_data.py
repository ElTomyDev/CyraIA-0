import pandas as pd
import os

class TrainCsvData:
    
    csv_path = "graphics_and_data/data/data.csv"
    csv = None
    
    def read_or_create() -> pd.DataFrame:
        if not os.path.exists(TrainCsvData.csv_path):
            os.makedirs('graphics_and_data/data/', exist_ok=True)
            columns = [
            'age',
            'best_reward',
            'generations',
            'upgrade_food_dist_bonus',
            'food_eat_bonus',
            'food_found_bonus',
            'hunger_good_bonus',
            'no_upgrade_food_dist_penalty',
            'no_food_in_range_penalty',
            'hunger_hungry_penalty',
            'hunger_critic_penalty',
            '---',
            'energy_recharge_bonus',
            'energy_good_bonus',
            'energy_weary_penalty',
            'energy_critic_penalty',
            '---',
            'health_recove_bonus',
            'health_any_bonus',
            'health_good_bonus',
            'health_loss_penalty',
            'health_wounded_penalty',
            'health_critic_penalty',
            'dead_penalty',
            '---',
            'change_direction_bonus',
            'away_border_bonus',
            'border_penalty',
            'corner_penalty',
            'repeat_position_penalty']
            dataframe = pd.DataFrame(columns=columns)
            dataframe.to_csv(TrainCsvData.csv_path, index=False)
            TrainCsvData.csv = dataframe
            return 
        TrainCsvData.csv = pd.read_csv(TrainCsvData.csv_path)
    
    def save_csv() -> None:
        """
        Se encarga de guardar los cambios del csv.
        """
        TrainCsvData.csv.to_csv(TrainCsvData.csv_path, index=False)
    
    def add_new_train_data_row() -> None:
        """
        Crea una nueva fila en el csv con nuevos datos.
        """
        from trainer.env.rewards_and_penalty import RewardsAndPenalty
        TrainCsvData.read_or_create()
        TrainCsvData.csv.loc[len(TrainCsvData.csv)]=[
            f"{1 if len(TrainCsvData.csv) == 0 else TrainCsvData.get_current_age() + 1}",
            f"{0.0}",
            f"{0}",
            f"{RewardsAndPenalty.upgrade_food_dist_bonus}",
            f"{RewardsAndPenalty.food_eat_bonus}",
            f"{RewardsAndPenalty.food_found_bonus}",
            f"{RewardsAndPenalty.hunger_good_bonus}",
            f"{RewardsAndPenalty.no_upgrade_food_dist_penalty}",
            f"{RewardsAndPenalty.no_food_in_range_penalty}",
            f"{RewardsAndPenalty.hunger_hungry_penalty}",
            f"{RewardsAndPenalty.hunger_critic_penalty}",
            "---",
            f"{RewardsAndPenalty.energy_recharge_bonus}",
            f"{RewardsAndPenalty.energy_good_bonus}",
            f"{RewardsAndPenalty.energy_weary_penalty}",
            f"{RewardsAndPenalty.energy_critic_penalty}",
            "---",
            f"{RewardsAndPenalty.health_recove_bonus}",
            f"{RewardsAndPenalty.health_any_bonus}",
            f"{RewardsAndPenalty.health_good_bonus}",
            f"{RewardsAndPenalty.health_loss_penalty}",
            f"{RewardsAndPenalty.health_wounded_penalty}",
            f"{RewardsAndPenalty.health_critic_penalty}",
            f"{RewardsAndPenalty.dead_penalty}",
            f"---",
            f"{RewardsAndPenalty.change_direction_bonus}",
            f"{RewardsAndPenalty.away_border_bonus}",
            f"{RewardsAndPenalty.border_penalty}",
            f"{RewardsAndPenalty.corner_penalty}",
            f"{RewardsAndPenalty.repeat_position_penalty}"]
        TrainCsvData.save_csv()
        
    
    def update_gen_and_rewards_data(age, generation, best_reward) -> None:
        """
        Actualiza la generacion y la mejor recompensa del ultimo indice del data frame.
        """
        TrainCsvData.read_or_create()
        TrainCsvData.csv.loc[TrainCsvData.csv['age'] == age, "best_reward"] = f"{best_reward}"
        TrainCsvData.csv.loc[TrainCsvData.csv['age'] == age, "generations"] = f"{generation}"
        TrainCsvData.save_csv()

    def recove_best_reward_and_gen() -> None:
        """
        Recupera el mejor reward del anterior entrenamiento.
        """
        TrainCsvData.read_or_create()
        TrainCsvData.csv.iat[len(TrainCsvData.csv)-1, 0] = TrainCsvData.csv.iat[len(TrainCsvData.csv)-2, 0]
        TrainCsvData.csv.iat[len(TrainCsvData.csv)-1, 1] = TrainCsvData.csv.iat[len(TrainCsvData.csv)-2, 1]
        TrainCsvData.save_csv()
    
    def get_train_data_by_age(age:int) -> None:
        """ Retorna los datos de entrenamiento de la era indicada (age) """
        TrainCsvData.read_or_create()
        return TrainCsvData.csv.loc[TrainCsvData.csv['age'] == age]
    
    def get_current_age() -> int:
        """ Devuelve la ultima era ingresada """
        TrainCsvData.read_or_create()
        return int(TrainCsvData.csv.loc[TrainCsvData.csv.index[-1], 'age'])