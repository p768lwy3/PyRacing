from bs4 import BeautifulSoup
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
import datetime
import numpy as np
import pandas as pd
import psycopg2
import re
import time

html_parser = "html.parser"
index_url = 'https://racing.hkjc.com/racing/information/English/Horse/SelectHorseByChar.aspx?ordertype={0}'
horse_url = "https://racing.hkjc.com/racing/information/english/Horse/Horse.aspx?HorseId={0}&Option=1"
class database(object):
    def __init__(self):
        self.host = "localhost"
        self.user = "hkjc_user"
        self.password = "hkjc_password"
        self.db = "hkjc"
        self.con = psycopg2.connect(host = self.host, 
                                   user = self.user, 
                                   password = self.password, 
                                   port = "5432",
                                   database = self.db)
        self.cur = self.con.cursor()
        return
   
    def horseupdate(self):
        opts = Options()
        opts.set_headless()
        assert opts.set_headless
        browser = Chrome(options=opts)
        browser.get(index_url.format('A'))    
        for c in range(ord('A'), ord('Z') + 1):
            time.sleep(1)
            browser.get(index_url.format(chr(c)))    
            print ('Got index {0}'.format(chr(c)))
            soup = BeautifulSoup(browser.page_source, html_parser)
            #print(soup.prettify())
            for li in soup.find_all("li", {"class": "table_eng_text"}):
                horse_name = li.text.rstrip()
                horse_no = li.a['href'][-12:]
                print('> update horse: {0}({1})...'.format(horse_name, horse_no))           
                browser.get(horse_url.format(horse_no))
                self.__updatehorseinfo__(browser.page_source,horse_no)
                self.__updatepastrecord__(browser.page_source,horse_no)

    def gameupdate(self):
        """
        url = 'http://racing.hkjc.com/racing/info/meeting/Results/English/{0}/'
        req = requests.get(url.format('Local/20180506/ST'), headers = headers)
        if req.status_code == requests.codes.ok:
            url_list = []
            soup = BeautifulSoup(req.content, html_parser)
            select = soup.find('select', {"id": "raceDateSelect", "name": "raceDateSelect"})
            for option in select.find_all("option"):
                if "value" in option.attrs:
                    if not "Simulcast" in option["value"]:
                        url_list.append(url.format(option["value"]))
            print(url_list)
        """
        date_wed = datetime.datetime(2018, 5, 2)
        date_sat = datetime.datetime(2018, 5, 5)
        date_sun = datetime.datetime(2018, 5, 6)
        while date_wed.year != 2017:
            string_wed = date_wed.strftime("%Y%m%d")
            string_sat = date_sat.strftime("%Y%m%d")
            string_sun = date_sun.strftime("%Y%m%d")
            url_list = []
            url_list = self.__findgame__(string_wed)
            """
            for i in range(3):
                try:
                    url_list = self.__findgame__(string_wed)
                    break
                except:
                    print('Cannot find {0}'.format(string_wed))
            for url in url_list:
                try:
                    self.__crawlgame__(url)
                    break
                except:
                    pass
            for i in range(3):
                try:
                    url_list = self.__findgame__(string_sat)
                    break
                except:
                    print('Cannot find {0}'.format(string_sat))
            for url in url_list:
                try:
                    self.__crawlgame__(url)
                    break
                except:
                    pass
            for i in range(3):
                try:
                    url_list = self.__findgame__(string_sun)
                    break
                except:
                    print('Cannot find {0}'.format(string_sun))
            for url in url_list:
                try:
                    self.__crawlgame__(url)
                    break
                except:
                    pass
            """
            date_wed -= datetime.timedelta(7)
            date_sat -= datetime.timedelta(7)
            date_sun -= datetime.timedelta(7)

        return
    
    def __findgame__(self, date):
        url = "http://racing.hkjc.com/racing/info/meeting/Results/English/Local/{0}/"
        req = requests.get(url.format(date), headers = headers)
        if req.status_code == requests.codes.ok:
            soup = BeautifulSoup(req.content, html_parser)
            url_list = []
            # get the place of race
            race = soup.find('td', {"class": "tdAlignL number13 color_black"}).text
            race = ' '.join(race.split()[-2:])
            if race == "Sha Tin":
                place = "ST"
            elif race == "Happy Valley":
                place = "HV"
            
            # get the number of games:
            games = soup.find('tr', {"valign": "middle", "bgcolor": "#ffffff"})
            games = games.find_all('td', {"nowrap": "nowrap", "style": "text-align:center;"})
            no = 0
            for g in games:
                no += 1
            for i in range(no):
                url_list.append(url.format(date) + '{0}/{1}'.format(place, (no + 1)))
            
            return url_list
                
    def __crawlgame__(self, url):
        req = requests.get(url, headers = headers)
        if req.status_code == requests.codes.ok:
            soup = BeautifulSoup(req.content, html_parser)
            gameid = soup.find('div', {'class': "boldFont14 color_white trBgBlue"}).text
            gameid = gameid.split('(')[1].replace(')', '')
            date = url.split('/')[-3]
            gameid += '_' + date[-2:] + date[-4:-2] + date[-6:-4]
            # game information
            table = soup.find("table", {"class": "tableBorder0 font13"})
            results = []
            for row in table.find_all('td'):
                results.append(row.text)
                if not row.find('span') is None:
                    results.append(row.find('span').text)
            df = pd.DataFrame(results)
            df.drop(17, 0, inplace = True)
            
            class_ = str(df.iloc[0, 0]).split()[1]
            dist_ = re.search('(\w+)M', str(df.iloc[1, 0])).group(1)
            dist_ = int(dist_)
            going_ = str(df.iloc[3, 0])
            course_ = str(df.iloc[6, 0]).split()
            coursetype = course_[0]
            course_ = course_[2].replace('"', '')
            bonus_ = str(df.iloc[7, 0]).split()[1].replace(',', '')
            try:
                bonus_ = int(bonus_)
            except:
                bonus_ = 0
            
            query = 'INSERT INTO GameInfo (RaceID, RaceClass, Dist, Going, CourseType, '\
                'Course, Bouns) VALUES ("{0}", "{1}", {2}, "{3}", "{4}", "{5}", {6});'.format(
                gameid, class_, dist_, going_, coursetype, course_, bonus_)
            
            # race record
            col = []
            col_names = soup.find('tr', {"class": 
                "tdAlignVT trBgBlue1 fontStyle color_white LBFont14 "})
            for col_name in col_names.find_all('td'):
                col.append(col_name.text)
            col = [c.replace('\r', '').replace('\n', '').replace('\t', '').replace(':', "").strip() for c in col]
            records = []
            record = []
            table = soup.find("table", {"class": 
                "tableBorder trBgBlue tdAlignC number12 draggable"})
            for row in table.find_all("tr", {"class": ['trBgGrey','trBgWhite']}):
                for cell in row.find_all('td'):
                    if not cell.find('a') is None:
                        r = cell.find('a').text
                        if not cell is None:
                            r = r + cell.text
                        record.append(r)
                    elif not cell is None:
                        record.append(cell.text)
                records.append(record)
                record = []
            records = pd.DataFrame(records)
            length = len(records.columns)
            counter = 1
            for j in range(10, length - 2):
                col_name = 'position_' + str(counter)
                col.insert(j, col_name)
                counter += 1
            records.columns = col
            records['HorseNo'] = pd.Series([re.search('\((.*?)\)', str(value)).group(1)
                for value in records['Horse']])
            records.drop('Horse', axis = 1, inplace = True)
            records.Jockey = records.Jockey.map(lambda x: 
                x[:len(x)//2] if x[len(x)//2:] in x[:len(x)//2] else x)
            records.Trainer = records.Trainer.map(lambda x: 
                x[:len(x)//2] if x[len(x)//2:] in x[:len(x)//2] else x)               
            print(records)
            for idx, row in records.iterrows():
                query = 'INSERT INTO GameRecord (RaceID, HorseID, Pla, HorseNo, Jockey, '\
                    'Trainer, ActWt, DeclarHorseWt, Dr, LBW, FinishTime, WinOdds) VALUES '\
                    '({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}, {9}, {10}, {11});'.format(
                        gameid, row['HorseNo'], row['Plc.'], row['Horse No.'], 
                        row['Jockey'], row['Trainer'], row['ActualWt.'], 
                        row['Declar.Horse Wt.'], row['Draw'], row['LBW'],
                        row['Finish Time'], row['Win Odds'])
                print(query)
                    
                

    def __updatehorseinfo__(self, page, horse_no):
        info = {}
        soup = BeautifulSoup(page, html_parser)
        #print(soup.prettify())
        title = soup.find('td', class_ = "subsubheader").get_text().strip()
        if len(title) > 6:
            #print('Got '+title)
            title = str(title).rsplit(" ",1)
            name = title[0].strip().replace('\'','\'\'')
            number = title[1].replace('(', '').replace(')', '').replace('\'','\'\'')
        else:
            name = None
            number = str(title).replace('(', '').replace(')', '').strip()
        #table = soup.find_all('table')[7] # here should find a better way to search?
        table = soup.find('table', class_ = "table_eng_text")
        l = []
        for i, td in enumerate(table.find_all('td')):
            d = str(td.text.strip())
            if (i-1) % 3 != 0:
                l.append(d)
        
        l = [a.split('/') if '/' in a else a for a in l]
        
        for i in range(len(l)):
            try:
                if isinstance(l[i], list):
                    for j in range(len(l[i])):
                        l[i][j] = l[i][j].replace('\r', '').replace(
                            '\n', '').replace('\t', '').replace(':', '').replace('\'','\'\'').strip()
                else:
                    l[i] = l[i].replace('\r', '').replace(
                        '\n', '').replace('\t', '').replace(':', '').replace('\'','\'\'').strip()
            except:
                pass
        #print(l)
        country = l[1][0]
        age = int(l[1][1])
        color = l[3][0]
        sex = l[3][1]
        importtype = l[5]
        
        try:
            seasonstakes = int(''.join([d for d in l[7] if d.isdigit()]))
        except:
            seasonstakes = 0
        
        try:
            totalstakes = int(''.join([d for d in l[9] if d.isdigit()]))
        except:
            totalstakes = 0
        
        starts123 = re.findall(r'\d+', l[11])
        starts123 = '-'.join(starts123)
        
        try:
            startspast10 = int(''.join([d for d in l[13] if d.isdigit()]))
        except:
            startspast10 = 0
        
        table = soup.find_all('table', class_ = "table_eng_text")[1]
        l2 = []
        for i, td in enumerate(table.find_all('td')):
            d = str(td.text.strip())
            if (i-1) % 3 != 0:
                l2.append(d)
        
        for i in range(len(l2)):
            try:
                l2[i] = l2[i].replace('\r', '').replace(
                    '\n', '').replace('\t', '').replace(':', '').replace('\'','\'\'').strip()
            except:
                pass
        
        #print(l2)
        trainer = l2[1]
        owner = l2[3].split(',')[0]
        owner = owner[0:63]
        
        try:
            currentrating = int(''.join([d for d in l2[5] if d.isdigit()]))
        except:
            currentrating = 0
        
        try:
            startrating = int(''.join([d for d in l2[7] if d.isdigit()]))
        except:
            startrating = 0
        sire = l2[9]
        dam = l2[11]
        damssire = l2[13]
        
        query = 'INSERT INTO HorseInfo (HorseID, Name, Country, Age, Color, '\
                'Sex, ImportType, SeasonStakes, TotalStakes, First3Starts, '\
                'StartsPast10, Trainer, Owner, CurrentRating, StartRating, '\
                'Sire, Dam, DamSire) VALUES (\'{0}\', \'{1}\', \'{2}\', {3}, '\
                '\'{4}\', \'{5}\', \'{6}\', {7}, {8}, \'{9}\', {10}, \'{11}\', \'{12}\', {13}, '\
                '{14}, \'{15}\', \'{16}\', \'{17}\')'\
                'ON CONFLICT ON CONSTRAINT horseinfo_pkey DO NOTHING'.format(
                  number, name, country, age, color, sex, importtype, seasonstakes,
                  totalstakes, starts123, startspast10, trainer, owner, currentrating, 
                  startrating, sire, dam, damssire)
                #'ON DUPLICATE KEY UPDATE HorseID = VALUES(HorseID);
        #print(query)
        self.cur.execute(query)
        self.con.commit()
        return

    def __updatepastrecord__(self, page, horse_no):
        soup = BeautifulSoup(page, html_parser)
        l = []
        if soup.find("table", class_ = "bigborder") is not None:
            for raw0 in soup.find("table", class_ = "bigborder").find_all("tr", 
                {"bgcolor": ['#F3F1E6', '#E3E1D7', '#EBEEF5', '#DBDEE5', '#F8F4EF', '#E7E4DF']}):
                for raw1 in raw0.find_all("td"):
                    l.append(str(raw1.text.strip()))
                    l = [x for x in l if x != '']
                for k in range(18, len(l), 18):
                    try:
                        if l[k].startswith('-'):
                            del l[k]
                    except:
                        pass
            if not l:
                return
            l = np.asarray(l).reshape(-1, 18)
            #print(l)
            df = pd.DataFrame({'RaceIndex': l[:, 0], 'Pla': l[:, 1], 'Date': l[:, 2],
                'RC/Track/Course': l[:, 3], 'Dist': l[:, 4], 'G': l[:, 5], 
                'RaceClass': l[:, 6], 'Dr': l[:, 7], 'Rtg': l[:, 8], 
                'Trainer': l[:, 9], 'Jockey': l[:, 10], 'LBW': l[:, 11], 
                'WinOdds': l[:, 12], 'ActWt': l[:, 13], 'RunningPosition': l[:, 14],
                'FinishTime': l[:, 15], 'DeclarHorseWt': l[:, 16], 'Gear': l[:, 17]})
            df['HorseNo'] = horse_no
            df.RaceIndex = df.RaceIndex.map(lambda x:
                "999" if not x.isdigit() else x)
            df = df[df.RaceIndex != "999"] # remove oversea or etc.
            df.RunningPosition = df.RunningPosition.map(lambda x:
                '-'.join(re.findall(r'\d+', x)))
            df.FinishTime = df.FinishTime.replace('--', '0.00.00')
            # df.FinishTime = df.FinishTime.str.replace('.', ':')
            # df.FinishTime = pd.to_datetime(df.FinishTime, format = '%M.%S.%f')
            # df.Date = pd.to_datetime(df.Date, format = '%d/%m/%y')
            # df.Date = df.Date.date()
            df = df.join(df['RC/Track/Course'].str.split('/', expand = True).rename(
                columns = {0: 'RC', 1: 'Track', 2: 'Course'}))
            if not 'Course' in df.columns:
                df['Course'] = '-'
            df.Course = df.Course.map(lambda x: "-" if x is None else x)
            for col in ['RC', 'Track', 'Course']:
                df[col] = df[col].map(lambda x: x.replace('"', '').strip())
                df[col] = df[col].fillna('-')
            for col in ['Pla', 'Dr']:
                df[col] = df[col].map(lambda x: '99' if not x.isdigit() else x)
            for col in ['ActWt', 'DeclarHorseWt', 'WinOdds']:
                df[col] = df[col].map(lambda x: '0' if not x.isdigit() else x)
            df.Rtg = df.Rtg.map(lambda x: '999' if not x.isdigit() else x)
            df['RaceNo'] = df.apply(lambda x:
                x.RaceIndex + '_' + x.Date.replace('/', ''), axis = 1)
            df.Date = df.Date.map(lambda x: '20' + x[6:] + '-' + x[3:5] + '-' + x[0:2])
            for col in ['RaceIndex', 'Pla', 'Dist', 'DeclarHorseWt', 'Rtg', 
                'Dr', 'ActWt']:
                df[col] = df[col].astype('int64')
            df.WinOdds = df.WinOdds.astype('float64')
            for col in ['RaceClass', 'Jockey', 'Trainer']:
                df[col] = df[col].map(str).map(str.strip).astype('str')
            df.Trainer = df.Trainer.map(lambda x: x.replace('\'', '\'\''))
            
            for idx, r in df.iterrows():
                query = 'INSERT INTO PastRecord (RaceID, HorseID, RaceIndex, Pla, RaceDate, '\
                'RC, Track, Course, Dist, G, RaceClass, Dr, Rtg, Trainer, Jockey, LBW, WinOdds, '\
                'ActWt, RunningPosition, FinishTime, DeclarHorseWt, Gear) VALUES (\'{0}\', \'{1}\', '\
                '{2}, {3}, \'{4}\', \'{5}\', \'{6}\', \'{7}\', {8}, \'{9}\', \'{10}\', {11}, {12}, \'{13}\', '\
                '\'{14}\', \'{15}\', {16}, {17}, \'{18}\', \'{19}\', {20}, \'{21}\') '\
                'ON CONFLICT ON CONSTRAINT pastrecord_pkey DO NOTHING'.format(
                    r.RaceNo, r.HorseNo, r.RaceIndex, r.Pla, r.Date, r.RC, r.Track, r.Course, r.Dist, 
                    r.G, r.RaceClass, r.Dr, r.Rtg, r.Trainer, r.Jockey, r.LBW, r.WinOdds, r.ActWt, 
                    r.RunningPosition, r.FinishTime, r.DeclarHorseWt, r.Gear)
                self.cur.execute(query)
            self.con.commit()
        else:
            print('There is no racing record of {0}.'.format(horse_no))
    
