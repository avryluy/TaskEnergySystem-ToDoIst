from datetime import datetime
from utils import visualizations as v
from utils import credentials as c
from utils import todoist_api, data_handler
from utils.logger import logger

def main():
    logger.info("Initiating Program")
    data = {}
    data['archive'] = c.FILE_PATH
    api = todoist_api.ToDoistAPIClient()
    data["projects"] = api.get_projects()
    
    last_saved_date = data_handler.DataProcessor(data).max_date('CompletedDate')
    data["api_tasks"] = api.get_tasks_by_date(last_saved_date, datetime.now())
    
    logger.info("Api Data collected.")
    
    handler = data_handler.DataProcessor(data)
    handler.combine_tasks()
    handler.merge_dataframes()
    handler.save_to_csv()
    graphs = v.TaskGraphs(handler.distilled_tasks_df,c.SAVE_DIR)
    graphs.generate_all_charts()
    
    return 0

if __name__ == "__main__":
    main()