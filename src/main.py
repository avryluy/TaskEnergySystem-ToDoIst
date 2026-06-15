# import visualizations
from utils import credentials as c
from utils import todoist_api, data_handler






def main():
    data = {}
    data['archive'] = c.FILE_PATH
    api = todoist_api.ToDoistAPIClient()
    data["projects"] = api.get_projects()
    data["api_tasks"] = api.get_tasks_by_date
    handler = data_handler.DataProcessor(data)
    return 0