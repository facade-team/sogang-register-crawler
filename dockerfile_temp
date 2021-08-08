FROM python:3.8

#ENV DEBIAN_FRONTEND=nointeractive

# Run
#RUN apt-get update
#RUN apt-get install -y wget gnupg gnupg2
# RUN wget http://zlib.net/zlib-1.2.8.tar.gz -O - | tar -xz
#RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
#RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
#RUN apt-get update
#RUN apt-get install -y google-chrome-stable
#RUN pip install xlrd
#RUN pip install pyvirtualdisplay
#RUN apt-get install xvfb

# Adding trusting keys to apt for repositories
#RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
# Adding Google Chrome to the repositories
#RUN sh -c 'echo "deb [arch=arm64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
# Updating apt to see and install Google Chrome
#RUN apt-get -y update
# Magic happens
#RUN apt-get install -y google-chrome-stable

# Install requirements
RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add source code
ADD bot /home/bot
ADD app.py /home
ADD requirements.txt /home
ADD driver /home/driver 

WORKDIR /home

# ENTRYPOINT
CMD ["/home/app.py"]
ENTRYPOINT ["python"]