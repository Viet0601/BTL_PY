import re
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import pandas as pd
from bs4 import BeautifulSoup
import time
import unicodedata
from selenium.webdriver.support import expected_conditions as EC
import uuid
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
import os
import sqlite3
from selenium.webdriver.chrome.options import Options
def slugify_name(name):
    """
    Chuyển tên cầu thủ thành dạng URL (slug) cho footballtransfers.com
    Ví dụ:
      João Félix -> joao-felix
      Thiago Alcântara -> thiago-alcantara
      Pierre-Emerick Aubameyang -> pierre-emerick-aubameyang
    """
    name = unicodedata.normalize('NFD', name)
    name = name.encode('ascii', 'ignore').decode('utf-8')
    name = name.lower().strip()
    name = re.sub(r'[\s_]+', '-', name)
    name = re.sub(r'[^a-z0-9\-]', '', name)
    name = name.strip('-')
    return name

# ------------------------------
# 🔹 KIỂM TRA LINK CẦU THỦ CÓ TỒN TẠI KHÔNG
# ------------------------------
def url_exists(url):
    try:
        r = requests.head(url, allow_redirects=True, timeout=5)
        return r.status_code == 200
    except:
        return False


# ------------------------------
# 🔹 HÀM CRAWL DỮ LIỆU TỪ TRANG CÁ NHÂN CẦU THỦ
# ------------------------------
def extract_player_page_data(browser, player_url):
    """Lấy dữ liệu từ trang cá nhân của cầu thủ trên footballtransfers.com"""
    try:
        if not url_exists(player_url):
            return {"market_value": "N/A", "rating": "N/A"}

        browser.get(player_url)
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.player-tag'))
        )
        html_content = browser.page_source
        soup = BeautifulSoup(html_content, 'lxml')

        # 🏷️ Giá trị chuyển nhượng
        value_elem = soup.select_one('span.player-tag')
        market_value = value_elem.get_text(strip=True) if value_elem else "N/A"

        # 📊 Kỹ năng & tiềm năng
        skill_elem = soup.select_one('div.teamInfoTop-skill__skill')
        pot_elem = soup.select_one('div.teamInfoTop-skill__pot')

        def extract_number(text):
            match = re.search(r'(\d+(\.\d+)?)', text)
            return float(match.group(1)) if match else None

        skill = extract_number(skill_elem.get_text(strip=True)) if skill_elem else None
        pot = extract_number(pot_elem.get_text(strip=True)) if pot_elem else None
        rating = f"{skill}/{pot}" if skill and pot else "N/A"

        return {
            "market_value": market_value,
            "rating": rating
        }

    except Exception as e:
        print(f"⚠️ Không thể lấy dữ liệu từ {player_url}: {e}")
        return {"market_value": "N/A", "rating": "N/A"}


LINKS_URL_TO_CRAWL = {
    'Standard Stats': ('https://fbref.com/en/comps/9/2024-2025/stats/2024-2025-Premier-League-Stats', 'stats_standard'),
    'Shooting': ('https://fbref.com/en/comps/9/2024-2025/shooting/2024-2025-Premier-League-Stats', 'stats_shooting'),
    'Passing': ('https://fbref.com/en/comps/9/2024-2025/passing/2024-2025-Premier-League-Stats', 'stats_passing'),
    'Goal and Shot Creation': ('https://fbref.com/en/comps/9/2024-2025/gca/2024-2025-Premier-League-Stats', 'stats_gca'),
    'Defense': ('https://fbref.com/en/comps/9/2024-2025/defense/2024-2025-Premier-League-Stats', 'stats_defense'),

    'Possession': ('https://fbref.com/en/comps/9/2024-2025/possession/2024-2025-Premier-League-Stats', 'stats_possession'),
    'Miscellaneous': ('https://fbref.com/en/comps/9/2024-2025/misc/2024-2025-Premier-League-Stats', 'stats_misc'),
    'Goalkeeping': ('https://fbref.com/en/comps/9/2024-2025/keepers/2024-2025-Premier-League-Stats', 'stats_keeper')
}
PLAYER_KEY_TO_CRAWL = [
    'name', 'nationality', 'position', 'team', 'age', 'games', 'games_starts',
    'minutes', 'goals', 'assist', 'cards_yellow', 'cards_red', 'xg', 'xg_assist',
    'progressive_carries', 'progressive_passes', 'progressive_passes_received', 'goals_per90',
    'assists_per90', 'xg_per90', 'xg_assist_per90', 'gk_goals_against_per90', 'gk_save_pct',
    'gk_clean_sheets_pct', 'gk_pens_save_pct', 'shots_on_target_pct', 'shots_on_target_per90',
    'goals_per_shot', 'average_shot_distance', 'passes_completed', 'passes_pct', 'passes_total_distance',
    'passes_pct_short', 'passes_pct_medium', 'passes_pct_long', 'assisted_shots',
    'passes_into_final_third', 'passes_into_penalty_area', 'crosses_into_penalty_area',
    'sca', 'sca_per90', 'gca', 'gca_per90', 'tackles', 'tackles_won', 'challenges',
    'challenges_lost', 'blocks', 'blocked_shots', 'blocked_passes', 'interceptions', 'touches',
    'touches_def_pen_area', 'touches_def_3rd', 'touches_mid_3rd', 'touches_att_3rd',
    'touches_att_pen_area', 'take_ons', 'take_ons_won_pct', 'take_ons_tackled_pct', 'carries',
    'carries_progressive_distance', 'carries_into_final_third', 'carries_into_penalty_area', 'miscontrols',
    'dispossessed', 'passes_received', 'fouls', 'fouled', 'offsides', 'crosses',
    'ball_recoveries', 'aerials_won', 'aerials_lost', 'aerials_won_pct'
]

# -----------------------------------------
def initialize_player_dict():
    
    return {key: 'N/a' for key in PLAYER_KEY_TO_CRAWL}

# -----------------------------------------
def scrape_standard_stats():

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.implicitly_wait(10) # Chờ các phần tử trang tải
    try:
        url = LINKS_URL_TO_CRAWL['Standard Stats'][0]
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, LINKS_URL_TO_CRAWL['Standard Stats'][1])))
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        table = soup.find('table', attrs={'id': LINKS_URL_TO_CRAWL['Standard Stats'][1]})

        player_set = {}

        if not table:
            print("Error: Could not find the 'Standard Stats' table.")
            return player_set

        rows = table.find_all('tr', attrs={'data-row': True})

        for row in rows:
            try:
                name = row.find('td', attrs={'data-stat': 'player'}).text.strip()
                nationality = row.find('td', attrs={'data-stat': 'nationality'}).text.strip()
                position = row.find('td', attrs={'data-stat': 'position'}).text.strip()
                team = row.find('td', attrs={'data-stat': 'team'}).text.strip()
                age = row.find('td', attrs={'data-stat': 'age'}).text.strip()
                games = row.find('td', attrs={'data-stat': 'games'}).text.strip()
                games_starts = row.find('td', attrs={'data-stat': 'games_starts'}).text.strip()
                minutes_str = row.find('td', attrs={'data-stat': 'minutes'}).text.strip()
                goals = row.find('td', attrs={'data-stat': 'goals'}).text.strip()
                assist = row.find('td', attrs={'data-stat': 'assists'}).text.strip()
                cards_yellow = row.find('td', attrs={'data-stat': 'cards_yellow'}).text.strip()
                cards_red = row.find('td', attrs={'data-stat': 'cards_red'}).text.strip()
                xg = row.find('td', attrs={'data-stat': 'xg'}).text.strip()
                xg_assist = row.find('td', attrs={'data-stat': 'xg_assist'}).text.strip()
                progressive_carries = row.find('td', attrs={'data-stat': 'progressive_carries'}).text.strip()
                progressive_passes = row.find('td', attrs={'data-stat': 'progressive_passes'}).text.strip()
                progressive_passes_received = row.find('td', attrs={'data-stat': 'progressive_passes_received'}).text.strip()
                goals_per90 = row.find('td', attrs={'data-stat': 'goals_per90'}).text.strip()
                assists_per90 = row.find('td', attrs={'data-stat': 'assists_per90'}).text.strip()
                xg_per90 = row.find('td', attrs={'data-stat': 'xg_per90'}).text.strip()
                xg_assist_per90 = row.find('td', attrs={'data-stat': 'xg_assist_per90'}).text.strip()

                player_data = initialize_player_dict()
                player_data.update({
                    'name': name,
                    'nationality': nationality,
                    'position': position,
                    'team': team,
                    'age': age,
                    'games': games,
                    'games_starts': games_starts,
                    'minutes': minutes_str,
                    'goals': goals,
                    'assist': assist,
                    'cards_yellow': cards_yellow,
                    'cards_red': cards_red,
                    'xg': xg,
                    'xg_assist': xg_assist,
                    'progressive_carries': progressive_carries,
                    'progressive_passes': progressive_passes,
                    'progressive_passes_received': progressive_passes_received,
                    'goals_per90': goals_per90,
                    'assists_per90': assists_per90,
                    'xg_per90': xg_per90,
                    'xg_assist_per90': xg_assist_per90
                })

                minutes_str_cleaned = minutes_str.replace(',', '')
                if minutes_str_cleaned.isdigit() and int(minutes_str_cleaned) <= 90:
                    continue

                player_key = str(name) + str(team)
                player_set[player_key] = player_data

            except Exception as e:
                print(f"Error processing row: {e}")
                continue

    finally:
        driver.quit()

    return player_set

# -----------------------------------------
def update_goalkeeping_stats(player_set):
    """Update player data with goalkeeping statistics.
    Cập nhật dữ liệu cầu thủ với thống kê thủ môn."""
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.implicitly_wait(10)
    try:
        url = LINKS_URL_TO_CRAWL['Goalkeeping'][0]
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, LINKS_URL_TO_CRAWL['Goalkeeping'][1])))
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        table = soup.find('table', attrs={'id': LINKS_URL_TO_CRAWL['Goalkeeping'][1]})

        if not table:
            print("Error: Could not find the 'Goalkeeping' table.")
            return

        rows = table.find_all('tr', attrs={'data-row': True})

        for row in rows:
            try:
                name = row.find('td', attrs={'data-stat': 'player'}).text.strip()
                team = row.find('td', attrs={'data-stat': 'team'}).text.strip()
                player_key = str(name) + str(team)

                if player_key in player_set:
                    player_set[player_key].update({
                        'gk_goals_against_per90': row.find('td', attrs={'data-stat': 'gk_goals_against_per90'}).text.strip(),
                        'gk_save_pct': row.find('td', attrs={'data-stat': 'gk_save_pct'}).text.strip(),
                        'gk_clean_sheets_pct': row.find('td', attrs={'data-stat': 'gk_clean_sheets_pct'}).text.strip(),
                        'gk_pens_save_pct': row.find('td', attrs={'data-stat': 'gk_pens_save_pct'}).text.strip()
                    })
            except Exception as e:
                print(f"Error processing goalkeeping row: {e}")
                continue

    finally:
        driver.quit()

# -----------------------------------------
def update_shooting_stats(player_set):
    """Update player data with shooting statistics.
    Cập nhật dữ liệu cầu thủ với thống kê sút bóng."""
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.implicitly_wait(10)
    try:
        url = LINKS_URL_TO_CRAWL['Shooting'][0]
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, LINKS_URL_TO_CRAWL['Shooting'][1])))
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        table = soup.find('table', attrs={'id': LINKS_URL_TO_CRAWL['Shooting'][1]})

        if not table:
            print("Error: Could not find the 'Shooting' table.")
            return

        rows = table.find_all('tr', attrs={'data-row': True})

        for row in rows:
            try:
                name = row.find('td', attrs={'data-stat': 'player'}).text.strip()
                team = row.find('td', attrs={'data-stat': 'team'}).text.strip()
                player_key = str(name) + str(team)

                if player_key in player_set:
                    player_set[player_key].update({
                        'shots_on_target_pct': row.find('td', attrs={'data-stat': 'shots_on_target_pct'}).text.strip(),
                        'shots_on_target_per90': row.find('td', attrs={'data-stat': 'shots_on_target_per90'}).text.strip(),
                        'goals_per_shot': row.find('td', attrs={'data-stat': 'goals_per_shot'}).text.strip(),
                        'average_shot_distance': row.find('td', attrs={'data-stat': 'average_shot_distance'}).text.strip()
                    })
            except Exception as e:
                print(f"Error processing shooting row: {e}")
                continue

    finally:
        driver.quit()

# -----------------------------------------
def update_passing_stats(player_set):
    """Update player data with passing statistics.
    Cập nhật dữ liệu cầu thủ với thống kê chuyền bóng."""
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.implicitly_wait(10)
    try:
        url = LINKS_URL_TO_CRAWL['Passing'][0]
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, LINKS_URL_TO_CRAWL['Passing'][1])))
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        table = soup.find('table', attrs={'id': LINKS_URL_TO_CRAWL['Passing'][1]})

        if not table:
            print("Error: Could not find the 'Passing' table.")
            return

        rows = table.find_all('tr', attrs={'data-row': True})

        for row in rows:
            try:
                name = row.find('td', attrs={'data-stat': 'player'}).text.strip()
                team = row.find('td', attrs={'data-stat': 'team'}).text.strip()
                player_key = str(name) + str(team)

                if player_key in player_set:
                    player_set[player_key].update({
                        'passes_completed': row.find('td', attrs={'data-stat': 'passes_completed'}).text.strip(),
                        'passes_pct': row.find('td', attrs={'data-stat': 'passes_pct'}).text.strip(),
                        'passes_total_distance': row.find('td', attrs={'data-stat': 'passes_total_distance'}).text.strip(),
                        'passes_pct_short': row.find('td', attrs={'data-stat': 'passes_pct_short'}).text.strip(),
                        'passes_pct_medium': row.find('td', attrs={'data-stat': 'passes_pct_medium'}).text.strip(),
                        'passes_pct_long': row.find('td', attrs={'data-stat': 'passes_pct_long'}).text.strip(),
                        'assisted_shots': row.find('td', attrs={'data-stat': 'assisted_shots'}).text.strip(),
                        'passes_into_final_third': row.find('td', attrs={'data-stat': 'passes_into_final_third'}).text.strip(),
                        'passes_into_penalty_area': row.find('td', attrs={'data-stat': 'passes_into_penalty_area'}).text.strip(),
                        'crosses_into_penalty_area': row.find('td', attrs={'data-stat': 'crosses_into_penalty_area'}).text.strip(),
                        'progressive_passes': row.find('td', attrs={'data-stat': 'progressive_passes'}).text.strip()
                    })
            except Exception as e:
                print(f"Error processing passing row: {e}")
                continue

    finally:
        driver.quit()

# -----------------------------------------
def update_goal_shot_creation_stats(player_set):
    """Update player data with goal and shot creation statistics.
    Cập nhật dữ liệu cầu thủ với thống kê tạo bàn và tạo cơ hội sút."""
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.implicitly_wait(10)
    try:
        url = LINKS_URL_TO_CRAWL['Goal and Shot Creation'][0]
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, LINKS_URL_TO_CRAWL['Goal and Shot Creation'][1])))
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        table = soup.find('table', attrs={'id': LINKS_URL_TO_CRAWL['Goal and Shot Creation'][1]})

        if not table:
            print("Error: Could not find the 'Goal and Shot Creation' table.")
            return

        rows = table.find_all('tr', attrs={'data-row': True})

        for row in rows:
            try:
                name = row.find('td', attrs={'data-stat': 'player'}).text.strip()
                team = row.find('td', attrs={'data-stat': 'team'}).text.strip()
                player_key = str(name) + str(team)

                if player_key in player_set:
                    player_set[player_key].update({
                        'sca': row.find('td', attrs={'data-stat': 'sca'}).text.strip(),
                        'sca_per90': row.find('td', attrs={'data-stat': 'sca_per90'}).text.strip(),
                        'gca': row.find('td', attrs={'data-stat': 'gca'}).text.strip(),
                        'gca_per90': row.find('td', attrs={'data-stat': 'gca_per90'}).text.strip()
                    })
            except Exception as e:
                print(f"Error processing goal and shot creation row: {e}")
                continue

    finally:
        driver.quit()

# -----------------------------------------
def update_defensive_stats(player_set):
    """Update player data with defensive actions statistics.
    Cập nhật dữ liệu cầu thủ với thống kê hành động phòng ngự."""
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.implicitly_wait(10)
    try:
        url = LINKS_URL_TO_CRAWL['Defense'][0]
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, LINKS_URL_TO_CRAWL['Defense'][1])))
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        table = soup.find('table', attrs={'id': LINKS_URL_TO_CRAWL['Defense'][1]})

        if not table:
            print("Error: Could not find the 'Defense' table.")
            return

        rows = table.find_all('tr', attrs={'data-row': True})

        for row in rows:
            try:
                name = row.find('td', attrs={'data-stat': 'player'}).text.strip()
                team = row.find('td', attrs={'data-stat': 'team'}).text.strip()
                player_key = str(name) + str(team)

                if player_key in player_set:
                    player_set[player_key].update({
                        'tackles': row.find('td', attrs={'data-stat': 'tackles'}).text.strip(),
                        'tackles_won': row.find('td', attrs={'data-stat': 'tackles_won'}).text.strip(),
                        'challenges': row.find('td', attrs={'data-stat': 'challenges'}).text.strip(),
                        'challenges_lost': row.find('td', attrs={'data-stat': 'challenges_lost'}).text.strip(),
                        'blocks': row.find('td', attrs={'data-stat': 'blocks'}).text.strip(),
                        'blocked_shots': row.find('td', attrs={'data-stat': 'blocked_shots'}).text.strip(),
                        'blocked_passes': row.find('td', attrs={'data-stat': 'blocked_passes'}).text.strip(),
                        'interceptions': row.find('td', attrs={'data-stat': 'interceptions'}).text.strip()
                    })
            except Exception as e:
                print(f"Error processing defensive actions row: {e}")
                continue

    finally:
        driver.quit()

# -----------------------------------------
def update_possession_stats(player_set):
    """Update player data with possession statistics.
    Cập nhật dữ liệu cầu thủ với thống kê kiểm soát bóng."""
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.implicitly_wait(10)
    try:
        url = LINKS_URL_TO_CRAWL['Possession'][0]
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, LINKS_URL_TO_CRAWL['Possession'][1])))
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        table = soup.find('table', attrs={'id': LINKS_URL_TO_CRAWL['Possession'][1]})

        if not table:
            print("Error: Could not find the 'Possession' table.")
            return

        rows = table.find_all('tr', attrs={'data-row': True})

        for row in rows:
            try:
                name = row.find('td', attrs={'data-stat': 'player'}).text.strip()
                team = row.find('td', attrs={'data-stat': 'team'}).text.strip()
                player_key = str(name) + str(team)

                if player_key in player_set:
                    player_set[player_key].update({
                        'touches': row.find('td', attrs={'data-stat': 'touches'}).text.strip(),
                        'touches_def_pen_area': row.find('td', attrs={'data-stat': 'touches_def_pen_area'}).text.strip(),
                        'touches_def_3rd': row.find('td', attrs={'data-stat': 'touches_def_3rd'}).text.strip(),
                        'touches_mid_3rd': row.find('td', attrs={'data-stat': 'touches_mid_3rd'}).text.strip(),
                        'touches_att_3rd': row.find('td', attrs={'data-stat': 'touches_att_3rd'}).text.strip(),
                        'touches_att_pen_area': row.find('td', attrs={'data-stat': 'touches_att_pen_area'}).text.strip(),
                        'take_ons': row.find('td', attrs={'data-stat': 'take_ons'}).text.strip(),
                        'take_ons_won_pct': row.find('td', attrs={'data-stat': 'take_ons_won_pct'}).text.strip(),
                        'take_ons_tackled_pct': row.find('td', attrs={'data-stat': 'take_ons_tackled_pct'}).text.strip(),
                        'carries': row.find('td', attrs={'data-stat': 'carries'}).text.strip(),
                        'carries_progressive_distance': row.find('td', attrs={'data-stat': 'carries_progressive_distance'}).text.strip(),
                        'carries_into_final_third': row.find('td', attrs={'data-stat': 'carries_into_final_third'}).text.strip(),
                        'carries_into_penalty_area': row.find('td', attrs={'data-stat': 'carries_into_penalty_area'}).text.strip(),
                        'miscontrols': row.find('td', attrs={'data-stat': 'miscontrols'}).text.strip(),
                        'dispossessed': row.find('td', attrs={'data-stat': 'dispossessed'}).text.strip(),
                        'passes_received': row.find('td', attrs={'data-stat': 'passes_received'}).text.strip()
                    })
            except Exception as e:
                print(f"Error processing possession row: {e}")
                continue

    finally:
        driver.quit()

# -----------------------------------------
def update_miscellaneous_stats(player_set):
    """Update player data with miscellaneous statistics.
    Cập nhật dữ liệu cầu thủ với thống kê linh tinh."""
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.implicitly_wait(10)
    try:
        url = LINKS_URL_TO_CRAWL['Miscellaneous'][0]
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, LINKS_URL_TO_CRAWL['Miscellaneous'][1])))
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        table = soup.find('table', attrs={'id': LINKS_URL_TO_CRAWL['Miscellaneous'][1]})

        if not table:
            print("Error: Could not find the 'Miscellaneous' table.")
            return

        rows = table.find_all('tr', attrs={'data-row': True})

        for row in rows:
            try:
                name = row.find('td', attrs={'data-stat': 'player'}).text.strip()
                team = row.find('td', attrs={'data-stat': 'team'}).text.strip()
                player_key = str(name) + str(team)

                if player_key in player_set:
                    player_set[player_key].update({
                        'fouls': row.find('td', attrs={'data-stat': 'fouls'}).text.strip(),
                        'fouled': row.find('td', attrs={'data-stat': 'fouled'}).text.strip(),
                        'offsides': row.find('td', attrs={'data-stat': 'offsides'}).text.strip(),
                        'crosses': row.find('td', attrs={'data-stat': 'crosses'}).text.strip(),
                        'ball_recoveries': row.find('td', attrs={'data-stat': 'ball_recoveries'}).text.strip(),
                        'aerials_won': row.find('td', attrs={'data-stat': 'aerials_won'}).text.strip(),
                        'aerials_lost': row.find('td', attrs={'data-stat': 'aerials_lost'}).text.strip(),
                        'aerials_won_pct': row.find('td', attrs={'data-stat': 'aerials_won_pct'}).text.strip()
                    })
            except Exception as e:
                print(f"Error processing miscellaneous row: {e}")
                continue

    finally:
        driver.quit()

# -----------------------------------------
def get_player_name(player_dict):
    """Extract player name from dictionary for sorting.
    Trích xuất tên cầu thủ từ từ điển để sắp xếp."""
    return player_dict.get('name', '')

# -----------------------------------------
def format_player_data(player_dict):
    """Format player data into a list for export in correct order.
    Định dạng dữ liệu cầu thủ thành danh sách để xuất theo thứ tự đúng."""
    export_order_keys = [
        'name', 'nationality', 'team', 'position', 'age', 'games', 'games_starts', 'minutes', 'goals', 'assist',
        'cards_yellow', 'cards_red', 'xg', 'xg_assist', 'progressive_carries', 'progressive_passes',
        'progressive_passes_received', 'goals_per90', 'assists_per90', 'xg_per90', 'xg_assist_per90',
        'gk_goals_against_per90', 'gk_save_pct', 'gk_clean_sheets_pct', 'gk_pens_save_pct', 'shots_on_target_pct',
        'shots_on_target_per90', 'goals_per_shot', 'average_shot_distance', 'passes_completed', 'passes_pct',
        'passes_total_distance', 'passes_pct_short', 'passes_pct_medium', 'passes_pct_long', 'assisted_shots',
        'passes_into_final_third', 'passes_into_penalty_area', 'crosses_into_penalty_area', 'sca', 'sca_per90',
        'gca', 'gca_per90', 'tackles', 'tackles_won', 'challenges', 'challenges_lost', 'blocks', 'blocked_shots',
        'blocked_passes', 'interceptions', 'touches', 'touches_def_pen_area', 'touches_def_3rd', 'touches_mid_3rd',
        'touches_att_3rd', 'touches_att_pen_area', 'take_ons', 'take_ons_won_pct', 'take_ons_tackled_pct', 'carries',
        'carries_progressive_distance', 'carries_into_final_third', 'carries_into_penalty_area', 'miscontrols',
        'dispossessed', 'passes_received', 'fouls', 'fouled', 'offsides', 'crosses', 'ball_recoveries', 'aerials_won',
        'aerials_lost', 'aerials_won_pct'
    ]

    nationality = player_dict.get('nationality', 'N/a')
    age = player_dict.get('age', 'N/a')
    nationality_processed = nationality.split()[1] if ' ' in nationality else nationality
    age_processed = age.split('-')[0] if '-' in age else age

    exported_list = []
    for key in export_order_keys:
        if key == 'nationality':
            exported_list.append(nationality_processed)
        elif key == 'age':
            exported_list.append(age_processed)
        else:
            exported_list.append(player_dict.get(key, 'N/a'))

    return exported_list

# -----------------------------------------
import sqlite3
import pandas as pd

def export_to_csv_and_db(player_set_dict, db_path='premier_league_stats.db'):
    """Export player data to CSV and update all player info into SQLite DB."""

    playerlist = list(player_set_dict.values())
    playerlist.sort(key=get_player_name)
    result = [format_player_data(player_dict) for player_dict in playerlist]

    # Các tên cột đầy đủ (75 cột)
    export_order_keys = [
        'name', 'nationality', 'team', 'position', 'age', 'games', 'games_starts', 'minutes', 'goals', 'assist',
        'cards_yellow', 'cards_red', 'xg', 'xg_assist', 'progressive_carries', 'progressive_passes',
        'progressive_passes_received', 'goals_per90', 'assists_per90', 'xg_per90', 'xg_assist_per90',
        'gk_goals_against_per90', 'gk_save_pct', 'gk_clean_sheets_pct', 'gk_pens_save_pct', 'shots_on_target_pct',
        'shots_on_target_per90', 'goals_per_shot', 'average_shot_distance', 'passes_completed', 'passes_pct',
        'passes_total_distance', 'passes_pct_short', 'passes_pct_medium', 'passes_pct_long', 'assisted_shots',
        'passes_into_final_third', 'passes_into_penalty_area', 'crosses_into_penalty_area', 'sca', 'sca_per90',
        'gca', 'gca_per90', 'tackles', 'tackles_won', 'challenges', 'challenges_lost', 'blocks', 'blocked_shots',
        'blocked_passes', 'interceptions', 'touches', 'touches_def_pen_area', 'touches_def_3rd', 'touches_mid_3rd',
        'touches_att_3rd', 'touches_att_pen_area', 'take_ons', 'take_ons_won_pct', 'take_ons_tackled_pct', 'carries',
        'carries_progressive_distance', 'carries_into_final_third', 'carries_into_penalty_area', 'miscontrols',
        'dispossessed', 'passes_received', 'fouls', 'fouled', 'offsides', 'crosses', 'ball_recoveries', 'aerials_won',
        'aerials_lost', 'aerials_won_pct'
    ]

    column_names = [  # Tên cột cho CSV, bạn có thể giữ nguyên như cũ hoặc rút gọn
        'Name', 'Nation', 'Team', 'Position', 'Age', 'Matches Played', 'Starts', 'Minutes', 'Goals', 'Assists',
        'Yellow Cards', 'Red Cards', 'Expected Goals (xG)', 'Expected Assist Goals (xAG)', 'Progressive Carries (PrgC)',
        'Progressive Passes (PrgP)', 'Progressive Passes Received (PrgR)', 'Goals per 90', 'Assists per 90',
        'xG per 90', 'xAG per 90', 'Goals Against per 90 (GA90)', 'Save Percentage (Save%)', 'Clean Sheets Percentage (CS%)',
        'Penalty Kicks Save Percentage', 'Shots on Target Percentage (SoT%)', 'Shots on Target per 90 (SoT/90)',
        'Goals per Shot (G/Sh)', 'Average Shot Distance (Dist)', 'Passes Completed (Cmp)', 'Pass Completion Percentage (Cmp%)',
        'Total Passing Distance (TotDist)', 'Short Pass Completion Percentage', 'Medium Pass Completion Percentage',
        'Long Pass Completion Percentage', 'Key Passes (KP)', 'Passes into Final Third (1/3)', 'Passes into Penalty Area (PPA)',
        'Crosses into Penalty Area (CrsPA)', 'Shot-Creating Actions (SCA)', 'SCA per 90', 'Goal-Creating Actions (GCA)',
        'GCA per 90', 'Tackles (Tkl)', 'Tackles Won (TklW)', 'Challenges (Tkl)', 'Challenges Lost (TklD)', 'Blocks',
        'Blocked Shots (Sh)', 'Blocked Passes (Pass)', 'Interceptions (Int)', 'Touches', 'Touches in Defensive Penalty Area',
        'Touches in Defensive Third', 'Touches in Middle Third', 'Touches in Attacking Third', 'Touches in Attacking Penalty Area',
        'Take-Ons (Att)', 'Take-On Success Percentage (Succ%)', 'Take-On Tackled Percentage (Tkl%)', 'Carries',
        'Progressive Carrying Distance (TotDist)', 'Carries into Final Third (1/3)', 'Carries into Penalty Area (CPA)',
        'Miscontrols (Mis)', 'Dispossessed (Dis)', 'Passes Received (Rec)', 'Fouls Committed (Fls)', 'Fouls Drawn (Fld)',
        'Offsides (Off)', 'Crosses (Crs)', 'Ball Recoveries (Recov)', 'Aerials Won (Won)', 'Aerials Lost (Lost)',
        'Aerials Won Percentage (Won%)'
    ]

    # 1. Xuất CSV
    df = pd.DataFrame(result, columns=column_names)
    df.to_csv("premier_league_player_stats.csv", index=False, encoding='utf-8')
    print("✅ Data exported to CSV.")

    # 2. Lưu vào SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 3. Tạo bảng đầy đủ nếu chưa có
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        {', '.join([f"{col} TEXT" for col in export_order_keys])}
    );
    """
    cursor.execute(create_table_sql)

    # 4. Xóa dữ liệu cũ nếu cần
    cursor.execute("DELETE FROM players")

    # 5. Chèn toàn bộ dữ liệu
    insert_sql = f"""
    INSERT INTO players ({', '.join(export_order_keys)})
    VALUES ({', '.join(['?'] * len(export_order_keys))})
    """
    cursor.executemany(insert_sql, result)
    conn.commit()
    conn.close()
    print(f"✅ Dữ liệu đầy đủ đã được lưu vào bảng 'players' trong {db_path}")

# -----------------------------------------
#------------------------------------------
#Export ra sqlite


# ------------------------ 1. Khởi tạo trình duyệt -------------------------
def initialize_browser():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    browser = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    browser.implicitly_wait(10)
    return browser
# ------------------------ 3. Tạo bảng chuyển nhượng -------------------------
def create_transfer_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS player_transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player TEXT NOT NULL,
            club TEXT,
            market_value TEXT,
            rating TEXT
        )
    """)
    conn.commit()

# ------------------------ 4. Chèn dữ liệu vào bảng -------------------------
def insert_transfer_data(conn, data_list):
    sql = """
        INSERT INTO player_transfers (player, club, market_value, rating)
        VALUES (?, ?, ?, ?)
    """
    for row in data_list:
        conn.execute(sql, (row['player'], row['club'], row['market_value'], row['rating']))
    conn.commit()

# ------------------------ 5. Lấy toàn bộ tên cầu thủ từ DB -------------------------
def get_all_players_from_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, team FROM players")
    players = cursor.fetchall()
    print(f"🔍 Số cầu thủ đọc từ DB: {len(players)}")  # kiểm tra lại số lượng
    conn.close()
    return [{'name': name, 'team': team} for name, team in players]


def extract_page_data(browser, page_url):
    """Lấy danh sách cầu thủ từ 1 trang Premier League"""
    try:
        browser.get(page_url)
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'table.table-striped.leaguetable'))
        )
        html_content = browser.page_source
        soup = BeautifulSoup(html_content, 'lxml')

        table = soup.select_one('table.table.table-striped.leaguetable')
        if not table:
            return []

        rows = table.select('tbody tr')
        extracted_data = []

        for row in rows:
            try:
                name_elem = row.select_one('a[href*="/players/"]')
                team_elem = row.select_one('span.td-team__teamname')
                value_elem = row.select_one('span.player-tag')
                skill_elem = row.select_one('div.table-skill__skill')
                pot_elem = row.select_one('div.table-skill__pot')

                player_name = name_elem.get_text(strip=True) if name_elem else None
                player_link = name_elem['href'] if name_elem and name_elem.has_attr('href') else None
                club = team_elem.get_text(strip=True) if team_elem else None
                value = value_elem.get_text(strip=True) if value_elem else "N/A"

                def extract_num(text):
                    match = re.search(r'(\d+(\.\d+)?)', text)
                    return float(match.group(1)) if match else None

                skill = extract_num(skill_elem.get_text(strip=True)) if skill_elem else None
                pot = extract_num(pot_elem.get_text(strip=True)) if pot_elem else None
                rating = f"{skill}/{pot}" if skill and pot else "N/A"

                if player_name:
                    extracted_data.append({
                        "player": player_name.strip(),
                        "club": club,
                        "market_value": value,
                        "rating": rating,
                        "link": player_link
                    })
            except Exception as e:
                print(f"⚠️ Lỗi đọc hàng: {e}")
                continue

        return extracted_data

    except Exception as e:
        print(f"❌ Lỗi khi xử lý {page_url}: {e}")
        return []


# ------------------------------
# 🔹 CẬP NHẬT DỮ LIỆU VÀO DATABASE
# ------------------------------
def update_transfer_values_to_db(db_path='premier_league_stats.db'):
    all_players_raw = get_all_players_from_db(db_path)

    name_map = {}
    found_map = {}

    for player in all_players_raw:
        key = player['name'].strip().lower()
        name_map[key] = player
        found_map[key] = False

    print(f"🔍 Tổng số cầu thủ trong DB: {len(name_map)}")

    collected = []
    browser = initialize_browser()
    base_url = "https://www.footballtransfers.com/en/players/uk-premier-league"

    try:
        # ---- 1️⃣ Crawl 22 trang Premier League ----
        for page in range(1, 23):
            page_url = base_url if page == 1 else f"{base_url}/{page}"
            print(f"🌍 Crawling page {page}...")
            data = extract_page_data(browser, page_url)

            for player in data:
                name_lower = player['player'].strip().lower()

                if name_lower in name_map and not found_map[name_lower]:
                    found_map[name_lower] = True
                    original = name_map[name_lower]
                    collected.append({
                        'player': original['name'],
                        'club': original['team'],
                        'market_value': player.get('market_value', 'N/A'),
                        'rating': player.get('rating', 'N/A')
                    })
            time.sleep(1)

        # ---- 2️⃣ Cầu thủ không tìm thấy -> crawl từ trang cá nhân ----
        not_found_count = 0
        for key, was_found in found_map.items():
            if not was_found:
                not_found_count += 1
                p = name_map[key]
                slug = slugify_name(p['name'])
                player_url = f"https://www.footballtransfers.com/en/players/{slug}"
                print(f"🔎 Tìm thêm: {p['name']} → {player_url}")

                extra_data = extract_player_page_data(browser, player_url)
                collected.append({
                    'player': p['name'],
                    'club': p['team'],
                    'market_value': extra_data['market_value'],
                    'rating': extra_data['rating']
                })
                time.sleep(1)

        print(f"⚠️ Cầu thủ không có trong 22 trang: {not_found_count}")

    finally:
        browser.quit()

    # ✅ Ghi vào SQLite
    conn = sqlite3.connect(db_path)
    create_transfer_table(conn)
    insert_transfer_data(conn, collected)
    conn.close()

    print(f"✅ Đã lưu {len(collected)} cầu thủ vào bảng 'player_transfers' trong {db_path}")

# ------------------------ 7. Chạy hàm chính -------------------------

# Chạy thử

#------------------------------------------
def main():
    """Main function to orchestrate the scraping and exporting process.
    Hàm chính để điều phối quá trình thu thập và xuất dữ liệu."""
    print("Starting data scraping...")
    player_set = scrape_standard_stats()
    if not player_set:
        print("No player data collected. Exiting.")
        return

    print("Updating player data with additional stats...")
    update_goalkeeping_stats(player_set)
    update_shooting_stats(player_set)
    update_passing_stats(player_set)
    update_goal_shot_creation_stats(player_set)
    update_defensive_stats(player_set)
    update_possession_stats(player_set)
    update_miscellaneous_stats(player_set)

    print("Exporting data to CSV...")
    export_to_csv_and_db(player_set)
    # export_to_sqlite(player_set)
    print("💰 Thu thập và lưu giá trị chuyển nhượng...")
    update_transfer_values_to_db("premier_league_stats.db")

# -----------------------------------------
if __name__ == "__main__":
    main()