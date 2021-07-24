from bot.config import driver_path, target_url, options, MYSQL_DATABASE_URI
from selenium import webdriver
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy import create_engine
from bot.util.xpaths import searchOption, departments, contentTable, contentTableBodyId
from bot.util.columns import columns

def lxmlToDataframe(departmentNumber, html, isTotal, mid_df):
  '''
  크롤링한 데이터를 스크래핑하여 DataFrame으로 저장
  '''
  soup = BeautifulSoup(html, 'lxml')
  res = soup.find("tbody", id=contentTableBodyId)
  trs = res.find_all('tr')
  
  crawled_data = [[] for _ in range(26)]
  
  for tr in trs:
    tds = tr.find_all('td')
    for idx, td in enumerate(tds):
        if not td.find('span') == None:
            crawled_data[idx].append(td.find('span').text)
        else:
            crawled_data[idx].append(' ')
  print('Crawled Data Length : ' + str(len(crawled_data[0])))
  
  df = pd.DataFrame()
  
  for i in range(26):
    df[columns[i]] = crawled_data[i]
  
  subject_ids = []
  for i in range(len(crawled_data[0])):
      subject_ids.append('21-2-'+crawled_data[4][i]+'-'+crawled_data[5][i])
  
  if isTotal:
    df['subject_id'] = subject_ids
    df['전인교육원'] = 0
    return df
  else:
    for i in range(len(subject_ids)):
      mid_df.loc[mid_df['subject_id'] == subject_ids[i], '전인교육원'] = departmentNumber+1
    print('Mid Check : '+str(mid_df['전인교육원'].unique()))
    return mid_df

def Crawler():
  '''
  학부 전체 테이블에 대해서 모든 정보를 크롤링 하는 함수
  '''
  print('Processing step [ 1 / 5 ]')
  print('Main Crawling start')
  driver = webdriver.Chrome(executable_path=driver_path, options=options)
  driver.get(target_url)
  driver.implicitly_wait(30)
  print('Entering Target Page...')
  
  # 대분류 Form 클릭
  sleep(0.5)
  driver.find_element_by_xpath(searchOption['대분류']).click()

  # 학부 클릭
  sleep(0.5)
  driver.find_element_by_xpath(searchOption['학부']).click()

  # 검색 클릭
  sleep(1.0)
  driver.find_element_by_xpath(searchOption['검색']).click()

  print('Resource fetching...')
  element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, contentTable)))
  print('Resource fetching done')
  print('Saving data...')

  # 스크래핑
  html = driver.page_source
  result_df = lxmlToDataframe(0, html, True, None)
  print('Main Crawling done.')
  driver.close()
  total_result_table = setDepartments(result_df)
  
  engine = create_engine(MYSQL_DATABASE_URI, encoding='utf-8')
  conn = engine.connect()
  total_result_table.to_sql(name='s21_2_t1', if_exists='replace', con=engine, index=False)
  conn.close()
  return True

def setDepartments(df):
  '''
  전인교육원에 속하는지 여부를 표시하기 위한 함수
  해당없음 : 0
  공통필수 : 1
  공통선택 : 2
  자유선택 : 3
  전공입문 : 4
  '''
  print('Sub Crawling start')
  for idx in range(4):
    print('------------------------')
    print('Processing step [ {} / 5 ]'.format(idx+2))
    driver = webdriver.Chrome(executable_path=driver_path, options=options)
    driver.get(target_url)
    driver.implicitly_wait(30)
    print('Entering Target Page...')
    
    # 대분류 Form 클릭
    sleep(0.5)
    driver.find_element_by_xpath(searchOption['대분류']).click()

    # 학부 클릭
    sleep(0.5)
    driver.find_element_by_xpath(searchOption['학부']).click()
    
    # 배경 클릭
    sleep(0.5)
    driver.find_element_by_xpath(searchOption['배경']).click()

    # 소분류 Form 클릭
    sleep(0.5)
    driver.find_element_by_xpath(searchOption['소분류']).click()
    
    # 소분류 선택 (전인교육원)
    sleep(0.5)
    driver.find_element_by_xpath(departments[idx]).click()

    # 검색 클릭
    sleep(1.0)
    driver.find_element_by_xpath(searchOption['검색']).click()
    
    print('Resource fetching...')
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, contentTable)))
    print('Resource fetching done')
    print('Saving data...')
    
    html = driver.page_source
    df = lxmlToDataframe(idx, html, isTotal=False, mid_df=df)
    driver.close()
    sleep(1)
  
  print('Total Logic Done :)')
  return df