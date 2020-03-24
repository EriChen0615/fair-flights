# -*- coding: utf-8 -*-
"""
Created on Sat Mar 21 00:17:14 2020

@author: asus
"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import datetime
import sqlalchemy as db
import csv
import time
import string
import urllib
import re

def _append_query(url,attr,value):
    if url[-1] == '?':
        return url + attr + '=' + value
    else:
        return url + '&' + attr + '=' + value

def _append_cities(url,dept_code,dest_code):
    return url + dept_code.lower() + '-' + dest_code.lower() + '?'

def _iata_code(airport):
    """
    look up airport IATA code from Wikipedia. If a city has multiple airports look up the city code
    """
    print(f"looking up IATA code for {airport} from wikipedia...")
    iata_base_url = 'https://en.wikipedia.org/wiki/List_of_airports_by_IATA_code:_' 
    initial = iter(string.ascii_uppercase)
    code = None
    terminate = False
    while True:
        try:
            iata_url = iata_base_url + next(initial)
            print('searching',iata_url)
        except StopIteration:
            terminate = True
        finally:
            pass
        
        with urllib.request.urlopen(iata_url) as response:
            html = response.read()
            soup = BeautifulSoup(html, 'lxml')
            airport_elem = soup.find_all(title=airport)
            for elem in airport_elem:
                if elem.parent.parent.find(text=re.compile(r'metropolitan area')):
                    code = elem.parent.parent.contents[1].get_text()[:3]
                    return code
                else:
                    code = elem.parent.parent.contents[1].get_text()[:3]
                    continue
          
        if terminate:
            if code is None:
                print(f"cannot find IATA code for {airport}")
            return code
           
          
    
      

def gen_query_url(dept_code, dest_code, dep_date, one_way = True, return_date=None , n_adult=1, n_child=0, n_infant=0, direct_flight=0):
    """
    depdate=year[xxxx]-month[xx]-day[xx]
    """
    #base_url = 'https://flights.ctrip.com/international/search/oneway-lon-sha?'
    base_url = 'https://flights.ctrip.com/international/search/oneway-'
    base_url = _append_cities(base_url,dept_code,dest_code)
    base_url = _append_query(base_url, 'depdate', dep_date)
    return base_url

def parse_page(driver):
    
    flights = []
    
    #scroll down until end of page
    for i in range(10):
        js="var q=document.documentElement.scrollTop=" + str(1000*i)
        driver.execute_script(js)
        try:
            elem = WebDriverWait(driver,10).until(
                    EC.presence_of_all_elements_located((By.XPATH, '//div[@class="flight-airline"]'))
            )
        except TimeoutException:
            time.sleep(1)
        finally:
            pass
        
        soup = BeautifulSoup(driver.page_source,'lxml')
                
        flight_items = soup.find_all('div', 'flight-item')
        for flight in flight_items:
            data = {}
            # .get_text() is used to retrieve the text part only
            if flight.find('div','flight-airline') is None:
                continue
            
            # departure/arrival data
            data['date'] = soup.find(class_='date').get_text()
            data['airline'] = flight.find('div','flight-airline').find('span').get_text()
            data['dept_time'] = flight.find(class_='depart-box').find(class_='time').get_text()
            data['dept_port'] = flight.find(class_='depart-box').find(class_='airport').find('span').get_text()
            data['dest_time'] = flight.find(class_='arrive-box').find("div", class_='time').get_text()
            data['dest_port'] = flight.find(class_='arrive-box').find(class_='airport').find('span').get_text()
            data['price'] = flight.find(class_='price-box').find('div').get_text()
            
            # transfer data
            arrow_box = flight.find(class_='arrow-box')
            transfer = [] 
            for transfer_info in arrow_box.find_all(class_='transfer-info'):
                transfer.append(transfer_info.get_text())
            data['transfer'] = transfer
            data['transfer_times'] = len(transfer)
            
            reminder = flight.find(class_='remind')
            if reminder is not None:
                data['remind'] = reminder.get_text()
            else:
                data['remind'] = 'No Reminder'
                
            # utf-8 encoding
            for item in data.items():
                if type(item) == 'string':
                    item.encode('utf-8')
                    
            if data not in flights:
                flights.append(data)
        
    return flights

def process_flight_data(flights):
    # processing data
    for date, data in flights.items():
        for flight in data:
            [h, m] = flight['dept_time'].split(':')
            dept_datetime = datetime.datetime.strptime(f"{date} {flight['dept_time']}","%Y-%m-%d %H:%M")
            [h, m] = flight['dest_time'][:5].split(':')
            d =  flight['dest_time'][ int(flight['dest_time'].find('+')) + 1 ]
            dest_datetime = dept_datetime + datetime.timedelta(days=int(d))
            dest_datetime = dest_datetime.replace(hour=int(h), minute=int(m))
    #        print(dept_datetime)fli
    #        print(dest_datetime)
            dt = dest_datetime - dept_datetime
            flight['duration'] = "{:4.2f}".format(dt.days * 24 + dt.seconds/3600)
            
def store_flights_pipeline(flights, file):
    """
    flights: dict of search result of a date, key is date
    results: list of dicts containing flight results
    flight: dict containing information for one flight
    """
    counter = 0
    with open(file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        head = False
        for date, results in flights.items():
            #writer.writerow([date])
            if not head:
                headers = [header for header in results[0].keys()]
                writer.writerow(headers)
                head = True
            for flight in results:
                result_row = []
                for __, data in flight.items():
                    result_row.append(data)
                writer.writerow(result_row)
                counter += 1
    print(f"{counter} records of flights have been stored into {file}")


            
            
    
    
#    # storing data with database
#    engine = db.create_engine('sqlite:///flights.db')
#    connection = engine.connect()
#    metadata = db.Metadata()
    
        
if __name__ == '__main__':

    date = datetime.datetime.today()
    
    # initialize driver (headless chrome option)
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=chrome_options)
    
    dept_date = datetime.datetime.strptime('2020-04-1', '%Y-%m-%d')
    dept_city = 'London'
    dest_city = 'Guangzhou'
    
    dept_code = None
    dest_code = None # IATA code for destination airport, if None program will look it up from wikipedia
    dept_code = dept_code or _iata_code(dept_city)
    dest_code = dest_code or _iata_code(dest_city)
    
    flex_day_range = 30
    date_list = [dept_date + datetime.timedelta(days=x) for x in range(flex_day_range)]
    filename = "ctrip_search_on_"+ date.strftime("%Y-%m-%d") + "_from_" + dept_city + '_to_' + dest_city  + '.csv'
    flights = {}
    
    for date in date_list:
        print(f"Searching for flight on {date}")
        driver.get(gen_query_url(dept_code,dest_code, date.strftime('%Y-%m-%d')))
        # dismiss alert
        try:    
            elem = WebDriverWait(driver,10).until(
                    EC.presence_of_element_located((By.XPATH, '//a[@class="btn"]'))
            )
            elem.click()
        except TimeoutException:
            pass
        except NoSuchElementException:
            pass
        except ElementClickInterceptedException:
            time.sleep(2)
            elem.click()
            
        finally:
            pass
        
        # sort from lowest price
        try:    
            elem = WebDriverWait(driver,10).until(
                    EC.element_to_be_clickable((By.XPATH, '//li[@u_key="sort_header_entry" and contains(@class, "ticket-price")]'))
            )
            elem.click()
            #driver.implicitly_wait(10)
        except ElementClickInterceptedException:
            continue
        
        finally: 
            try:
                elem = WebDriverWait(driver,10).until(
                    EC.presence_of_all_elements_located((By.XPATH, '//div[@u_key="flight_detail"]'))
                )
            finally:
                flights[date.strftime('%Y-%m-%d')] = parse_page(driver)
        print(f"{len(flights[date.strftime('%Y-%m-%d')])} flights found on this date")
        
    process_flight_data(flights)
    store_flights_pipeline(flights, filename)
    
#    for key, data in flights.items():
#        print('----------------------------------------------------')
#        print('Flight date on ', key)
#        print(data)
       
#