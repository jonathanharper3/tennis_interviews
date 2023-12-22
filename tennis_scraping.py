import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

def remove_character(string, char_list):
    for char in char_list:
        string = string.replace(char, "")
    return string

url = 'http://www.asapsports.com/showcat.php?id=7&event=yes'
response = requests.get(url)
html_content = response.text

soup = BeautifulSoup(html_content, 'html.parser')

abc_url_list = []
a_tags = soup.find_all('a')
for a_tag in a_tags:
    href = a_tag.get('href')
    if 'show_player' in href:
        abc_url_list.append(href)

player_url_list = []
for url in abc_url_list:
    response = requests.get(url)
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    a_tags = soup.find_all('a')
    for a_tag in a_tags:
        href = a_tag.get('href')
        if 'php?id' in href:
            player_url_list.append(href)

comp_url_list = []
for url in player_url_list:
    response = requests.get(url)
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    a_tags = soup.find_all('a')
    for a_tag in a_tags:
        href = a_tag.get('href')
        if 'show_interview' in href:
            comp_url_list.append(href)

df = pd.DataFrame(columns=['Name', 'Question', 'Answer'])
urls = []
problem_urls = []
pattern = r'\([^)]*\)'

for url in comp_url_list:
    
# url = 'http://www.asapsports.com/show_interview.php?id=24178'

    response = requests.get(url)
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    soup = str(soup).strip()
    soup = remove_character(soup, '\n')

    name_pattern = r'show_player.php\?id=[0-9]+">(.+?)</a>'
    name = re.findall(name_pattern, soup)[0]
    name = name.upper()

    question_pattern = r'Q\..*?(?=(?:' + re.escape(name) + '|[A-Z]+\s[A-Z]+:))'
    answer_pattern = re.escape(name) + r':.*?(?=(?:Q\.|FastScripts Transcript|End of FastScripts|THE MODERATOR:))'

    question_matches = re.findall(question_pattern, soup)
    answer_matches = re.findall(answer_pattern, soup)

    formatted_questions = []
    formatted_answers = []

    for question_match in question_matches:
        question = remove_character(question_match, ["Q.", "</b>", "<b>", "<br/>", "<p>", "</p>", "\'", "Â", "?",
                                                     "</strong>", "Ã", "©"])
        question = re.sub(pattern, '', question)
        question = question.strip()

        formatted_questions.append(question)

    for answer_match in answer_matches:
        answer = remove_character(answer_match, [name, ":", "</b>", "<p>", "</p>", "<strong>", "<b>", "<br/>", 
                                                 "\'", "Â", "</strong>", "Ã", "©"])
        answer = re.sub(pattern, '', answer)
        answer = answer.strip()
        formatted_answers.append(answer)

    if len(formatted_questions) != len(formatted_answers):
        problem_urls.append(url)
        continue
    else:
        urls.append(url)

    for question, answer in zip(formatted_questions, formatted_answers):
        df = df.append({'Name': name, 'Question': question, 'Answer': answer}, ignore_index=True)

df = df.drop(df[df['Question'] == ''].index)
df = df.drop(df[df['Answer'] == ''].index)

df.to_csv('tennis.csv', index=False)
