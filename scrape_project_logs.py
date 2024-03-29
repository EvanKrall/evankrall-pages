#!./venv/bin/python3

import urllib.parse
import os
import textwrap
import traceback
import requests
from bs4 import BeautifulSoup
import datetime
from zoneinfo import ZoneInfo
from slugify import slugify
import urllib
import posixpath

PROJECT_NUM = "177256"
SHORT_NAME = "pipad"  # HTML and images will be put in subdirectories with this name
TITLE_PREFIX = "Pipad: "


def parse_post_time(post_time):
    if post_time.endswith("minutes ago"):
        minutes = int(post_time.split(" ")[0])
        return datetime.datetime.now().astimezone() - datetime.timedelta(minutes=minutes)
    try:
        return datetime.datetime.strptime(post_time, "%m/%d/%Y at %H:%M").astimezone()
    except ValueError:
        return datetime.datetime.strptime(
            input(f"Couldn't parse post time {post_time}; please give me a date in the format `%m/%d/%Y at %H:%M`: "),
            "%m/%d/%Y at %H:%M"
        ).astimezone()


def scrape_individual_log(url):
    slug = posixpath.basename(urllib.parse.urlparse(url).path)
    html_file_path = f"content/posts/{SHORT_NAME}/logs/{slug}.html"
    if os.path.exists(html_file_path):
        print(f"Already have {html_file_path}, skipping scraping {url}")
        return

    print(f"Scraping log entry {url}")
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text)

    title = soup.find_all("h1")[0].get_text()
    post_time = soup.find_all("span", {"class": "time-card"})[0].get_text()
    post_time_dt = parse_post_time(post_time)

    header = textwrap.dedent(f"""
        ---
        title: {TITLE_PREFIX + title!r}
        date: {post_time_dt.isoformat()}
        draft: false
        ---
        <p><em>View or comment on this project log on <a href="{url}">Hackaday.io</a></em></p>
        """
    ).strip("\n")

    content_divs = soup.find_all("div", {"class": "post-content"})
    post_content = content_divs[0] # content_divs[1] is the comments.

    # I used <tt> in some places, let's switch to <code>
    for tt in post_content.find_all("tt"):
        tt.name = "code"

    for img in post_content.find_all("img", {"class": "lazy"}):
        del img['class']
        img_url = img['data-src']
        del img['data-src']
        img_filename = posixpath.basename(urllib.parse.urlparse(img_url).path)
        img["src"] = f'/img/{SHORT_NAME}/{img_filename}'
        img_local_path = f"static/img/{SHORT_NAME}/{img_filename}"
        if not os.path.exists(img_local_path):
            try:
                img_resp = requests.get(img_url, timeout=1.0)
                img_resp.raise_for_status()
            except:
                print(f"Couldn't download {img_url}; please download it and put it at {img_local_path}")
                traceback.print_exc()
            else:
                with open(img_local_path, 'wb+') as f:
                    f.write(img_resp.content)


    full_contents = header + "\n" + post_content.decode_contents()

    os.makedirs(os.path.dirname(html_file_path), exist_ok=True)
    with open(html_file_path, 'w+') as f:
        print(f"Writing contents to {html_file_path}")
        f.write(full_contents)


def walk_project_logs():
    logs_url = f"https://hackaday.io/project/{PROJECT_NUM}/logs?sort=oldest"

    while True:
        resp = requests.get(logs_url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text)
        buildlog_ul = soup.find("ul", {"class": "buildlogs-list"})
        for element_title in buildlog_ul.find_all("h3", {"class": "element-title"}):
            link = element_title.find("a")
            scrape_individual_log(urllib.parse.urljoin(logs_url, link['href']))

        pagination = soup.find("div", {"class": "pagination"})
        next_button = pagination.find("a", {"class": "next-button"})
        if next_button:
            next_page_url = next_button["href"]
            logs_url = urllib.parse.urljoin(logs_url, next_page_url)
        else:
            break


if __name__ == "__main__":
    try:
        walk_project_logs()
    except requests.exceptions.HTTPError as err:
        print(err.request.url)
        print(err)
        print(err.response.text)
