from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException,TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

import pandas as pd
import numpy as np

import time,json,math,sys,os,platform,math
import re

from pyaudio import PyAudio
import sys

from pymongo import MongoClient

class InvalidSectionName(Exception):
	__module__ = Exception.__module__ #avoid __main__ before the user-defined exception

class skip_profile(Exception):
	def __init__(self):
		print('Exception occured: Skipping current profile.')

class stop_program_execution(Exception):
	def __init__(self):
		print('Exception occured: Stopping execution of the program')

def manage_exception(Error):
	_, _, exception_traceback = sys.exc_info()
	print(f'Error Type: {type(Error).__name__}\nError Name: {Error}\nLine no.: {exception_traceback.tb_lineno}')

"""Alert the user by playing a fixed frequency sound."""
def sine_tone(duration):
	frequency=440 #Hz
	volume=1
	sample_rate=22050
	n_samples = int(sample_rate * duration)
	restframes = n_samples % sample_rate

	audio_object = PyAudio()
	stream = audio_object.open(format=audio_object.get_format_from_width(1), # 8bit
	channels=1, # mono
	rate=sample_rate,
	output=True)

	s = lambda t: volume * math.sin(2 * math.pi * frequency * t / sample_rate)
	samples = (int(s(sample) * 0x7f + 0x80) for sample in range(n_samples))
	for buffer in zip(*[samples]*sample_rate): # write several samples at a time
		stream.write(bytes(bytearray(buffer)))

	# fill remainder of frameset with silence
	stream.write(b'\x80' * restframes)

	stream.stop_stream()
	stream.close()
	audio_object.terminate()

def extract_integer_from_string(string):
	if not isinstance(string,str):
		return None
	if len(string)==0:
		#print('Cannot extract integer. Empty string')
		return None
	try:
		return int(re.findall(r'\b\d+\b', string)[0])
	except Exception as Error:
		#print(f'Error in extracting integer value from the string- {string}')
		return None

def print_list(list_format_data,ending_character='\n'):
	for individual_element in list_format_data:
		print(individual_element,end=ending_character)
	print()

def create_database_connection(URL):
	try:
		connection = MongoClient(URL)
		print("Connected successfully to MongoDB")
		return connection
	except:
		print("Could not connect to MongoDB")
		return None

def update_database(database_name,collection_name,data,primary_key_value):
	try:
		database_name[collection_name].insert_one({"_id":primary_key_value,'data':data})
		print('successfully updated database.')
	except Exception as Error:
		print('Error in updating the database.')
		manage_exception(Error)

class extract_linkedin_data:
	
	def __init__(self,section):
		driver=webdriver.Chrome(executable_path='/usr/bin/chromedriver')
		self.driver=driver
		self.scrape_multiple_linkedin_profiles(section)

	#initialize Chrome WebDriver and sign in into LinkedIn.
	def sign_in(self):
		try:
			self.driver.get('https://www.linkedin.com')
			
			class_name='nav__button-secondary'
			#first_sign_in_button = WebDriverWait(driver,5).until(EC.presence_of_element_located((By.CLASS_NAME,class_name)))
			self.click_buttons(self.driver,xpath_value=f'//a[@class="{class_name}"]')
			
			WebDriverWait(self.driver,10).until(EC.presence_of_element_located((By.ID,'username')))
			email='ronithsinha17@gmail.com'
			password='Thirdpass123@'
			
			input_email_id=self.find_nth_child(self.driver,xpath_value='//input[@id="username"]',child_index=0)
			input_password=self.find_nth_child(self.driver,xpath_value='//input[@id="password"]',child_index=0)
			
			self.send_delayed_keys(input_email_id,email,delay=0.2)
			self.send_delayed_keys(input_password,password,delay=0.2)
			
			self.click_buttons(self.driver,xpath_value='//button[@aria-label="Sign in"]')
			if not self.check_for_linkedin_verification_page():
				print('Error in initalizing driver.')
				return None
			
			to_search=['linkedin.com/feed','linkedin.com/home']
			while not any(string in self.driver.current_url for string in to_search):
				time.sleep(1)

		except TimeoutException as Error:
			print('The sign in page took too long to load.')
			raise(stop_program_execution())

	def check_if_page_loaded(self,max_duration=20):
		count=0
		time.sleep(1)
		while not self.driver.execute_script("return document.readyState")=="complete":
			time.sleep(1)
			if count>max_duration:
				return None
			count+=1
		return 1

	def send_delayed_keys(self,element,text,delay):
		for character in text:
			time.sleep(delay)
			element.send_keys(character)
		time.sleep(delay)

	#find all elements containing the given xpath.
	def find_elements_by_xpath(self,parent_element,xpath_value):
		if parent_element == None:
			return None
		desired_elements=parent_element.find_elements_by_xpath(xpath_value)
		return desired_elements

	#find the nth(n=child_index) element containing the given xpath.
	def find_nth_child(self,parent_element,xpath_value,child_index):
		if parent_element == None:
			return None
		desired_elements=parent_element.find_elements_by_xpath(xpath_value)
		if len(desired_elements)==0:
			#print('The parent element does not contain any element that matches the required child element')
			return None
		if child_index<len(desired_elements):
			return desired_elements[child_index]
		return None

	#click all buttons containing the given xpath.
	def click_buttons(self,parent_element,xpath_value):
		if parent_element == None:
			return None
		while True:
			button_elements=parent_element.find_elements_by_xpath(xpath_value)
			if len(button_elements)==0:
				return None
			for button in button_elements:
				self.driver.execute_script("arguments[0].click();",button)
			ready_state=self.check_if_page_loaded()
			time.sleep(3)
			if not ready_state:
				#print('Unable to load page completely')
				return None
			

	#check whether the elements with the given xpath exist or not.
	def check_elements_by_xpath(self,parent_element,xpath_value):
		if parent_element == None:
			return None
		desired_elements=parent_element.find_elements_by_xpath(xpath_value)
		if len(desired_elements):
			return 1
		return None

	#get the text of the element containing the given xpath.
	def get_element_text(self,parent_element,xpath_value,substring_to_be_removed=''):
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

	#get the attribute of the element containing the given xpath.
	def get_element_attribute(self,parent_element,xpath_value,attribute_name):
		if parent_element == None:
			return None
		desired_elements=parent_element.find_elements_by_xpath(xpath_value)
		if len(desired_elements)==0:
			return None
		if len(desired_elements)==1:
			return desired_elements[0].get_attribute(attribute_name)
		required_data=[]
		for element in desired_elements:
			required_data.append(element.get_attribute(attribute_name))
		return required_data

	def fetch_basic_details(self):
		try:
			required_data={}
			#print('Basic Details')
			name=self.get_element_text(self.driver,xpath_value='//li[@class="inline t-24 t-black t-normal break-words"]')
			#print(name)
			required_data['name']=name
			description=self.get_element_text(self.driver,xpath_value='//h2[@class="mt1 t-18 t-black t-normal break-words"]')
			#print(description)
			required_data['description']=description

			location_and_followers_details=self.get_element_text(self.driver,xpath_value='//li[@class="t-16 t-black t-normal inline-block"]')
			if isinstance(location_and_followers_details,list):
				if len(location_and_followers_details)==2:
					location=location_and_followers_details[0]
					followers=location_and_followers_details[1]
					required_data['location']=location
					required_data['followers']=followers

					#print(location)
					#print(followers)
			else:
				#print(location_and_followers_details)
				required_data['location']=location_and_followers_details
			connections=self.get_element_text(self.driver,xpath_value='//span[@class="t-16 t-black t-normal"]')
			#print(connections)
			#print()
			required_data['connections']=connections
			return required_data
		except Exception as Error:
			#print('Error in fetching basic details.')
			manage_exception(Error)
			return None

	def fetch_about_section_details(self):
		try:
			#print('About Section')
			about_section_found=self.check_elements_by_xpath(self.driver,xpath_value='//section[contains(@class,"pv-about-section")]')
			if about_section_found==1:
				self.click_buttons(self.driver,xpath_value='//p[contains(@class,"pv-about__summary-text")]//a[@id="line-clamp-show-more-button"]')
				about_section_details=self.get_element_text(self.driver,xpath_value='//p[contains(@class,"pv-about__summary-text")]',substring_to_be_removed='see less')
				#print(about_section)
				#print()
				return about_section_details
			return None
		except Exception as Error:
			print('Error in fetching About section details')
			manage_exception(Error)
			return None

	def fetch_experience_details(self):
		try:
			#print('Experience Section')
			experience_section_xpath_value='//section[@id="experience-section"]'
			experience_section_found=self.check_elements_by_xpath(self.driver,experience_section_xpath_value)
			if experience_section_found==1:
				experience_section_element=self.find_nth_child(self.driver,experience_section_xpath_value,child_index=0)
				self.click_buttons(experience_section_element,xpath_value='.//button[@aria-expanded="false"]')
				experience_elements=self.find_elements_by_xpath(experience_section_element,xpath_value='.//li/section')
				all_positions_data=[]
				for element in experience_elements:
					one_organization_multiple_positions_element=self.find_elements_by_xpath(element,xpath_value='.//div[contains(@class,"pv-entity__role-details-container")]')
					if len(one_organization_multiple_positions_element):
						#print('Multiple positions in one organization')
						company_name=self.get_element_text(element,xpath_value='.//div[contains(@class,"pv-entity__company-summary-info")]/h3/span[not(@class="visually-hidden")]')
						#print(f'Company Name: {company_name}')
						
						one_organization_multiple_positions_data=[]
						for position in one_organization_multiple_positions_element:
							position_name=self.get_element_text(position,xpath_value='./div/h3/span[not(@class="visually-hidden")]')
							position_details=self.get_element_text(position,xpath_value='.//p[contains(@class,"pv-entity__description")]',substring_to_be_removed='see less')
							employment_year_range=self.get_element_text(position,xpath_value='.//h4[@class="pv-entity__date-range t-14 t-black--light t-normal"]',substring_to_be_removed='Dates Employed\n')
							employment_duration_years=self.get_element_text(position,xpath_value='.//h4[@class="t-14 t-black--light t-normal"]',substring_to_be_removed='Employment Duration\n')

							#print(f'Position Name: {position_name}')
							#print(f'Position Details:\n{position_details}')
							#print(f'Employment Year Range: {employment_year_range}')
							#print(f'Employment Duration: {employment_duration_years}')

							position_data={'position name':position_name,'position details':position_details,'employment year range':employment_year_range,'employment duration':employment_duration_years}
							one_organization_multiple_positions_data.append(position_data)

						all_positions_data.extend([{'company name':company_name,'multiple positions details':one_organization_multiple_positions_data}])
							
					else:
						#print('One position')
						position_name=self.get_element_text(element,xpath_value='.//div[contains(@class,"pv-entity__summary-info--background-section")]/h3')
						company_name=self.get_element_text(element,xpath_value='.//p[contains(@class,"pv-entity__secondary-title")]')
						position_details=self.get_element_text(element,xpath_value='.//p[contains(@class,"pv-entity__description")]',substring_to_be_removed='see less')
						employment_year_range=self.get_element_text(element,xpath_value='.//h4[@class="pv-entity__date-range t-14 t-black--light t-normal"]',substring_to_be_removed='Dates Employed\n')
						employment_duration_years=self.get_element_text(element,xpath_value='.//h4[@class="t-14 t-black--light t-normal"]',substring_to_be_removed='Employment Duration\n')

						position_data={'company name':company_name,'position name':position_name,'position details':position_details,'employment year range':employment_year_range,'employment duration':employment_duration_years}
						all_positions_data.append(position_data)

						#print(f'Company Name: {company_name}')
						#print(f'Position Name: {position_name}')
						#print(f'Position Details:\n{position_details}')
						#print(f'Employment Year Range: {employment_year_range}')
						#print(f'Employment Duration: {employment_duration_years}')
						
					#print()
				return all_positions_data
			return None
		except Exception as Error:
			print('Error in fetching Experience details')
			manage_exception(Error)
			return None

	def fetch_education_details(self):
		try:	
			#print('Education Section')
			education_section_xpath_value='//section[@id="education-section"]'
			education_section_found=self.check_elements_by_xpath(self.driver,education_section_xpath_value)
			if education_section_found==1:
				education_section_element=self.find_nth_child(self.driver,education_section_xpath_value,0)
				education_elements=self.find_elements_by_xpath(education_section_element,xpath_value='.//li[contains(@class,"pv-education-entity")]')
				all_courses_data=[]
				for element in education_elements:
					university_name=self.get_element_text(element,xpath_value='.//h3[contains(@class,"pv-entity__school-name")]')
					degree_name=self.get_element_text(element,xpath_value='.//p[contains(@class,"pv-entity__degree-name")]',substring_to_be_removed='Degree Name\n')
					domain_name=self.get_element_text(element,xpath_value='.//p[contains(@class,"pv-entity__fos")]',substring_to_be_removed='Field Of Study\n')
					grade=self.get_element_text(element,xpath_value='.//p[contains(@class,"pv-entity__grade")]',substring_to_be_removed='Grade\n')
					course_description=self.get_element_text(element,xpath_value='.//p[contains(@class,"pv-entity__description")]',substring_to_be_removed='see less')
					
					course_data={'university name':university_name,'degree name':degree_name,'domain name':domain_name,'grade':grade,'course description':course_description}
					all_courses_data.append(course_data)
					#print(f'University: {university_name}')
					#print(f'Degree Name: {degree_name}')
					#print(f'Domain Name: {domain_name}')
					#print(f'Grade: {grade}')
					#print(f'Course Description: {course_description}')
					#print()
				return all_courses_data
			return None
		except Exception as Error:
			print('Error in fetching Education details')
			manage_exception(Error)
			return None

	def fetch_licenses_and_certifications_details(self):
		try:
			#print('Licenses and Certifications Section')
			licenses_and_certifications_section_xpath_value='//section[@id="certifications-section"]'
			licenses_and_certifications_section_found=self.check_elements_by_xpath(self.driver,licenses_and_certifications_section_xpath_value)
			if licenses_and_certifications_section_found==1:
				licenses_and_certifications_section_element=self.find_nth_child(self.driver,licenses_and_certifications_section_xpath_value,0)
				self.click_buttons(licenses_and_certifications_section_element,xpath_value='.//button[@aria-expanded="false"]')
				licenses_and_certifications_elements=self.find_elements_by_xpath(licenses_and_certifications_section_element,xpath_value='.//li[contains(@class,"pv-certification-entity")]')

				all_licenses_and_ceritifications_data=[]
				for element in licenses_and_certifications_elements:
					certification_name=self.get_element_text(element,xpath_value='.//div[contains(@class,"pv-entity__summary-info")]/h3')
					#print(f'Certification Name: {certification_name}')

					issuing_authority_element=self.find_nth_child(element,xpath_value='.//p[contains(@class,"t-14")]',child_index=0)
					issuing_authority=self.get_element_text(issuing_authority_element,'.',substring_to_be_removed='Issuing authority\n')
					#print(f'Issuing Authority: {issuing_authority}')

					credentialID_element=self.find_nth_child(element,xpath_value='.//p[contains(@class,"t-14 t-black--light")]',child_index=0)
					credentialID=self.get_element_text(credentialID_element,'.',substring_to_be_removed='Credential Identifier\nCredential ID ')
					#print(f'Credential ID: {credentialID}')

					credential_link=self.get_element_attribute(element,".//a[contains(@class,'pv-certifications-entity__credential-link')]",'href')
					#print(f'Credential Link: {credential_link}')
					#print()

					certification_data={'certification name':certification_name,'certification issuing authority':issuing_authority,'credential ID':credentialID,'credential link':credential_link}
					all_licenses_and_ceritifications_data.append(certification_data)

				return all_licenses_and_ceritifications_data
			return None
		except Exception as Error:
			print('Error in fetching Licenses and Certifications details')
			manage_exception(Error)
			return None

	def fetch_skills_and_endorsements_details(self):
		try:
			#print('Skills and Endorsements Section')
			skills_and_endorsements_section_xpath_value='//section[contains(@class,"pv-skill-categories-section")]'
			skills_and_endorsements_section_found=self.check_elements_by_xpath(self.driver,skills_and_endorsements_section_xpath_value)
			if skills_and_endorsements_section_found==1:
				skills_and_endorsements_element=self.find_nth_child(self.driver,skills_and_endorsements_section_xpath_value,0)
				self.click_buttons(skills_and_endorsements_element,xpath_value='.//button[@aria-expanded="false"]')
				skills_list=self.get_element_text(skills_and_endorsements_element,xpath_value='.//span[contains(@class,"pv-skill-category-entity__name-text")]')
				#print('Skills List')
				#print_list(skills_list,ending_character=' ')
				#print()
				return skills_list
			return None
		except Exception as Error:
			print('Error in fetching Skills and Endorsements details')
			manage_exception(Error)
			return None    

	def fetch_recommendations_details(self):
		try:
			#print('Recommendations Section')
			recommendations_section_xpath_value='//button[contains(@class,"ml0") and contains(@class,"artdeco-tab") and contains(@class,"ember-view")]'
			recommendations_section_found=self.check_elements_by_xpath(self.driver,recommendations_section_xpath_value)
			if recommendations_section_found==1:
				recommendations_text=self.get_element_text(self.driver,recommendations_section_xpath_value)
				no_of_recommendations=extract_integer_from_string(recommendations_text)
				return no_of_recommendations
			return None
		except Exception as Error:
			print('Error in fetching Recommendations details')
			manage_exception(Error)
			return None           

	def fetch_honors_and_awards_details(self,accomplishment_section_element):
		try:
			#print('Honors and Awards Section')
			honors_section_element=self.find_nth_child(accomplishment_section_element,xpath_value='.//section[contains(@class,"honors")]',child_index=0)
			if honors_section_element:
				self.click_buttons(honors_section_element,xpath_value='.//button[@aria-expanded="false"]')
				honors_and_awards_elements=self.find_elements_by_xpath(self.driver,xpath_value='.//ul[contains(@class,"pv-accomplishments-block__list")]/li')
				all_honor_and_awards_data=[]
				for honor_and_award in honors_and_awards_elements:
					honor_title=self.get_element_text(honor_and_award,xpath_value='.//h4[contains(@class,"pv-accomplishment-entity__title")]',substring_to_be_removed='honor title\n')
					honor_issuer=self.get_element_text(honor_and_award,xpath_value='.//span[contains(@class,"pv-accomplishment-entity__issuer")]',substring_to_be_removed='honor issuer\n')
					honor_description=self.get_element_text(honor_and_award,xpath_value='.//p[contains(@class,"pv-accomplishment-entity__description")]',substring_to_be_removed='honor description\n')
					honor_link=self.get_element_attribute(honor_and_award,xpath_value='.//a[contains(@class,"pv-accomplishment-entity__external-source")]',attribute_name='href')
					
					#print(f'Honor Title: {honor_title}')
					#print(f'Honor Issuer: {honor_issuer}')
					#print(f'Honor Description: {honor_description}')
					#print(f'Honor Link: {honor_link}')
					#print()

					honor_and_awards_data={'honor title':honor_title,'honor issuer':honor_issuer,'honor description':honor_description,'honor link':honor_link}
					all_honor_and_awards_data.append(honor_and_awards_data)
				return all_honor_and_awards_data
			return None
		except Exception as Error:
			print('Error in fetching Honors and Awards details')
			manage_exception(Error)
			return None

	def fetch_courses_details(self,accomplishment_section_element):
		try:
			#print('Courses Section')
			courses_section_element=self.find_nth_child(accomplishment_section_element,xpath_value='.//section[contains(@class,"courses")]',child_index=0)
			if courses_section_element:
				self.click_buttons(courses_section_element,xpath_value='.//button[@aria-expanded="false"]')
				courses_elements=self.find_elements_by_xpath(courses_section_element,xpath_value='.//ul[contains(@class,"pv-accomplishments-block__list")]/li')
				all_online_courses_data=[]
				for course_element in courses_elements:
					course_name=self.get_element_text(course_element,xpath_value='.//h4[contains(@class,"pv-accomplishment-entity__title")]',substring_to_be_removed='Course name\n') 
					#print(f'Course name: {course_name}')
					#print()
					all_online_courses_data.append(course_name)
				return all_online_courses_data
			return None
		except Exception as Error:
			print('Error in fetching Courses details')
			manage_exception(Error)
			return None

	def fetch_projects_details(self,accomplishment_section_element):
		try:
			#print('Projects Section')
			projects_section_element=self.find_nth_child(accomplishment_section_element,xpath_value='.//section[contains(@class,"projects")]',child_index=0)
			if projects_section_element:
				self.click_buttons(projects_section_element,xpath_value='.//button[@aria-expanded="false"]')
				projects_elements=self.find_elements_by_xpath(projects_section_element,xpath_value='.//ul[contains(@class,"pv-accomplishments-block__list")]/li')
				all_projects_data=[]
				for project in projects_elements:
					project_name=self.get_element_text(project,xpath_value='.//h4[contains(@class,"pv-accomplishment-entity__title")]',substring_to_be_removed='Project name\n')
					project_description=self.get_element_text(project,xpath_value='.//p[contains(@class,"pv-accomplishment-entity__description")]',substring_to_be_removed='Project description\n')
					project_link=self.get_element_attribute(project,xpath_value='.//a[contains(@class,"pv-accomplishment-entity__external-source")]',attribute_name='href')

					#print(f'Project Name: {project_name}')
					#print(f'Project Description: {project_description}')
					#print(f'Project Link: {project_link}')
					#print()
					project_data={'project name':project_name,'project description':project_description,'project link':project_link}
					all_projects_data.append(project_data)
				return all_projects_data
			return None
		except Exception as Error:
			print('Error in fetching Projects details')
			manage_exception(Error)
			return None          

	def fetch_publications_details(self,accomplishment_section_element):
		try:
			#print('Publications Section')
			publication_section_element=self.find_nth_child(accomplishment_section_element,xpath_value='.//section[contains(@class,"publications")]',child_index=0)
			if publication_section_element:
				self.click_buttons(publication_section_element,xpath_value='.//button[@aria-expanded="false"]')
				publication_elements=self.find_elements_by_xpath(publication_section_element,xpath_value='.//ul[contains(@class,"pv-accomplishments-block__list")]/li')
				all_publications_data=[]
				for publication in publication_elements:
					publication_title=self.get_element_text(publication,xpath_value='.//h4[contains(@class,"pv-accomplishment-entity__title")]',substring_to_be_removed='publication title\n')
					publication_issuer=self.get_element_text(publication,xpath_value='.//span[contains(@class,"pv-accomplishment-entity__publisher")]',substring_to_be_removed='publication description\n')
					publication_description=self.get_element_text(publication,xpath_value='.//p[contains(@class,"pv-accomplishment-entity__description")]',substring_to_be_removed='publication description\n')
					publication_link=self.get_element_attribute(publication,xpath_value='.//a[contains(@class,"pv-accomplishment-entity__external-source")]',attribute_name='href')

					#print(f'Publication Title: {publication_title}')
					#print(f'Publication Issuer: {publication_issuer}')
					#print(f'Publication Description: {publication_description}')
					#print(f'Publication Link: {publication_link}')
					#print()
					publication_data={'publication title':publication_title,'publication issuer':publication_issuer,'publication description':publication_description,'publication link':publication_link}
					all_publications_data.append(publication_data)
				return all_publications_data
			return None
		except Exception as Error:
			print('Error in fetching Publications details')
			manage_exception(Error)
			return None        

	def fetch_patents_details(self,accomplishment_section_element):
		try:
			#print('Patents Section')
			patents_section_element=self.find_nth_child(accomplishment_section_element,xpath_value='.//section[contains(@class,"patents")]',child_index=0)
			if patents_section_element:
				self.click_buttons(patents_section_element,xpath_value='.//button[@aria-expanded="false"]')
				patents_elements=self.find_elements_by_xpath(patents_section_element,xpath_value='.//ul[contains(@class,"pv-accomplishments-block__list")]/li')
				all_patents_data=[]
				for patent in patents_elements:
					patent_title=self.get_element_text(patent,xpath_value='.//h4[contains(@class,"pv-accomplishment-entity__title")]',substring_to_be_removed='Patent title\n')
					patent_description=self.get_element_text(patent,xpath_value='.//p[contains(@class,"pv-accomplishment-entity__description")]',substring_to_be_removed='Patent description\n')
					patent_link=self.get_element_attribute(patent,xpath_value='.//a[contains(@class,"pv-accomplishment-entity__external-source")]',attribute_name='href')

					#print(f'Patent Title: {patent_title}')
					#print(f'Patent Description: {patent_description}')
					#print(f'Patent Link: {patent_link}')
					#print()
					patent_data={'patent title':patent_title,'patent description':patent_description,'patent link':patent_link}
					all_patents_data.append(patent_data)
				return all_patents_data
			return None
		except Exception as Error:
			print('Error in fetching Patents details')
			manage_exception(Error)
			return None

	def fetch_accomplishments_details(self):
		try:
			#print('Accomplishments Section')
			required_data={}
			accomplishment_section_xpath_value='//section[contains(@class,"pv-accomplishments-section")]'
			accomplishment_section_found=self.check_elements_by_xpath(self.driver,accomplishment_section_xpath_value)
			if accomplishment_section_found==1:
				accomplishment_section_element=self.find_nth_child(self.driver,accomplishment_section_xpath_value,child_index=0)

				#Honors and Awards.
				honors_and_awards_data=self.fetch_honors_and_awards_details(accomplishment_section_element)

				#Courses.
				courses_data=self.fetch_courses_details(accomplishment_section_element)

				#Projects.
				projects_data=self.fetch_projects_details(accomplishment_section_element)

				#Publications.
				publications_data=self.fetch_publications_details(accomplishment_section_element)

				#Patents.
				patents_data=self.fetch_patents_details(accomplishment_section_element)
			
				required_data['honors and awards']=honors_and_awards_data
				required_data['courses']=courses_data
				required_data['projects']=projects_data
				required_data['publications']=publications_data
				required_data['patents']=patents_data
				
				return required_data
			return None
		except Exception as Error:
			print('Error in fetching Accomplishments details')
			manage_exception(Error)
			return None

	"""
	check if LinkedIn Verification process has come up. If yes, then alert the user by playing a fixed frequency
	sound (using 'sine_tone()' function) and then wait until the verification process is manually completed by the
	user.
	"""
	def check_for_linkedin_verification_page(self):
		if ('https://www.linkedin.com/checkpoint' in self.driver.current_url) or (self.check_elements_by_xpath(self.driver,'//h1[contains(@text,"Let\'s do a quick security check\")]')==1):
			print('Reached LinkedIn Verification page. Manual verification required!')
			sine_tone(20)

			print('Waiting for linkedin verification process to be over.')
			to_search=['linkedin.com/feed','linkedin.com/home','linkedin.com/in/']
			while not any(string in self.driver.current_url for string in to_search):
				sine_tone(10)
			return 1		
		return 1

	"""
	The profile might not be available or the profile link might re-direct us to the LinkedIn feed itself or the
	LinkedIn verification process might pop up. We need to detect and handle each of these situations.
	"""
	def handle_anomalies(self):
		try:
			to_search=['linkedin.com/feed','linkedin.com/home']
			if any(string in self.driver.current_url for string in to_search):
				print('Reached LinkedIn feed')
				return None

			if self.check_elements_by_xpath(self.driver,xpath_value='//a[contains(@text,"Sign in")]') or self.check_elements_by_xpath(self.driver,xpath_value='//button[contains(@text,"Sign in")]'):
				print('Need to Sign In first.')
				print('Waiting for LinkedIn Sign In process to be over. If the user is already signed in, just go to "https://www.linkedin.com/feed"')
				to_search=['linkedin.com/feed','linkedin.com/home','linkedin.com/in/']
				while not any(string in self.driver.current_url for string in to_search):
					sine_tone(10)
				return 1

			if self.driver.current_url=='https://www.linkedin.com/in/unavailable/':
				print('Current profile is unavailable')
				return None

			if self.check_elements_by_xpath(self.driver,xpath_value='//h1[contains(@text,"Page not found")]'):
				print('Page not found')
				return None

			if self.check_for_linkedin_verification_page():
				return 1
				print('Anomaly on LinkedIn Verification page. Cannot detect the anomaly.')
				return None

			return 1
		
		except Exception as Error:
			manage_exception(Error)
			sine_tone(30)
			
	#scroll the page until the desired element is found.
	def scroll_page_until_element_found(self,xpath_value,max_iterations=30):
		iterations=1
		while iterations<=max_iterations:
			desired_element=self.check_elements_by_xpath(self.driver,xpath_value)
			if desired_element==1:
				return 1
			self.driver.find_element_by_xpath('//body').send_keys(Keys.PAGE_DOWN)
			ready_state=self.check_if_page_loaded(max_duration=5)
			if not ready_state:
				return None
			iterations+=1
		print('Unable to scroll down to the element.')
		print(f'URL: {self.driver.current_url}\nIterations: {iterations}')
		sine_tone(10)
		return None

	#scrape the linkedin profile of the specified LinkedIn profile.
	def scrape_linkedin_profile(self,profile_link):
		try:
			
			self.driver.get(profile_link)
			if not self.check_if_page_loaded():
				return None

			#detect the anomalies possible on the page.
			anomalies_handled=self.handle_anomalies()
			if not anomalies_handled:
				raise(skip_profile())
			
			#scroll to the bottom of the page and load everything on the page.
			scroll_successful=None
			max_iterations=3
			current_iteration=1
			while current_iteration<=max_iterations:
				scroll_successful=self.scroll_page_until_element_found(xpath_value='//p[@id="globalfooter-copyright"]')
				if scroll_successful:
					break
				current_iteration+=1
				self.driver.refresh()
			if not scroll_successful:
				raise(skip_profile())

			required_data={}

			#Basic details.
			basic_details=self.fetch_basic_details()
			
			#About.
			about_section_data=self.fetch_about_section_details()
			
			#Experience.
			experience_data=self.fetch_experience_details()
			
			#Education.
			education_data=self.fetch_education_details()
			
			#Licenses and Certifications.
			licenses_and_certifications_data=self.fetch_licenses_and_certifications_details()
			
			#Skills and Endorsements.
			skills_and_endorsements_data=self.fetch_skills_and_endorsements_details()
			
			#Recommendations.
			recommendations_data=self.fetch_recommendations_details()
			
			#Accomplishments.
			accomplishments_data=self.fetch_accomplishments_details()

			required_data['general details']=basic_details
			required_data['about section data']=about_section_data
			required_data['experience']=experience_data
			required_data['education']=education_data
			required_data['licenses and certifications']=licenses_and_certifications_data
			required_data['skills and endorsements']=skills_and_endorsements_data
			required_data['recommendations']=recommendations_data
			required_data['accomplishments']=accomplishments_data

			return required_data

		except skip_profile as Error:
			return None

		except KeyboardInterrupt as Error:
			raise(stop_program_execution())

		except Exception as Error:
			if type(Error).__name__=='MaxRetryError':
				print('Chrome Webdriver not reachable.')
				raise(stop_program_execution())
			if self.driver==None:
				print('Cannot fetch the Chrome Webdriver object.')
				raise(stop_program_execution())
			print('Error in getting LinkedIn data')
			manage_exception(Error)
			return None

	def scrape_multiple_linkedin_profiles(self,section):
		try:
			connection=create_database_connection('mongodb://localhost:27017/')
			linkedin_database = connection.linkedin_database
			collection_name=f'{section}_linkedin_data'
			linkedin_profile_data=linkedin_database[collection_name]

			last_record=list(linkedin_profile_data.find().sort([('_id', -1)]).limit(1))
			last_record_id=-1
			
			try:
				last_record_id=last_record[0]['_id']
			except IndexError as Error:
				print(f'Empty collection: {collection_name}')

			missed_profiles=[]
			filename=f'kaggle_{section}_users_profile_dataframe.csv'
			linkedin_profile_list=pd.read_csv(filename)['linkedin_profile_link'].values

			self.sign_in()

			for count,profile_link in enumerate(linkedin_profile_list[last_record_id+1:]):
				if isinstance(profile_link,str): #if the profile link is not of class 'str', it is a NaN value.
					current_record_id=count+last_record_id+1
					print(f'Count: {current_record_id}\nProfile link: {profile_link}')
					scraped_linkedin_data=self.scrape_linkedin_profile(profile_link)
					if isinstance(scraped_linkedin_data,dict):
						#for key,value in scraped_linkedin_data.items():
							#print(key,value)
						update_database(linkedin_database,collection_name,scraped_linkedin_data,current_record_id)
					else:
						print('Data could not be fetched from the specified linkedin profile.')
						
		except KeyboardInterrupt as stop_cell:
			print('Stopping program execution')
		except stop_program_execution as stop_cell:
			pass
		except Exception as Error:
			manage_exception(Error)
if __name__ == "__main__":
	try:
		section=sys.argv[1]
		if section not in ['competitions','notebooks','datasets','discussions']:
			error_message=f"Invalid section name '{section}'. Please enter either of the following: competitions,notebooks,datasets,discussions"
			raise InvalidSectionName(error_message)
		extract_linkedin_data(section)
	except KeyboardInterrupt:
		print('Stopping execution of the program')