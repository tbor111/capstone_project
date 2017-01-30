#!/usr/bin/env python

from bs4 import BeautifulSoup
import cookielib
import urllib2
import requests

def get(url):
    #request = urllib2.Request(url)
    #response = urllib2.urlopen(url) #request
    response = requests.get(url)
    html = response.content
    soup = BeautifulSoup(html.decode('utf-8', 'ignore'), 'html.parser')




    #soup = BeautifulSoup(urlopen(url).read().decode('utf-8', 'ignore'), 'html.parser')
    results = soup.find_all('div', attrs = {'class': 'story-body'})
    return results
