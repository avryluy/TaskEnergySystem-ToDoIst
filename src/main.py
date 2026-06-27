from datetime import datetime
from utils import visualizations as v
from utils import credentials as c
from utils import todoist_api, data_handler
from utils.logger import logger
# import pandas as pd
# from pathlib import Path

def main():
    logger.info("Initiating Program")
    data = {}
    data['archive'] = c.FILE_PATH
    api = todoist_api.ToDoistAPIClient()
    data["projects"] = api.get_projects()
    # text = 'api_tasks' in data.keys()
    # print(text)
    last_saved_date = data_handler.DataProcessor(data).max_date('CompletedDate')
    data["api_tasks"] = api.get_tasks_by_date(last_saved_date, datetime.now())
    # del last_saved_date
    # df = pd.DataFrame(data["api_tasks"])
    # print(df.columns)
    # df.to_csv(Path(Path.cwd(), c.SAVE_DIR , "/raw_api.csv"))
    logger.info("Api Data collected.")
    # print(data["api_tasks"])
    handler = data_handler.DataProcessor(data)
    # print(handler.api_df.columns)
    handler.combine_tasks()
    # print(handler.distilled_tasks_df.columns)
    # if isinstance(handler.api_df, pd.DataFrame):
    #     handler.api_df.to_csv(Path(Path.cwd(), c.SAVE_DIR , "/api_tablev2.csv"))
    # print(handler.projects_df.columns)
    # print(handler.api_df.columns)
    # print(handler.distilled_tasks_df.columns)
    handler.merge_dataframes()
    # print(handler.csv_df.columns)
    # print(handler.COLUMNS_RENAMED)
    handler.save_to_csv()
    graphs = v.TaskGraphs(handler.distilled_tasks_df,c.SAVE_DIR)
    graphs.generate_all_charts()
    
    return 0

if __name__ == "__main__":
    main()