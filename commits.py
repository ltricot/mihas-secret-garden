import requests

import json
import math
import re


USER = 'ltricot'
REPO = 'CSE201_Prototype'
TARGET = 'Smakson'

# weird github shit in header
pattern = re.compile(
    r'<.*\?page=([0-9]*)>; rel="next",\s'
    r'<.*\?page=([0-9]*)>; rel="last"'
)

url = (
    f'https://api.github.com/repos/{USER}'
    f'/{REPO}/commits'
)

def commits(target, url):
    page, last = 1, math.inf
    while page <= last:
        resp = requests.get(url, params={'page': page})

        if resp.status_code % 100 != 2:
            raise RuntimeError('Rate limited')

        # paging
        if 'link' in resp.headers:
            match = pattern.match(resp.headers['link'])
            if not match:
                continue

            page = int(match.group(1))
            last = int(match.group(2))

        jso = resp.json()
        for commit in jso:
            # author = commit['commit']['author']['name']
            # if author != target:
            #     continue

            yield commit


try:
    jso = list(commits(TARGET, url))
except RuntimeError:
    print('Rate limited')
    exit()

with open('commits.json', 'w') as f:
    json.dump({REPO: jso}, f)
