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
#retired_url = "https://racing.hkjc.com/racing/information/English/Horse/OtherHorse.aspx?HorseId={0}"
race_url = 'https://racing.hkjc.com/racing/information/English/Racing/LocalResults.aspx?RaceDate={0}'

def is_float(x):
    try:
        float(x)
        return True
    except ValueError:
        return False

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
   
    def raceupdate(self):
        opts = Options()
        opts.set_headless()
        assert opts.set_headless
        browser = Chrome(options=opts)
        browser.get('https://racing.hkjc.com/racing/information/English/Racing/LocalResults.aspx')
        time.sleep(2)

        date_sat = datetime.datetime(2013, 9, 7)
        date_sun = datetime.datetime(2013, 9, 8)
        date_wed = datetime.datetime(2013, 9,11)
        while date_wed.year < 2017:
            string_wed = date_wed.strftime("%Y/%m/%d")
            string_sat = date_sat.strftime("%Y/%m/%d")
            string_sun = date_sun.strftime("%Y/%m/%d")
            self.__search_dates__(browser,string_sat)
            self.__search_dates__(browser,string_sun)
            self.__search_dates__(browser,string_wed)
            date_wed += datetime.timedelta(7)
            date_sat += datetime.timedelta(7)
            date_sun += datetime.timedelta(7)
        return

    """
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
     """

    def fill_missing_horses(self,browser,horseid):
        self.cur.execute(
            'select horseid from horseinfo where ' \
            'horseid = \'{0}\''.format(horseid))
        if self.cur.fetchone() is None:
            print('> update horse: {0}...'.format(horseid))           
            browser.get(horse_url.format(horseid))
            retired = re.search('OtherHorse',browser.current_url)
            self.__updatehorseinfo__(retired,browser.page_source,horseid)
            self.__updatepastrecord__(browser.page_source,horseid)

    def __search_dates__(self,browser,date):
        print("> finding races for {0}".format(date))
        (place,url_list) = self.__findraces__(browser,date)
        if url_list:
            horses_in_race = self.__crawlrace__(browser,date,place,url_list)
            for horseid in horses_in_race:
                self.fill_missing_horses(browser,horseid)
        else:
            print(" No races found for {0}".format(date))
    
    def __findraces__(self, browser, date):
        browser.get(race_url.format(date))
        soup = BeautifulSoup(browser.page_source, html_parser)
        url_list = []
        # get the place of race
        race = soup.find("span", class_ = "f_fl f_fs13")
        if race is None:
            return("",url_list)
        race = race.text
        race = ' '.join(race.split()[-2:])
        if race == "Sha Tin":
            place = "ST"
        elif race == "Happy Valley":
            place = "HV"
        else:
            place = race[0:2].upper()
        # get the number of races:
        races = soup.find('table', class_ = "f_fs12 f_fr js_racecard")
        races = races.find_all('td')
        no = 0
        for i in range((len(races)-2)):
            url_list.append(race_url.format(date) + '&Racecourse={0}&RaceNo={1}'.format(place, (i + 1)))
        return (place,url_list)
            
    def __crawlrace__(self, browser,date,place,url_list):
        racedate = date
        print("> got races for {0} on {1}".format(place, date))
        date = date.split('/')
        horses_in_race = []
        for race_url in url_list:
            try:
                browser.get(race_url)
            except:
                print("Error retrieving {0}".format(race_url))
                continue

            soup = BeautifulSoup(browser.page_source, html_parser)
            try:
                raceid = soup.find('tr', class_ = "bg_blue color_w font_wb").text
            except: 
                print("Error getting raceid")
                continue

            raceid = raceid.split('(')[1].replace(')', '').rstrip().zfill(3)
            raceid += '_' + date[2] + date[1] + date[0][2:4]
            print("Parsing raceid: {0}".format(raceid))
            # race information
            table = soup.find("tbody", class_ = "f_fs13")
            results = []
            for row in table.find_all('td'):
                if row.text != "":
                    results.append(row.text)
                    if not row.find('span') is None:
                        results.append(row.find('span').text)
            df = pd.DataFrame(results)
            #with pd.option_context('display.max_rows', None, 'display.max_columns', None):
            #    print(df)

            class_ = str(df.iloc[0, 0]).split(" - ")[0]
            dist_ = re.search('(\w+)M', str(df.iloc[0, 0])).string.split(" - ")[1]
            dist_ = int(dist_.replace('M', ''))
            going_ = str(df.iloc[2, 0])
            course_ = str(df.iloc[5, 0]).split(" - ")
            track = course_[0]
            try:
                course_ = course_[1].replace('"', '')
            except:
                course_ = 'Null'
        
            query = 'INSERT INTO raceInfo (RaceID, RaceClass, RaceDate, Venue, Track, Course, Going, '\
                'Dist) VALUES (\'{0}\', \'{1}\', \'{2}\', \'{3}\', \'{4}\', \'{5}\',\'{6}\', {7}) '\
                'ON CONFLICT ON CONSTRAINT raceinfo_pkey DO NOTHING'.format(
                raceid, class_, racedate, place, track, course_, going_, dist_)
            self.cur.execute(query)
            self.con.commit()    
            #print(query)

            # race record
            race_results = soup.find('div', class_ = "performance")
            col = []
            col_names = race_results.find('tr', class_ = "bg_blue color_w")
            for col_name in col_names.find_all('td'):
                col.append(col_name.text.replace('.', "").replace(' ', ""))
            col = [c.replace('\r', '').replace('\n', '').replace('\t', '').replace(':', "").strip() for c in col]
            records = []
            record = []
            table = race_results.find("tbody", class_ = "f_fs12")
            
            for row in table.find_all("tr"):
                for cell in row.find_all('td'):
                    if not cell.find('a') is None:
                        r = cell.a['href'][-12:]
                        if re.search("HK_20[0-2][0-9]_\w{4}", r):
                            record.append(r)
                        else:
                            record.append(cell.text.strip())
                    elif not cell is None:
                        record.append(cell.text.strip())
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
            
            # If there is a void race, Win Odds (And running position) aren't list in the table
            if not 'WinOdds' in records.columns:
                continue
            records.Jockey = records.Jockey.map(lambda x: 
                x[:len(x)//2] if x[len(x)//2:] in x[:len(x)//2] else x)
            records.Jockey = records.Jockey.map(lambda x:
                x.replace('\'','\'\''))         
            records.Trainer = records.Trainer.map(lambda x: 
                x[:len(x)//2] if x[len(x)//2:] in x[:len(x)//2] else x)     
            records.Trainer = records.Trainer.map(lambda x:
                x.replace('\'','\'\''))         
            records.Plc = records.Plc.map(lambda x: 'Null' if not x.isdigit() else x)
            records.HorseNo = records.HorseNo.map(lambda x: 'Null' if not x.isdigit() else x)
            records.DeclarHorseWt = records.DeclarHorseWt.map(lambda x: 
                'Null' if not x.isdigit() else x)
            records.Draw = records.Draw.map(lambda x: 'Null' if not x.isdigit() else x)

            records.WinOdds = records.WinOdds.map(lambda x: float(x) 
                if is_float(x) else 'Null')
            
            horses_in_race += records.Horse.tolist()
            #print(records)
            for idx, row in records.iterrows():
                query = 'INSERT INTO RaceResults (RaceID, HorseID, Pla, HorseNo, '\
                    'Draw, LBW, FinishTime, WinOdds) VALUES '\
                    '(\'{0}\', \'{1}\', {2}, {3}, {4}, \'{5}\', \'{6}\', {7}) '\
                    'ON CONFLICT ON CONSTRAINT raceresults_pkey DO NOTHING'.format(
                        raceid, row['Horse'], row['Plc'], row['HorseNo'], 
                        row['Draw'], row['LBW'], row['FinishTime'], row['WinOdds'])
                #print(query)
                self.cur.execute(query)
                self.con.commit()
        return(horses_in_race)
            

    def __updatehorseinfo__(self, retired, page, horse_no):
        info = {}
        soup = BeautifulSoup(page, html_parser)
        #print(soup.prettify())
        title = soup.find('td', class_ = "subsubheader").get_text().strip()
        print('Got '+title)
        if len(title) > 6:
            title = str(title).rsplit(" ",1)
            if title[1] == "(Retired)":
               name = title[0].rsplit(" ",1)[0].strip().replace('\'','\'\'')
            else:
               name = title[0].strip().replace('\'','\'\'')
        else:
            name = None
        
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
        
        #print(l)
        #print(l2)
        
        country = l[1][0]
        if retired:
            age = 'Null'
            seasonstakes = 0
            totalstakes = int(''.join([d for d in l[9] if d.isdigit()]))
            starts123 = re.findall(r'\d+', l[9])
            starts123 = '-'.join(starts123)
            startspast10 = 0
            currentrating = 0
            startrating = 0
            sire = l2[5]
            dam = l2[7]
            damssire = l2[9]
        else:
            age = int(l[1][1])
            seasonstakes = int(''.join([d for d in l[7] if d.isdigit()]))
            totalstakes = 0
            starts123 = re.findall(r'\d+', l[11])
            starts123 = '-'.join(starts123)
            startspast10 = int(''.join([d for d in l[13] if d.isdigit()]))
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

        color = l[3][0]
        sex = l[3][1]
        importtype = l[5]
        
        owner = l2[3].split(',')[0]
        owner = owner[0:63]
        
        
        # Change this to update the fields that would vary on conflict instead of ignore
        query = 'INSERT INTO HorseInfo (HorseID, Name, Country, Age, Color, '\
                'Sex, ImportType, SeasonStakes, TotalStakes, Starts123, '\
                'StartsPast10, Owner, CurrentRating, StartRating, '\
                'Sire, Dam, DamSire) VALUES (\'{0}\', \'{1}\', \'{2}\', {3}, '\
                '\'{4}\', \'{5}\', \'{6}\', {7}, {8}, \'{9}\', {10}, \'{11}\', {12}, {13}, '\
                '\'{14}\', \'{15}\', \'{16}\')'\
                'ON CONFLICT ON CONSTRAINT horseinfo_pkey DO NOTHING'.format(
                #update age, stakes, start*, trainer, owner, ratings
                  horse_no, name, country, age, color, sex, importtype, seasonstakes,
                  totalstakes, starts123, startspast10, owner, currentrating, 
                  startrating, sire, dam, damssire)
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
            
            for col in ['ActWt', 'DeclarHorseWt']:
                df[col] = df[col].map(lambda x: 'Null' if not x.isdigit() else x)
            df.Rtg = df.Rtg.map(lambda x: '999' if not x.isdigit() else x)
            df.Date = df.Date.map(lambda x: x.replace('/', ''))
            df['RaceNo'] = df.apply(lambda x:
                x.RaceIndex + '_' + x.Date[0:2] + x.Date[2:4] + x.Date[-2:], axis = 1)
            #for col in ['DeclarHorseWt', 'Rtg', 'ActWt']:
            #    df[col] = df[col].astype('int64')
            for col in ['RaceClass', 'Jockey', 'Trainer']:
                df[col] = df[col].map(str).map(str.strip).astype('str')
            df.Trainer = df.Trainer.map(lambda x: x.replace('\'', '\'\''))
            df.Jockey = df.Jockey.map(lambda x: x.replace('\'', '\'\''))
            
 
            for idx, r in df.iterrows():
                query = 'INSERT INTO PastRecord (RaceID, HorseID, '\
                'Rtg, Trainer, Jockey, ActWt, RunningPosition, DeclarHorseWt, Gear) VALUES ('\
                '\'{0}\', \'{1}\', {2}, \'{3}\', \'{4}\', {5}, \'{6}\', {7}, \'{8}\') '\
                'ON CONFLICT ON CONSTRAINT pastrecord_pkey DO NOTHING'.format(
                    r.RaceNo, r.HorseNo, r.Rtg, r.Trainer, r.Jockey, r.ActWt, 
                    r.RunningPosition, r.DeclarHorseWt, r.Gear)
                #print(query)
                self.cur.execute(query)
            self.con.commit()
        else:
            print('There is no racing record of {0}.'.format(horse_no))
    
