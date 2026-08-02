from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure
from pandas import DataFrame

from utils import config
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
        self.now = datetime.now(tz=timezone(
            -timedelta(hours=5),
              name="CDT"))
        self.saved_paths = []        
    
    def datetime_string(self,date: datetime) -> str:
        return datetime.strftime(date, self.date_format)

    # Timeframe filters
    def get_timeframe_df(self, timeframe: str) -> DataFrame | None:
        self.task_data['CompletedDate_dt'] = pd.to_datetime(self.task_data['CompletedDate_dt'], errors='coerce')
        try:
            if timeframe == 'this week':
                start_of_week = self.now - timedelta(days= self.now.weekday())
                output = self.task_data[self.task_data['CompletedDate_dt'] >= start_of_week]
                return output
            elif timeframe == 'this month':
                start_of_month = self.now.replace(day=1,hour=0,minute=0,second=0)
                logger.info(f"Start of Month: {start_of_month}")
                output = self.task_data[self.task_data['CompletedDate_dt'] >= start_of_month]
                return output
            else: # all time
                output = self.task_data
                return output
        except TypeError as e:
            print(f"Column data is not datetime {type(self.task_data['CompletedDate_dt'].iloc[0])}\n\n {e}")
        
    def save_figure(self, chart: Figure, title: str) -> str:

        save_path = Path(self.save_path, f"{datetime.strftime(self.now, config.FILE_DATE_FORMAT)}_{title.replace(" ", "_")}.png")
        chart.savefig(save_path,bbox_inches="tight")
        logger.info(f"Chart Saved: {save_path!s}")
        return str(save_path)
        
    def deplete_recharge_piechart(self, dataframe: DataFrame,  timeframe: str)-> None:
        # 1. Pie chart: depleting vs recharging
        title = f'Depleting vs Recharging ({timeframe})'
        depleting = dataframe[dataframe[self.lable_name].apply(lambda x: 'depleting' in x)]
        recharging = dataframe[dataframe[self.lable_name].apply(lambda x: 'recharging' in x)]
        
        # Note: A task could have both, but for a simple pie chart we might need to handle exclusivity or just count occurrences
        # Let's count unique tasks that have at least one of these
        depleting_count = len(depleting)
        recharging_count = len(recharging)
        
        fig = plt.figure(figsize=(6, 6))
        plt.pie([depleting_count, recharging_count], labels=['Depleting', 'Recharging'], autopct='%1.1f%%', colors=['red', 'green'])
        plt.title(title)
        figure_path = self.save_figure(fig, title)
        self.saved_paths.append(figure_path)
        plt.close(fig)


    def other_tasks_piechart(self, dataframe: DataFrame, timeframe: str)-> None:
        # 2. Pie chart: labels excluding depleting and recharging
        title = f'Non Depleting and Recharging ({timeframe})'

        other_tasks = dataframe[~dataframe[self.lable_name].apply(lambda x: 'depleting' in x or 'recharging' in x)]
        label_counts = other_tasks[self.lable_name].explode().value_counts()
        
        if not label_counts.empty:
            fig = plt.figure(figsize=(8, 8))
            label_counts.plot(kind='pie', autopct='%1.1f%%')
            plt.title(title)
            figure_path = self.save_figure(fig, title)
            self.saved_paths.append(figure_path)
            plt.close(fig)

    def energybytype_barchart(self, dataframe: DataFrame, timeframe: str)-> None:
        # 3. Bar chart: energy_high, energy_medium, energy_low grouped by depleting/recharging
        title = f"Energy Levels by Group ({timeframe})"
        energy_tasks = dataframe[dataframe[self.lable_name].apply(
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
            
            fig, ax = plt.subplots(figsize=(10,7))

            pivot_df.plot(kind="bar", ax=ax)
            ax.set_title(title)
            ax.tick_params(axis="x",rotation=20)
            # fig = pivot_df.plot(kind='bar', figsize=(10, 6))
            figure_path = self.save_figure(fig, title)
            self.saved_paths.append(figure_path)
            # plt.savefig(self.save_path + f"/chart_3_{timeframe.replace(" ", "_")}.png")
            plt.close(fig)

    def generate_all_charts(self) -> list[str]:
        for tf in self.timeframes:
            df = self.get_timeframe_df(tf)
            if df is not None:
                df.Name = tf
                logger.info(f"Generating graphs for - {df.Name}")
                # print(df)
                self.deplete_recharge_piechart(df, df.Name)
                self.other_tasks_piechart(df, df.Name)
                self.energybytype_barchart(df, df.Name)
        return self.saved_paths
