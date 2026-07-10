import requests
from bs4 import BeautifulSoup
import urllib.request
import re
import json

"""
The function will eventually clear the html page at the bottom and overwrite the same local file for each new url
"""
def scrape_job_info(url):
    r = requests.get(url)

    def save_html(html, path):
        with open(path, 'wb') as f:
            f.write(html)

    save_html(r.content, 'workday_com')

def store_workday_listing(url):

    HTMLFile = open('workday_com.html', 'r')
    contents = HTMLFile.read()

    soup = BeautifulSoup(contents, 'html.parser')

    script = soup.find('script')
    script_dict = json.loads(script.text)
    accessed_url = url
    title = script_dict['title']
    date_posted = script_dict['datePosted']
    description = script_dict['description']
    employment_type = script_dict['employmentType']
    hiring_organization = script_dict['hiringOrganization']['name']
    jobID = script_dict['identifier']['value']
    jobLocation = script_dict['jobLocation']['address']['addressLocality']

    print('Url: ' + accessed_url,
        '\nTitle: ' + title,
        '\nDate Posted: ' + date_posted,
        '\nEmployment Type: ', employment_type,
        '\nHiring Organization: ', hiring_organization,
        '\nJob ID: ', jobID,
        '\nJob Location: ', jobLocation)

    #Next step: Pushing these variables into a MongoDB

url = 'https://salesforce.wd1.myworkdayjobs.com/en-US/External_Career_Site/job/California---San-Francisco/Summer-2023-Intern---Software-Engineer_JR155116-2?d=cta-nav-sjb-1&jobFamilyGroup=8db2f0ed342347eb8bac553488d8d12e&Location_Country=bc33aa3152ec42d4995f4791a106ed09'
#only want to scrape once to prevent IP blocking
#will eventually be re-written in dev environment to only run the function based on unique URLs not already stored in MongoDB
"""
if url not in MongoDB:
    scrape
"""
#scrape_job_info(url)
store_workday_listing(url)