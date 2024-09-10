# Import necessary libraries
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re
import numpy as np

#Launch my webdriver

url = 'https://www.indeed.com/jobs?q=Data+Science&l=Los+Angeles%2C+CA&vjk=74cadd03cb0dd918'
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
driver.get(url)
# a chrome pop-up should be seen

# all the scraping

# Create empty lists where data will be stored in
job_titles = []
company_names = []
company_ratings = []
company_locations = []
job_pays = []
descriptions = []
posted = []

#Find pagination element (navigation bar)
pagination = driver.find_element(By.XPATH, ".//nav[contains(@role, 'navigation')]")
#Locate where the last page on the current bar is
last_page = pagination.find_elements(By.XPATH, ".//a[contains(@data-testid, 'pagination-page-5')]")[-1].text
# Deals with loading time of the page, wait 10 seconds to make sure it won't respond
driver.set_page_load_timeout(10)

#iterate through all the pages
for page_num in range(1, int(last_page) + 18):

    container = driver.find_element(By.XPATH, ".//div[contains(@id, 'mosaic-jobResults')]")
    all_jobs = container.find_elements(By.XPATH, ".//div[contains(@class, 'job_seen_beacon')]")
    # Iterate through all jobs in all_jobs list
    for job in all_jobs:
        title = job.find_element(By.XPATH, ".//h2[contains(@class, 'jobTitle')]").text
        # not all jobs have a valid location in the same spot, so the try and except handles this
        try:
            location = job.find_element(By.XPATH, ".//div[contains(@class, 'company_location')]").text.split("\n")[1]
        except:
            location = job.find_element(By.XPATH, ".//div[contains(@class, 'company_location')]").text.split("\n")[0]
        
        company = job.find_element(By.XPATH, ".//div[contains(@class, 'company_location')]").text.split("\n")[0]
        when_posted= job.find_element(By.XPATH, ".//tr[contains(@class, 'underShelfFooter')]").text.split("\n")[-1].strip("More...")
        description = job.find_element(By.XPATH, ".//tr[contains(@class, 'underShelfFooter')]").text.split("\n")[0]
        # Some jobs also don't always include salary so the try and except checks this
        try:
            string = job.find_element(By.XPATH, ".//div[contains(@class, 'salary-snippet-container')]").text
            listy = string.split()
            for element in listy:
                # if it has a dollar sign then I know it is a pay amount
                if "$" in element:
                    pay = element
        except:
            pay = "NaN"

        #append all categories
        job_titles.append(title)
        job_pays.append(pay)
        company_names.append(company)
        descriptions.append(description)
        company_locations.append(location)
        posted.append(when_posted)
    page_num += 1
    #try to click to the next page if there is one to go to
    try:
        #sometimes page content loads slower than elements so wait handles this
        next = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//a[contains(@aria-label, 'Next Page')]")))
        print(next)
        next.click()
    except:
        #print statement shows how many pages I was able to get for my data
        print(f'failed {page_num-1}')
        break
#quit the driver now that I am done with it
driver.quit()

# all the data cleaning
#separate into city and state

#try getting hybrid or remote status
def enviro(location):
    if "Hybrid" in location or "hybrid" in location:
        return 'Hybrid'
    elif "Remote" in location or "remote" in location:
        return "Remote"
    elif "On-Site" in location or "on-site" in location:
        return 'On-Site'
    else:
        return np.nan
    

cities = []
states = []
enviros = []
# Parse location data
for location in company_locations:
    parts = location.split(', ')
    if len(parts) > 1:
        job_enviro = enviro(location)
        #remove modality keywords from locations
        city = parts[0].replace("Hybrid", "")
        city = city.replace("remote", '')
        city = city.replace("Remote", '')
        city = city.replace("Hybrid", '')
        city = city.replace('in', '')
        cities.append(city)
        states.append("CA")
        enviros.append(job_enviro)
    else:
        cities.append(np.nan)
        states.append('CA')
        enviros.append(np.nan)


#make salaries integers
salaries = []
for salary in job_pays:
    if salary == "NaN" or salary == "" :
        salaries.append(np.nan)
    else:
        salary = salary.replace('$', '')
        salary = salary.replace(',', '')
        salary_list = salary.split('.')
        if len(salary_list[0]) <= 3:
            #Then I know it is hourly rate
            salaries.append(float(salary) * 40 * 52)
        else:
            salaries.append(float(salary))

# create my dataframe
job_info = pd.DataFrame({"Title": job_titles,
              "Company": company_names,
              "Location": company_locations,
              'Work_Environment': enviros,
              "Job_Description": descriptions,
              "When_Posted": posted,
              "Pay": salaries,
              "City":cities,
               "State": states})


# fix locations and add ratings column
ratings = []
def fix_location(value):
    try:
        rating = float(value)
        ratings.append(rating)
        return np.nan
    except:
        ratings.append(np.nan)
        return value

job_info['Location'] = job_info["Location"].apply(fix_location)
job_info['Rating'] = ratings
job_info = job_info.drop(columns=['Location'])
job_info.to_csv("4-01.csv")