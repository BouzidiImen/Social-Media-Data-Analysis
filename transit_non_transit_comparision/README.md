# Description :world_map:

This folder contains codes needed to cope with geographic shapefiles of Hong Kong and the collected tweets. All the codes could be split into the following categories:

## 1. Prepare the data and paths

Firstly, we list all the directories needed in this folder

- The paths being used in dealing with shapefiles are given here: [read_data.py](https://github.com/bright1993ff66/Social-Media-Data-Analysis/blob/master/transit_non_transit_comparision/read_data.py)
- Other paths could be found in [here](https://github.com/bright1993ff66/Social-Media-Data-Analysis/blob/master/read_data.py)

Then, you could use [ArcMap]( http://desktop.arcgis.com/en/arcmap/ ) to locate each tweet with TPU attribute.

Then we start preparing the datasets for the cross sectional study and the longitudinal study.

### 1.1 Prepare the dataset for cross sectional study

<span style='color:red'>In the cross sectional study</span>, the TPU units which intersect with **500-meter geographic buffer** are seen as TN-TPUs while the other TPUs are classified as the Non-TN TPUs. More specifically,

- Firstly, you could load the [station_location.csv]( https://github.com/bright1993ff66/Social-Media-Data-Analysis/blob/master/transit_non_transit_comparision/station_location.csv ) to ArcMap and generate 500-meter geographic buffers around the stations. Then by doing [intersect analysis]( https://pro.arcgis.com/en/pro-app/tool-reference/analysis/intersect.htm ), you could check which TPU unit intersect with the created geographic buffers
- The following figure shows the TN TPUs and Non-TN TPUs in the cross sectional study: ![TN TPUs and Non-TN TPUs](https://github.com/bright1993ff66/Social-Media-Data-Analysis/blob/master/Figures/tn_tpus_nontn_tpus.png)

Lastly, by conducting [spatial join analysis]( https://pro.arcgis.com/en/pro-app/tool-reference/analysis/spatial-join.htm ), you could check whether one tweet is posted in the TN TPUs and Non-TN TPUs.

### 1.2 Prepare the dataset for longitudinal study

<span style='color:red'>In the longitudinal study</span>, we need to get tweets for both the treatment group and the control group(to be updated...):

- For instance, for Ho Man Tin MTR station, the following plot shows the buffer area, annulus area and the tweets posted in these areas: ![Longitudinal Plot](https://github.com/bright1993ff66/Social-Media-Data-Analysis/blob/master/Figures/longitudinal_study_plot.png)

## 2. Cross Sectional and Longitudinal Studies

<span style='color:red'>For the cross sectional study</span>, the code [cross_sectional_study.py](https://github.com/bright1993ff66/Social-Media-Data-Analysis/blob/master/transit_non_transit_comparision/cross_sectional_study.py) load the social demographic variables, normalize these data, and then build the regression model between the sentiment and the social demographic variables. All the social demographic variables we considered could be found in this [site](https://www.bycensus2016.gov.hk/en/bc-dp-tpu.html)

<span style='color:red'>For the longitudinal study</span>, the code [before_and_after_final_tpu.py]( https://github.com/bright1993ff66/Social-Media-Data-Analysis/blob/master/transit_non_transit_comparision/before_and_after_final_tpu.py ) draw the dashed line plot of sentiment for newly built stations on a monthly basis from July 7, 2016 to December 31, 2017. Moreover, it also shows the difference in tweet content before and after the opening of these stations, by drawing the wordcloud and topic modelling result

## 3. Difference in Difference Analysis

At last, the code [difference_in_difference_analysis.py]( https://github.com/bright1993ff66/Social-Media-Data-Analysis/blob/master/transit_non_transit_comparision/difference_in_difference_analysis.py ) illustrates how to build the difference in difference model to check the effectiveness of the transit neighborhood investment in the longitudinal study. 

The idea of selecting treatment and control groups and how to build the DID model are given in the following papers:

- [Transit-oriented economic development: The impact of light rail on new business starts in the Phoenix, AZ Region, USA](https://journals.sagepub.com/doi/full/10.1177/0042098017724119)
- [Do light rail transit investments increase employment opportunities? The case of Charlotte, North Carolina](https://rsaiconnect.onlinelibrary.wiley.com/doi/full/10.1111/rsp3.12184)

## 4. Strategy of Defining the Treatment Area and Control Area

Generally, to check the influence of a public service(such as subway and airport) to nearby areas(such as nearby people's sentiment, nearby places' economic development), the following two strategies could be considered:

- Some papers use the **circle-annulus setting** to define the treatment and control area, as illustrated before in subsection 1.2. Codes to prepare the data for this setting code be found in [create_data_for_circle_annulus_setting]( https://github.com/bright1993ff66/Social-Media-Data-Analysis/blob/master/transit_non_transit_comparision/create_data_for_circle_annulus_setting.py ). Moreover, codes to build the DID model based on the circle-annulus setting could be found in [before_and_after_final_circle]( https://github.com/bright1993ff66/Social-Media-Data-Analysis/blob/master/transit_non_transit_comparision/before_and_after_final_circle.py ). One representative work is: [Do light rail transit investments increase employment opportunities? The case of Charlotte, North Carolina](https://rsaiconnect.onlinelibrary.wiley.com/doi/full/10.1111/rsp3.12184)
- Other papers use the **census tracts** as the base to define the treatment area and control areas, since **census tracts** contain the local social demographic information. In this branch of method, researchers also draw circles around, for instance, the studied subway station. However, they use the census tracts which intersect with the buffers as the treatment area. Other census tracts which do not intersect with these buffers are considered as the control area.  One representative work is: [Transit investments and neighborhood change: On the likelihood of change]( https://www.sciencedirect.com/science/article/pii/S096669231730354X )

## More results would be updated in the following months...:blush:

