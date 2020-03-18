import requests
import csv
from bs4 import BeautifulSoup
from time import sleep
import asyncio
import re
import argparse


def parse(text, url, i):
    print("Parsing: #", str(i), url)
    soup = BeautifulSoup(text, features="lxml")
    try:
        title = re.search(
            r"<title>(.*) \| Devpost</title>", str(soup.select_one("title"))
        )[1]
        tagline = re.search(
            re.escape(title) + ' - (.*)" ',
            str(soup.select_one('meta[name="description"]')),
        )
        if tagline:
            tagline = tagline[1]
        raw_desc = soup.select_one("#app-details-left").findAll(
            "div", attrs={"id": None, "class": None}
        )[0]
        description = " ".join(raw_desc.strings)
        authors = [
            re.search("https://devpost.com/(.*)", member["href"])[1]
            for member in soup.select("li.software-team-member figure a")
        ]
        # Nullable fields
        links = [
            link["href"]
            for link in soup.select('ul[data-role="software-urls"] a')
            if "href" in link
        ]
        media = [link["href"] for link in soup.select("#gallery a") if "href" in link]
        media += [
            frame["src"] for frame in soup.select("#gallery iframe") if "src" in frame
        ]  # video embeds
        submitted = [
            hackathon["href"]
            for hackathon in soup.select(".software-list-content a")
            if "href" in hackathon
        ]
        submissions = soup.select(".software-list-content")
        win = {}
        for submission in submissions:
            name = submission.select_one("a")
            if "href" in name:
                name = name["href"]
                wins_lst = submission.select("li")
                wins_lst = [
                    "".join(i.strings)
                    .replace("\n", "")
                    .replace("Winner", "", 1)
                    .strip()
                    for i in wins_lst
                ]
                win[name] = wins_lst
        return {
            "url": url,
            "title": title,
            "tagline": tagline,
            "raw_desc": raw_desc,
            "description": description,
            "media": media,
            "links": links,
            "submitted": submitted,
            "authors": authors,
            "win": win,
        }
    except Exception as e:
        print(e)
        return False


async def scrape(url):
    global index
    i = index
    index += 1
    print("Now scraping: " + str(i))
    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(None, requests.get, url.strip())
    res = res.text
    parsed = parse(res, url, i)
    if parsed:
        csvwriter.writerow(parsed)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "indices",
        help="Input a start and end index",
        nargs="*",
        metavar=("start", "end"),
        default=[0, -1],
        type=int,
    )
    parser.add_argument("file", help="Input a file name", default="urls.txt", nargs="?")
    args = parser.parse_args()

    try:
        start = int(args.indices[0])
        end = int(args.indices[1])
    except Exception:
        start = 0
        end = -1

    name = args.file

    with open(name) as data:
        for _ in range(start):
                next(data)
        if end < 0:
            coroutines = [scrape(line) for line in data]
        else: 
            coroutines = [scrape(next(data)) for _ in range(end)] 
        await asyncio.gather(*coroutines)


if __name__ == "__main__":
    index = 0

    fieldnames = [
        "url",
        "title",
        "tagline",
        "raw_desc",
        "description",
        "media",
        "links",
        "submitted",
        "authors",
        "win",
    ]

    out = open("data.csv", "w+")

    csvwriter = csv.DictWriter(out, fieldnames)
    csvwriter.writeheader()
    # csvwriter.writerow({'url': 'test', 'title': 'many com, mas, a,'...})

    asyncio.get_event_loop().run_until_complete(main())

    asyncio.get_event_loop().close()
    out.close()
