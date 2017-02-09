#!/usr/bin/env python

from sqlalchemy import create_engine
import timestring
import psycopg2
import pandas as pd

class ArticleData():
    def __init__(self): pass

    def call(self):
        engine = create_engine('postgresql://teresaborcuch@localhost:5433/capstone')

        # get data from all three tables and add source column
        query1 = "SELECT DISTINCT ON(title) title, date, body, section FROM fox_news;"
        fox_data = pd.read_sql(query1, engine)
        fox_data['source'] = ['Fox']*len(fox_data)

        query2 = "SELECT DISTINCT ON(title) title, date, body, section FROM ny_times;"
        nyt_data = pd.read_sql(query2, engine)
        nyt_data['source'] = ['NYT'] * len(nyt_data)

        query3 = "SELECT DISTINCT ON(title) title, date, body, section FROM washington_post;"
        wp_data = pd.read_sql(query3, engine)
        wp_data['source'] = ['WP']*len(wp_data)

        # merge the dataframes into one big one
        data = pd.concat([nyt_data, fox_data, wp_data], axis = 0)

        # drop those with empty or suspiciously short bodies
        problem_rows = []
        for i, row in data.iterrows():
            try:
                if len(row[2]) < 200:
                    problem_rows.append(row.name)
            except TypeError:
                problem_rows.append(row.name)

        data = data.drop(data.index[problem_rows])

        # fix the dates
        new_dates = []
        for x in data['date']:
            if type(x) == int:
                x = str(x)
                x = timestring.Date(x[:4] + '-' + x[4:6] + '-' + x[6:8])
                new_dates.append(x)
            else:
                new_dates.append(x)
        data['date'] = new_dates

        # create the condensed section
        def condense_section(x):
            if 'world' in x:
                section = 'world'
            elif 'pinion' in x:
                section = 'opinion'
            elif 'business' in x:
                section = 'business'
            elif ('politic' in x) or ('us' in x):
                section = 'politics'
            elif ('entertain' in x) or ('art' in x) or ('theater' in x) or ('book' in x) or ('movie' in x) or ('travel' in x) or ('fashion' in x) or ('style' in x) or ('dining' in x):
                section = 'entertainment'
            elif 'sport' in x:
                section = 'sports'
            elif ('health' in x) or ('science' in x) or ('well' in x):
                section = 'sci_health'
            elif('tech' in x):
                section = 'technology'
            elif ('education' in x):
                section = 'education'
            else:
                section = 'other'
            return section

        data['condensed_section'] = [condense_section(x) for x in data['section']]

        return data
