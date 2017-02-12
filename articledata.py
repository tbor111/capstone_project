#!/usr/bin/env python
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import psycopg2
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from nltk.sentiment.util import *
from nltk.corpus import sentiwordnet as swn
from nltk.tag.perceptron import PerceptronTagger
from nltk.tag import StanfordNERTagger
from nltk.tokenize import word_tokenize
import os


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

def get_sent_scores(data = None):
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

def count_entities(data = None, title = True):
    # set up tagger
    os.environ['CLASSPATH'] = "/Users/teresaborcuch/stanford-ner-2013-11-12/stanford-ner.jar"
    os.environ['STANFORD_MODELS'] = '/Users/teresaborcuch/stanford-ner-2013-11-12/classifiers'
    st = StanfordNERTagger('english.all.3class.distsim.crf.ser.gz')

    tagged_titles = []
    persons = []
    places = []

    for x in data[section]:
        tokens = word_tokenize(x)
        tags = st.tag(tokens)
        tagged_titles.append(tags)

    for pair_list in tagged_titles:
        person_count = 0
        place_count = 0
        for pair in pair_list:
            if pair[1] == 'PERSON':
                person_count +=1
            elif pair[1] == 'LOCATION':
                place_count +=1
            else:
                continue
        persons.append(person_count)
        places.append(place_count)

    if title:
        data['total_persons_title'] = persons
        data['total_places_title'] = places

    else:
        data['total_persons_body'] = persons
        data['total_places_body'] = places

    return data


def evaluate_entities(data = None, section = None, source = None):
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

    # set up tagger
    os.environ['CLASSPATH'] = "/Users/teresaborcuch/stanford-ner-2013-11-12/stanford-ner.jar"
    os.environ['STANFORD_MODELS'] = '/Users/teresaborcuch/stanford-ner-2013-11-12/classifiers'
    st = StanfordNERTagger('english.all.3class.distsim.crf.ser.gz')
    # dictionaries to hold counts of entities
    person_dict = {}
    place_dict = {}

    for x in masked_data['body']:
        tokens = word_tokenize(x)
        tags = st.tag(tokens)
        for pair in tags:
            if pair[1] == 'PERSON':
                if pair[0] not in person_dict.keys():
                    person_dict[pair[0]] = 1
                else:
                    person_dict[pair[0]] +=1
            elif pair[1] == 'LOCATION':
                if pair[0] not in place_dict.keys():
                    place_dict[pair[0]] = 1
                else:
                    place_dict[pair[0]] += 1

    return person_dict, place_dict


class EvaluateTime():

    def __init__(self, data = None, section = None, source = None, topic = None, date = None):
        self.data = data
        self.section = section
        self.source = source
        self.topic = topic
        self.date = date

    def call(self):
        #self.plot_date_dict,
        self.range_date_dict = self.make_dict()
        return self

    def make_dict(self):
        # define masks
        section_mask = (self.data['condensed_section'] == self.section)
        source_mask = (self.data['source'] == self.source)
        date_mask = (self.data['date'] > self.date)

        # initialize lists for plot_date_dict
        topic_scores = []
        dates = []

        # initialize other dict
        range_date_dict = {}

        if not self.date:
            print "Please select a start date."

        # make plot_date_dict from appropriate subset of data
        else:
            if self.section and self.source:
                masked_data = self.data[section_mask & source_mask & date_mask]

            elif self.section and (not self.source):
                masked_data = self.data[section_mask & date_mask]

            elif self.source and (not self.section):
                masked_data = self.data[source_mask & date_mask]

            else:
                masked_data = self.data[date_mask]

            for i, row in masked_data.iterrows():

                if self.topic in row[2]:
                    topic_scores.append(row[6])
                    dates.append(row[1])

                    # add to range_date_dict where keys are the dates and the vales are a list of scores
                    if row[1] not in range_date_dict.keys():
                        range_date_dict[row[1]] = [row[6]]

                    elif row[1] in range_date_dict.keys():
                        (range_date_dict[row[1]]).append(row[6])

        #plot_date_dict = {'date': dates, 'score': topic_scores}
        return range_date_dict #plot_date_dict,

    def plot_time(self):

        x = self.range_date_dict.keys()
        x.sort()
        ordered_x = []
        y = []
        for val in x:
            ordered_x.append(val)
            values = self.range_date_dict[val]
            mean = np.mean(values)
            y.append(mean)

        # define upper and lower boundaries for error bars
        upper_bounds = [max(self.range_date_dict[x]) for x in ordered_x]
        lower_bounds = [min(self.range_date_dict[x]) for x in ordered_x]

        # define distance for upper error bar
        y_upper = zip(y, upper_bounds)
        upper_error = [abs(pair[0] - pair[1]) for pair in y_upper]

        # define distance for lower error bar
        y_lower = zip(y, lower_bounds)
        lower_error = [abs(pair[0] - pair[1]) for pair in y_lower]

        asymmetric_error = [lower_error, upper_error]

        plt.plot(ordered_x, y, c = 'r', marker = 'o')
        plt.errorbar(ordered_x, y, yerr = asymmetric_error, ecolor = 'r', capthick = 1)
        plt.xlim(min(ordered_x) + timedelta(days = -1), max(ordered_x) + timedelta(days = 1))
        plt.xticks(rotation = 70)
        plt.show()
