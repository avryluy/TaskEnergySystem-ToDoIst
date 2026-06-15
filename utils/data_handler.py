from datetime import datetime
from pathlib import Path
from dateutil import parser as dateparser
import pandas as pd
from pandas import DataFrame
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

    def isoToString(self, date, format) -> str:
        if isinstance(date, str):
            date = dateparser.parse(date) 
        return date.strftime(format = format)

    def column_is_type(self, df) -> str | None:
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

    def load_csv(self, path: Path) -> None:
        if Path.exists(self.data_path):
            self.csv_df = pd.read_csv(path).infer_objects()
        else:
            self.csv_df = None
        return

    def date_iso(self, date: datetime) -> str:
        return date.isoformat()

    def max_date(self, col: str) -> datetime:
        if self.csv_df is None:
            return datetime.now().replace(day=1) 
        maxdate = self.csv_df[f'{col}'].max()
        return dateparser.parse(maxdate)

    def build_dataframe(self, data: dict | list, columns: list | None = None, renames: dict[str, str] | None = None) -> DataFrame:
        df = pd.DataFrame(data).infer_objects()
        if columns:
            df = df[columns]
        if renames:
            df = df.rename(columns=renames)
        return df
        
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
        
        return 
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
# ----------- #
#   OLD WAY   #
# full_data = pd.merge(
#     left=combined_df,
#     right=proj_df,
#     how="left",
#     left_on="project_id",
#     right_on="ProjectID",
# )

# final_df = full_data.drop(columns=COLUMN_TEMPLATE["drop"], errors="ignore")

# final_df = final_df.rename(columns=COLUMNS_RENAMED)

# final_df["IsRecurringTask"] = final_df["IsRecurringTask"].fillna(value=False)
# final_df["DueDate"] = final_df["DueDate"].fillna("1900/01/01")
# final_df["TaskDuration"] = final_df["TaskDuration"].fillna(0)
# final_df["ParentTaskID"] = final_df["ParentTaskID"].fillna(value="")
# final_df = final_df[list(COLUMNS_RENAMED.values())]


# if df is None:
#     final_df.to_csv(data_path, index=False)
# else:
#     for i, row in final_df.iterrows():
#         if row["TaskID"] not in df["TaskID"].values:
#             print(f"Task {row['TaskID']} not in existing tasks")
#             row_to_append = row.to_frame().T
#             row_to_append.to_csv(data_path, mode="a", index=False, header=False)
#             refreshed_df = pd.concat([df, row.to_frame().T], ignore_index=True)
#         else:
#             refreshed_df = df

# Notes 06/14/2026
# Based on the # Notes and # OLD WAY sections in data_handler.py, here is your progress feedback:
# ✅ Completed / Good Progress
# - Class Structure: You've successfully moved core helpers (column_is_type, split_column) into the DataProcessor class.
# - New Methods: load_csv, date_iso, and max_date are implemented and ready to be used.
# - Refactoring Path: The "OLD WAY" is clearly identified and commented out, providing a clear roadmap for what needs to be migrated.
# 🏗️ Next Steps (Remaining Refactoring)
# To fully move from procedural to object-oriented logic, you should focus on the following:
# 1. Methodize Data Transformation: 
# Move the logic from lines 116–125 into dedicated methods. For example:
# - merge_projects(self, combined_df, proj_df): To handle the left merge with project data.
# - clean_dataframe(self, df): To handle renaming, dropping columns, and the specific NaN fills (e.g., IsRecurringTask to False).
# 2. Integrate File Handling & State:
# - Update load_csv to encapsulate the start_date determination logic mentioned in Note #3.
# - Create a method (e.g., save_to_csv) to handle the "append if new" logic currently found in lines 128–138.
# 3. Dependency Injection:
# - Instead of relying on global variables, consider passing projects and items into the DataProcessor constructor or the specific methods that need them.
# 4. Note Clarification:
# - isoToString: The note suggests a bug with datetime objects, but your current implementation (lines 27–30) actually handles t

# Notes

# The refactoring is off to a good start, but there is significant work remaining to fully move the procedural logic into the `DataProcessor` class.

# ### Progress Summary
# *   **Class Structure**: You've successfully defined the `DataProcessor` class and moved core helper functions like `column_is_type` and `split_column` into it.
# *   **Decommissioning**: The "OLD WAY" section is correctly commented out, clearly marking the target for removal.
# *   **New Methods**: You've added `load_csv`, `date_iso`, and `max_date`, which are good building blocks for the new architecture.

# ### Areas for Improvement
# 1.  **Fix `isoToString` Bug**:
#     As we discussed, `isoToString` (line 24) will fail if passed a `datetime` object. You should update it to check the type:
#     ```python
#     def isoToString(self, date, format) -> str:
#         if isinstance(date, str):
#             date = dateparser.parse(date)
#         return date.strftime(format=format)
#     ```

# 2.  **Move Processing Logic**:
#     The bulk of the data manipulation (merging, renaming, and filling NaNs) is still running at the script level (lines 116–175). These should be moved into methods within `DataProcessor` (e.g., `process_data`, `clean_dataframe`).

# 3.  **Integrate File Handling**:
#     The logic that checks if the file exists and determines the `start_date` (formerly lines 97–111) should be encapsulated within `load_csv` or a similar initialization method to ensure the class handles its own state correctly.

# 4.  **Dependency Injection**:
#     The script currently relies on global variables `projects` and `items`. These should ideally be passed into the `DataProcessor` constructor or its processing methods to make the class more testable and modular.

# ---

