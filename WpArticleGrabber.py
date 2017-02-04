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
    #url = 'https://www.washingtonpost.com/politics'
    response = requests.get(url)
    html = response.content
    soup = BeautifulSoup(html.decode('utf-8', 'ignore'), 'html.parser')
    results = soup.find_all('h3', attrs = {'class': ''})
    print response.status_code
    return results

def make_dict(results):
# initialize lists
    titles = []
    dates = []
    links = []
    bodies = []
    authors = []
    sections = []

    for x in results:
        link = x.find('a')['href']
        match1 = re.search('^https://www.washingtonpost.com/video', link)
        match2 = re.search('story.html', link)
        if not match1 and match2:
            links.append(link)

    # resoup link
    for link in links:
        response = requests.get(link)
        html = response.content
        new_soup = BeautifulSoup(html.decode('utf-8', 'ignore'), 'html.parser')

        # get title
        title = new_soup.find('title').text.strip().replace(' - The Washington Post','')
        titles.append(title)

        # get body
        all_p = ''
        body = new_soup.find('article', itemprop = 'articleBody')
        paragraphs = body.find_all('p')
        for p in paragraphs:
            new_p = p.text.strip().encode('ascii', 'ignore')
            all_p = all_p + new_p
        bodies.append(all_p)

        # get author
        author = ''
        author_list = new_soup.find_all('span', attrs = {'itemprop': 'name'})
        for a in author_list:
            a = a.text.strip()
            author = author + ',' + a
        authors.append(author)

        # get date
        date = new_soup.find('span', attrs = {'itemprop': 'datePublished'})['content']
        dates.append(date)

        # get section
        scripts = new_soup.find_all('script')
        pattern = 'var commercialNode'

        for script in scripts:
            #if (pattern.match(str(script.string))):
            match = re.search(pattern, str(script))
            if match:
                text = script.text.strip()
                text_list = text.split(';')
                for x in text_list:
                    match = re.search(pattern, x)
                    if match:
                        section = x.replace('var commercialNode=', '').replace('"','')


        sections.append(section)

        data_dict = {
            'title': titles, 'link': links, 'author': authors,
            'body': bodies, 'section': sections, 'date': dates
        }
    return data_dict

def make_df(data_dict):
    df = pd.DataFrame(data_dict)
    return df

def main():
    section_list = [
    'world','national','politics','entertainment',
    'business', 'lifestyle','opinions','sports']
    for x in section_list:
        url = 'http://www.washingtonpost.com/' + x
    #url = raw_input('> ')
        results = make_soup(url)
        data_dict = make_dict(results)
        df = make_df(data_dict)
        # create engine
        engine = create_engine('postgresql://teresaborcuch@localhost:5433/capstone')
        Session = sessionmaker(bind=engine)
        session = Session()
        # clear staging
        clear_staging_query = 'DELETE FROM wp_staging *;'
        engine.execute(clear_staging_query)
        session.commit()
        # add df to staging
        df.to_sql('wp_staging', engine, if_exists = 'append', index = False)
        # move unique rows from staging to ny_times
        move_unique_query = '''
        INSERT INTO washington_post (title, date, author, body, link, section)
        SELECT title, date, author, body, link, section
        FROM wp_staging
        WHERE NOT EXISTS (SELECT title, date, author, body, link, section
        FROM washington_post
        WHERE washington_post.title = wp_staging.title);
        '''
        engine.execute(move_unique_query)
        session.commit()
        session.close()
        print "Done"

if __name__ == "__main__":
    main()
