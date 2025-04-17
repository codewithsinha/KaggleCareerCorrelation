from bs4 import BeautifulSoup
import requests

import pandas as pd
import time,sys,json,os

from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import datetime

class InvalidSectionName(Exception):
    __module__ = Exception.__module__ #avoid __main__ before the user-defined exception

def manage_exception(Error):
	_, _, exception_traceback = sys.exc_info()
	print(f'Error Type: {type(Error).__name__}')
	print(f'Error Name: {Error}')
	print(f'Line no.: {exception_traceback.tb_lineno}')

def transform_participation_data(participation_data):
    column_names=[]
    column_values=[]
    for section in participation_data:
        current_section=participation_data[section]
        for feature in current_section:
            column_names.append(f'{section}_{feature}')
            column_values.append(current_section[feature])
    return column_names,column_values

#returns a dictionary with only a subset of its data.
def with_specific_keys(d, keys):
    return {x: d[x] for x in d if x in keys}

#returns data containing information about the user's participation in competitions, notebooks(scripts), datasets
#and discussions.
def get_participation_details(data):
    participation_data={}
    keys = ["tier", "totalResults","rankPercentage","rankCurrent","rankHighest","totalGoldMedals","totalSilverMedals","totalBronzeMedals"]
    sections=['competitions','scripts','datasets','discussions']
    for section in sections:
        summary=data[f'{section}Summary']
        desired_data=with_specific_keys(summary,keys)
        participation_data[section]=desired_data
    return participation_data

def years_since_joining(joined_date):
    try:
        current_date=datetime.today().strftime('%Y-%m-%d')

        joined_date=list(map(int,joined_date.split('-')))
        current_date=list(map(int,current_date.split('-')))

        joined_date=datetime(joined_date[0],joined_date[1],joined_date[2])
        current_date=datetime(current_date[0],current_date[1],current_date[2])

        time_difference=relativedelta(current_date,joined_date)
        years_difference=round(time_difference.years+time_difference.months/12,2)
    except Exception as Error:
        print('Error in obtaining years since the joining date')
        manage_exception(Error)
    
    return years_difference

def extract_individual_users_data(user_url):
    response = requests.get(user_url)
    if response.status_code==404:
        print('Error. Page could not be found on Kaggle.')
        return None
    if response.status_code==429:
        print('Too many requests')            
        return -1
    if response.status_code!=200:
        print(f'Unknown error. Response status code:{response.status_code}')
        return -1
    response_soup = BeautifulSoup(response.content, 'html5lib') 
    data = response_soup.find_all('script')
    required_data= data[-3].text
    consider_text_after='Kaggle.State.push('
    consider_text_before=');performance && performance.mark && performance.mark("ProfileContainerReact.componentCouldBootstrap");'
    dictionary_format_data=json.loads(required_data.split(consider_text_after)[1].split(consider_text_before)[0])
    return dictionary_format_data

def process_data(data,requirement='complete'):
    processed_data={}
    processed_data['name']=data['displayName']
    processed_data['username']=data['userName']
    processed_data['occupation']=data['occupation']
    processed_data['organization']=data['organization']
    processed_data['linkedin_profile_link']=data['linkedInUrl']
    processed_data['city']=data['city']
    processed_data['region']=data['region']
    processed_data['country']=data['country']

    joined_date=data['userJoinDate'].split('T')[0]
    processed_data['years_since_joined']=round(years_since_joining(joined_date),3)

    participation_data=get_participation_details(data)
    column_names,column_values=transform_participation_data(participation_data)
    for i,j in zip(column_names,column_values):
        processed_data[i]=j

    if requirement=='keys':
        return list(processed_data.keys())
    elif requirement=='values':
        return list(processed_data.values())
    elif requirement=='complete':
        return processed_data
    else:
        print('Requirement not specified properly')

def create_kaggle_users_dataframe(section):
    filename=f'kaggle_{section}_users_profile_dataframe.csv'
    if filename not in os.listdir():
        user_url='https://www.kaggle.com/abhishek'
        raw_data=extract_individual_users_data(user_url)
        columns=process_data(raw_data,requirement='keys')
        individual_users_dataframe=pd.DataFrame(columns=columns)
    else:
        individual_users_dataframe=pd.read_csv(filename)

    starting_index=len(individual_users_dataframe)
    print(starting_index)
    rankings_dataframe_filename=f'{section}_dataframe.csv'
    print(section)
    rankings_profile_list=pd.read_csv(rankings_dataframe_filename)['Profile'].values
    
    #Kaggle allows limited data to be scraped at a time, so after sending too many requests, we wait for 20 
    #minutes before sending the next batch of requests.
    for count,profile_link in enumerate(rankings_profile_list[starting_index:]):
        print(f'Count: {count+1}')
        print(f'Current Length: {starting_index+count}')
        try:
            raw_data=extract_individual_users_data(profile_link)
            while raw_data==-1:
                print('Waiting for 20 minutes')
                now = datetime.now()
                current_time = now.strftime("%H:%M") 
                print("Current Time: ", current_time)
                individual_users_dataframe.to_csv(filename,index=False)
                time.sleep(1200) #wait for 20 minutes before sending the next request.
                raw_data=extract_individual_users_data(profile_link)
            if raw_data==None:
                print('Skipping this profile')
                continue
            processed_data=process_data(raw_data)
            individual_users_dataframe=individual_users_dataframe.append(processed_data,ignore_index=True)
            print('Successfully inserted data')
        except KeyboardInterrupt:
            print('Stopping execution of the program')
            break
        except Exception as Error:
            print('Error in creating users dataframe')
            manage_exception(Error)
            break
    individual_users_dataframe.to_csv(filename,index=False)
    return individual_users_dataframe

if __name__ == "__main__":
    try:
        section=sys.argv[1]
        if section not in ['competitions','notebooks','datasets','discussions']:
            error_message=f"Invalid section name '{section}'. Please enter either of the following: competitions,notebooks,datasets,discussion"
            raise InvalidSectionName(error_message)
        create_kaggle_users_dataframe(section=section)
    except KeyboardInterrupt:
        print('Stopping execution of the program')
