#!/usr/bin/env python
from sqlalchemy import create_engine
from datetime import datetime
import psycopg2
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from nltk.sentiment.util import *
from nltk.corpus import sentiwordnet as swn
from nltk.tag.perceptron import PerceptronTagger

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
                x = (x[:4] + '-' + x[4:6] + '-' + x[6:8]).replace(' 00:00:00','')
                x = datetime.strptime(x, '%Y-%m-%d')
                new_dates.append(x)
            else:
                x = str(x).replace(' 00:00:00','')
                x = datetime.strptime(x, '%Y-%m-%d')
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
            elif ('politic' in x) or ('us' in x):
                section = 'politics'
            else:
                section = 'other'
            return section

        data['condensed_section'] = [condense_section(x) for x in data['section']]

        def compute_score(sentence):
            tagger = PerceptronTagger()
            taggedsentence = []
            sent_score = []
            taggedsentence.append(tagger.tag(sentence.split()))
            wnl = nltk.WordNetLemmatizer()
            for idx, words in enumerate(taggedsentence):
                for idx2, t in enumerate(words):
                    newtag = ''
                    lemmatizedsent = wnl.lemmatize(t[0])
                    if t[1].startswith('NN'):
                        newtag = 'n'
                    elif t[1].startswith('JJ'):
                        newtag = 'a'
                    elif t[1].startswith('V'):
                        newtag = 'v'
                    elif t[1].startswith('R'):
                        newtag = 'r'
                    else:
                        newtag = ''
                    if (newtag != ''):
                        synsets = list(swn.senti_synsets(lemmatizedsent, newtag))
                        score = 0.0
                        if (len(synsets) > 0):
                            for syn in synsets:
                                score += syn.pos_score() - syn.neg_score()
                            sent_score.append(score / len(synsets))
                if (len(sent_score)==0 or len(sent_score)==1):
                    return (float(0.0))
                else:
                    return (sum([word_score for word_score in sent_score]) / (len(sent_score)))
        data['SA_body'] = [compute_score(x) for x in data['body']]
        data['SA_title'] = [compute_score(x) for x in data['title']]
        data['SA_diff'] = abs(data['SA_title'] - data['SA_body'])

        return data

def evaluate_topic(data = None, section = None, source = None, topic = None):
    topic_scores = []
    nontopic_scores = []

    section_mask = (data['condensed_section'] == section)
    source_mask = (data['source'] == source)

    if section and source:
        masked_data = data[section_mask & source_mask]

    elif section:
        masked_data = data[section_mask]

    elif source:
        masked_data = data[source_mask]

    else:
        masked_data = data

    for i, row in masked_data.iterrows():

        if topic in row[2]:
            topic_scores.append(row[6])

        else:
            nontopic_scores.append(row[6])

    score_dict = {'topic': topic_scores, 'nontopic': nontopic_scores}

    '''

    ts = np.mean(score_dict['topic'])
    nts = np.mean(score_dict['nontopic'])

    sns.set_style("whitegrid", {'axes.grid' : False})
    fig, ax = plt.subplots(figsize = (10,6))
    for x in score_dict.keys():
        ax = sns.distplot(score_dict[x], kde = False, label = x)
        ax.set_xlabel("Distribution of Sentiment Scores on {}".format(topic))
    ax.legend()
    ax.set_xlim(-0.1, 0.1)
    '''

    return score_dict
