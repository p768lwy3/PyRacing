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


def getPastdata(HorseNo, StartDate=datetime(1999,1,1), EndDate=datetime.now()):
  url = 'http://www.hkjc.com/english/racing/horse.asp?HorseNo={0}&Option=1#htop'.format(HorseNo)
  list_req = requests.get(url, headers=headers)
  if(list_req.status_code == requests.codes.ok):
    soup = BeautifulSoup(list_req.content, HTML_PARSER)
    l=[]
    if(soup.find('table',attrs={'class':'bigborder'}) is not None):
      for rawdatasets in soup.find('table', attrs = {'class':'bigborder'}).find_all('tr', 
        attrs={'bgcolor':['#F3F1E6','#E3E1D7','#EBEEF5','#DBDEE5','#F8F4EF','#E7E4DF']}):
        for rawdata in rawdatasets.find_all('td'):
          l.append(str(rawdata.text.strip()))
          l = [x for x in l if x != '']
      for k in range(18, len(l), 18):
        try:
          if(l[k].startswith('-')):
            del l[k]
        except:
          pass
      l = (np.asarray(l)).reshape(len(l)//18,18)
      df = pd.DataFrame({'Race Index':l[:,0],'Pla.':l[:,1],'Date':l[:,2],'RC/Track/Course':l[:,3],'Dist.':l[:,4],'G':l[:,5],
           'Race Class':l[:,6],'Dr':l[:,7],'Rtg.':l[:,8],'Trainer':l[:,9],'Jockey':l[:,10],'LBW':l[:,11],'Win Odds':l[:,12],
           'Act. Wt.':l[:,13],'Running Position':l[:,14],'Finish Time':l[:,15],'Declar. Horse Wt.':l[:,16],'Gear':l[:,17]})
      """Clear the data, Make the dtypes correct
         How should I replace the '--' in different column? Also, how should I convert the string to number? And, how to deal with Track and 
         SiteConditions? <- This should be converting to dummy variable. Is it better to split the equipment to boolean variable? <- This should 
         be done easily."""
      for i in range(len(df['Race Index'])):
        if not df.loc[i, 'Race Index'].isdigit():
          df.loc[i, 'Race Index'] = 999
      for i in range(len(df['Running Position'])):
        df.loc[i,'Running Position'] = '-'.join([j for j in df.loc[i, 'Running Position'] if j.isdigit()])
      df['Finish Time'] = df['Finish Time'].replace('--','0:00:00')
      for i in range(len(df['Finish Time'])):
        df.loc[i,'Finish Time'] = df.loc[i, 'Finish Time'].replace('.',':')
      df['Finish Time'] = pd.to_datetime(df['Finish Time'], format='%M:%S:%f')
      df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%y')
      for i in range(len(df['Date'])):
        df.loc[i, 'Date'] = df.loc[i, 'Date'].date()
      df = df.join(df['RC/Track/Course'].str.split('/',expand=True).rename(columns={0:'RC', 1:'Track',2:'Course'}))
      df = df.drop('RC/Track/Course', axis=1)
      for i in ['RC','Track','Course']:
        for j in range(0,len(df['RC'])):
          try:
            df.loc[j,i] = df.loc[j,i].replace('"','').strip()
          except:
            pass
        df[i] = df[i].fillna(value='-')	
      df['Declar. Horse Wt.'] = df['Declar. Horse Wt.'].replace('--','0'); df['Dr'] = df['Dr'].replace('--','99')
      df['Win Odds'] = df['Win Odds'].replace('---','0'); df['Rtg.'] = df['Rtg.'].replace('--','999')
      for i in ['Race Index','Pla.','Dist.','Declar. Horse Wt.','Rtg.','Dr','Act. Wt.']:
        for j in range(0,len(df[i])):
          try:
            df.loc[j,i] = df.loc[j,i].astype('int64')
          except:
            pass
      ## Here are some problems so the dtypes cannot be converted...
      df['Win Odds'] = df['Win Odds'].astype('float64')
      for i in ['Race Class', 'Jockey', 'Trainer']:
        df[i] = df[i].map(str).map(str.strip).astype('str')
      return df[(df['Date']>StartDate)&(df['Date']<EndDate)] # (df['Rist.'].isin(['1200', '1650'])) etc.
    else:
      print('  There is no racing record of the horse in {0}'.format(url))
