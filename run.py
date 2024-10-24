import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
from openpyxl import load_workbook

def generate_match_id(date, opponent, goals):
    return f"{date.strip().replace(' ', '_').replace('/', '-')}_{opponent.strip().replace(' ', '_').replace('/', '-')}_{goals.strip()}"

def get_team_rating(rating_page_url):
    page = requests.get(rating_page_url)
    soup = BeautifulSoup(page.text, "html.parser")
    rating_element = soup.find('div', class_='col-auto font-tabular-nums fw-bold')
    return rating_element.text.strip() if rating_element else 'No Rating Found'

def scrapStats():
    pageToScrape = requests.get("https://proclubshead.com/24/club-league-matches/gen5-12115349/")
    soup = BeautifulSoup(pageToScrape.text, "html.parser")

    matches_container = soup.find('div', class_='col-12 col-lg-8')
    if not matches_container:
        print("No matches container found.")
        return

    date = matches_container.find('div', class_='h5')
    match_data = {'Date': date.text.strip() if date else 'No Date Found'}

    match_containers = matches_container.find_all('div', class_='mb-3')
    if not match_containers:
        print("No match containers found.")
        return

    first_match = match_containers[0]
    opponent = first_match.find('div', class_='col text-start text-truncate')
    match_data['Opponent'] = opponent.text.strip() if opponent else 'No Opponent Found'

    stat_rows = first_match.find_all('div', class_='align-items-center g-2 row')

    goals_row = next((row for row in stat_rows if row.find('div', class_='col text-center').text.strip() == 'Goals'), None)
    if goals_row:
        goal_elements = goals_row.find_all('div', class_='col-auto font-tabular-nums fw-bold order-first')
        match_data['Goals'] = goal_elements[0].text.strip() if len(goal_elements) >= 1 else 'No Team Goals Found'

    goalsop_row = next((row for row in stat_rows if row.find('div', class_='col text-center').text.strip() == 'Goals'), None)
    if goalsop_row:
        goal_elements = goalsop_row.find_all('div', class_='col-auto font-tabular-nums fw-bold')
        match_data['GoalsOpponent'] = goal_elements[0].text.strip() if len(goal_elements) >= 1 else 'No Opponent Goals Found'

    match_data['ID'] = generate_match_id(match_data.get('Date', 'No Date Found'),
                                          match_data.get('Opponent', 'No Opponent Found'),
                                          match_data.get('Goals', 'No Team Goals Found'))

    for row in stat_rows:
        stat_name_element = row.find('div', class_='col text-center')
        stat_value_elements = row.find_all('div', class_='col-auto font-tabular-nums fw-bold order-first')

        if stat_name_element:
            stat_name = stat_name_element.text.strip().lower()
            if stat_name in ['shots', 'shot success rate', 'passes made', 'pass attempts', 'pass success rate', 'tackles made', 'tackle attempts', 'tackle success rate', 'red cards']:
                match_data[stat_name] = stat_value_elements[0].text.strip() if len(stat_value_elements) > 0 else ''

    rating_page_url = "https://proclubshead.com/24/club/gen5-12115349/"
    match_data['Rating'] = get_team_rating(rating_page_url)

    df = pd.DataFrame([match_data])

    column_order = [
        'ID', 'Date', 'Opponent', 'Goals', 'GoalsOpponent',
        'shots', 'shot success rate', 'passes made', 'pass attempts',
        'pass success rate', 'tackles made', 'tackle attempts',
        'tackle success rate', 'red cards', 'Rating'
    ]
    df = df.reindex(columns=column_order)

    excel_file = 'EA FC24 Clubs Stats.xlsx'

    if os.path.exists(excel_file):
        with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            existing_df = pd.read_excel(excel_file, sheet_name='Match Data', engine='openpyxl')
            updated_df = pd.concat([existing_df, df], ignore_index=True)
            updated_df.drop_duplicates(subset=['ID'], inplace=True)
            updated_df.to_excel(writer, sheet_name='Match Data', index=False)
    else:
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Match Data', index=False)

    print(f"Data written to {excel_file}")

scrapStats()

while True:
    scrapStats()
    time.sleep(60)  # Sleep for 2 minutes (120 seconds)
