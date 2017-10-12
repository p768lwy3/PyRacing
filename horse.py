from __future__ import division, print_function, absolute_import

import os, re, requests, time, warnings
import numpy as np
import pandas as pd

from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
from dateutil import parser

warnings.filterwarnings("ignore")

HTML_PARSER = "html.parser"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0'}

def getInfo(horseno):
  url = 'http://www.hkjc.com/english/racing/horse.asp?HorseNo={0}&Option=1#htop'.format(horseno)
  list_req = requests.get(url, headers=headers)
  if(list_req.status_code == requests.codes.ok):
    horseinfo={}; l=[]
    soup = BeautifulSoup(list_req.content, HTML_PARSER)
    name = soup.find('td', attrs = {'class':'subsubheader'}).get_text().strip()
    horseinfo['Name'] = (str(name).split('\xa0'))[0] if(len(name) > 6) else None
    horseinfo['HorseNo'] = (str(name).split('\xa0'))[1].replace('(', '').replace(')', '') if(len(name)>6) else str(name).replace('(', '').replace(')', '').strip()
    soup = BeautifulSoup(list_req.content, HTML_PARSER)
    infotable = soup.find_all('table')[7]
    i = 0; l = []
    for td in infotable.find_all('td'):
      if td.find_all('option') == []:
        data = str(td.text.strip())
      elif td.find_all('option') != []:
        data = []
        for option in td.find_all('option'):
          data.append(option.text)
      if i % 2 != 0:
        l.append(data)
      i += 1

    for i in range(len(l)):
      if '/' in l[i]:
        l[i] = l[i].split('/')
    for i in range(len(l)):
      try:
        if(isinstance(l[i], list)):
          for j in range(len(l[i])):
            l[i][j] = (l[i][j].replace('\r','').replace('\n','').replace('\t','').replace(':','')).strip()
        else:
          l[i] = (l[i].replace('\r','').replace('\n','').replace('\t','').replace(':','')).strip()
      except:
        pass

    horseinfo['Country'] = l[0][0]; horseinfo['Age'] = l[0][1]
    horseinfo['Trainer'] = l[1]; horseinfo['Colour'] = l[2][0]
    horseinfo['Sex'] = l[2][1]; horseinfo['Owner'] = l[3]
    horseinfo['ImportType'] = l[4]; horseinfo['CurrentRating'] = l[5]
    horseinfo['CurrentRating'] = ''.join([j for j in horseinfo['CurrentRating'] if j.isdigit()])
    horseinfo['SeasonStakes'] = l[6]; horseinfo['SeasonStakes'] = ''.join([j for j in horseinfo['SeasonStakes'] if j.isdigit()])
    horseinfo['StartofSeasonRating'] = l[7]; horseinfo['StartofSeasonRating'] = ''.join([j for j in horseinfo['StartofSeasonRating'] if j.isdigit()])
    horseinfo['TotalStakes'] = l[8]; horseinfo['TotalStakes'] = ''.join([j for j in horseinfo['TotalStakes'] if j.isdigit()])
    horseinfo['Sire'] = l[9]; horseinfo['123Starts'] = l[10]
    horseinfo['123Starts'] = '-'.join([j for j in horseinfo['123Starts'] if j.isdigit()]) # problem: ten digital are splited!
    horseinfo['Dam'] = l[11]; horseinfo['StartsinPast10Race'] = l[12]
    horseinfo['StartsinPast10Race'] = ''.join([j for j in horseinfo['StartsinPast10Race'] if j.isdigit()])
    horseinfo["Dam's Sire"] = l[13]; horseinfo['Same Sire'] = l[14] # this have problem, cant crawl from the tabel
    df = pd.DataFrame.from_dict(list(horseinfo.items()))
    df = df.set_index([0])

    return df
