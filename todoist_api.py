from utils.credentials import api_key
import requests


class ToDoistAPIClient:
    """Handles Data collection from ToDoist API"""
    BASE_URL = "https://api.todoist.com/api/v1/"

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {api_key}"
            }
        self.request_body = {"since": None, "until": None, "limit": "200"}

    def todoistRequest(url, param, header):
        items = []
        result_type = "items"
        cursor = None
        
        if "project" in url:
            result_type = "results"
        
        while True:
        
            if cursor:
                param["cursor"] = cursor

            response = requests.get(url, params=param, headers=header)
            response.raise_for_status()
            data = response.json()

            items.extend(data.get(result_type))

            cursor = data.get("next_cursor")
            if not cursor:
                break
        return items

    def get_projects(self):
        projects_url = self.BASE_URL + "projects/"
        response = self.todoistRequest(projects_url, self.param, self.headers)
        return response

    def get_tasks_by_date(self,start_date=None, end_date=None):
            """Fetches tasks from a defined daterange"""
            task_url = self.BASE_URL + "tasks/completed/by_completion_date/"
            self.param['since'] = start_date
            self.param['until'] = end_date
            response = self.todoistRequest(task_url, self.param, self.headers)
            return response
