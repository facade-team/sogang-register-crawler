from bot.util.departments import years, semesters
from bot.config import driver_path, target_url, options, MYSQL_DATABASE_URI,server_driver_path
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
from bot.util.departments import departments, departments_text_list

days = []
start_time = []
end_time = []
classrooms = []

def lxmlToDataframe(index, html, isTotal, year, semester, mid_df):
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
  print('Data Length : ' + str(len(crawled_data[0])))
  
  df = pd.DataFrame()
  
  for i in range(26):
    df[columns[i]] = crawled_data[i]
  
  subject_ids = []
  for i in range(len(crawled_data[0])):
      subject_ids.append(year+'-'+semester+'-'+crawled_data[4][i]+'-'+crawled_data[5][i])
  
  if isTotal:
    df['subject_id'] = subject_ids
    df['department'] = ''
    return df
  else:
    for i in range(len(subject_ids)):
      if mid_df[mid_df['subject_id'] == subject_ids[i]]['department'].values == '':
        mid_df.loc[mid_df['subject_id'] == subject_ids[i],'department'] = departments[departments_text_list[index]]
      else:
        mid_df.loc[mid_df['subject_id'] == subject_ids[i],'department'] += ' {}'.format(departments[departments_text_list[index]])
    print('department id : {}'.format(departments[departments_text_list[index]]))
    return mid_df


def split_day_time_classroom(x):
    arr = x.split(" ")
    if arr[0] == '' or arr[0] == '\xa0':
        days.append('')
        start_time.append('')
        end_time.append('')
        classrooms.append('')
    else:
        days.append(arr[0])
        start_end_time = arr[1].split('~')
        start_time.append(start_end_time[0])
        end_time.append(start_end_time[1])
        if len(arr) == 3 and arr[2] != '':
            classrooms.append(arr[2])
        else:
            classrooms.append('')

def preprocessor(df):
  '''
  일부 컬럼 추가 및 수정을 위한 데이터 전처리기
  1. 학점 Int로 변형
  2. 수업 요일, 시작시간, 종료시간, 강의실 분리
  3. 대면 여부 추가
  4. 강의 언어 추가
  '''
  
  # 1. 학점 Int로 변형
  df.loc[:, '학점'] = df.loc[:, '학점'].map(lambda x : int(float(x)) if x in ['1.0', '2.0', '3.0'] else 0)
  
  # 2. 수업 요일, 시작시간, 종료시간, 강의실 분리
  df['수업시간_강의실'].map(lambda x : split_day_time_classroom(x))
  df['요일'] = days
  df['시작시간'] = start_time
  df['종료시간'] = end_time
  df['강의실'] = classrooms
  
  # 3. 대면 여부 추가
  df['대면여부'] = '미정'
  df.loc[df['비고'].map(lambda x : x.startswith('[비대면]')), '대면여부'] = '비대면'
  df.loc[df['비고'].map(lambda x : x.startswith('[대면]')), '대면여부'] = '대면'
  
  # 4. 강의 언어 추가
  df['강의언어'] = '한국어'
  df.loc[df['영어강의'] == 'O', '강의언어'] = '영어'
  df.loc[df['중국어강의'] == 'O', '강의언어'] = '중국어'
  
  # 5. 비고 에서 [대면], [비대면] 제거
  df.loc[:, '비고'] = df['비고'].map(lambda x: x.replace("[대면]", ""))
  df.loc[:, '비고'] = df['비고'].map(lambda x: x.replace("[비대면]", ""))
  df.loc[:, '비고'] = df['비고'].map(lambda x: x[1:] if len(x) > 0 and x[0] == ' ' else x)
  return df


def set_departments(year_xpath, semester_xpath, department_text_list, department_id_list, year, semester, df):
  # print('Sub Crawling start')
  for idx, department in enumerate(department_text_list):
    start = time.time()
    print(' ')
    print('Processing step [ {} / {} ]'.format(idx+1, len(department_text_list)))
    print('{} crawling start'.format(department))
    department_xpath = '//*[@id="{}"]'.format(department_id_list[idx])
    driver = webdriver.Chrome(executable_path=server_driver_path, options=options)
    driver.get(target_url)
    print('Entering Target Page...')
    driver.implicitly_wait(30)
    
    # 개설년도 Form 선택 후 클릭
    sleep(1.0)
    driver.find_element_by_xpath('//*[@id="WD25"]').click()

    # 개설년도 클릭
    sleep(1.0)
    driver.find_element_by_xpath(year_xpath).click()



    # 학기 Form 선택 후 클릭
    sleep(2)
    driver.find_element_by_xpath('//*[@id="WD4A"]').click()

    # 학기 선택
    sleep(0.5)
    driver.find_element_by_xpath(semester_xpath).click()
    # WD4C WD4D WD4E WD4F
    
    
    # 대분류 Form 클릭
    sleep(2)
    driver.find_element_by_xpath(searchOption['대분류']).click()

    # 학부 클릭
    sleep(0.5)
    driver.find_element_by_xpath(searchOption['학부']).click()
    # Wait for department list
    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, '//*[@id="WD91-scrl"]/div/div')))

    # 배경 클릭
    sleep(0.5)
    driver.find_element_by_xpath(searchOption['배경']).click()


    # 소분류 Form 클릭
    sleep(1.5) 
    driver.find_element_by_xpath(searchOption['소분류']).click()
    
    # 소분류 선택
    sleep(0.5)
    driver.find_element_by_xpath(department_xpath).click()

    # 검색 클릭
    sleep(1.0)
    driver.find_element_by_xpath(searchOption['검색']).click()
    
    print('Resource fetching...')
    html = None
    try:
      WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, contentTable)))
      print('Resource fetching done')
      print('Saving data...')
      
      html = driver.page_source
      df = lxmlToDataframe(idx, html, isTotal=False, year=year, semester=semester, mid_df=df)
      print("{} crawling done".format(department))
    except:
      print('Resource fetching done. Nothing fetched.')
    finally:
      driver.close()
      
      # 중간 크롤링 결과 임시 테이블에 저장
      print('Saving data to DB...')
      engine = create_engine(MYSQL_DATABASE_URI, encoding='utf-8')
      conn = engine.connect()
      table_name = 's{}_{}_t'.format(year, semester)
      SQL = "SELECT * FROM {}".format(table_name)
      db_df = pd.read_sql(SQL, conn) 
      db_df.loc[:, 'department'] = df.loc[:, 'department']
      db_df.iloc[:, 1:].to_sql(name=table_name, if_exists='replace', con=conn, index=True, index_label='id')
      conn.close()
      print('Saving done')
      print("WorkingTime: {} sec".format(time.time()-start))
      sleep(1)
  return df

def get_departments(html):
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
  return department_text_list, department_id_list

def Crawler():
  year_list = ['18','19']
  semester_list = ['1','s','2','w']
  
  for i in range(8):
    global days
    global start_time
    global end_time
    global classrooms
    
    days = []
    start_time = []
    end_time = []
    classrooms = []
    
    year = year_list[i//4]
    semester = semester_list[i%4]
    
    start = time.time()
    department_text_list = []
    department_id_list = []
    print('{} year, {} semester crawling start.'.format(year_list[i//4], semester_list[i%4]))
    driver = webdriver.Chrome(executable_path=server_driver_path, options=options)
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
    
    # 검색 클릭
    sleep(1.5)
    driver.find_element_by_xpath('//*[@id="WDB4"]').click()


    print('Resource fetching...')
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, contentTable)))
    print('Resource fetching done')
    print('Saving data...')

    # 스크래핑
    html = driver.page_source
    department_text_list, department_id_list = get_departments(html)
    result_df = lxmlToDataframe(0, html, isTotal=True, year=year_list[i//4], semester=semester_list[i%4], mid_df=None)
    print('{} year, {} semester crawling done.'.format(year_list[i//4], semester_list[i%4]))
    driver.close()
    
    # 몇가지 컬럼 전처리
    result_df_ = preprocessor(result_df)
    
    # 초반 크롤링 결과 임시 테이블에 저장
    print('Saving data to DB...')
    engine = create_engine(MYSQL_DATABASE_URI, encoding='utf-8')
    conn = engine.connect()
    table_name = 's{}_{}_t'.format(year_list[i//4], semester_list[i%4])
    result_df_.to_sql(name=table_name, if_exists='replace', con=conn, index=True, index_label='id')
    conn.close()
    print('Saving done')
    
    # 소분류(학부) 컬럼을 위한 추가 크롤링
    total_result_table = set_departments(year_xpath, semester_xpath, department_text_list, department_id_list, year, semester, result_df_)
    
    print(' ')
    print('Saving data to DB...')
    engine = create_engine(MYSQL_DATABASE_URI, encoding='utf-8')
    conn = engine.connect()
    
    SQL = "SELECT * FROM {}".format(table_name)
    total_db = pd.read_sql(SQL, conn)
    total_table_name = 's{}_{}'.format(year_list[i//4], semester_list[i%4])
    total_db.iloc[:, 1:].to_sql(name=total_table_name, if_exists='replace', con=engine, index=True, index_label='id')
    conn.close()
    print('s{}_{} Logic Done :)'.format(year_list[i//4], semester_list[i%4]))
    print("s{}_{} WorkingTime: {} sec".format(year_list[i//4], semester_list[i%4], time.time()-start))
    print(" ")
  print('Total Logic Done :)')
  return True