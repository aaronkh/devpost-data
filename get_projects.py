import requests
import csv
from bs4 import BeautifulSoup
from time import sleep
import asyncio
import webbrowser
import re

index = 0

fieldnames = ['url', 'title', 'tagline', 'raw_desc', 'description', 'media', 'links', 'submitted', 'authors', 'win']
out = open('data.csv', 'w+')

csvwriter = csv.DictWriter(out, fieldnames)
csvwriter.writeheader()
# csvwriter.writerow({'url': 'test', 'title': 'many com, mas, a,'...})
data = open('tests.txt')

def parse(text, url):
    soup = BeautifulSoup(text, features='lxml')
    title = re.search(r'<title>(.*) \| Devpost</title>', str(soup.select_one('title')))[1]
    tagline = re.search(title + ' - (.*)" ', str(soup.select_one('meta[name="description"]')))[1]
    raw_desc = soup.select_one('#app-details-left').findAll('div', attrs={'id': None, 'class': None})[0]
    description = ' '.join(raw_desc.strings)
    authors = [re.search('https://devpost.com/(.*)', member['href'])[1] for member in soup.select('li.software-team-member figure a')]
    # Nullable fields
    links = [link['href'] for link in soup.select('ul[data-role="software-urls"] a')]
    media = [link['href'] for link in soup.select('#gallery a')]
    media += [frame['src'] for frame in soup.select('#gallery iframe')] # video embeds
    submitted = [hackathon['href'] for hackathon in soup.select('.software-list-content a')]
    submissions = soup.select('.software-list-content')
    win = {}
    for submission in submissions:
        name = submission.select_one('a')['href']
        wins_lst = submission.select('li')
        wins_lst = [''.join(i.strings).replace('\n', '').replace('Winner', '', 1).strip() for i in wins_lst]
        win[name] = wins_lst
    return {
        'url': url,
        'title': title,
        'tagline': tagline, 
        'raw_desc': raw_desc, 
        'description': description,
        'media': media, 
        'links': links,
        'submitted': submitted,
        'authors': authors,
        'win': win
    }

async def scrape(url):
    global index 
    i = index
    index += 1
    print('Now scraping: ' + str(i))
    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(None, requests.get, url.strip())
    res = res.text 
    parsed = parse(res, url)
    csvwriter.writerow(parsed)

async def main():
    coroutines = [scrape(line) for line in data]
    await asyncio.gather(*coroutines)

asyncio.get_event_loop().run_until_complete(main())

asyncio.get_event_loop().close()
data.close()
out.close()
