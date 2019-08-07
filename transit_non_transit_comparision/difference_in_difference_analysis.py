import pandas as pd
import numpy as np
import csv
import os
import pytz
from datetime import datetime
from collections import Counter

import read_data
import before_and_after_final

# statistics
import statsmodels.api as sm
import statsmodels.formula.api as smf

from matplotlib import pyplot as plt
import seaborn as sns
from matplotlib import rc
rc('mathtext', default='regular')

# Hong Kong and Shanghai share the same time zone.
# Hence, we transform the utc time in our dataset into Shanghai time
time_zone_hk = pytz.timezone('Asia/Shanghai')
studied_stations = before_and_after_final.TransitNeighborhood_Before_After.before_after_stations
october_23_start = datetime(2016, 10, 23, 0, 0, 0, tzinfo=time_zone_hk)
october_23_end = datetime(2016, 10, 23, 23, 59, 59, tzinfo=time_zone_hk)
december_28_start = datetime(2016, 12, 28, 0, 0, 0, tzinfo=time_zone_hk)
december_28_end = datetime(2016, 12, 28, 23, 59, 59, tzinfo=time_zone_hk)
start_date = datetime(2016, 5, 7, tzinfo=time_zone_hk)
end_date = datetime(2017, 12, 31, tzinfo=time_zone_hk)

before_after_stations = ['Whampoa', 'Ho Man Tin', 'South Horizons', 'Wong Chuk Hang', 'Ocean Park',
                             'Lei Tung']


def transform_string_time_to_datetime(string):
    """
    :param string: the string which records the time of the posted tweets
    :return: a datetime object which could get access to the year, month, day easily
    """
    datetime_object = datetime.strptime(string, '%Y-%m-%d %H:%M:%S+08:00')
    final_time_object = datetime_object.replace(tzinfo=time_zone_hk)
    return final_time_object


def get_tweets_based_on_date(file_path:str, station_name:str, start_date, end_date, buffer_radius=500):
    """
    :param file_path: path which saves the folders of each TN
    :param station_name: the name of MTR station in each TN
    :param start_date: the start date of the time range we consider
    :param end_date: the end date of the time range we consider
    :return: a filtered dataframe which contains tweets in a specific time range
    """
    combined_dataframe = pd.read_csv(os.path.join(file_path, station_name, station_name+'_{}m_tn_tweets.csv'.format(buffer_radius)),
                                     encoding='latin-1')
    combined_dataframe['hk_time'] = combined_dataframe.apply(
        lambda row: transform_string_time_to_datetime(row['hk_time']), axis=1)
    combined_dataframe['year'] = combined_dataframe.apply(
        lambda row: row['hk_time'].year, axis=1
    )
    combined_dataframe['month'] = combined_dataframe.apply(
        lambda row: row['hk_time'].month, axis=1
    )
    combined_dataframe['day'] = combined_dataframe.apply(
        lambda row: row['hk_time'].day, axis=1
    )
    # Only consider the tweets posted in a specific time range
    time_mask = (combined_dataframe['hk_time'] >= start_date) & (combined_dataframe['hk_time'] <= end_date)
    filtered_dataframe = combined_dataframe.loc[time_mask]
    # Fix the column name of the cleaned_text
    filtered_dataframe.rename(columns = {'cleaned_te': 'cleaned_text', 'user_id_st':'user_id_str'},
                              inplace=True)
    return filtered_dataframe


def get_nontn_tweets(station_name, folder_path):
    data_path = os.path.join(os.path.join(folder_path, station_name, station_name+'_tweets_annulus'))
    non_tn_tweets = pd.read_csv(os.path.join(data_path, station_name+'_1000_erase_500.csv'), encoding='latin-1')
    return non_tn_tweets


def add_post_variable(string, opening_start_date, opening_end_date):
    time_object = transform_string_time_to_datetime(string)
    if time_object > opening_end_date:
        return 1
    elif time_object < opening_start_date:
        return 0
    else:
        return 'not considered'


def build_regress_datafrane_for_one_newly_built_station(treatment_dataframe, control_dataframe,
                                                        station_open_start_date, station_open_end_date,
                                                        open_year_plus_month):
    # check the date
    assert open_year_plus_month in ['2016_10', '2016_12']
    result_dataframe = pd.DataFrame(columns=['Time', 'T_i_t', 'Post', 'Sentiment', 'Activity'])
    # build the T_i_t variable
    ones_list = [1] * treatment_dataframe.shape[0]
    treatment_dataframe['T_i_t'] = ones_list
    zeros_list = [0] * control_dataframe.shape[0]
    control_dataframe['T_i_t'] = zeros_list
    # build the post variable
    treatment_dataframe['Post'] = treatment_dataframe.apply(
        lambda row: add_post_variable(row['hk_time'], opening_start_date=station_open_start_date,
                                      opening_end_date=station_open_end_date), axis=1)
    print('Check the post variable distribution of treatment group: {}'.format(
        Counter(treatment_dataframe['Post'])))
    print('Check the T_i_t variable distribution of treatment group: {}'.format(
        Counter(treatment_dataframe['T_i_t'])))
    control_dataframe['Post'] = control_dataframe.apply(
        lambda row: add_post_variable(row['hk_time'], opening_start_date=station_open_start_date,
                                      opening_end_date=station_open_end_date), axis=1)
    print('Check the post variable distribution of control group: {}'.format(
        Counter(control_dataframe['Post'])))
    print('Check the T_i_t variable distribution of control group: {}'.format(
        Counter(control_dataframe['T_i_t'])))
    combined_dataframe = pd.concat([treatment_dataframe, control_dataframe], axis=0, sort=True)
    combined_dataframe = combined_dataframe.reset_index(drop=True)
    # We don't consider the tweets posted on the open date
    combined_dataframe_without_not_considered = \
        combined_dataframe.loc[combined_dataframe['Post'] != 'not considered']
    combined_data_copy = combined_dataframe_without_not_considered.copy()
    combined_data_copy['month_plus_year'] = combined_data_copy.apply(
        lambda row: str(int(float(row['year']))) + '_' + str(int(float(row['month']))), axis=1)
    sentiment_dict = {}
    activity_dict = {}
    for _, dataframe in combined_data_copy.groupby(['month_plus_year', 'T_i_t', 'Post']):
        time = str(list(dataframe['month_plus_year'])[0])
        t_i_t = str(list(dataframe['T_i_t'])[0])
        post = str(list(dataframe['Post'])[0])
        sentiment_dict[time + '_' + t_i_t + '_' + post] = before_and_after_final.pos_percent_minus_neg_percent(dataframe)
        activity_dict[time + '_' + t_i_t + '_' + post] = np.log(dataframe.shape[0])
    result_dataframe_copy = result_dataframe.copy()
    time_list = []
    t_i_t_list = []
    post_list = []
    sentiment_list = []
    activity_list = []
    for key in list(sentiment_dict.keys()):
        # don't consider the tweets posted in 2016_10(for Whampoa and Ho Man Tin) or 2016_12(for other stations)
        if key[:7] != open_year_plus_month:
            time_list.append(key[:-4])
            t_i_t_list.append(int(key[-3]))
            post_list.append(int(key[-1]))
            sentiment_list.append(sentiment_dict[key])
            activity_list.append(activity_dict[key])
        else:
            pass
    result_dataframe_copy['Time'] = time_list
    result_dataframe_copy['T_i_t'] = t_i_t_list
    result_dataframe_copy['Post'] = post_list
    result_dataframe_copy['Sentiment'] = sentiment_list
    result_dataframe_copy['Activity'] = activity_list
    return result_dataframe_copy


def build_dataframe_based_on_set(datapath, tpu_set):
    tpu_name_list = []
    dataframe_list = []
    for tpu in tpu_set:
        tpu_name_list.append(tpu)
        dataframe = pd.read_csv(os.path.join(datapath, tpu, tpu+'_data.csv'), encoding='utf-8', dtype='str',
                                quoting=csv.QUOTE_NONNUMERIC)
        dataframe_list.append(dataframe)
    combined_dataframe = pd.concat(dataframe_list, axis=0)
    return combined_dataframe


if __name__ == '__main__':

    path = os.path.join(read_data.transit_non_transit_comparison_before_after, 'tpu_data_with_visitors')
    kwun_tong_line_treatment_dict = {}
    kwun_tong_line_control_dict = {}
    south_island_line_treatment_dict = {}
    south_island_line_control_dict = {}

    kwun_tong_line_treatment_tpu_set = {'243', '245', '236', '213'}
    kwun_tong_line_control_tpu_set = {'247', '234', '242', '212', '235'}
    south_horizons_lei_tung_treatment_tpu_set = {'174'}
    south_horizons_lei_tung_control_tpu_set = {'172', '182'}
    ocean_park_wong_chuk_hang_treatment_tpu_set = {'175'}
    ocean_park_wong_chuk_hang_control_tpu_set = {'184', '183', '182'}
    tpu_213_set, tpu_236_set, tpu_243_set, tpu_245_set = {'213'}, {'236'}, {'243'}, {'245'}

    kwun_tong_line_treatment_dataframe = build_dataframe_based_on_set(datapath=path,
                                                                      tpu_set=kwun_tong_line_treatment_tpu_set)
    kwun_tong_line_control_dataframe = build_dataframe_based_on_set(datapath=path,
                                                                    tpu_set=kwun_tong_line_control_tpu_set)
    south_horizons_lei_tung_treatment_dataframe = build_dataframe_based_on_set(datapath=path,
                                                                               tpu_set=south_horizons_lei_tung_treatment_tpu_set)
    south_horizons_lei_tung_control_dataframe = build_dataframe_based_on_set(datapath=path,
                                                                             tpu_set=south_horizons_lei_tung_control_tpu_set)
    ocean_park_wong_chuk_hang_treatment_dataframe = build_dataframe_based_on_set(datapath=path,
                                                                                 tpu_set=ocean_park_wong_chuk_hang_treatment_tpu_set)
    ocean_park_wong_chuk_hang_control_dataframe = build_dataframe_based_on_set(datapath=path,
                                                                               tpu_set=ocean_park_wong_chuk_hang_control_tpu_set)
    tpu_213_treatment_dataframe = build_dataframe_based_on_set(datapath=path, tpu_set=tpu_213_set)
    tpu_236_treatment_dataframe = build_dataframe_based_on_set(datapath=path, tpu_set=tpu_236_set)
    tpu_243_treatment_dataframe = build_dataframe_based_on_set(datapath=path, tpu_set=tpu_243_set)
    tpu_245_treatment_dataframe = build_dataframe_based_on_set(datapath=path, tpu_set=tpu_245_set)

    print('************************DID Analysis Starts....************************')
    print('Overall Treatment and Control Comparison...')
    print('---------------------Kwun Tong Line---------------------------')
    kwun_tong_line_result_dataframe = build_regress_datafrane_for_one_newly_built_station(
        treatment_dataframe=kwun_tong_line_treatment_dataframe,
        control_dataframe=kwun_tong_line_control_dataframe,
        station_open_start_date=october_23_start,
        station_open_end_date=october_23_end,
        open_year_plus_month='2016_10')
    reg_kwun_tong_line_sentiment = smf.ols('Sentiment ~ T_i_t+Post+Post:T_i_t', kwun_tong_line_result_dataframe).fit()
    reg_kwun_tong_line_activity = smf.ols('Activity ~ T_i_t+Post+Post:T_i_t', kwun_tong_line_result_dataframe).fit()
    print('----The sentiment did result-----')
    print(reg_kwun_tong_line_sentiment.summary())
    print('----The activity did result-----')
    print(reg_kwun_tong_line_activity.summary())
    print('-------------------------------------------------------\n')

    print('---------------------South Horizons & Lei Tung---------------------------')
    south_horizons_lei_tung_result_dataframe = build_regress_datafrane_for_one_newly_built_station(
        treatment_dataframe=south_horizons_lei_tung_treatment_dataframe,
        control_dataframe=south_horizons_lei_tung_control_dataframe,
        station_open_start_date=december_28_start,
        station_open_end_date=december_28_end,
        open_year_plus_month='2016_12')
    reg_south_horizons_lei_tung_sentiment = smf.ols('Sentiment ~ T_i_t+Post+Post:T_i_t',
                                          south_horizons_lei_tung_result_dataframe).fit()
    reg_south_horizons_lei_tung_activity = smf.ols('Activity ~ T_i_t+Post+Post:T_i_t',
                                          south_horizons_lei_tung_result_dataframe).fit()
    print('----The sentiment did result-----')
    print(reg_south_horizons_lei_tung_sentiment.summary())
    print('----The activity did result-----')
    print(reg_south_horizons_lei_tung_activity.summary())
    print('-------------------------------------------------------\n')

    print('---------------------Ocean Park & Wong Chuk Hang---------------------------')
    ocean_park_wong_chuk_hang_result_dataframe = build_regress_datafrane_for_one_newly_built_station(
        treatment_dataframe=ocean_park_wong_chuk_hang_treatment_dataframe,
        control_dataframe=ocean_park_wong_chuk_hang_control_dataframe,
        station_open_start_date=december_28_start,
        station_open_end_date=december_28_end,
        open_year_plus_month='2016_12')
    reg_ocean_park_wong_chuk_hang_sentiment = smf.ols('Sentiment ~ T_i_t+Post+Post:T_i_t',
                                          ocean_park_wong_chuk_hang_result_dataframe).fit()
    reg_ocean_park_wong_chuk_hang_activity = smf.ols('Activity ~ T_i_t+Post+Post:T_i_t',
                                                      ocean_park_wong_chuk_hang_result_dataframe).fit()
    print('----The sentiment did result-----')
    print(reg_ocean_park_wong_chuk_hang_sentiment.summary())
    print('----The activity did result-----')
    print(reg_ocean_park_wong_chuk_hang_activity.summary())
    print('-------------------------------------------------------\n')

    print('For the Kwun Tong Line, if we look at each TPU in the treatment group....')
    print('For TPU 213: ')
    tpu_213_result_dataframe = build_regress_datafrane_for_one_newly_built_station(
        treatment_dataframe=tpu_213_treatment_dataframe,
        control_dataframe=kwun_tong_line_control_dataframe,
        station_open_start_date=october_23_start,
        station_open_end_date=october_23_end,
        open_year_plus_month='2016_10')
    reg_213_sentiment = smf.ols('Sentiment ~ T_i_t+Post+Post:T_i_t', tpu_213_result_dataframe).fit()
    reg_213_activity = smf.ols('Activity ~ T_i_t+Post+Post:T_i_t', tpu_213_result_dataframe).fit()
    print('----The sentiment did result-----')
    print(reg_213_sentiment.summary())
    print('----The activity did result-----')
    print(reg_213_activity.summary())
    print('-------------------------------------------------------\n')

    print('For TPU 236: ')
    tpu_236_result_dataframe = build_regress_datafrane_for_one_newly_built_station(
        treatment_dataframe=tpu_236_treatment_dataframe,
        control_dataframe=kwun_tong_line_control_dataframe,
        station_open_start_date=october_23_start,
        station_open_end_date=october_23_end,
        open_year_plus_month='2016_10')
    reg_236_sentiment = smf.ols('Sentiment ~ T_i_t+Post+Post:T_i_t', tpu_236_result_dataframe).fit()
    reg_236_activity = smf.ols('Activity ~ T_i_t+Post+Post:T_i_t', tpu_236_result_dataframe).fit()
    print('----The sentiment did result-----')
    print(reg_236_sentiment.summary())
    print('----The activity did result-----')
    print(reg_236_activity.summary())
    print('-------------------------------------------------------\n')

    print('For TPU 243: ')
    tpu_243_result_dataframe = build_regress_datafrane_for_one_newly_built_station(
        treatment_dataframe=tpu_243_treatment_dataframe,
        control_dataframe=kwun_tong_line_control_dataframe,
        station_open_start_date=october_23_start,
        station_open_end_date=october_23_end,
        open_year_plus_month='2016_10')
    reg_243_sentiment = smf.ols('Sentiment ~ T_i_t+Post+Post:T_i_t', tpu_243_result_dataframe).fit()
    reg_243_activity = smf.ols('Activity ~ T_i_t+Post+Post:T_i_t', tpu_243_result_dataframe).fit()
    print('----The sentiment did result-----')
    print(reg_243_sentiment.summary())
    print('----The activity did result-----')
    print(reg_243_activity.summary())
    print('-------------------------------------------------------\n')

    print('For TPU 245: ')
    tpu_245_result_dataframe = build_regress_datafrane_for_one_newly_built_station(
        treatment_dataframe=tpu_245_treatment_dataframe,
        control_dataframe=kwun_tong_line_control_dataframe,
        station_open_start_date=october_23_start,
        station_open_end_date=october_23_end,
        open_year_plus_month='2016_10')
    reg_245_sentiment = smf.ols('Sentiment ~ T_i_t+Post+Post:T_i_t', tpu_245_result_dataframe).fit()
    reg_245_activity = smf.ols('Activity ~ T_i_t+Post+Post:T_i_t', tpu_245_result_dataframe).fit()
    print('----The sentiment did result-----')
    print(reg_245_sentiment.summary())
    print('----The activity did result-----')
    print(reg_245_activity.summary())
    print('-------------------------------------------------------\n')
