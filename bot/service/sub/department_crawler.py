from bot.util.departments import years, semesters
from bot.config import driver_path, target_url, options, MYSQL_DATABASE_URI
from selenium import webdriver
from time import sleep
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy import create_engine
from bot.util.xpaths import searchOption, contentTable, contentTableBodyId
from bot.util.columns import columns

def lxml_to_dataframe(year, semester, html, df):
  # 소분류 상위 div 추출
  soup = BeautifulSoup(html, 'lxml')
  departments = soup.find("div", id='WD91-scrl')
  departments_div = departments.find_all('div')
  
  # 소분류(학부) text 추출
  department_text_list = []
  department_id_list = []
  for idx, element in enumerate(departments_div):
      if idx > 0 :
          department_text_list.append(element.text)
          department_id_list.append(element.attrs['id'])
  text_col_name = 's{}_{}_text'.format(year, semester)
  id_col_name = 's{}_{}_id'.format(year, semester)
  
  df = pd.concat([df,pd.Series(department_text_list, name=text_col_name)],axis=1)
  df = pd.concat([df,pd.Series(department_id_list, name=id_col_name)],axis=1)
  #df[text_col_name] = department_text_list
  #df[id_col_name] = department_id_list
  print('data length : {}'.format(len(department_text_list)))
  return df

def Crawler():
  year_list = ['20','21']
  semester_list = ['1','s','2','w']
  df = pd.DataFrame()
  
  for i in range(7):
    print('{} year, {} semester crawling start.'.format(year_list[i//4], semester_list[i%4]))
    driver = webdriver.Chrome(executable_path=driver_path, options=options)
    driver.get(target_url)
    driver.implicitly_wait(30)
    print('Entering Target Page...')
    
    year_xpath = '//*[@id="{}"]'.format(years[year_list[i//4]])
    semester_xpath = '//*[@id="{}"]'.format(semesters[semester_list[i%4]])
    
    # 개설년도 Form 선택 후 클릭
    sleep(0.5)
    driver.find_element_by_xpath('//*[@id="WD25"]').click()

    # 개설년도 클릭
    sleep(0.5)
    driver.find_element_by_xpath(year_xpath).click()



    # 학기 Form 선택 후 클릭
    sleep(0.5)
    driver.find_element_by_xpath('//*[@id="WD4A"]').click()

    # 학기 선택
    sleep(0.5)
    driver.find_element_by_xpath(semester_xpath).click()
    # WD4C WD4D WD4E WD4F

    # 소속구분 Form 선택 후 클릭
    sleep(0.5)
    driver.find_element_by_xpath('//*[@id="WD7E"]').click()

    # 학부 클릭
    sleep(0.5)
    driver.find_element_by_xpath('//*[@id="WD80"]').click()

    print('Resource fetching...')
    element = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="WD91-scrl"]/div/div')))
    print('Resource fetching done')
    print('Saving data...')

    # 스크래핑
    html = driver.page_source
    df = lxml_to_dataframe(year_list[i//4], semester_list[i%4], html, df)
    print('{} year, {} semester crawling done.'.format(year_list[i//4], semester_list[i%4]))
    print(' ')
    driver.close()
    
  print(' ')
  print('Saving data to DB...')
  engine = create_engine(MYSQL_DATABASE_URI, encoding='utf-8')
  conn = engine.connect()
  df.to_sql(name='departments', if_exists='replace', con=engine, index=True, index_label='id')
  conn.close()
  print('Total Logic Done :)')
  return True