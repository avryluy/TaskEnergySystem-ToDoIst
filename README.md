# TaskEnergySystem-ToDoIst

## Overview
TaskEnergySystem-ToDoIst is a Python-based automation tool designed to synchronize, process, and visualize project tasks from `Todoist`. It fetches tasks via the Todoist API, merges them with local archived data, cleans the resulting datasets (handling complex nested structures like due dates), generates visual analytics (charts/graphs), and sends a summary report via email.

The system is particularly geared towards tracking "Energy Systems" tasks, distinguishing between depleting and recharging activities over various timeframes (week, month, all-time).

## Key Features

- **Todoist Integration:** Automatically fetches projects and tasks from Todoist using the official API.
- **Data Distillation:** Processes raw JSON responses into structured Pandas DataFrames, handling column mapping and nested dictionary expansion.
- **Smart Date Handling:** Uses dateparser to normalize varied date formats into a consistent standard.
- **Data Archiving:** Maintains a local CSV-based archive to ensure persistence and allow for historical analysis across multiple runs.
- **Visual Analytics:** Generates a suite of charts (e.g., Energy Levels by Group, Depleting vs. Recharging) saved to a local data/output directory.
- **Automated Reporting:** Automatically emails the generated report and graph paths to a designated recipient.

## Project Structure

- src/main.py: The primary entry point that orchestrates the execution flow.
- utils/:
    - data_handler.py: Core logic for DataFrame manipulation, merging, and cleaning.
    - todoist_api.py: Client for interacting with the Todoist REST API.
    - mailer.py: Handles SMTP configuration and report delivery.
    - visualizations.py: Logic for generating charts and graphs.
    - config.py: Centralized configuration for mappings, date formats, and file paths.
    - credentials.py: Secure storage for API keys and SMTP credentials.
    - logger.py: Standardized logging configuration.
- data/: Contains input CSVs and the output/ directory for generated images.

## Prerequisites

- Python 3.12+
- A Todoist account with API access.
- An SMTP server (e.g., Gmail, Outlook) for automated reporting.

## Installation & Setup

1. Clone the repository and navigate to the project root.
2. Create a virtual environment:
    ```python 
    -m venv .venv
    .\.venv\Scripts\activate```
3. Install dependencies:
   `pip install -r requirements.txt`
4. Configure Credentials:
    Edit `utils/credentials.py` to include:
5. Configure Project Mappings:
    Adjust `utils/config.py` to match your specific Todoist project names and column structures.

## Usage

Run the main script to initiate the synchronization and reporting process:
``` python
python src/main.py
```

## Workflow

1. **Fetch:** The program connects to Todoist and retrieves projects and tasks since the last recorded completion date.
2. **Process:** The `DataProcessor` cleans the "due" fields and merges new tasks with the data/ archive.
3. **Distill:** Tasks are filtered and renamed based on configurations in `config.py`.
4. **Visualize:** `TaskGraphs` generates images for various metrics.
5. **Report:** The `Mailer` sends the final summary.

## Technical Notes

- **Data Integrity:** The system uses `pd.merge` to join tasks with project metadata to ensure every task is associated with its correct parent project.
- **Persistence:** The `save_to_csv` method ensures that only unique new tasks are appended to the archive, preventing duplication.
- **Timezone Awareness:** The system defaults to CDT (Central Daylight Time) for date calculations.