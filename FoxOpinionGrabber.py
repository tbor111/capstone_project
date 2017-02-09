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
    soup = BeautifulSoup(html, 'html.parser')
    results = soup.find_all('article')
    print response.status_code
    return results

def make_dict(results):
    # create lists
    links = []
    titles = []
    sections = []
    authors = []
    bodies = []
    dates = []

    # get link
    for x in results:
        h1 = x.find('h1')
        link = h1.find('a')['href']
        links.append(link)

    for link in links:
        url = 'http://www.foxnews.com' + link
        response = requests.get(url)
        html = response.content
        new_soup = BeautifulSoup(html, 'html.parser')

        # get title
        title = new_soup.find('title').text.strip().replace('| Fox News', '')
        titles.append(title)

        # get date
        date = new_soup.find('meta', attrs = {'name': 'dc.date'})['content']
        dates.append(date)

        # get author
        author_div = new_soup.find('div', attrs = {'class': 'm author'})
        try:
            author = author_div.find('img')['alt']
        except AttributeError:
            author = "None found"
        authors.append(author)

        # get body
        all_p = ''
        body = new_soup.find('div', attrs = {'class': 'article-text'})
        paragraphs = body.find_all('p')
        for p in paragraphs:
            p = p.text.strip().encode('ascii','ignore')
            all_p = all_p + p
        bodies.append(all_p)

        # get section
        section = new_soup.find('h2', attrs = {'class': 'section-title'}).text.strip()
        sections.append(section)

    my_dict = {
        'title': titles, 'link': links, 'author': authors, 'body': bodies,
        'section': sections, 'date': dates
    }
    return my_dict

def make_df(my_dict):
    df = pd.DataFrame(my_dict)
    return df

def main():
    url = 'http://foxnews.com/opinion.html'
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
