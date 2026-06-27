from matplotlib.figure import Figure
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
        self.date_format = config.DATE_FORMAT
        self.tag_colors = config.TAG_COLOR_MAP
        self.timeframes = ['this week', 'this month', 'all time']
        self.save_path = Path(Path.cwd(), path)
        self.lable_name = "TaskLabels"
        self.now = datetime.now()
        pass
    
    def datetime_string(self,date: datetime) -> str:
        return datetime.strftime(date, self.date_format)

    # Timeframe filters
    def get_timeframe_df(self, timeframe: str) -> DataFrame:

        if timeframe == 'this week':
            start_of_week = self.now - timedelta(days= self.now.weekday())
            return self.task_data[self.task_data['CompletedDate'] >= self.datetime_string(start_of_week)]
        elif timeframe == 'this month':
            start_of_month = self.now.replace(day=1)
            return self.task_data[self.task_data['CompletedDate'] >= self.datetime_string(start_of_month)]
        else: # all time
            return self.task_data
        
    def save_figure(self, chart: Figure, title: str) -> None:

        save_path = Path(self.save_path, f"{datetime.strftime(self.now, config.FILE_DATE_FORMAT)}_{title.replace(" ", "_")}.png")
        chart.savefig(save_path)
        logger.info(f"Chart Saved: {str(save_path)}")
        return


    def deplete_recharge_piechart(self, timeframe: str)-> None:
        # 1. Pie chart: depleting vs recharging
        title = f'Depleting vs Recharging ({timeframe})'
        depleting = self.task_data[self.task_data[self.lable_name].apply(lambda x: 'depleting' in x)]
        recharging = self.task_data[self.task_data[self.lable_name].apply(lambda x: 'recharging' in x)]
        
        # Note: A task could have both, but for a simple pie chart we might need to handle exclusivity or just count occurrences
        # Let's count unique tasks that have at least one of these
        depleting_count = len(depleting)
        recharging_count = len(recharging)
        
        fig = plt.figure(figsize=(6, 6))
        plt.pie([depleting_count, recharging_count], labels=['Depleting', 'Recharging'], autopct='%1.1f%%', colors=['red', 'green'])
        plt.title(title)
        self.save_figure(fig, title)
        plt.close(fig)


    def other_tasks_piechart(self, timeframe: str)-> None:
        # 2. Pie chart: labels excluding depleting and recharging
        title = f'Non Depleting and Recharging ({timeframe})'

        other_tasks = self.task_data[~self.task_data[self.lable_name].apply(lambda x: 'depleting' in x or 'recharging' in x)]
        label_counts = other_tasks[self.lable_name].explode().value_counts()
        
        if not label_counts.empty:
            fig = plt.figure(figsize=(8, 8))
            label_counts.plot(kind='pie', autopct='%1.1f%%')
            plt.title(title)
            self.save_figure(fig, title)
            plt.close(fig)

    def energybytype_barchart(self, timeframe: str)-> None:
        # 3. Bar chart: energy_high, energy_medium, energy_low grouped by depleting/recharging
        title = f"Energy Levels by Group ({timeframe})"
        energy_tasks = self.task_data[self.task_data[self.lable_name].apply(
            lambda x: any(e in x for e in ['energy_high', 'energy_medium', 'energy_low']))]
    
        # Grouping logic
        results = []
        for _, row in energy_tasks.iterrows():
            labels = row[self.lable_name]
            energy_type = next((e for e in ['energy_high', 'energy_medium', 'energy_low'] if e in labels), None)
            is_depleting = 'depleting' in labels
            is_recharging = 'recharging' in labels
            
            group = "Depleting" if is_depleting else ("Recharging" if is_recharging else "Neither")
            results.append({'EnergyType': energy_type, 'Group': group})
        
        if results:
            res_df = pd.DataFrame(results)
            pivot_df = res_df.groupby(['Group', 'EnergyType']).size().unstack(fill_value=0)
            
            fig, ax = plt.subplots(figsize=(10,6))

            pivot_df.plot(kind="bar", ax=ax)
            ax.set_title(title)
            
            # fig = pivot_df.plot(kind='bar', figsize=(10, 6))
            self.save_figure(fig, title)
            # plt.savefig(self.save_path + f"/chart_3_{timeframe.replace(" ", "_")}.png")
            plt.close(fig)

    def generate_all_charts(self)-> None:
        for tf in self.timeframes:
            df = self.get_timeframe_df(tf)
            df.Name = tf
            logger.info(f"Generating graphs for - {df.Name}")
            self.deplete_recharge_piechart(df.Name)
            self.other_tasks_piechart(df.Name)
            self.energybytype_barchart(df.Name)
