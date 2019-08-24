import re
import os
import pandas as pd
import csv
import pytz
from datetime import datetime
from geopy.distance import vincenty

# For plots
from matplotlib import pyplot as plt
import seaborn as sns

import read_data

time_zone_hk = pytz.timezone('Asia/Shanghai')

# The replacement patterns used in cleaning the raw text data
replacement_patterns = [
    (r"won\'t", "will not"),
    (r"[^A-Za-z0-9^,!.\/'+-=]", " "),
    (r"can\'t", "cannot"),
    (r"I\'m", "I am"),
    (r"ain\'t", 'is not'),
    (r"(\d+)(k)", r"\g<1>000"),
    # \g<1> are using back-references to capture part of the matched pattern
    # \g means referencing group content in the previous pattern. <1> means the first group. In the following case, the first group is w+
    (r"(\w+)\'ll", "\g<1> will"),
    (r"(\w+)n\'t", "\g<1> not"),
    (r"(\w+)\'ve", "\g<1> have"),
    (r"(\w+)\'s", "\g<1> is"),
    (r"(\w+)\'re", "\g<1> are"),
    (r"(\w+)\'d", "\g<1> would")
]


# A RegexpReplacer to clean some texts based on specified patterns
class RegexpReplacer(object):
    def __init__(self, patterns):
        self.patterns = [(re.compile(regex), repl) for (regex, repl) in replacement_patterns]

    def replace(self, text):
        s = text
        for (pattern, repl) in self.patterns:
            s = re.sub(pattern=pattern, repl=repl, string=s)  # subn returns the times of replacement
        return s


def read_local_csv_file(path, filename, dtype_str=True):
    if dtype_str:
        dataframe = pd.read_csv(os.path.join(path, filename), encoding='utf-8', quoting=csv.QUOTE_NONNUMERIC,
                                dtype='str', index_col=0)
    else:
        dataframe = pd.read_csv(os.path.join(path, filename), encoding='utf-8', quoting=csv.QUOTE_NONNUMERIC,
                                index_col=0)
    return dataframe


def transform_string_time_to_datetime(string):
    """
    :param string: the string which records the time of the posted tweets(this string's timezone is HK time)
    :return: a datetime object which could get access to the year, month, day easily
    """
    datetime_object = datetime.strptime(string, '%Y-%m-%d %H:%M:%S+08:00')
    final_time_object = datetime_object.replace(tzinfo=time_zone_hk)
    return final_time_object


def number_of_tweet_user(df):
    user_num = len(set(df['user_id_str']))
    tweet_num = df.shape[0]
    print('Total number of tweet is: {}; Total number of user is {}'.format(
        tweet_num, user_num))


# Use this function to select the MTR-related tweets
def find_tweet(keywords, tweet):
    result = ''
    for word in tweet:
        if word in keywords:
            result = True
        else:
            result = False
    return result


# get the hk_time column based on the created_at column
def get_hk_time(df):
    changed_time_list = []
    for _, row in df.iterrows():
        time_to_change = datetime.strptime(row['created_at'], '%a %b %d %H:%M:%S %z %Y')
        # get the hk time
        changed_time = time_to_change.astimezone(time_zone_hk)
        changed_time_list.append(changed_time)
    df['hk_time'] = changed_time_list
    return df


# get the year, month, day information of based on any tweet dataframe
def get_year_month_day(df):
    df_copy = df.copy()
    df_copy['year'] = df_copy.apply(lambda row: row['hk_time'].year, axis=1)
    df_copy['month'] = df_copy.apply(lambda row: row['hk_time'].month, axis=1)
    df_copy['day'] = df_copy.apply(lambda row: row['hk_time'].day, axis=1)
    return df_copy


# Calculate the haversine distance between two points based on latitude and longitude
# More about the haversine distance: https://en.wikipedia.org/wiki/Haversine_formula
def distance_calc(row, station_lat, station_lon):
    start = (row['lat'], row['lon'])
    stop = (station_lat, station_lon)
    return vincenty(start, stop).meters


"""
An instance of using haversine_distance to calculate the distance of two points
lat1 = 52.2296756
lon1 = 21.0122287
Whampoa_lat = 22.3051
Whampoa_lon = 114.1895
Ho_Man_Tin_lat = 22.3094
Ho_Man_Tin_lon = 114.1827

print(distance(lat1, lon1, Whampoa_lat, Whampoa_lon))
"""


def select_data_based_on_location(row, station_lat, station_lon):
    if distance_calc(row, station_lat, station_lon) < 500:
        result = 'TRUE'
    else:
        result = 'FALSE'
    return result


def read_text_from_multi_csvs(path):
    all_csv_files = os.listdir(path)
    dataframes = []
    for file in all_csv_files:
        dataframe = pd.read_csv(os.path.join(path, file), encoding='latin-1', dtype='str',
                                quoting=csv.QUOTE_NONNUMERIC)
        dataframes.append(dataframe)
    combined_dataframes = pd.concat(dataframes, sort=True)
    return combined_dataframes


def build_dataframe_for_urban_rate(source_dataframe):
    result_dataframe = pd.DataFrame(columns=['Year', 'US', 'China', 'World'])
    China_dataframe = source_dataframe.loc[source_dataframe['Country Name'] == 'China']
    us_dataframe = source_dataframe.loc[source_dataframe['Country Name'] == 'United States']
    World_dataframe = source_dataframe.loc[source_dataframe['Country Name'] == 'World']
    year_list = list(range(1960, 2019, 1))
    result_dataframe['Year'] = year_list
    result_dataframe['US'] = us_dataframe.values[0][4:]
    result_dataframe['China'] = China_dataframe.values[0][4:]
    result_dataframe['World'] = World_dataframe.values[0][4:]
    return result_dataframe


def build_line_graph_urban_rate(dataframe):
    x = list(dataframe['Year'])
    y_china = list(dataframe['China'])
    y_us = list(dataframe['US'])
    y_world = list(dataframe['World'])

    figure, ax = plt.subplots(1, 1, figsize=(20, 10))
    lns1 = ax.plot(x, y_world, 'k-', label='World', linestyle='--', marker='o')
    lns2 = ax.plot(x, y_china, 'y-', label='China', linestyle='--', marker='^')
    lns3 = ax.plot(x, y_us, 'b-', label='US', linestyle='--', marker='^')

    lns = lns1 + lns2 + lns3
    labs = [l.get_label() for l in lns]
    ax.legend(lns, labs)

    ax.set_xlabel('Time')
    ax.set_ylabel('Urban Population Rate %')
    ax.set_title('Urban Population Rate for US, China and World from 1960 to 2018')
    plt.savefig(os.path.join(read_data.plot_path_2017, 'urban_rate_plot.png'))
    plt.show()


def build_bar_plot_distribution_comparison(**key_list_dict):
    name_list = list(key_list_dict.keys())
    if len(name_list) ==  1:
        value_list = key_list_dict[name_list[0]]
    else:
        return 'Not Worked Out'
    sentiment_tag = ['Positive', 'Neutral', 'Negative']
    x_values_for_plot = list(range(len(sentiment_tag)))
    fig, ax = plt.subplots(1,1, figsize=(10, 8))

    ax.bar(x_values_for_plot, value_list, color='red')
    ax.set_xticks(x_values_for_plot)
    ax.set_xticklabels(sentiment_tag)
    filename = name_list[0] + '_distribution'
    fig.savefig(os.path.join(read_data.human_review_result_path, filename))
    plt.show()


def classifiers_performance_compare(filename):
    result_dataframe = pd.DataFrame(columns=['metrics', 'performance', 'Classifiers'])

    accuracy_list = [0.64, 0.70, 0.70, 0.67]
    precision_list = [0.48, 0.47, 0.51, 0.52]
    recall_list = [0.50, 0.48, 0.51, 0.54]
    f1_list = [0.47, 0.47, 0.51, 0.50]

    performance_list = accuracy_list + precision_list + recall_list + f1_list
    metrics_list = ['Accuracy'] * 4 + ['Precision'] * 4 + ['Recall'] * 4 + ['F1 Score'] * 4
    classifier_list = ['Decision Tree', 'Random Forest', 'SVM', 'Neural Net'] * 4

    result_dataframe['metrics'] = metrics_list
    result_dataframe['performance'] = performance_list
    result_dataframe['Classifiers'] = classifier_list

    fig_classifier_compare, ax = plt.subplots(1, 1, figsize=(10, 8))
    # qualitative_colors = sns.color_palette("Set1", 4)
    # sns.set_palette(qualitative_colors)
    sns.barplot(x="metrics", y="performance", hue="Classifiers", data=result_dataframe, ax=ax,
                palette=["#6553FF", "#E8417D", "#FFAC42", '#A5FF47'])
    fig_classifier_compare.savefig(os.path.join(read_data.human_review_result_path, filename))
    plt.show()


def draw_urban_rate_main(dataframe):
    data_for_plot = build_dataframe_for_urban_rate(dataframe)
    build_line_graph_urban_rate(dataframe=data_for_plot)


if __name__ == '__main__':
    urban_rate_dataframe = pd.read_csv(os.path.join(read_data.datasets, 'urban_rate.csv'), encoding='latin-1',
                                       dtype=str)
    draw_urban_rate_main(urban_rate_dataframe)

    # draw the barplot which shows the distribution of sentiment label
    build_bar_plot_distribution_comparison(**{'total_sentiment_label_comparison': [1942, 2920, 137]})

    # draw bar plot which show the performance of various algorithms
    classifiers_performance_compare(filename= 'classifier_performance_compare.png')
    

    









