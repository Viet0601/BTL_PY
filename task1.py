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
import re
import unicodedata
EXCEPTIONS_SLUG = {
    "Jota Silva":"joao-pedro-ferreira-silva",
    "Diego Gómez":"diego-gomez-19",
    "Marc Cucurella":"marc-cucurella-saseta",
    "Nathan Wood-Gordon":"nathan-wood",
    "Ezri Konsa":"ezri-konsa-ngoyo",
    "Gabriel Martinelli":"gabriel-martinelli-1",
    "Idrissa Gana Gueye":"idrissa-gueye",
    "Joelinton":"joelinton-cassio-joelinton",
    "Ben White":"ben-white-1",
    "Antonee Robinson":"antonee-robinson-1",
    "Romain Esse":"romain-esse-1",
    "Solly March":"solomon-march",
    "Kyle Walker-Peters":"kyle-walkerpeters",
    "Hákon Valdimarsson":"hakon-rafn-valdimarsson",
    "Solly March":"solomon-march",
    "Albert Grønbaek": "albert-gronbak",
    "Antony": "antony-matheus-dos-santos",
    "Armel Bella Kotchap": "armel-bellakotchup",
    "Ben Johnson":"benjamin-johnson",
    "Bilal El Khannouss":"bilal-el-khannous",
    "Bobby De Cordova-Reid":"bobby-decordovareid",
    "Caleb Okoli":"memeh-caleb-okoli",
    "Danny Ings":"daniel-william-john-ings",
    "Darwin Núñez":"darwin-gabriel-nunez-ribeiro",
    "Edmond-Paris Maghoma":"edmondparis-maghoma",
    "Emi Buendía":"emiliano-buendia",
    "Fabio Carvalho":"fabio-carvalho-3",
    "Ferdi Kadioglu":"ferdi-erenay-kadioglu",
    "Harry Clarke":"harrison-clarke",
    "Hwang Hee-chan":"heechan-hwang",
    "Jack Clarke":"jack-clarke-1",
    "Jack Taylor":"jack-taylor-1",
    "Jaden Philogene Bidace":"jaden-philogenebidace",
    "Jahmai Simpson-Pusey":"jahmai-simpsonpusey",
    "Jakub Kiwior":"jakub-piotr-kiwior",
    "Jens Cajuste":"jenslys-michel-cajuste",
"Jesper Lindstrøm":"jesper-grange-lindstrom",
"Joe Aribo":"joseph-oluwaseyi-temitope-ayodelearibo",
"Julian Araujo":"julian-vincente-araujo",
"Julio Enciso":"julio-cesar-enciso",
"Jáder Durán":"jhon-jader-duran-palacio",
"Jørgen Strand Larsen":"jorgen-strand-strand-larsen",
"Kamaldeen Sulemana":"kamal-deen-sulemana",
"Kostas Tsimikas":"konstantinos-tsimikas",
"Luis Díaz":"luis-fernando-diaz-marulanda",
"Mads Roerslev":"mads-roerslev-rasmussen",
"Manuel Akanji":"manuel-obafemi-akanji",
"Matt O'Riley":"matthew-oriley",
"Max Kilman":"maximilian-kilman",
"Miguel Almirón":"miguel-angel-almiron-rejala",
"Mykhailo Mudryk":"mykhaylo-mudryk",
"Nicolas Jackson":"nicolas-jackson-1",
"Nélson Semedo":"nelsinho-1",
"Pervis Estupiñán":"pervis-josue-estupinan-tenorio",
"Ramón Sosa":"ramon-sosa-acosta",
"Rasmus Højlund":"rasmus-winther-hojlund",
"Renato Veiga":"renato-palma-veiga",
"Ricardo Pereira":"ricardo-pereira-1",

"Sam Morsy":"samy-morsy",
"Sammie Szmodics":"samuel-szmodics",
"Son Heung-min":"heungmin-son",
"Tommy Doyle":"thomas-doyle-1",
"Toti Gomes":"toti-antonio-gomes",
"Trent Alexander-Arnold":"trent-alexanderarnold",
"Victor Bernth Kristiansen":"victor-kristiansen",
"Welington":"welington-damascena",
"William Smallbone":"william-anthony-patrick-smallbone",
"Yehor Yarmoliuk":"yegor-yarmolyuk"

    # ... thêm các trường hợp đặc biệt khác
}
def slugify_name(name: str) -> str:
    import re, unicodedata

    name = name.strip().lower()
    replacements = {
        'ø': 'o', 'œ': 'oe', 'æ': 'ae', 'å': 'a', 'ä': 'a',
        'á':'a','à':'a','â':'a','ã':'a','č':'c','ć':'c','ç':'c',
        'é':'e','è':'e','ê':'e','ë':'e',
        'í':'i','ì':'i','î':'i','ï':'i',
        'ñ':'n','ó':'o','ò':'o','ô':'o','õ':'o','ö':'o',
        'ú':'u','ù':'u','û':'u','ü':'u','ß':'ss','š':'s','ž':'z','ý':'y','ÿ':'y'
    }
    for src, target in replacements.items():
        name = name.replace(src, target)
    name = unicodedata.normalize('NFD', name)
    name = name.encode('ascii','ignore').decode('utf-8')
    name = re.sub(r'[\s_]+','-',name)
    name = re.sub(r'[^a-z0-9\-]','',name)
    return name.strip('-')


def get_player_slug(name: str) -> str:
    # Nếu có ngoại lệ, dùng slug thủ công
    if name in EXCEPTIONS_SLUG:
        return EXCEPTIONS_SLUG[name]
    # Nếu không, dùng hàm chuẩn
    return slugify_name(name)
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
    'Goalkeeping': ('https://fbref.com/en/comps/9/2024-2025/keepers/2024-2025-Premier-League-Stats', 'stats_keeper'),
    'Advanced Goalkeeping': ('https://fbref.com/en/comps/9/2024-2025/keepersadv/2024-2025-Premier-League-Stats', 'stats_keeper_adv'),
    'Passing Type': ('https://fbref.com/en/comps/9/2024-2025/passing_types/2024-2025-Premier-League-Stats', 'stats_passing_types'),
    'Playing Time': ('https://fbref.com/en/comps/9/2024-2025/playingtime/2024-2025-Premier-League-Stats', 'stats_playing_time')
}
PLAYER_KEY_TO_CRAWL = [
    
    'name', 'nationality', 'position', 'team', 'age','born', 'games', 'games_starts',
    'minutes','minutes_90s', 'goals', 'assist','goals_assists','goals_pens','pens_made','pens_att' ,'cards_yellow', 'cards_red', 'xg',
    'npxg', 'xg_assist','npxg_xg_assist',
    'progressive_carries', 'progressive_passes', 'progressive_passes_received', 'goals_per90',
    'assists_per90','goals_assists_per90','goals_pens_per90','goals_assists_pens_per90', 'xg_per90', 'xg_assist_per90',
    'xg_xg_assist_per90','npxg_per90','npxg_xg_assist_per90',

    'minutes_per_game','minutes_pct','minutes_per_start','games_complete','games_subs','minutes_per_sub','unused_subs',
    'points_per_game','on_goals_for','on_goals_against','plus_minus','plus_minus_per90','plus_minus_wowy','on_xg_for',
    'on_xg_against','xg_plus_minus','xg_plus_minus_per90','xg_plus_minus_wowy',


    'gk_goals_against','gk_goals_against_per90','gk_shots_on_target_against','gk_saves', 'gk_save_pct','gk_wins',
    'gk_ties','gk_losses','gk_clean_sheets',''
    'gk_clean_sheets_pct','gk_pens_att','gk_pens_allowed','gk_pens_saved','gk_pens_missed', 'gk_pens_save_pct',

    'gk_free_kick_goals_against','gk_corner_kick_goals_against','gk_own_goals_against','gk_psxg',
    'gk_psnpxg_per_shot_on_target_against','gk_psxg_net','gk_psxg_net_per90','gk_passes_completed_launched',
    'gk_passes_launched','gk_passes_pct_launched','gk_passes','gk_passes_throws','gk_pct_passes_launched','gk_passes_length_avg',
    'gk_goal_kicks','gk_pct_goal_kicks_launched','gk_goal_kick_length_avg','gk_crosses','gk_crosses_stopped','gk_crosses_stopped_pct',
    'gk_def_actions_outside_pen_area','gk_def_actions_outside_pen_area_per90','gk_avg_distance_def_actions',
     
    'shots','shots_on_target','shots_on_target_pct','shots_per90', 'shots_on_target_per90',
    'goals_per_shot','goals_per_shot_on_target', 'average_shot_distance','shots_free_kicks','npxg_per_shot','xg_net','npxg_net',
 
    'passes_completed','passes', 'passes_pct', 'passes_total_distance','passes_progressive_distance','passes_completed_short',
    'passes_short','passes_pct_short','passes_completed_medium','passes_medium', 'passes_pct_medium','passes_completed_long',
    'passes_long','passes_pct_long','pass_xa','xg_assist_net', 'assisted_shots',
    'passes_into_final_third', 'passes_into_penalty_area', 'crosses_into_penalty_area',

    'passes_live','passes_dead','passes_free_kicks','through_balls','passes_switches','throw_ins','corner_kicks','corner_kicks_in',
    'corner_kicks_out','corner_kicks_straight','passes_offsides','passes_blocked',

    'sca', 'sca_per90','sca_passes_live','sca_passes_dead','sca_take_ons','sca_shots','sca_fouled','sca_defense', 'gca', 
    'gca_per90', 'gca_passes_live','gca_passes_dead','gca_take_ons','gca_shots','gca_fouled','gca_defense',
    
    'tackles', 'tackles_won','tackles_def_3rd','tackles_mid_3rd','tackles_att_3rd','challenge_tackles', 'challenges',
    'challenge_tackles_pct','challenges_lost', 'blocks', 'blocked_shots', 'blocked_passes', 'interceptions',
    'tackles_interceptions','clearances','errors',
    
    
    
    'touches','touches_def_pen_area', 'touches_def_3rd', 'touches_mid_3rd', 'touches_att_3rd',
    'touches_att_pen_area','touches_live_ball', 'take_ons','take_ons_won', 'take_ons_won_pct','take_ons_tackled',
    'take_ons_tackled_pct', 'carries','carries_distance',
    'carries_progressive_distance','carries_into_final_third',
    'carries_into_penalty_area', 'miscontrols',
    'dispossessed', 'passes_received',
    
    'fouls', 'fouled', 'offsides', 'crosses','pens_won','pens_conceded','own_goals',
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
                birth_year = row.find('td', attrs={'data-stat': 'birth_year'}).text.strip()
                games = row.find('td', attrs={'data-stat': 'games'}).text.strip()
                games_starts = row.find('td', attrs={'data-stat': 'games_starts'}).text.strip()
                minutes_str = row.find('td', attrs={'data-stat': 'minutes'}).text.strip()
                minutes_90s = row.find('td', attrs={'data-stat': 'minutes_90s'}).text.strip()
                goals = row.find('td', attrs={'data-stat': 'goals'}).text.strip()
                assist = row.find('td', attrs={'data-stat': 'assists'}).text.strip()
                goals_assists = row.find('td', attrs={'data-stat': 'goals_assists'}).text.strip()
                goals_pens = row.find('td', attrs={'data-stat': 'goals_pens'}).text.strip()
                pens_made = row.find('td', attrs={'data-stat': 'pens_made'}).text.strip()
                pens_att = row.find('td', attrs={'data-stat': 'pens_att'}).text.strip()
                cards_yellow = row.find('td', attrs={'data-stat': 'cards_yellow'}).text.strip()
                cards_red = row.find('td', attrs={'data-stat': 'cards_red'}).text.strip()
                xg = row.find('td', attrs={'data-stat': 'xg'}).text.strip()
                npxg = row.find('td', attrs={'data-stat': 'npxg'}).text.strip()
                npxg_xg_assist = row.find('td', attrs={'data-stat': 'npxg_xg_assist'}).text.strip()
                goals_assists_per90 = row.find('td', attrs={'data-stat': 'goals_assists_per90'}).text.strip()
                goals_pens_per90 = row.find('td', attrs={'data-stat': 'goals_pens_per90'}).text.strip()
                goals_assists_pens_per90 = row.find('td', attrs={'data-stat': 'goals_assists_pens_per90'}).text.strip()
                xg_xg_assist_per90 = row.find('td', attrs={'data-stat': 'xg_xg_assist_per90'}).text.strip()
                npxg_per90 = row.find('td', attrs={'data-stat': 'npxg_per90'}).text.strip()
                npxg_xg_assist_per90 = row.find('td', attrs={'data-stat': 'npxg_xg_assist_per90'}).text.strip()
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
                    'npxg':npxg,
                    'npxg_per90':npxg_per90,
                    'npxg_xg_assist':npxg_xg_assist,
                    'goals_assists':goals_assists,
                    'goals_assists_pens_per90':goals_assists_pens_per90,
                    'goals_assists_per90':goals_assists_per90,
                    'npxg_xg_assist_per90':npxg_xg_assist_per90,
                    'goals_pens_per90':goals_pens_per90,
                    'xg_xg_assist_per90':xg_xg_assist_per90,
                    'name': name,
                    'nationality': nationality,
                    'position': position,
                    'team': team,
                    'age': age,
                    'born': birth_year,
                    'games': games,
                    'games_starts': games_starts,
                    'minutes': minutes_str,
                    'minutes_90s': minutes_90s,
                    'goals': goals,
                    'pens_made':pens_made,
                    'pens_att':pens_att,
                    'assist': assist,
                    'goals_assists': goals_assists,
                    'goals_pens': goals_pens,
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
                        'gk_pens_save_pct': row.find('td', attrs={'data-stat': 'gk_pens_save_pct'}).text.strip(),

                        'gk_goals_against':row.find('td', attrs={'data-stat': 'gk_goals_against'}).text.strip(),
                        'gk_shots_on_target_against':row.find('td', attrs={'data-stat': 'gk_shots_on_target_against'}).text.strip(),
                        'gk_saves':row.find('td', attrs={'data-stat': 'gk_saves'}).text.strip(),
                        'gk_wins':row.find('td', attrs={'data-stat': 'gk_wins'}).text.strip(),
                         'gk_ties':row.find('td', attrs={'data-stat': 'gk_ties'}).text.strip(),
                         'gk_losses':row.find('td', attrs={'data-stat': 'gk_losses'}).text.strip(),
                         'gk_clean_sheets':row.find('td', attrs={'data-stat': 'gk_clean_sheets'}).text.strip(),
                        'gk_pens_att':row.find('td', attrs={'data-stat': 'gk_pens_att'}).text.strip(),
                        'gk_pens_allowed':row.find('td', attrs={'data-stat': 'gk_pens_allowed'}).text.strip(),
                        'gk_pens_saved':row.find('td', attrs={'data-stat': 'gk_pens_saved'}).text.strip(),
                        'gk_pens_missed':row.find('td', attrs={'data-stat': 'gk_pens_missed'}).text.strip()
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
                        'shots':row.find('td', attrs={'data-stat': 'shots'}).text.strip(),
                        'shots_on_target':row.find('td', attrs={'data-stat': 'shots_on_target'}).text.strip(),
                        'shots_per90':row.find('td', attrs={'data-stat': 'shots_per90'}).text.strip(),
                        'goals_per_shot_on_target':row.find('td', attrs={'data-stat': 'goals_per_shot_on_target'}).text.strip(), 
                        'average_shot_distance':row.find('td', attrs={'data-stat': 'average_shot_distance'}).text.strip(),
                        'shots_free_kicks':row.find('td', attrs={'data-stat': 'shots_free_kicks'}).text.strip(),
                        'npxg_per_shot':row.find('td', attrs={'data-stat': 'npxg_per_shot'}).text.strip(),
                        'xg_net':row.find('td', attrs={'data-stat': 'xg_net'}).text.strip(),
                        'npxg_net':row.find('td', attrs={'data-stat': 'npxg_net'}).text.strip(),
                        'shots_on_target_pct': row.find('td', attrs={'data-stat': 'shots_on_target_pct'}).text.strip(),
                        'shots_on_target_per90': row.find('td', attrs={'data-stat': 'shots_on_target_per90'}).text.strip(),
                        'goals_per_shot': row.find('td', attrs={'data-stat': 'goals_per_shot'}).text.strip(),
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
                        'passes':row.find('td', attrs={'data-stat': 'passes'}).text.strip(),
                        'passes_progressive_distance':row.find('td', attrs={'data-stat': 'passes_progressive_distance'}).text.strip(),
                        'passes_completed_short':row.find('td', attrs={'data-stat': 'passes_completed_short'}).text.strip(),
                        'passes_short':row.find('td', attrs={'data-stat': 'passes_short'}).text.strip(),
                        'passes_completed_medium':row.find('td', attrs={'data-stat': 'passes_completed_medium'}).text.strip(),
                        'passes_medium':row.find('td', attrs={'data-stat': 'passes_medium'}).text.strip(),
                        'passes_completed_long':row.find('td', attrs={'data-stat': 'passes_completed_long'}).text.strip(),
                        'passes_long':row.find('td', attrs={'data-stat': 'passes_long'}).text.strip(),
                        'pass_xa':row.find('td', attrs={'data-stat': 'pass_xa'}).text.strip(),
                        'xg_assist_net':row.find('td', attrs={'data-stat': 'xg_assist_net'}).text.strip(),
   

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
                        'sca_passes_live':row.find('td', attrs={'data-stat': 'sca_passes_live'}).text.strip(),
                        'sca_passes_dead':row.find('td', attrs={'data-stat': 'sca_passes_dead'}).text.strip(),
                        'sca_take_ons':row.find('td', attrs={'data-stat': 'sca_take_ons'}).text.strip(),
                        'sca_shots':row.find('td', attrs={'data-stat': 'sca_shots'}).text.strip(),
                        'sca_fouled':row.find('td', attrs={'data-stat': 'sca_fouled'}).text.strip(),
                        'sca_defense':row.find('td', attrs={'data-stat': 'sca_defense'}).text.strip(),
                        'gca_passes_live':row.find('td', attrs={'data-stat': 'gca_passes_live'}).text.strip(),
                        'gca_passes_dead':row.find('td', attrs={'data-stat': 'gca_passes_dead'}).text.strip(),
                        'gca_take_ons':row.find('td', attrs={'data-stat': 'gca_take_ons'}).text.strip(),
                        'gca_shots':row.find('td', attrs={'data-stat': 'gca_shots'}).text.strip(),
                        'gca_fouled':row.find('td', attrs={'data-stat': 'gca_fouled'}).text.strip(),
                        'gca_defense':row.find('td', attrs={'data-stat': 'gca_defense'}).text.strip(),
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
                        'tackles_def_3rd':row.find('td', attrs={'data-stat': 'tackles_def_3rd'}).text.strip(),
                        'tackles_mid_3rd':row.find('td', attrs={'data-stat': 'tackles_mid_3rd'}).text.strip(),
                        'tackles_att_3rd':row.find('td', attrs={'data-stat': 'tackles_att_3rd'}).text.strip(),
                        'challenge_tackles':row.find('td', attrs={'data-stat': 'challenge_tackles'}).text.strip(),
                        'challenge_tackles_pct':row.find('td', attrs={'data-stat': 'challenge_tackles_pct'}).text.strip(),
                        'tackles_interceptions':row.find('td', attrs={'data-stat': 'tackles_interceptions'}).text.strip(),
                        'clearances':row.find('td', attrs={'data-stat': 'clearances'}).text.strip(),
                        'errors':row.find('td', attrs={'data-stat': 'errors'}).text.strip(),

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
                        'passes_received': row.find('td', attrs={'data-stat': 'passes_received'}).text.strip(),
                        'touches_live_ball':row.find('td', attrs={'data-stat': 'touches_live_ball'}).text.strip(),
                        'take_ons_won':row.find('td', attrs={'data-stat': 'take_ons_won'}).text.strip(),
                        'take_ons_tackled':row.find('td', attrs={'data-stat': 'take_ons_tackled'}).text.strip(),
                        'carries_distance':row.find('td', attrs={'data-stat': 'carries_distance'}).text.strip(),
                        'progressive_passes_received':row.find('td', attrs={'data-stat': 'progressive_passes_received'}).text.strip()
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
                        'aerials_won_pct': row.find('td', attrs={'data-stat': 'aerials_won_pct'}).text.strip(),
                        'pens_won':row.find('td', attrs={'data-stat': 'pens_won'}).text.strip(),
                        'pens_conceded':row.find('td', attrs={'data-stat': 'pens_conceded'}).text.strip(),
                        'own_goals':row.find('td', attrs={'data-stat': 'own_goals'}).text.strip()
                    })
            except Exception as e:
                print(f"Error processing miscellaneous row: {e}")
                continue

    finally:
        driver.quit()
def update_playing_time_stats(player_set):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.implicitly_wait(10)
    try:
        url = LINKS_URL_TO_CRAWL['Playing Time'][0]
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, LINKS_URL_TO_CRAWL['Playing Time'][1])))
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        table = soup.find('table', attrs={'id': LINKS_URL_TO_CRAWL['Playing Time'][1]})

        if not table:
            print("Error: Could not find the 'Playing Time' table.")
            return

        rows = table.find_all('tr', attrs={'data-row': True})

        for row in rows:
            try:
                name = row.find('td', attrs={'data-stat': 'player'}).text.strip()
                team = row.find('td', attrs={'data-stat': 'team'}).text.strip()
                player_key = str(name) + str(team)

                if player_key in player_set:
                    player_set[player_key].update({
                        'minutes_per_game':row.find('td', attrs={'data-stat': 'minutes_per_game'}).text.strip(),
                        'minutes_pct':row.find('td', attrs={'data-stat': 'minutes_pct'}).text.strip(),
                        'minutes_per_start':row.find('td', attrs={'data-stat': 'minutes_per_start'}).text.strip(),
                        'games_complete':row.find('td', attrs={'data-stat': 'games_complete'}).text.strip(),
                        'games_subs':row.find('td', attrs={'data-stat': 'games_subs'}).text.strip(),
                        'minutes_per_sub':row.find('td', attrs={'data-stat': 'minutes_per_sub'}).text.strip(),
                        'unused_subs':row.find('td', attrs={'data-stat': 'unused_subs'}).text.strip(),
                        'points_per_game':row.find('td', attrs={'data-stat': 'points_per_game'}).text.strip(),
                        'on_goals_for':row.find('td', attrs={'data-stat': 'on_goals_for'}).text.strip(),
                        'on_goals_against':row.find('td', attrs={'data-stat': 'on_goals_against'}).text.strip(),
                        'plus_minus':row.find('td', attrs={'data-stat': 'plus_minus'}).text.strip(),
                        'plus_minus_per90':row.find('td', attrs={'data-stat': 'plus_minus_per90'}).text.strip(),
                        'plus_minus_wowy':row.find('td', attrs={'data-stat': 'plus_minus_wowy'}).text.strip(),
                        'on_xg_for':row.find('td', attrs={'data-stat': 'on_xg_for'}).text.strip(),
                        'on_xg_against':row.find('td', attrs={'data-stat': 'on_xg_against'}).text.strip(),
                        'xg_plus_minus':row.find('td', attrs={'data-stat': 'xg_plus_minus'}).text.strip(),
                        'xg_plus_minus_per90':row.find('td', attrs={'data-stat': 'xg_plus_minus_per90'}).text.strip(),
                        'xg_plus_minus_wowy':row.find('td', attrs={'data-stat': 'xg_plus_minus_wowy'}).text.strip()
                    })
            except Exception as e:
                print(f"Error processing playing time row: {e}")
                continue

    finally:
        driver.quit()
def update_passing_type_stats(player_set):
 
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.implicitly_wait(10)
    try:
        url = LINKS_URL_TO_CRAWL['Passing Type'][0]
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, LINKS_URL_TO_CRAWL['Passing Type'][1])))
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        table = soup.find('table', attrs={'id': LINKS_URL_TO_CRAWL['Passing Type'][1]})

        if not table:
            print("Error: Could not find the 'Passing Type' table.")
            return

        rows = table.find_all('tr', attrs={'data-row': True})

        for row in rows:
            try:
                name = row.find('td', attrs={'data-stat': 'player'}).text.strip()
                team = row.find('td', attrs={'data-stat': 'team'}).text.strip()
                player_key = str(name) + str(team)

                if player_key in player_set:
                    player_set[player_key].update({
                        'passes_live':row.find('td', attrs={'data-stat': 'passes_live'}).text.strip(),
                        'passes_dead':row.find('td', attrs={'data-stat': 'passes_dead'}).text.strip(),
                        'passes_free_kicks':row.find('td', attrs={'data-stat': 'passes_free_kicks'}).text.strip(),
                        'through_balls':row.find('td', attrs={'data-stat': 'through_balls'}).text.strip(),
                        'passes_switches':row.find('td', attrs={'data-stat': 'passes_switches'}).text.strip(),
                        'throw_ins':row.find('td', attrs={'data-stat': 'throw_ins'}).text.strip(),
                        'corner_kicks':row.find('td', attrs={'data-stat': 'corner_kicks'}).text.strip(),
                        'corner_kicks_in':row.find('td', attrs={'data-stat': 'corner_kicks_in'}).text.strip(),
                        'corner_kicks_out':row.find('td', attrs={'data-stat': 'corner_kicks_out'}).text.strip(),
                        'corner_kicks_straight':row.find('td', attrs={'data-stat': 'corner_kicks_straight'}).text.strip(),
                        'passes_offsides':row.find('td', attrs={'data-stat': 'passes_offsides'}).text.strip(),
                        'passes_blocked':row.find('td', attrs={'data-stat': 'passes_blocked'}).text.strip()
                    })
            except Exception as e:
                print(f"Error processing Passing Type row: {e}")
                continue

    finally:
        driver.quit()
def update_advanced_goalkeeper_stats(player_set):
  
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.implicitly_wait(10)
    try:
        url = LINKS_URL_TO_CRAWL['Advanced Goalkeeping'][0]
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, LINKS_URL_TO_CRAWL['Advanced Goalkeeping'][1])))
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        table = soup.find('table', attrs={'id': LINKS_URL_TO_CRAWL['Advanced Goalkeeping'][1]})

        if not table:
            print("Error: Could not find the 'Advanced Goalkeeping' table.")
            return

        rows = table.find_all('tr', attrs={'data-row': True})

        for row in rows:
            try:
                name = row.find('td', attrs={'data-stat': 'player'}).text.strip()
                team = row.find('td', attrs={'data-stat': 'team'}).text.strip()
                player_key = str(name) + str(team)

                if player_key in player_set:
                    player_set[player_key].update({
                        'gk_free_kick_goals_against': row.find('td', attrs={'data-stat': 'gk_free_kick_goals_against'}).text.strip(),
                        'gk_corner_kick_goals_against': row.find('td', attrs={'data-stat': 'gk_corner_kick_goals_against'}).text.strip(),
                        'gk_own_goals_against': row.find('td', attrs={'data-stat': 'gk_own_goals_against'}).text.strip(),
                        'gk_psxg': row.find('td', attrs={'data-stat': 'gk_psxg'}).text.strip(),
                        'gk_psnpxg_per_shot_on_target_against': row.find('td', attrs={'data-stat': 'gk_psnpxg_per_shot_on_target_against'}).text.strip(),
                        'gk_psxg_net': row.find('td', attrs={'data-stat': 'gk_psxg_net'}).text.strip(),
                        'gk_psxg_net_per90': row.find('td', attrs={'data-stat': 'gk_psxg_net_per90'}).text.strip(),
                        'gk_passes_completed_launched': row.find('td', attrs={'data-stat': 'gk_passes_completed_launched'}).text.strip(),
                        'gk_passes_launched': row.find('td', attrs={'data-stat': 'gk_passes_launched'}).text.strip(),
                        'gk_passes_pct_launched': row.find('td', attrs={'data-stat': 'gk_passes_pct_launched'}).text.strip(),
                        'gk_passes': row.find('td', attrs={'data-stat': 'gk_passes'}).text.strip(),
                        'gk_passes_throws': row.find('td', attrs={'data-stat': 'gk_passes_throws'}).text.strip(),
                        'gk_pct_passes_launched': row.find('td', attrs={'data-stat': 'gk_pct_passes_launched'}).text.strip(),
                        'gk_passes_length_avg': row.find('td', attrs={'data-stat': 'gk_passes_length_avg'}).text.strip(),
                        'gk_goal_kicks': row.find('td', attrs={'data-stat': 'gk_goal_kicks'}).text.strip(),
                        'gk_pct_goal_kicks_launched': row.find('td', attrs={'data-stat': 'gk_pct_goal_kicks_launched'}).text.strip(),
                        'gk_goal_kick_length_avg': row.find('td', attrs={'data-stat': 'gk_goal_kick_length_avg'}).text.strip(),
                        'gk_crosses': row.find('td', attrs={'data-stat': 'gk_crosses'}).text.strip(),
                        'gk_crosses_stopped': row.find('td', attrs={'data-stat': 'gk_crosses_stopped'}).text.strip(),
                        'gk_crosses_stopped_pct': row.find('td', attrs={'data-stat': 'gk_crosses_stopped_pct'}).text.strip(),
                        'gk_def_actions_outside_pen_area': row.find('td', attrs={'data-stat': 'gk_def_actions_outside_pen_area'}).text.strip(),
                        'gk_def_actions_outside_pen_area_per90': row.find('td', attrs={'data-stat': 'gk_def_actions_outside_pen_area_per90'}).text.strip(),
                        'gk_avg_distance_def_actions': row.find('td', attrs={'data-stat': 'gk_avg_distance_def_actions'}).text.strip(),
                    })
            except Exception as e:
                print(f"Error processing Advanced Goalkeeping row: {e}")
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
    'name', 'nationality', 'position', 'team', 'age','born', 'games', 'games_starts',
    'minutes','minutes_90s', 'goals', 'assist','goals_assists','goals_pens','pens_made','pens_att' ,'cards_yellow', 'cards_red', 'xg',
    'npxg', 'xg_assist','npxg_xg_assist',
    'progressive_carries', 'progressive_passes', 'progressive_passes_received', 'goals_per90',
    'assists_per90','goals_assists_per90','goals_pens_per90','goals_assists_pens_per90', 'xg_per90', 'xg_assist_per90',
    'xg_xg_assist_per90','npxg_per90','npxg_xg_assist_per90',

    'gk_goals_against','gk_goals_against_per90','gk_shots_on_target_against','gk_saves', 'gk_save_pct','gk_wins',
    'gk_ties','gk_losses','gk_clean_sheets',''
    'gk_clean_sheets_pct','gk_pens_att','gk_pens_allowed','gk_pens_saved','gk_pens_missed', 'gk_pens_save_pct',
     
    'shots','shots_on_target','shots_on_target_pct','shots_per90', 'shots_on_target_per90',
    'goals_per_shot','goals_per_shot_on_target', 'average_shot_distance','shots_free_kicks','npxg_per_shot','xg_net','npxg_net',
 
    'passes_completed', 'passes_pct', 'passes_total_distance',
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

    nationality = player_dict.get('nationality', 'N/a')
    age = player_dict.get('age', 'N/a')
    nationality_processed = nationality.split()[1] if ' ' in nationality else nationality
    age_processed = age.split('-')[0] if '-' in age else age

    exported_list = []
    for key in PLAYER_KEY_TO_CRAWL:
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

def export_to_csv_and_db(player_set_dict, db_path='cau_thu.db'):
    """Export player data to CSV and update all player info into SQLite DB."""

    playerlist = list(player_set_dict.values())
    playerlist.sort(key=get_player_name)
    result = [format_player_data(player_dict) for player_dict in playerlist]

    # Các tên cột đầy đủ (75 cột)
    export_order_keys = [
    'name', 'nationality', 'position', 'team', 'age','born', 'games', 'games_starts',
    'minutes','minutes_90s', 'goals', 'assist','goals_assists','goals_pens','pens_made','pens_att' ,'cards_yellow', 'cards_red', 'xg',
    'npxg', 'xg_assist','npxg_xg_assist',
    'progressive_carries', 'progressive_passes', 'progressive_passes_received', 'goals_per90',
    'assists_per90','goals_assists_per90','goals_pens_per90','goals_assists_pens_per90', 'xg_per90', 'xg_assist_per90',
    'xg_xg_assist_per90','npxg_per90','npxg_xg_assist_per90',

    'gk_goals_against','gk_goals_against_per90','gk_shots_on_target_against','gk_saves', 'gk_save_pct','gk_wins',
    'gk_ties','gk_losses','gk_clean_sheets',''
    'gk_clean_sheets_pct','gk_pens_att','gk_pens_allowed','gk_pens_saved','gk_pens_missed', 'gk_pens_save_pct',
     
    'shots','shots_on_target','shots_on_target_pct','shots_per90', 'shots_on_target_per90',
    'goals_per_shot','goals_per_shot_on_target', 'average_shot_distance','shots_free_kicks','npxg_per_shot','xg_net','npxg_net',
 
    'passes_completed', 'passes_pct', 'passes_total_distance',
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

    # column_names = [  # Tên cột cho CSV, bạn có thể giữ nguyên như cũ hoặc rút gọn
    #     'Name', 'Nation', 'Team', 'Position', 'Age', 'Matches Played', 'Starts', 'Minutes', 'Goals', 'Assists',
    #     'Yellow Cards', 'Red Cards', 'Expected Goals (xG)', 'Expected Assist Goals (xAG)', 'Progressive Carries (PrgC)',
    #     'Progressive Passes (PrgP)', 'Progressive Passes Received (PrgR)', 'Goals per 90', 'Assists per 90',
    #     'xG per 90', 'xAG per 90', 'Goals Against per 90 (GA90)', 'Save Percentage (Save%)', 'Clean Sheets Percentage (CS%)',
    #     'Penalty Kicks Save Percentage', 'Shots on Target Percentage (SoT%)', 'Shots on Target per 90 (SoT/90)',
    #     'Goals per Shot (G/Sh)', 'Average Shot Distance (Dist)', 'Passes Completed (Cmp)', 'Pass Completion Percentage (Cmp%)',
    #     'Total Passing Distance (TotDist)', 'Short Pass Completion Percentage', 'Medium Pass Completion Percentage',
    #     'Long Pass Completion Percentage', 'Key Passes (KP)', 'Passes into Final Third (1/3)', 'Passes into Penalty Area (PPA)',
    #     'Crosses into Penalty Area (CrsPA)', 'Shot-Creating Actions (SCA)', 'SCA per 90', 'Goal-Creating Actions (GCA)',
    #     'GCA per 90', 'Tackles (Tkl)', 'Tackles Won (TklW)', 'Challenges (Tkl)', 'Challenges Lost (TklD)', 'Blocks',
    #     'Blocked Shots (Sh)', 'Blocked Passes (Pass)', 'Interceptions (Int)', 'Touches', 'Touches in Defensive Penalty Area',
    #     'Touches in Defensive Third', 'Touches in Middle Third', 'Touches in Attacking Third', 'Touches in Attacking Penalty Area',
    #     'Take-Ons (Att)', 'Take-On Success Percentage (Succ%)', 'Take-On Tackled Percentage (Tkl%)', 'Carries',
    #     'Progressive Carrying Distance (TotDist)', 'Carries into Final Third (1/3)', 'Carries into Penalty Area (CPA)',
    #     'Miscontrols (Mis)', 'Dispossessed (Dis)', 'Passes Received (Rec)', 'Fouls Committed (Fls)', 'Fouls Drawn (Fld)',
    #     'Offsides (Off)', 'Crosses (Crs)', 'Ball Recoveries (Recov)', 'Aerials Won (Won)', 'Aerials Lost (Lost)',
    #     'Aerials Won Percentage (Won%)'
    # ]

    # # 1. Xuất CSV
    # df = pd.DataFrame(result, columns=column_names)
    # df.to_csv("premier_league_player_stats.csv", index=False, encoding='utf-8')
    # print("✅ Data exported to CSV.")

    # 2. Lưu vào SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 3. Tạo bảng đầy đủ nếu chưa có
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        {', '.join([f"{col} TEXT" for col in PLAYER_KEY_TO_CRAWL])}
    );
    """
    cursor.execute(create_table_sql)

    # 4. Xóa dữ liệu cũ nếu cần
    cursor.execute("DELETE FROM players")

    # 5. Chèn toàn bộ dữ liệu
    insert_sql = f"""
    INSERT INTO players ({', '.join(PLAYER_KEY_TO_CRAWL)})
    VALUES ({', '.join(['?'] * len(PLAYER_KEY_TO_CRAWL))})
    """
    cursor.executemany(insert_sql, result)
    conn.commit()
    conn.close()
    print(f"✅ Dữ liệu đầy đủ đã được lưu vào bảng với {len(PLAYER_KEY_TO_CRAWL)} cột")
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
def update_transfer_values_to_db(db_path='cau_thu.db'):
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
                # slug = slugify_name(p['name'])
                slug = get_player_slug(p['name'])
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
    update_playing_time_stats(player_set)
    update_goalkeeping_stats(player_set)
    update_advanced_goalkeeper_stats(player_set)
    update_shooting_stats(player_set)
    update_passing_stats(player_set)
    update_passing_type_stats(player_set)
    update_goal_shot_creation_stats(player_set)
    update_defensive_stats(player_set)
    update_possession_stats(player_set)
    update_miscellaneous_stats(player_set)

    print("Exporting data to CSV...")
    export_to_csv_and_db(player_set)
    # # export_to_sqlite(player_set)
    print("💰 Thu thập và lưu giá trị chuyển nhượng...")
    update_transfer_values_to_db("cau_thu.db")

# -----------------------------------------
if __name__ == "__main__":
    main()