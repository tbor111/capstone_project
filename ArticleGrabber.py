#!/usr/bin/env python

import sys
import pandas as pd
from bs4 import BeautifulSoup
import cookielib
import urllib2
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
import re

def make_soup(url):
    #request = urllib2.Request(url)
    #response = urllib2.urlopen(url) #request
    response = requests.get(url)
    html = response.content
    soup = BeautifulSoup(html.decode('utf-8', 'ignore'), 'html.parser')

    #soup = BeautifulSoup(urlopen(url).read().decode('utf-8', 'ignore'), 'html.parser')
    results = soup.find_all('div', attrs = {'class': 'story-body'})
    print response.status_code
    return results

def make_dict(results):

    # initialize lists
    titles = []
    dates = []
    links = []
    full_texts = []
    authors = []
    sections = []

    # scrape results into lists
    for x in results:
        # get link
        link = x.find('a')['href']
        # set regex to eliminate interactive features
        match = re.search('^https://www.nytimes.com/20', link)
        if match:
            links.append(link)

    # resoup it
    for link in links:
        all_p = ''
        cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        new_soup = BeautifulSoup(opener.open(link).read().decode('utf-8', 'ignore'), 'html.parser')
        # get the article content
        body = new_soup.find_all('p', attrs = {'class': 'story-body-text story-content'})
        for p in body:
            new_p = p.text.strip()
            all_p = all_p + new_p
        full_texts.append(all_p)

        # get titles
        title = new_soup.find('meta', attrs = {'property': 'og:title'})['content']
        titles.append(title)

        # get authors
        author = new_soup.find('meta', attrs = {'name': 'author'})['content']
        authors.append(author)

        # get sections
        section = new_soup.find('meta', attrs = {'name': 'CG'})['content']
        sections.append(section)

        # get dates
        date = new_soup.find('meta', attrs = {'name': 'pdate'})['content']
        dates.append(date)

    data_dict = {
        'title': titles, 'link': links, 'author': authors, 'body': full_texts,
        'section': sections, 'date': dates
    }
    return data_dict

def make_dataframe(data_dict):
    df = pd.DataFrame(data_dict)
    return df


def main():
    url = raw_input('> ')
    results = make_soup(url)
    data_dict = make_dict(results)
    df = make_dataframe(data_dict)
    # create engine
    engine = create_engine('postgresql://teresaborcuch@localhost:5433/capstone')
    Session = sessionmaker(bind=engine)
    session = Session()
    # clear staging
    clear_staging_query = 'DELETE FROM nyt_staging *;'
    engine.execute(clear_staging_query)
    session.commit()
    # add df to staging
    df.to_sql('nyt_staging', engine, if_exists = 'append', index = False)
    # move unique rows from staging to ny_times
    move_unique_query = '''
    INSERT INTO ny_times (title, date, author, body, link, section)
    SELECT title, date, author, body, link, section
    FROM nyt_staging
    WHERE NOT EXISTS (SELECT title, date, author, body, link, section
    FROM ny_times
    WHERE ny_times.title = nyt_staging.title);
    '''
    engine.execute(move_unique_query)
    session.commit()
    session.close()
    print "Done"

if __name__ == "__main__":
    main()
