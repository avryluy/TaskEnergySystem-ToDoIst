import requests

from utils.credentials import api_key
from utils.logger import logger


class ToDoistAPIClient:
    """Handles Data collection from ToDoist API"""

    BASE_URL = "https://api.todoist.com/api/v1/"

    def __init__(self):
        logger.info("ToDoist API Module Initialized.")
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        )

    def _make_request(self, endpoint: str, params: dict | None = None) -> list[dict]:
        url = f"{self.BASE_URL}{endpoint}"
        items = []
        cursor = None
        logger.info(f"Making request for ToDoist {endpoint}")
        while True:
            request_params = params.copy() if params else {}
            if cursor:
                request_params["cursor"] = cursor

            try:
                response = self.session.get(url, params=request_params)
                response.raise_for_status()
                data = response.json()
                results_key = "results" if "project" in endpoint else "items"
                logger.info(f"Request Session results key:{results_key}")
                items.extend(data.get(results_key))
                cursor = data.get("next_cursor")
            except Exception as e:
                logger.error(e)
            if not cursor:
                break
        return items

    def get_projects(self):
        """Fetch all projects."""
        return self._make_request("projects/")

    def get_tasks_by_date(self, start_date=None, end_date=None):
        """Fetches tasks from a defined daterange"""
        params = {}
        params["limit"] = 200
        if start_date:
            params["since"] = start_date
        if end_date:
            params["until"] = end_date
        return self._make_request("tasks/completed/by_completion_date/", params=params)
