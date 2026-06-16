from datetime import datetime
from pathlib import Path
from typing import Any
from dateutil import parser as dateparser
import pandas as pd
from pandas import DataFrame, Series
from utils import config

class DataProcessor:
    "Handles all data manipulation and storing into archive."

    COLUMN_TEMPLATE = config.TODOIST_COLUMNS
    COLUMNS_RENAMED = dict(
        zip(config.TODOIST_COLUMNS["keep"], config.TODOIST_COLUMNS["renamed"])
    )
    DATE_FORMAT = r"%Y/%m/%d"

    def __init__(self, data: dict) -> None:
        self.most_recent_date = None
        self.csv_df = self.load_csv(data['archive'])
        self.projects_df = self.build_dataframe(data['projects'])
        self.data_path = Path(Path.cwd(), r"data/", data['archive'])
        self.api_df = self.build_dataframe(data= data['api_tasks'], columns= self.COLUMN_TEMPLATE["keep"], renames=self.COLUMNS_RENAMED)
        self.distilled_tasks_df = None
## HELPERS
    def date_iso(self, date: datetime) -> str:
        return date.isoformat()
    
    def isoToString(self, date, format) -> str:
        if isinstance(date, str):
            date = dateparser.parse(date) 
        return date.strftime(format = format)

    def column_is_type(self, df: Series[Any]) -> str | None:
        
        return df.transform(lambda x: x.apply(type)).drop_duplicates().iloc[0]

    def split_column(self, data: DataFrame, split: str, key: int) -> DataFrame:
        test = data[[key, split]]
        test = test[test.iloc[:, 1].notna()]
        if self.column_is_type(test.iloc[:, 1]) is dict:
            unnest = test[split].apply(pd.Series)
        source_names = unnest.columns.tolist()
        updated_names = [
            split.capitalize() + part.capitalize() for part in source_names
        ]

        rename_zip = zip(source_names, updated_names)
        rename_dict = dict(rename_zip)

        renamed = unnest.rename(rename_dict, axis=1)
        output = test.join(renamed)
        return output

    def build_dataframe(self, data: dict | list, columns: list | None = None, renames: dict[str, str] | None = None) -> DataFrame:
        df = pd.DataFrame(data).infer_objects()
        if columns:
            df = df[columns]
        if renames:
            df = df.rename(columns=renames)
        return df
    
    def load_csv(self, path: Path) -> None:
        if Path.exists(self.data_path):
            self.csv_df = pd.read_csv(path).infer_objects()
        else:
            self.csv_df = None

        self.most_recent_date = self.max_date('CompletedDate')
        return
    
    def max_date(self, col: str) -> datetime:
        if self.csv_df is None:
            return datetime.now().replace(day=1) 
        maxdate = self.csv_df[f'{col}'].max()
        return dateparser.parse(maxdate)

        
    def combine_tasks(self) -> None:
        if self.csv_df is not None:
            self.distilled_tasks_df = pd.concat([self.api_df, self.csv_df]).reset_index(drop=True)
        else:
            self.distilled_tasks_df = self.api_df
        return

    def get_df_id(self, dataframe: DataFrame) -> int:
        val = dataframe.columns.get_loc("id")
        if not isinstance(val, int):
            raise ValueError(f"Expected single 'id' column, but found {type(val)}")
        return val
        
    def clean_dates(self) -> None:
        if self.distilled_tasks_df is None:
            raise ValueError("Expected Dataframe but found: None")

        pkey = self.get_df_id(self.distilled_tasks_df)
        date_columns = self.split_column(data=self.distilled_tasks_df,split="due",key=self.get_df_id(self.distilled_tasks_df) )
        date_columns['DueDate'] = date_columns['DueDate'].apply(dateparser.parse)
        date_columns['DueDate'] = [date.strftime(self.DATE_FORMAT) for date in date_columns['DueDate']]
        combined_df = pd.merge(left =self.distilled_tasks_df, right = date_columns, on=pkey, how='left')
        dates_to_convert = ["added_at", "completed_at", "updated_at"]

        combined_df[dates_to_convert] = combined_df[dates_to_convert].apply(
            lambda row: [self.isoToString(rowItem, self.DATE_FORMAT) for rowItem in row]
        )
        self.distilled_tasks_df = combined_df
        return
    
    def clean_dataframe(self, name: DataFrame)-> DataFrame:

        # if not hasattr(self, name):
        #         raise AttributeError(f"Data Processor has no attribute {name}")
        # df = getattr(self, name)
        df = name
        fill_values = {
            'IsRecurringTask': False,
            'DueDate': '1900/01/01',
            'TaskDuration': 0,
            'ParentTaskId': ""
        }
        df = df.drop(columns=self.COLUMN_TEMPLATE["drop"], errors="ignore")
        df = df.rename(columns=self.COLUMNS_RENAMED)
        df = df.fillna(fill_values)
        return df
    
    def merge_dataframes(self) -> None:
        if self.distilled_tasks_df is None:
            raise ValueError("Expected Distilled Data to exist. Found None")
        output = pd.merge(
            left = self.distilled_tasks_df,
            right = self.projects_df,
            how = "left",
            left_on="project_id",
            right_on = "ProjectID"
        )
        output = self.clean_dataframe(output)
        self.distilled_tasks_df = output
        # return output
    
    def save_to_csv(self)-> None:
        if self.distilled_tasks_df is None:
            raise ValueError()
        if self.csv_df is None:
            self.distilled_tasks_df.to_csv(self.data_path, index=False)
            return
        for i, row in self.distilled_tasks_df.iterrows():
            if row["TaskID"] not in self.csv_df["TaskID"].values:
                new_task = row.to_frame().T
                new_task.to_csv(self.data_path, mode="a", index=False, header=False)
        return
