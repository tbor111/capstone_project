# Capstone Project Documentation

## capstone_project.articledata

### **Classes**

#### class articledata.ArticleData

Utility class to retrieve data from Postgres database.

Methods:

**call()** retrieves data and performs basic cleaning and formatting (eliminates articles with bodies < 200 characters, condenses diverse sections, eliminates '| Fox News' suffix from relelvant titles).

**get_sent_scores()** filters ArticleData object by source, section, and for a particular topic.

  Parameters:
  data = EvaluateTime object
  source = newspaper of choice ('Fox', 'NYT', 'WP')
  section = condensed section name ('world', 'politics', 'sci_health', 'entertainment', 'opinion', 'sports', 'bus_tech', 'education', 'other')
  topic = string containing keyword of your choice


  Returns: dictionary of scores for articles in section, from source containing the topic, and not containing the topic

**count_entities()** counts total persons and places mentioned in ArticleData object.

  Parameters:
  data = EvaluateTime object
  title = Boolean, whether or to count in title or body of articles

  Returns: EvaluateTime object with columns for count of persons and places

**evaluate_entities()** identifies which persons or places are mentioned in a particular section or source.

  Parameters:
  data = EvaluateTime object
  section = condensed section name ('world', 'politics', 'sci_health', 'entertainment', 'opinion', 'sports', 'bus_tech', 'education', 'other')
  source = source = newspaper of choice ('Fox', 'NYT', 'WP')

  Returns: dictionaries containing count of each person and count of each place

#### class articledata.EvaluateTime

Class to facilitate evaluating sentiment scores of articles on a particular topic over time.

Parameters:
data = ArticleData object with SA columns
section
section = condensed section name ('world', 'politics', 'sci_health', 'entertainment', 'opinion', 'sports', 'bus_tech', 'education', 'other')
source = source = newspaper of choice ('Fox', 'NYT', 'WP')
topic = keyword of interest
date = datetime of the earliest date to search for topic

Attributes:
data = EvaluateTime object with SA columns
section
section = condensed section name ('world', 'politics', 'sci_health', 'entertainment', 'opinion', 'sports', 'bus_tech', 'education', 'other')
source = source = newspaper of choice ('Fox', 'NYT', 'WP')
topic = keyword of interest
date = datetime of the earliest date to search for topic
range_date_dict = dictionary where keys are dates and values are list of score for every article in parent ArticleData object
groupings = a list of tuples zipping titles, dates, and sentiment scores


Methods:
**call()** assigns groupings and range_date_dict attributes

**make_dict()**
  Returns: range_date_dict, groupings


**plot_time()** plots range_date_dict with error bars

#### class highchartsplotter.HighChartPlotter

Structures data from an EvaluateTime object into Javascript arrays for plotting sentiment scores in HighCharts.

Parameters:
et = EvaluateTime object with sentiment scores

Attributes:
x_dates = list of unique dates from EvaluateTime object formatted for Epoch time in Javascript
y_means = list of mean article score on a particular date
error_pairs = list of lists containing the min and max score for articles on a particular day
date_list = list of dates, keys for range_date_dict
groups = groupings from EvaluateTime object
spline_series = y_means as a JavaScript array
error_bar_series = error_pairs as a Javascript array
min_titles = list of title names for lowest-scoring articles on a date
max_titles = list of title names for highest-scoring articles on a date
min_scatter_series = titles and scores of lowest-scoring articles in Javascript array
max_scatter_series = titles and scores of highest-scoring articles in Javascript array

Methods:
**call()** assigns attributes

**get_plotting_data()**
  Returns: x_dates, y_means, error_pairs, date_list

**get_spline_series()**
  Returns: spline_series

**get_error_bar_series()**
  Returns: error_bar_series

**get_titles()**
  Returns min_titles, max_titles

**get_scatter_points**
  Returns: min_scatter_series, max_scatter_series
