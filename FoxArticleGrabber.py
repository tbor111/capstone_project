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
    response = requests.get(url)
    html = response.content
    soup = BeautifulSoup(html.decode('utf-8', 'ignore'), 'html.parser')
    results = soup.find_all('li', attrs = {'class': 'nav-column'})
    print response.status_code
    return results

def make_dict(results):
    # create lists to hold results
    links = []
    titles = []
    dates = []
    sections = []
    bodies = []
    authors = []

    # get link
    for x in results:
        link = x.find('a')['href']
        links.append(link)

    # re-soup it
    for link in links:
        match = re.search('^http://', link)
        if not match:
            link = 'http://insider.foxnews.com' + link
        response = requests.get(link)
        html = response.content
        new_soup = BeautifulSoup(html.decode('utf-8', 'ignore'), 'html.parser')

        # get title
        title = new_soup.find('title').text.strip()
        titles.append(title)

        # get date
        date = new_soup.find('meta', attrs = {'name': 'dc.date'})['content']
        dates.append(date)

        # get section
        section = new_soup.find('meta', attrs = {'name': 'dc.subject'})['content']
        sections.append(section)

        # get author
        author = new_soup.find('span', attrs = {'id': 'author'}).text.strip()
        authors.append(author)

        # get body
        all_p = ''
        body = new_soup.find('div', attrs = {'class': 'articleBody'})
        paragraphs = body.find_all('p')
        for p in paragraphs:
            p = p.text.strip().encode('ascii','ignore')
            all_p = all_p + p
        bodies.append(all_p)

        my_dict = {
        'title': titles, 'link': links, 'author': authors, 'body': bodies,
        'section': sections, 'date': dates
    }
    return my_dict

def make_df(my_dict):
    df = pd.DataFrame(my_dict)
    return df

def main():
    url = 'http://insider.foxnews.com/latest'
    results = make_soup(url)
    data_dict = make_dict(results)
    df = make_df(data_dict)

    engine = create_engine('postgresql://teresaborcuch@localhost:5433/capstone')
    Session = sessionmaker(bind=engine)
    session = Session()
    # clear staging
    clear_staging_query = 'DELETE FROM fox_staging *;'
    engine.execute(clear_staging_query)
    session.commit()
    # add df to staging
    df.to_sql('fox_staging', engine, if_exists = 'append', index = False)
    # move unique rows from staging to ny_times
    move_unique_query = '''
    INSERT INTO fox_news (title, date, author, body, link, section)
    SELECT title, date, author, body, link, section
    FROM fox_staging
    WHERE NOT EXISTS (SELECT title, date, author, body, link, section
    FROM fox_news
    WHERE fox_news.title = fox_staging.title);
    '''
    engine.execute(move_unique_query)
    session.commit()
    session.close()
    print "Done"

if __name__ == "__main__":
    main()
