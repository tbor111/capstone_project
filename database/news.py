#!/usr/bin/env python

# takes a nytimes section url, collects data and inserts into db
import sys
import pandas as pd
import news_df
import soup
import news_dict
from sqlalchemy import create_engine
from bs4 import BeautifulSoup
import cookielib
import urllib2
#from urllib import urlopen

def get(url):
    engine = create_engine('postgresql://teresaborcuch@localhost:5433/capstone')
    my_soup = soup.get(url)
    my_news_dict = news_dict.get(my_soup)
    df = news_df.get(my_news_dict)
    df.to_sql('nytimes', engine, if_exists = 'append', index = False)
