import requests
from bs4 import BeautifulSoup
import time

i = 0
soup = BeautifulSoup(requests.get('https://devpost.com/software/newest').text, features='lxml')
last = soup.select_one('ul.pagination')
last = int(last.findChildren('li', recursive=False)[-2].find('a').text)
print('Indexing until page ' + str(last))
with open('urls.txt', 'a+') as f:
    while i <= last:
        soup = BeautifulSoup(
            requests.get(
                'https://devpost.com/software/newest?page=' + str(i)).text, 
            features='lxml')
        links = soup.find('div', {'class': 'portfolio-row'})
        links = links.findChildren('a')
        for link in links:
            f.write(link.get('href') + '\n')
        time.sleep(1) # let's not do it too fast...
        i += 1 
    f.close()
