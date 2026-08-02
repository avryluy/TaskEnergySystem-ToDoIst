from datetime import datetime, timedelta, timezone

from utils import credentials as c
from utils import data_handler, mailer, todoist_api
from utils import visualizations as v
from utils.logger import logger


def main():
    logger.info("Initiating Program")
    data = {}
    data['archive'] = c.FILE_PATH
    api = todoist_api.ToDoistAPIClient()
    data["projects"] = api.get_projects()
    
    last_saved_date = data_handler.DataProcessor(data).max_date('CompletedDate')
    data["api_tasks"] = api.get_tasks_by_date(last_saved_date, 
                                              datetime.now(tz=timezone(
            -timedelta(hours=5),
              name="CDT")))
    
    # df = pd.DataFrame(data["api_tasks"])
    # due_col = df["due"].isna()
    # print(due_col.any())
    # df.to_csv('debug_table.csv')
    # logger.info("Api Data collected.")
    
    handler = data_handler.DataProcessor(data)
    handler.combine_tasks()
    handler.merge_dataframes()
    handler.save_to_csv()
    graphs = v.TaskGraphs(handler.distilled_tasks_df,c.SAVE_DIR)
    graph_paths = graphs.generate_all_charts()
    mailer.Mailer.send_report(graph_paths)
    return 0

if __name__ == "__main__":
    main()