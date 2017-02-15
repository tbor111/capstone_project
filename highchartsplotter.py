#!/usr/bin/env python

from articledata import EvaluateTime
import numpy as np
import pandas as pd

class HighChartPlotter():
    def __init__(self, et):
        self.et = et

    def call(self):

        self.x_dates, self.y_means, self.error_pairs, self.date_list = self.get_plotting_data(),

        self.groups = et.groupings,

        self.spline_series = self.get_spline_series(),

        self.error_bar_series = self.get_error_bar_series(),

        self.min_titles, self.max_titles = self.get_titles(),

        self.min_scatter_series, self.max_scatter_series = self.get_scatter_points()


    def get_plotting_data(self):
        # get dates for x-axis
        date_list = self.et.range_date_dict.keys()
        date_list.sort()
        x_dates = [x.value// 10 ** 6 for x in date_list]

        # y-values
        y_values = [np.mean(self.et.range_date_dict[x]) for x in date_list]

        # error bars
        error_min_max = []
        for x in date_list:
            temp_list = []
            minimum = min(self.et.range_date_dict[x])
            maximum = max(self.et.range_date_dict[x])
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
        for x in self.groups:
            if x[1] not in min_score_titles.keys():
                min_score_titles[x[1]] = (x[2], x[0])
            elif x[1] in min_score_titles.keys():
                if x[2] < min_score_titles[x[1]][0]:
                    min_score_titles[x[1]] = (x[2], x[0])
                elif x[2] >= min_score_titles[x[1]][0]:
                    continue

        # max scores
        for x in self.groups:
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
