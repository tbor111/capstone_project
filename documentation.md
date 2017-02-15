### Capstone Project Documentation

## capstone_project.articledata

# **Classes**

class articledata.ArticleData

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

class articledata.EvaluateTime

Class to facilitate evaluating sentiment scores of articles on a particular topic over time.

Parameters:
data = EvaluateTime object with SA columns
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
range_date_dict =
groupings =


Methods:
**call()**

**make_dict()**

**plot_time()**
