#!/usr/bin/env python

import numpy as np
import pandas as pd
import json
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import psycopg2
import seaborn as sns
import matplotlib.pyplot as plt
from nltk.sentiment.util import *
from nltk.corpus import sentiwordnet as swn
from nltk.tag.perceptron import PerceptronTagger
from nltk.tag import StanfordNERTagger
from nltk.tokenize import word_tokenize
import os
import re

class SentimentPlotter():
    def __init__(self, data = None):
        self.data = data

    def call(self):

        self.data['SA_body'] = [self.compute_score(x) for x in self.data['body']]
        self.data['SA_title'] = [self.compute_score(x) for x in self.data['title']]

        return self

    def get_highcharts_series(self, section = None, source = None, topic = None, date = None):
        self.section = section
        self.source = source
        self.topic = topic
        self.date = date

        self.range_date_dict, self.groupings = self.make_dict()

        self.x_dates, self.y_means, self.error_pairs, self.date_list = self.get_plotting_data()

        self.spline_series = self.get_spline_series()

        self.error_bar_series = self.get_error_bar_series()

        self.min_titles, self.max_titles = self.get_titles()

        self.min_scatter_series, self.max_scatter_series = self.get_scatter_points()

        return self.spline_series, self.error_bar_series, self.min_scatter_series, self.max_scatter_series


    def compute_score(self, sentence):
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


    def make_dict(self):
        # define masks
        section_mask = (self.data['condensed_section'] == self.section)
        source_mask = (self.data['source'] == self.source)
        date_mask = (self.data['date'] > self.date)

        # initialize lists for plot_date_dict
        topic_scores = []
        dates = []
        groupings = []

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
                    topic_scores.append(row[6]) #body score
                    dates.append(row[1])
                    score_title_date = (row[0], row[1], row[6])
                    groupings.append(score_title_date)


                    # add to range_date_dict where keys are the dates and the values are a list of scores
                    if row[1] not in range_date_dict.keys():
                        range_date_dict[row[1]] = [row[6]]

                    elif row[1] in range_date_dict.keys():
                        (range_date_dict[row[1]]).append(row[6])
                return range_date_dict, groupings




    def get_plotting_data(self):
        # get dates for x-axis
        date_list = self.range_date_dict.keys()
        date_list.sort()
        x_dates = [x.value// 10 ** 6 for x in date_list]

        # y-values
        y_values = [np.mean(self.range_date_dict[x]) for x in date_list]

        # error bars
        error_min_max = []
        for x in date_list:
            temp_list = []
            minimum = min(self.range_date_dict[x])
            maximum = max(self.range_date_dict[x])
            temp_list.append(minimum)
            temp_list.append(maximum)
            error_min_max.append(temp_list)

        return x_dates, y_values, error_min_max, date_list

    def get_spline_series(self):
        # format splines for jsfiddle - do this first!
        d = []
        series = {'name': 'Mean Score', 'type': 'spline'}
        for x in range(len(self.date_list)):
            data_point = [self.x_dates[x], self.y_means[x]]
            d.append(data_point)
        series['data'] = d
        spline_series = json.dumps(series)
        return spline_series

    def get_error_bar_series(self):
        d = []
        series = {'color': '#FF0000', 'name': 'Range', 'type': 'errorbar', 'stemWidth': 3, 'whiskerLength': 0}
        for x in range(len(self.date_list)):
            data_point = [self.x_dates[x], self.error_pairs[x][0], self.error_pairs[x][1]]
            d.append(data_point)
        series['data'] = d
        error_series = json.dumps(series)
        return error_series

    def get_titles(self):
        min_score_titles = {}
        max_score_titles = {}

        # min scores
        for x in self.groupings:
            if x[1] not in min_score_titles.keys():
                min_score_titles[x[1]] = (x[2], x[0])
            elif x[1] in min_score_titles.keys():
                if x[2] < min_score_titles[x[1]][0]:
                    min_score_titles[x[1]] = (x[2], x[0])
                elif x[2] >= min_score_titles[x[1]][0]:
                    continue

        # max scores
        for x in self.groupings:
            if x[1] not in max_score_titles.keys():
                max_score_titles[x[1]] = (x[2], x[0])
            elif x[1] in max_score_titles.keys():
                if x[2] > max_score_titles[x[1]][0]:
                    max_score_titles[x[1]] = (x[2], x[0])
                elif x[2] <= max_score_titles[x[1]][0]:
                    continue

        min_titles = [min_score_titles[x][1].encode('ascii', 'ignore') for x in self.date_list]
        max_titles = [max_score_titles[x][1].encode('ascii','ignore') for x in self.date_list]

        return min_titles, max_titles

    def get_scatter_points(self):
        max_series = []

        for x in range(len(self.date_list)):
            data_point = {'showInLegend': False, 'type': 'scatter', 'color': '#FF0000',
                          'marker': {'symbol': 'circle', 'enabled': True, 'color': '#FF0000'},
                          'tooltip': {'pointFormat': '{point.y}'}}

            data_point['name'] = self.max_titles[x]

            data_list = [[self.x_dates[x], self.error_pairs[x][1]]]

            data_point['data'] = data_list
            max_series.append(data_point)

        max_series = json.dumps(max_series)

        # return minimum scatter points series
        min_series = []

        for x in range(len(self.date_list)):
            data_point = {'showInLegend': False, 'type': 'scatter', 'color': '#FF0000',
                          'marker': {'symbol': 'circle', 'enabled': True, 'color': '#FF0000'},
                          'tooltip': {'pointFormat': '{point.y}'}}
            # get title
            data_point['name'] = self.min_titles[x]

            data_list = [[self.x_dates[x], self.error_pairs[x][0]]]

            data_point['data'] = data_list

            min_series.append(data_point)

        min_series = json.dumps(min_series)

        return min_series, max_series

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
