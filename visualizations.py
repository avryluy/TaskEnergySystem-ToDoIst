import pandas as pd
import matplotlib.pyplot as plt
import ast
from datetime import datetime, timedelta
# import ost

# Load data
df = pd.read_csv('data/my-energysystem-tasks.csv')
df['CompletedDate'] = pd.to_datetime(df['CompletedDate'])

# Helper to parse TaskLabels
def parse_labels(label_str):
    try:
        return ast.literal_eval(label_str)
    except TypeError as e:
        print("Error: {}".format(e))
        return []

df['Labels'] = df['TaskLabels'].apply(parse_labels)

# Timeframe filters
def get_timeframe_df(df, timeframe):
    now = datetime.now()
    if timeframe == 'this week':
        start_of_week = now - timedelta(days=now.weekday())
        return df[df['CompletedDate'] >= start_of_week]
    elif timeframe == 'this month':
        start_of_month = now.replace(day=1)
        return df[df['CompletedDate'] >= start_of_month]
    else: # all time
        return df

timeframes = ['this week', 'this month', 'all time']

for tf in timeframes:
    current_df = get_timeframe_df(df, tf)
    print(f"--- {tf.upper()} ---")
    
    # 1. Pie chart: depleting vs recharging
    depleting = current_df[current_df['Labels'].apply(lambda x: 'depleting' in x)]
    recharging = current_df[current_df['Labels'].apply(lambda x: 'recharging' in x)]
    
    # Note: A task could have both, but for a simple pie chart we might need to handle exclusivity or just count occurrences
    # Let's count unique tasks that have at least one of these
    depleting_count = len(depleting)
    recharging_count = len(recharging)
    
    plt.figure(figsize=(6, 6))
    plt.pie([depleting_count, recharging_count], labels=['Depleting', 'Recharging'], autopct='%1.1f%%', colors=['red', 'green'])
    plt.title(f'Depleting vs Recharging ({tf})')
    plt.savefig(f'chart_1_{tf.replace(" ", "_")}.png')
    plt.close()

    # 2. Pie chart: labels excluding depleting and recharging
    other_tasks = current_df[~current_df['Labels'].apply(lambda x: 'depleting' in x or 'recharging' in x)]
    label_counts = other_tasks['Labels'].explode().value_counts()
    
    if not label_counts.empty:
        plt.figure(figsize=(8, 8))
        label_counts.plot(kind='pie', autopct='%1.1f%%')
        plt.title(f'Task Labels excluding Depleting/Recharging ({tf})')
        plt.savefig(f'chart_2_{tf.replace(" ", "_")}.png')
        plt.close()

    # 3. Bar chart: energy_high, energy_medium, energy_low grouped by depleting/recharging
    energy_tasks = current_df[current_df['Labels'].apply(lambda x: any(e in x for e in ['energy_high', 'energy_medium', 'energy_low']))]
    
    # Grouping logic
    results = []
    for _, row in energy_tasks.iterrows():
        labels = row['Labels']
        energy_type = next((e for e in ['energy_high', 'energy_medium', 'energy_low'] if e in labels), None)
        is_depleting = 'depleting' in labels
        is_recharging = 'recharging' in labels
        
        group = "Depleting" if is_depleting else ("Recharging" if is_recharging else "Neither")
        results.append({'EnergyType': energy_type, 'Group': group})
    
    if results:
        res_df = pd.DataFrame(results)
        pivot_df = res_df.groupby(['Group', 'EnergyType']).size().unstack(fill_value=0)
        pivot_df.plot(kind='bar', figsize=(10, 6))
        plt.title(f'Energy Levels by Group ({tf})')
        plt.savefig(f'chart_3_{tf.replace(" ", "_")}.png')
        plt.close()

print("Charts generated.")
