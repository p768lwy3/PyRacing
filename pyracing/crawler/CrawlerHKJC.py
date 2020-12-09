import re
from typing import Dict

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from . import Crawler
from .. import driver_path, html_parser
from ..utils import parse_cookies


class CrawlerHKJC(Crawler):
    def __init__(self):
        self.cookies = {}
        self.options = Options()
        self.options.headless = True

    def get_horses(self) -> Dict[str, str]:
        # Initiate variables for the function
        horses = {}
        url = "http://www.hkjc.com/english/racing/selecthorsebychar.asp?ordertype={0}"

        # Since Hong Kong Jockey Club website required to access with cookies, get that by selenium first.
        driver = webdriver.Firefox(executable_path=driver_path, options=self.options)
        driver.get(url.format("A"))
        try:
            _ = WebDriverWait(driver, 30).until(
                ec.visibility_of_element_located((By.CLASS_NAME, "commContent"))
            )

        except TimeoutException:
            raise Exception("Timeout to get cookies from the website")

        finally:
            cookies = driver.get_cookies()
            self.cookies = parse_cookies(cookies)
            driver.quit()

        for c in range(ord('A'), ord('Z') + 1):
            next_url = url.format(chr(c))
            request = requests.get(next_url, cookies=self.cookies)

            if request.status_code != requests.codes.ok:
                # Skip the page if network error
                # TODO: use logger to print the log string
                print("Network Error: status code {0}".format(request.status_code))
                continue

            soup = BeautifulSoup(request.content, html_parser)

            for li in soup.find_all("li", {"class": "table_eng_text"}):
                horse_name = li.text
                horse_no = li.a['href'][-4:]
                horses[horse_no] = horse_name

        return horses

    def get_games(self, game_date: str):
        # Initiate variables for the function
        url = "https://racing.hkjc.com/racing/information/English/Racing/ResultsAll.aspx?RaceDate={0}"

        # Get the cookie first
        driver = webdriver.Firefox(executable_path=driver_path, options=self.options)
        try:
            driver.get(url.format(game_date))

            # wait until the website is ready
            _ = WebDriverWait(driver, 30).until(
                ec.visibility_of_element_located((By.CSS_SELECTOR, "div.ResultsAll.commContent"))
            )

            # find the first race and click it
            race_card = driver.find_element_by_xpath('//table[@class="f_fs12 f_fr js_racecard"]/tbody/tr/td/a')
            race_card.click()
            _ = WebDriverWait(driver, 30).until(
                ec.visibility_of_element_located((By.CSS_SELECTOR, "div.localResults.commContent"))
            )

        except TimeoutException:
            raise Exception("Timeout to get cookies from the website")

        finally:
            cookies = driver.get_cookies()
            self.cookies = parse_cookies(cookies)
            driver.quit()

    @staticmethod
    def get_game(game_date: str, cookies: dict):
        url = "https://racing.hkjc.com/racing/information/English/Racing/LocalResults.aspx?RaceDate={0}".format(
            game_date)
        request = requests.get(url, cookies=cookies)
        soup = BeautifulSoup(request.content, html_parser)

        # parse the metadata of game
        game_id = soup.find('tr', {'class': "bg_blue color_w font_wb"}).text.strip()
        game_id = game_id.split('(')[1].replace(')', '')
        race_tab = soup.find("div", {'class': 'race_tab'}).find("tbody")
        _race = [row.text for row in race_tab.find_all('td') if len(row.text.strip()) > 0]
        row_0 = _race[0].split(" - ")
        race = {
            "GameID": game_id,
            "Class": row_0[0],
            "Distance": row_0[1],
            "": row_0[2],
            "Going": _race[2],
            "Match": _race[3],
            "Course": _race[5],
            "Bonus": _race[6],
            "Time": [_race[8], _race[9], _race[10]],
            "SectionalTime": [_race[12], _race[13], _race[14]]
        }

        # TODO: make the data table of metadata
        print(race)

        performance = soup.find('div', {'class': 'performance'}).find('tbody').find_all('tr')
        rows = []
        for tr in performance:
            row = []
            for td in tr.find_all('td'):
                row.append(re.sub("\s\s+", " ", td.text.strip()))

        # TODO: make the data table of performance
        print(rows)
