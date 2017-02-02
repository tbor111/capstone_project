#!/usr/bin/env python

import pandas as pd
from sqlalchemy import create_engine

def get_df():
    engine = create_engine('postgresql://teresaborcuch@localhost:5433/capstone')
    query = "SELECT DISTINCT ON(title) title, date, author, body, link, section FROM ny_times;"
    data = pd.read_sql(query, engine)
    return data

def write_text(article_type, article_feature):
    f = open('/Users/teresaborcuch/capstone_project/{}.txt'.format(filename), 'w')
    for i, row in data.iterrows():
        if row[5] == 'opinion':
            f.write(row[0].encode('utf-8'))
            f.write('\n')
    return f

def make_cloud():
    text = open(f).read()
    wordcloud = WordCloud().generate(text)

    plt.imshow(wordcloud)
    plt.axis("off")
