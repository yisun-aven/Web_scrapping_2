import os
import zipfile
from kaggle.api.kaggle_api_extended import KaggleApi
import pandas as pd
import csv
from bs4 import BeautifulSoup
import requests
import sys
from piazza_api import Piazza
import json
import pdfplumber

''' ***scrape csv*** '''
# Initialize Kaggle API
k = KaggleApi()
k.authenticate()

# Download the dataset
dataset = "kazanova/sentiment140"
file_name = "training.1600000.processed.noemoticon.csv"
zip_file = file_name + ".zip"

k.dataset_download_file(dataset, file_name=file_name)

# Check if the file has been downloaded
if os.path.exists(zip_file):
    # Unzip the file
    with zipfile.ZipFile(zip_file, "r") as zipref:
        zipref.extractall()
    print("File extracted.")
else:
    print("File not found.")


# Load the dataset
file_name = "training.1600000.processed.noemoticon.csv"
df = pd.read_csv(file_name, encoding='ISO-8859-1')
print("------operations on csv data------")

# Display the first few records
print("First few records:")
print(df.head())

# Calculate the size and dimensions of the dataset
print("\nDataset dimensions (rows, columns):", df.shape)
print("Total number of elements:", df.size)

# Identify missing data
print("\nMissing data in each column:")
print(df.isnull().sum())

# Additional basic statistics
print("\nBasic statistics:")
print(df.describe())

''' ***scrape forum (piazza)*** '''
# create piazza object
p = Piazza()

# Ask user to input Email and Password
Email = input("Please Enter Your Email:")
Password = input("Please Enter Your Password:")

# Log in the user with the specified email and password
p.user_login(Email, Password)

# Get the user profile
user_profile = p.get_user_profile()

# contact specific course network using network id
# Example:
# URL: https://piazza.com/class/l1b73g0zte25f2
# Network ID = l1b73g0zte25f2
cs143A = p.network("l1b73g0zte25f2")

# Storing all the posts in raw_datas
raw_datas = cs143A.iter_all_posts(sleep=1)

# initialize a list to store the extracted data
data_posts = []

# iterate through raw data and only extract (1) subject, (2) question content, (3) response content
for raw_data in raw_datas:
    # getting all the posts
    list_posts = raw_data["history"]
    temp_data = []
    for post in list_posts:
        subject = post["subject"]
        # Parse the HTML content
        soup_subject = BeautifulSoup(subject, 'html.parser')
        text_subject = soup_subject.get_text()

        question_content = post["content"]
        # Parse the HTML content
        soup_question = BeautifulSoup(question_content, 'html.parser')
        text_question = soup_question.get_text()

        data_posts.append({"Subject:": text_subject, "Question Content": text_question, "Response Content": ""})

    # getting all the response
    list_response = raw_data["children"]
    for response in list_response:
        try:
            response_contents = response["history"]
            for content in response_contents:
                response_content = content["content"]
                # Parse the HTML content
                soup_response = BeautifulSoup(response_content, 'html.parser')
                text_response = soup_response.get_text()

                data_posts[-1]["Response Content"] = text_response if len(text_response) > 1 else "No Response"
        except KeyError:
            # In case the post has no one responded
            print("")

# Convert JSON to DataFrame
df = pd.json_normalize(data_posts)

# Save to CSV file
df.to_csv("html_piazza_output.csv", index=False)

df = pd.read_csv("html_piazza_output.csv", encoding='utf-8')
print("------operations on web forum data------")
print("First few records:")
print(df.head())
print("\nDataset dimensions (rows, columns):", df.shape)
print("Total number of elements:", df.size)
print("\nMissing data in each column:")
print(df.isnull().sum())

''' ***scrape html (codecademy)*** '''
# url
url = 'https://www.codecademy.com/learn/fscj-22-algorithms/modules/wdcp-22-recursion-d930f071-374e-444b-b8d1-f6229c2c3735/cheatsheet'

# # Initialize the WebDriver (example with Chrome)
# chrome_driver_path='/Users/justinchen/Desktop/DSCI560/lab2/chromedriver_mac_arm64/chromedriver'
# driver = webdriver.Chrome(executable_path=chrome_driver_path)
# # Open the webpage
# driver.get('https://www.geeksforgeeks.org/python-string/?ref=lbp')
# Send a GET request to the URL
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')
else:
    print(f"Failed to retrieve the webpage. Status code: {response.status_code}")

# data list
cheatsheet = [['title', 'content', 'code_html']]

# find all blocks
blocks = soup.find_all('div', class_='gamut-imw2wj-LayoutGrid eapwrau0')

for block in blocks:
    title = block.find('h3', class_='styles_h3__VPpU9')
    content = block.find('p', class_='styles_p__TNq46')
    code_html = block.find_all('pre', class_='e1xf0hok0 gamut-1ous01k e1sl93ab0')

    temp = []
    temp.append(title.get_text())
    temp.append(content.get_text())
    if code_html:
        temp.append(code_html)
    else:
        temp.append('')
    cheatsheet.append(temp)

cheatsheet_data_filename = 'cheatsheet_data.csv'

with open(cheatsheet_data_filename, 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    for row in cheatsheet:
        writer.writerow(row)

df = pd.read_csv(cheatsheet_data_filename, encoding='utf-8')
print("------operations on html data------")
print("First few records:")
print(df.head())
print("\nDataset dimensions (rows, columns):", df.shape)
print("Total number of elements:", df.size)
print("\nMissing data in each column:")
print(df.isnull().sum())

''' ***scrape pdf (mit lecture slides)***'''
# course webpage
course_url = "https://ocw.mit.edu/courses/6-0001-introduction-to-computer-science-and-programming-in-python-fall-2016/"
response = requests.get(course_url)
soup = BeautifulSoup(response.text, 'html.parser')
lecture_slide_site = soup.find('a', {'data-uuid': "f39a25a3-5f6b-0d3e-6388-e9b2e8b7438e"})["href"]

# lecture slides and code webpage
url = "https://ocw.mit.edu"
lecture_slide_site = url + lecture_slide_site
response = requests.get(lecture_slide_site)
soup = BeautifulSoup(response.text, 'html.parser')


# for each lecture, find the slides
links = soup.find_all('tr')
number_of_lectures = len(links[1:])
lecture_titles = []

for i in links[1:]:
    list = i.find_all('td')
    lecture_number = list[0].text.strip()
    lecture_title = list[1].text.strip()
    lecture_slides_link = url + list[2].find('a')['href']
    lecture_code_link = url + list[3].find('a')['href'] # try to download code later in the project
    lecture_titles.append(lecture_title)
    response = requests.get(lecture_slides_link)
    soup = BeautifulSoup(response.text, 'html.parser')
    pdf_link = url + soup.find('a', {'class': 'download-link'})['href']

    # download pdf
    pdf_response = requests.get(pdf_link)
    with open(f"lecture {lecture_number}.pdf", 'wb') as f:
        f.write(pdf_response.content)

# read each pdf and append to a dataframe
df = pd.DataFrame({"lecture title": [], "lecture number": [], "slide title": [], "slide page number": [], "slide content": []})

for i in range(len(links[1:])):
    with pdfplumber.open(f"lecture {i + 1}.pdf") as pdf:
        # lecture title, lecture number, slide title, slide page number, slide content in a csv
        lecture_title = lecture_titles[i]
        for j in range(len(pdf.pages) - 1):
            p = pdf.pages[j]
            full_text = p.extract_text()
            for k in range(len(p.chars)):
                if p.chars[k]['size'] < 48:
                    slide_title = full_text[:k]
                    slide_content = full_text[k:].rsplit('\n', 1)[0]
                    break
            row = pd.DataFrame({"lecture title": [lecture_title], 
                                "lecture number": [i + 1], 
                                "slide title": [slide_title], 
                                "slide page number": [j + 1], 
                                "slide content": [slide_content]})
            df = pd.concat([df, row])

df.to_csv('lecture_pdf.csv')
df = pd.read_csv('lecture_pdf.csv', encoding='utf-8')
print("------operations on pdf data------")
print("First few records:")
print(df.head())
print("\nDataset dimensions (rows, columns):", df.shape)
print("Total number of elements:", df.size)
print("\nMissing data in each column:")
print(df.isnull().sum())