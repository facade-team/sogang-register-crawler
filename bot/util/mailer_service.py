import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def mail_sender(to,data):
  smtp = smtplib.SMTP_SSL('smtp.gmail.com', 465)
  smtp.ehlo()      # say Hello
  smtp.login('sonicdx886@gmail.com', 'rlatmddn52!')
  
  subject_name = data['data']['subject_name']

  msg_str = '{} 교과목 정보가 업데이트 되었습니다.<br />'.format(subject_name)
  for i in data['data']['data']:
    msg_str += '<strong>"{}"</strong> 항목에 대해 <strong>"{}"</strong> 에서, <strong>"{}"</strong> 으로 변경되었습니다.<br />'.format(i['column'], i['before'], i['after'])

  print(msg_str)
  msg = MIMEText(msg_str, 'html')
  
  data = MIMEMultipart()
  
  data['From'] = 'sonicdx886@gmail.com'
  data['To'] = to
  Subject_str = '[서강신청] {} 정보가 업데이트 되었습니다'.format(subject_name)
  data['Subject'] = Subject_str
  data.attach(msg)
  
  smtp.sendmail('sonicdx886@gmail.com', to, data.as_string())

  smtp.quit()
  print('Mail has sent to {}'.format(to))
  return True