from datetime import datetime
from pathlib import Path
from dateutil import parser as dateparser
import pandas as pd
from utils import config
# from typing import Dict, Type


class DataProcessor:
    "Handles all data manipulation and storing into archive."

    COLUMN_TEMPLATE = config.TODOIST_COLUMNS
    # FILENAME = "my-energysystem-tasks.csv"
    COLUMNS_RENAMED = dict(
        zip(config.TODOIST_COLUMNS["keep"], config.TODOIST_COLUMNS["renamed"])
    )
    DATE_FORMAT = r"%Y/%m/%d"

    def __init__(self, archive, api) -> None:
        self.most_recent_date = None
        self.csv_df = None
        self.data_path = Path(Path.cwd(), r"data/", archive)

    def isoToString(self, date, format) -> str:
        if isinstance(date, str):
            date = dateparser.parse(date) 
        return date.strftime(format = format)

    def column_is_type(self, df) -> str | None:
        return df.transform(lambda x: x.apply(type)).drop_duplicates().iloc[0]

    def split_column(self, data, split, key):
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

    def load_csv(self, path) -> None:
        if Path.exists(self.data_path):
            self.csv_df = pd.read_csv(path).infer_objects()
        return

    def date_iso(self, date: datetime) -> str:
        return date.isoformat()

    def max_date(self, date: str) -> datetime:
        if date is None:
            date = datetime.now().replace(day=1)
        else:
            maxdate = dateparser.parse(date)
        return maxdate


# ----------- #
#   OLD WAY   #
# COLUMN_TEMPLATE = config.TODOIST_COLUMNS
# FILENAME = "my-energysystem-tasks.csv"
# COLUMNS_RENAMED = dict(zip(config.TODOIST_COLUMNS['keep'],config.TODOIST_COLUMNS['renamed']))
# mostrecentdate = None
# df = None
# data_path = Path(Path.cwd(),r"data/",FILENAME)
# date_format = r"%Y/%m/%d"

# def isoToString(date, format):
#     input_date = dateparser.parse(date)
#     return input_date.strftime(format=format)

# def column_is_type(df):
#     return df.transform(lambda x: x.apply(type)).drop_duplicates().iloc[0]

# def split_column(data,split,key):
#     test = data[[key,split]]
#     test = test[test.iloc[:, 1].notna()]
#     # print(column_is_type(test.iloc[:,1]))
#     if column_is_type(test.iloc[:,1]) is dict:
#         unnest = test[split].apply(pd.Series)
#         source_names = unnest.columns.tolist()
#         updated_names = [split.capitalize() + part.capitalize() for part in source_names]

#         rename_zip = zip(source_names, updated_names)
#         rename_dict = dict(rename_zip)

#         renamed = unnest.rename(rename_dict, axis=1)
#         output = test.join(renamed)
#         return output

# Path.read_bytes(data_path)
# if Path.exists(data_path) is False:
#     print("file not found.\npull from earliest month start.")
# else:
#     print("file found. Opening to collect last task date")
#     df = pd.read_csv(data_path).infer_objects()
#     mostrecentdate = df['CompletedDate'].max()
#     end_date = datetime.now()

# if mostrecentdate is None:
#     print("No most recent date found")
#     start_date = datetime.now()
#     start_date = datetime.replace(start_date,day=1)
# else:
#     mostrecentdate = dateparser.parse(mostrecentdate)
#     start_date = mostrecentdate

# iso_start_date = start_date.isoformat()
# iso_end_date = end_date.isoformat()

proj_df = pd.DataFrame(projects)
proj_df = proj_df[["id", "name"]]
proj_df.rename(columns={"name": "ProjectName", "id": "ProjectID"}, inplace=True)

task_table = pd.DataFrame(items)

# if df is not None:
#     task_table = pd.concat([task_table,df])

task_table = task_table.reset_index(drop=True)
# task_table
id_column = (task_table.columns.get_loc("id"), "id")

date_columns = split_column(data=task_table, split="due", key=id_column[1])

if date_columns is not None:
    date_columns["DueDate"] = date_columns["DueDate"].apply(dateparser.parse)
    date_columns["DueDate"] = [
        date.strftime(date_format) for date in date_columns["DueDate"]
    ]
    combined_df = pd.merge(
        left=task_table, right=date_columns, on=id_column[1], how="left"
    )

dates_to_convert = ["added_at", "completed_at", "updated_at"]

combined_df[dates_to_convert] = combined_df[dates_to_convert].apply(
    lambda row: [isoToString(rowItem, date_format) for rowItem in row]
)

full_data = pd.merge(
    left=combined_df,
    right=proj_df,
    how="left",
    left_on="project_id",
    right_on="ProjectID",
)

final_df = full_data.drop(columns=COLUMN_TEMPLATE["drop"], errors="ignore")

final_df = final_df.rename(columns=COLUMNS_RENAMED)

final_df["IsRecurringTask"] = final_df["IsRecurringTask"].fillna(value=False)
final_df["DueDate"] = final_df["DueDate"].fillna("1900/01/01")
final_df["TaskDuration"] = final_df["TaskDuration"].fillna(0)
final_df["ParentTaskID"] = final_df["ParentTaskID"].fillna(value="")
final_df = final_df[list(COLUMNS_RENAMED.values())]


if df is None:
    final_df.to_csv(data_path, index=False)
else:
    for i, row in final_df.iterrows():
        if row["TaskID"] not in df["TaskID"].values:
            print(f"Task {row['TaskID']} not in existing tasks")
            row_to_append = row.to_frame().T
            row_to_append.to_csv(data_path, mode="a", index=False, header=False)
            refreshed_df = pd.concat([df, row.to_frame().T], ignore_index=True)
        else:
            refreshed_df = df


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

