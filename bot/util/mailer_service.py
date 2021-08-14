from bot.config import email, email_pw
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def mail_sender(to,data):
  smtp = smtplib.SMTP_SSL('smtp.gmail.com', 465)
  smtp.ehlo()      # say Hello
  smtp.login(email, email_pw)
  
  subject_name = data['data']['subject_name']
  professor_name = data['data']['professor_name']
  subject_id = data['data']['subject_id'][5:]
  
  if professor_name == '' or professor_name == None or professor_name.isspace():
    title_substring = '{}({})'.format(subject_name, subject_id)
  else:
    title_substring = '{}({}/{})'.format(subject_name, subject_id, professor_name)
  msg_str = '{} 교과목 정보가 업데이트 되었습니다.<br />'.format(title_substring)
  for i in data['data']['data']:
    msg_str += '<strong>"{}"</strong> 항목에 대해 <strong>"{}"</strong> 에서, <strong>"{}"</strong> 으로 변경되었습니다.<br />'.format(i['column'], i['before'], i['after'])

  print(msg_str)
  msg = MIMEText(msg_str, 'html')
  
  data = MIMEMultipart()
  
  data['From'] = email
  data['To'] = to
  Subject_str = '[서강신청] {} 정보가 업데이트 되었습니다'.format(title_substring)
  data['Subject'] = Subject_str
  data.attach(msg)
  
  smtp.sendmail(email, to, data.as_string())

  smtp.quit()
  print('Mail has sent to {}'.format(to))
  return True