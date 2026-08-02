from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

# from typing import Any
from dateutil import parser as dateparser
from pandas import DataFrame, Series

from utils import config
from utils.logger import logger


class DataProcessor:
    "Handles all data manipulation and storing into archive."



    def __init__(self, data: dict) -> None:
        logger.info("Data handler initialized.")
        self.data_path = Path(Path.cwd(), r"data/", data['archive'])
        self.date_format = config.DATE_FORMAT
        self.most_recent_date = None
        self.load_csv(self.data_path)
        # print('projects' in data.keys())
        if 'projects' in data:
            logger.info("Projects found in data keys")
            self.projects_df = self.build_dataframe(data = data['projects'], mapping=config.PROJECT_COLUMN_MAPPING)
            self.clean_projects()
        else:
            self.projects_df = None
        if 'api_tasks' in data:
            self.process_api_tasks(data= data['api_tasks'])
        else:
            self.api_df = None
        
        self.distilled_tasks_df = None
## HELPERS
    def date_iso(self, date: datetime) -> str:
        return date.isoformat()
    
    def isoToString(self, date, format) -> str:
        if isinstance(date, str):
            date = dateparser.parse(date) 
        return date.strftime(format = format)

    def column_is_type(self, df: Series) -> str | None:
        
        return df.transform(lambda x: x.apply(type)).drop_duplicates().iloc[0]

    def split_column(self, data: DataFrame, split: str, key: int) -> DataFrame:
        # print(data.info())
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

    def build_dataframe(self, data: dict | list, mapping: dict[str, str] | None = None) -> DataFrame:
        df = pd.DataFrame(data).infer_objects()
        # print(df.columns)
        if mapping:
            # filter down to columns i want to keep
            existing_source_cols = [c for c in mapping if c in df.columns]
            # print(f"columns to filter on: {existing_source_cols}")
            # print(f"mapping dict: {mapping}")
            if "due" in df.columns and "due" not in existing_source_cols:
                existing_source_cols.append("due")
            df = df[existing_source_cols]
            # rename columns
            # print(f"before renaming: {df.columns}")
            df = df.rename(columns=mapping)
            # print(f"after renaming:{df.columns}")
        return df
    
    def process_api_tasks(self, data):
        df = self.build_dataframe(data, config.TASK_COLUMN_MAPPING)
        df["CompletedDate_dt"] = pd.to_datetime(df["CompletedDate"],errors="coerce")
        #explode due dict into columns
        if "due" in df.columns:
            df = self.clean_dates(df)
            df = df.drop(columns=["due"], errors="ignore")
        
        df = df[[c for c in config.DISTILLED_TASK_COLUMNS if c in df.columns]]
        df = self.clean_dataframe(df)
        self.api_df = df

        
    def load_csv(self, path: Path) -> None:
        logger.info(f"Loading file to Dataframe:{path}")

        if Path.exists(path):
            self.csv_df = pd.read_csv(path).infer_objects()
            logger.info("csv file loaded successfully.")
        else:
            self.csv_df = None
            logger.warning(f"CSV loading failed. File did not exist at location: {path}")

        self.most_recent_date = self.max_date('CompletedDate')
        
    
    def max_date(self, col: str) -> datetime:
        if self.csv_df is None:
            now = datetime.now(tz=timezone(
            -timedelta(hours=5),
              name="CDT")).replace(day=1)
            default_date = (now - timedelta(days=90)).replace(day=1)
            return default_date 
        maxdate = self.csv_df[f'{col}'].max()
        return dateparser.parse(maxdate)
        
    def combine_tasks(self) -> None:
        logger.info("Combining archived tasks with newly pulled tasks")
        if self.csv_df is not None:
            if "ProjectName" in self.csv_df:
                self.csv_df = self.csv_df.drop(columns=["ProjectName"])
            self.distilled_tasks_df = pd.concat([self.api_df, self.csv_df]).reset_index(drop=True)
        elif self.api_df is not None:
            self.distilled_tasks_df = self.api_df
        else:
            logger.error("API and CSV dataframes are empty.")

    def get_df_id(self, dataframe: DataFrame) -> tuple:

        if "id" not in dataframe.columns:
            val = dataframe.columns.get_loc("TaskID")
            output = (val, "TaskID")    
        else:    
            val = dataframe.columns.get_loc("id")
            output = (val, "id")    
        if not isinstance(val, int):
            raise TypeError(f"Expected single 'id' column, but found {type(val)}")
        return output
        
    def clean_dates(self, df: DataFrame) -> DataFrame:
        if df['due'].isna().any() == True:
            logger.info("Due columns is empty. Skipping step.")
            # print(df.columns)
            df['DueDate'] = "1900/01/01"
            df['IsRecurringTask'] = False
            return df  
        print(df['due'].isna().any())
        pkey = self.get_df_id(df)
        date_columns = self.split_column(data = df, split="due",key=pkey[1])
        date_columns['DueDate'] = date_columns['DueDate'].apply(dateparser.parse)
        date_columns['DueDate'] = [date.strftime(self.date_format) for date in date_columns['DueDate']]
        combined_df = pd.merge(left= df, right=date_columns, on=pkey[1], how='left')
        colnames = config.DATE_COLUMNS
        combined_df[colnames] = combined_df[colnames].apply(
            lambda row: [self.isoToString(rowItem, self.date_format) for rowItem in row]
        )
        if "DueIs_recurring" in combined_df.columns:
            combined_df= combined_df.rename(columns={"DueIs_recurring":"IsRecurringTask"})
        return combined_df
    
    def clean_dataframe(self, name: DataFrame)-> DataFrame:
        # logger.info(f"Cleaning Dataframe: {str(name)}")
        # if not hasattr(self, name):
        #         raise AttributeError(f"Data Processor has no attribute {name}")
        # df = getattr(self, name)
        df = name
        fill_values = {
            'IsRecurringTask': False,
            'DueDate': '1900/01/01',
            'TaskDuration': 0,
            'ParentTaskID': ""
        }
        # df = df.rename(columns=self.COLUMNS_RENAMED)
        # df = df.drop(columns=self.COLUMN_TEMPLATE["drop"], errors="ignore")
        df = df.fillna(fill_values)
        return df
    
    def clean_projects(self) -> None:
    
        # columns = list(config.PROJECT_COLUMN_RENAMES.keys())
        if isinstance(self.projects_df, pd.DataFrame):
            # self.projects_df = self.projects_df[columns]
            # self.projects_df.rename(columns=config.PROJECT_COLUMN_RENAMES, inplace=True)
            self.projects_df.fillna("",inplace=True)
    
    def merge_dataframes(self) -> None:
        logger.info("Merging projects with tasks...")
        if not isinstance(self.distilled_tasks_df, DataFrame):
            raise TypeError("Expected Distilled Data to exist. Found None")
        if not isinstance(self.projects_df, DataFrame):
            raise TypeError("Expected Distilled Data to exist. Found None")
        
        if "ProjectID" not in self.distilled_tasks_df:
            self.distilled_tasks_df = self.clean_dataframe(self.distilled_tasks_df)

        output = pd.merge(
            left = self.distilled_tasks_df,
            right = self.projects_df,
            how = "left",
            left_on="ProjectID",
            right_on = "ProjectID"
        )

        output = self.clean_dataframe(output)
        self.distilled_tasks_df = output
        
    
    def save_to_csv(self)-> None:
        logger.info(f"CSV DataFrame Type: {type(self.csv_df)}")
        if not isinstance(self.distilled_tasks_df, DataFrame):
            raise TypeError()
        if not isinstance(self.csv_df, DataFrame):
            logger.debug("No archive file found. Saving all tasks...")
            self.distilled_tasks_df.to_csv(self.data_path, index=False)
            return
        logger.info("Appending new tasks to existing archive...")
        for i, row in self.distilled_tasks_df.iterrows():
            if row["TaskID"] not in self.csv_df["TaskID"].values:
                new_task = row.to_frame().T
                new_task.to_csv(self.data_path, mode="a", index=False, header=False)
        logger.info("Tasks saved to archive.")
        return
