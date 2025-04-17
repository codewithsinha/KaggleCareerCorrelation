from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd

import time,sys

class InvalidSectionName(Exception):
    __module__ = Exception.__module__ #avoid __main__ before the user-defined exception
    
def manage_exception(Error):
	_, _,exception_traceback = sys.exc_info()
	print(f'Error Type: {type(Error).__name__}')
	print(f'Error Name: {Error}')
	print(f'Line no.: {exception_traceback.tb_lineno}')

#find all elements containing the given xpath.
def find_elements_by_xpath(parent_element,xpath_value):
	if parent_element == None:
		return None
	desired_elements=parent_element.find_elements_by_xpath(xpath_value)
	return desired_elements

#find the nth(n=child_index) element containing the given xpath.
def find_nth_child(parent_element,xpath_value,child_index):
	if parent_element == None:
		return None
	desired_elements=parent_element.find_elements_by_xpath(xpath_value)
	if len(desired_elements)==0:
		print('The parent element does not contain any element that matches the required child element')
		return None
	if child_index<len(desired_elements):
		return desired_elements[child_index]
	return None

#get the text of the element containing the given xpath.
def get_element_text(parent_element,xpath_value,substring_to_be_removed=''):
	if parent_element == None:
		return None
	desired_elements=parent_element.find_elements_by_xpath(xpath_value)
	text=[]
	for element in desired_elements:
		text.append(element.text.replace(substring_to_be_removed,''))
	if len(desired_elements)==1:
		return text[0]
	if len(desired_elements)==0:
		return None
	return text

def extract_kaggle_rankings_data(url):
    driver=webdriver.Chrome(executable_path="/home/ronith/anaconda3/bin/chromedriver")
    driver.get(url)
    time.sleep(5)
    print('Starting to scroll down')
    
    #scroll down until the bottom of the page is reached.
    while True:
        last_leaderboard_rank_element=find_nth_child(driver,xpath_value='//div[@class="leaderboards__rank"]',child_index=-1)
        actions = ActionChains(driver)
        actions.move_to_element(last_leaderboard_rank_element).perform()
        footer_elements= driver.find_elements_by_class_name('leaderboards__list-footer')
        if len(footer_elements):
            break

    print('\nFinished scrolling\n')
    print('Starting scraping')

    #After the desired number of users have appeared on the page, start scraping the page for the desired
    #information.
    try:
        profiles_data=pd.DataFrame(columns=['Rank','Name','Tier','Gold','Silver','Bronze','Points'])
        
        profile_list=find_elements_by_xpath(driver,xpath_value="//div[@class='block-link block-link--bordered']")
        for index,profile in enumerate(profile_list):
            rank=get_element_text(profile,xpath_value=".//div[@class='leaderboards__rank']")
            
            tier_element=find_nth_child(profile,xpath_value=".//img[@title='grandmaster' or @title='master' or @title='expert' or @title='novice' or @title='contributor']",child_index=0)
            tier=tier_element.get_attribute('title')
            
            name=get_element_text(profile,xpath_value='.//div[@class="leaderboards__name"]')
            no_of_gold_medals=get_element_text(profile,xpath_value='.//div[@class="leaderboards__medal--gold"]')
            no_of_silver_medals=get_element_text(profile,xpath_value='.//div[@class="leaderboards__medal--silver"]')
            no_of_bronze_medals=get_element_text(profile,xpath_value='.//div[@class="leaderboards__medal--bronze"]')
            leaderboard_points=get_element_text(profile,xpath_value='.//div[@class="leaderboards__points"]')

            profiles_data.loc[index]=[rank,name,tier,no_of_gold_medals,no_of_silver_medals,no_of_bronze_medals,leaderboard_points]
            
    except Exception as Error:
        manage_exception(Error)
    driver.quit()
    
    profiles_data.set_index('Rank',inplace=True)
    return profiles_data

#if the feature lengths are unbalanced, we need to balance them so that we can create a uniform database.
#For example, while scraping, leaderboards_rank_list might have a different length as compared to 
#leaderboards_name_list. In this case, we first find the minimum length amongst all the features and then
#only consider all the features upto that specific length.

def remove_unwanted_data(data):
    minimum_length=min([len(individual_data) for individual_data in data])
    processed_data=[individual_data[:minimum_length] for individual_data in data]
    return processed_data

#This function returns a dataframe containing the processed data.
def create_dataframe(data):
    dictionary_data={'Name':data[0],'Profile':data[1],'Tier':data[2],'Gold':data[3],'Silver':data[4],'Bronze':data[5],
          'Points':data[6]}
    dataframe=pd.DataFrame(dictionary_data,index=[i+1 for i in range(len(data[0]))])
    return dataframe

def main(section):
    competitions_ranking_url='https://www.kaggle.com/rankings?sortBy=null&group=competitions'
    datasets_ranking_url='https://www.kaggle.com/rankings?sortBy=null&group=datasets'
    notebooks_ranking_url='https://www.kaggle.com/rankings?sortBy=null&group=notebooks'
    discussions_ranking_url='https://www.kaggle.com/rankings?sortBy=null&group=discussion'

    url_name=f'{section}_ranking_url'
    url=globals()[url_name]
    
    data=extract_kaggle_rankings_data(url)
    display(data)
    filename=f'{section}_dataframe.csv'
    dataframe.to_csv(filename,index=False)

if __name__ == "__main__":
    try:
        section=sys.argv[1]
        if section not in ['competitions','notebooks','datasets','discussions']:
            error_message=f"Invalid section name '{section}'. Please enter either of the following: competitions,notebooks,datasets,discussions"
            raise InvalidSectionName(error_message)
        main(section=section)
    except KeyboardInterrupt:
        print('Stopping execution of the program')
