#!/usr/bin/env python
# encoding=utf-8

from bot.service.current_semester import Crawler
import time

if __name__ == '__main__':
  start = time.time()
  Crawler()
  print("WorkingTime: {} sec".format(time.time()-start))
