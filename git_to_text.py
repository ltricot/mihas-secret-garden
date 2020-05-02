import requests
import json
"""
Since I am human this will be written as a script, not like what LOAN wrote.
Dumbass. Gingers, am I right?
Well this beautiful piece of art can be reformatted to be run with cmd line arguments as well.
Like Python scripts are meant to.
"""

OWNER = "ltricot" #also known as DUMBASS
REPO = "CSE201_prototype" #also known as the project of death
COMMITS_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/commits" #we know format strings since we are not plebs
SAVE_LOC = "MESSAGES/mihamits"
TOKEN = ""
USERNAME = "" #YOU REALLY NEED TO MAKE SURE THAT YOU ARE LOOKING FOR THE RIGHT THING, SINCE GIT HAS 1000123 DIFFERENT NAMES FOR COMITTER AND AUTHOR AND ALL THE OTHER BULLSHIT
AUTH_URL = f"https://api.github.com/users/{USERNAME}"
#ok let's get down to business
#I don't got no time to play around what is this
#Must be a circus in town, let's shut the shit down
#On these clowns, can I get a witness?


authentication = requests.get(AUTH_URL, auth=(USERNAME, TOKEN)) #so we r authenticated now
#Let's try getting user info
print("plan" in authentication.json()) #According to Github this means we gucci

#Now comes the bigboi part - we shall obtain de commits!

commits = requests.get(COMMITS_URL, auth=(USERNAME, TOKEN))

head = commits.headers #we get head
body = commits.json() #now we get body

def get_links(headers):
    "takes in header and returns dict with keys being the 'rel='s and the values the links to the pages"
    links = head['Link']
    pages = [link.strip() for link in links.split(',')]
    return dict(((page.split(';')[1].strip()[5:-1], page.split(';')[0].strip()[1:-1]) for page in pages)) #honestly fuck you loan, this is what u get

links = get_links(head)


def obtain_user_commit_messages(user, commits):
    """Basically takes in a list of commits in JSON format and gets out the messages of the ones corresponding to user"""
    return [msg['commit']['message'] for msg in commits if msg['commit']['author']['name'] == user]


cnt = 0
print(links)
while "next" in links:
    msgs = obtain_user_commit_messages(USERNAME, body)
    for msg in msgs:
        with open(SAVE_LOC + str(cnt) + ".txt", 'a', errors='ignore') as file: #again, cus fuck u loan
            if msg:
                file.write(msg.strip())
        cnt += 1
    commits = requests.get(links['next'], auth=(USERNAME, TOKEN))
    head = commits.headers
    body = commits.json()
    links = get_links(head)
    print(head)
    print(links)
else:
    msgs = obtain_user_commit_messages(USERNAME, body)
    for msg in msgs:
        with open(SAVE_LOC + str(cnt) + ".txt", 'a', errors='ignore') as file:
            if msg:
                file.write(msg.strip())
        cnt += 1






















