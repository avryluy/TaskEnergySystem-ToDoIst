import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from utils import config
from pandas import DataFrame
from pathlib import Path
from utils.logger import logger


class TaskGraphs:

    def __init__(self, data: DataFrame | None, path: str) -> None:
        logger.info("TaskGraphs initialized")
        if data is None:
            raise ValueError("DataFrame empty. Cannot initialize graph maker.")
        self.task_data = data
        self.tag_colors = config.TAG_COLOR_MAP
        self.timeframes = ['this week', 'this month', 'all time']
        self.save_path = str(Path.cwd()) + path
        # self.timeframe_df = self.get_timeframe_df(self.task_data, self.timeframes)
        pass

    # Timeframe filters
    def get_timeframe_df(self, timeframe: str) -> DataFrame:
        logger.info(f"CompletedDate colum: {type(self.task_data['CompletedDate'])}")
        # if isinstance(self.task_data['CompletedDate'], str):
        #     logger.warning("TaskData type is str when it should be datetime.datetime")
        now = datetime.now()
        # return self.task_data
        if timeframe == 'this week':
            start_of_week = now - timedelta(days=now.weekday())
            print(self.task_data['CompletedDate'].info())
            return self.task_data
            # return self.task_data[self.task_data['CompletedDate'] >= start_of_week]
        # elif timeframe == 'this month':
        #     start_of_month = now.replace(day=1)
        #     return self.task_data[self.task_data['CompletedDate'] >= start_of_month]
        else: # all time
            return self.task_data

    def deplete_recharge_piechart(self, timeframe: DataFrame)-> None:
        # 1. Pie chart: depleting vs recharging
        depleting = self.task_data[self.task_data['Labels'].apply(lambda x: 'depleting' in x)]
        recharging = self.task_data[self.task_data['Labels'].apply(lambda x: 'recharging' in x)]
        
        # Note: A task could have both, but for a simple pie chart we might need to handle exclusivity or just count occurrences
        # Let's count unique tasks that have at least one of these
        depleting_count = len(depleting)
        recharging_count = len(recharging)
        
        plt.figure(figsize=(6, 6))
        plt.pie([depleting_count, recharging_count], labels=['Depleting', 'Recharging'], autopct='%1.1f%%', colors=['red', 'green'])
        plt.title(f'Depleting vs Recharging ({timeframe})')
        # plt.savefig(self.save_path + f"/chart_1_{timeframe.replace(" ", "_")}.png")
        logger.info(f"depleting vs recharging Graph Saved - {timeframe.Name}")
        plt.close()

    def other_tasks_piechart(self, timeframe: DataFrame)-> None:
        # 2. Pie chart: labels excluding depleting and recharging
        other_tasks = self.task_data[~self.task_data['Labels'].apply(lambda x: 'depleting' in x or 'recharging' in x)]
        label_counts = other_tasks['Labels'].explode().value_counts()
        
        if not label_counts.empty:
            plt.figure(figsize=(8, 8))
            label_counts.plot(kind='pie', autopct='%1.1f%%')
            plt.title(f'Task Labels excluding Depleting/Recharging ({timeframe})')
            # plt.savefig(self.save_path + f"/chart_2_{timeframe.replace(" ", "_")}.png")
            plt.close()

    def energybytype_barchart(self, timeframe: DataFrame)-> None:
        # 3. Bar chart: energy_high, energy_medium, energy_low grouped by depleting/recharging
        energy_tasks = self.task_data[self.task_data['Labels'].apply(
            lambda x: any(e in x for e in ['energy_high', 'energy_medium', 'energy_low']))]
    
        # Grouping logic
        results = []
        for _, row in energy_tasks.iterrows():
            labels = row['Labels']
            energy_type = next((e for e in ['energy_high', 'energy_medium', 'energy_low'] if e in labels), None)
            is_depleting = 'depleting' in labels
            is_recharging = 'recharging' in labels
            
            group = "Depleting" if is_depleting else ("Recharging" if is_recharging else "Neither")
            results.append({'EnergyType': energy_type, 'Group': group})
        
        if results:
            res_df = pd.DataFrame(results)
            pivot_df = res_df.groupby(['Group', 'EnergyType']).size().unstack(fill_value=0)
            pivot_df.plot(kind='bar', figsize=(10, 6))
            plt.title(f'Energy Levels by Group ({timeframe})')
            # plt.savefig(self.save_path + f"/chart_3_{timeframe.replace(" ", "_")}.png")
            plt.close()

    def generate_all_charts(self)-> None:
        for tf in self.timeframes:
            df = self.get_timeframe_df(tf)
            df.Name = tf
            # self.deplete_recharge_piechart(df)
            # self.other_tasks_piechart(df)
            # self.energybytype_barchart(df)
            
            
    

