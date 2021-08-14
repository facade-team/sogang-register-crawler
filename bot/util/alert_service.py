import pandas as pd
import pymysql
from bot.config import host_name, username, password, database_name
from sqlalchemy import create_engine
from bot.util.mailer_service import mail_sender

query_cols = '학년도, 학기, 소속, 학과, 과목번호, 분반, 과목명, 강의계획서, 학점, 수업시간_강의실, 시간, 교수진, 수강생수, 영어강의, 중국어강의, 공학인증, 국제학생, Honors과목, 홀짝구분, 승인과목, 시험일자, 수강대상, 권장학년, 수강신청_참조사항, 과목_설명, 비고, subject_id, 대면여부, 강의언어'
query_cols_list = query_cols.split(', ')

def search_user_subject_table():
  engine = create_engine('mysql+pymysql://user:password@docker-mysql-test.cpabptw8fwxo.us-east-2.rds.amazonaws.com:3306/sogang_register?charset=utf8', encoding='utf-8')
  conn = engine.connect()
  SQL = "SELECT * FROM user_subject"
  r = conn.execute("SELECT * FROM user_subject")
  u_s_res = []
  for e in r:
      u_s_res.append(e)
  conn.close()
  return u_s_res


def send_mail(res_list):
  print(res_list)
  print('Changed data length : '.format(len(res_list)))
  u_s_list = search_user_subject_table()
  
  email_list = []
  for res in res_list:
      for elem in u_s_list:
          if elem[2] == res['subject_id']:
              data = {
                  'email' : elem[1],
                  'data' : res
              }
              email_list.append(data)
  
  for elem in email_list:
    mail_sender(elem['email'], elem)
  
  return True

def make_changed_data_list(crawled_df, db_df):
  res_list = []
  #new_subject_ids = crawled_df['subject_id'][~crawled_df['subject_id'].isin(db_df['subject_id'])].values.tolist()
  crawled_df_drop_indice = crawled_df['subject_id'][~crawled_df['subject_id'].isin(db_df['subject_id'])].index.values.tolist()
  crawled_df = crawled_df.drop(crawled_df_drop_indice).reset_index(drop=True)
  
  db_df_drop_indice = db_df['subject_id'][~db_df['subject_id'].isin(crawled_df['subject_id'])].index.values.tolist()
  db_df = db_df.drop(db_df_drop_indice).reset_index(drop=True)
  
  total_length = len(db_df.compare(crawled_df))
  for row_idx in range(total_length):
      index_length = len(db_df.compare(crawled_df).iloc[row_idx,:][db_df.compare(crawled_df).iloc[row_idx,:].notna()].index) // 2
      subject_id = db_df.loc[row_idx, 'subject_id']
      suject_name = db_df.loc[row_idx, '과목명']
      professor_name = db_df.loc[row_idx, '교수진']
      data_list = []
      for diff_idx in range(index_length):
          column_name = db_df.compare(crawled_df).iloc[row_idx,:][db_df.compare(crawled_df).iloc[row_idx,:].notna()].index[diff_idx*2][0]
          before = db_df.compare(crawled_df).iloc[row_idx,:][db_df.compare(crawled_df).iloc[row_idx,:].notna()][diff_idx*2]
          after = db_df.compare(crawled_df).iloc[row_idx,:][db_df.compare(crawled_df).iloc[row_idx,:].notna()][diff_idx*2+1]
          
          if before == '\xa0' or (type(before) == str and before.isspace()):
              before = ''
          if after == '\xa0' or (type(after) == str and after.isspace()):
              after = ''
          data = {
              'column': column_name,
              'before' : before,
              'after' : after
          }
          data_list.append(data)

      res_elem = {
          'subject_id' : subject_id,
          'subject_name' : suject_name,
          'professor_name' : professor_name,
          'data' : data_list
      }
      res_list.append(res_elem)
  return res_list

def fetch_data_from_db():
  conn = pymysql.connect(
      host=host_name,
      port=3306,
      user=username,
      passwd=password,
      db=database_name,
      charset='utf8'
  )
  SQL = "SELECT {} FROM s21_2;".format(query_cols)
  db_df = pd.read_sql(sql=SQL, con=conn)
  conn.close()
  return db_df

def compare_data(df):
  crawled_df = df.loc[:, query_cols_list]
  db_df = fetch_data_from_db()
  res_list = make_changed_data_list(crawled_df, db_df)
  send_mail(res_list)
  return True