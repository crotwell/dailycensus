#!/usr/bin/python3
import datetime
from common import *

testing=True

loadPeople(config)
today=todayAsStr()
makeCSV(today)
