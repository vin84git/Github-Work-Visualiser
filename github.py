#!/usr/bin/env python3

import click
import json
import os
import pprint
import requests
import sys
from concurrent.futures import ThreadPoolExecutor
from functools import partial

home = os.path.expanduser("~")
base_dir = os.path.join(home, ".github", "shephero")
data_dir = os.path.join(base_dir, "data")
user_path = os.path.join(base_dir, "user")
target_path = os.path.join(base_dir, "target")
token_path = os.path.join(base_dir, ".login")
os.makedirs(data_dir, exist_ok=True)

pp = pprint.PrettyPrinter(indent=4)

api = {}
api["base"]  = "https://api.github.com"
api["users"] = api["base"] + "/users"
api["repos"] = api["users"] + "/{}/repos"
api["commits"] = api["base"] + "/repos/{}/{}/commits"
token = None

def cached(path):
    res = None
    try:
        res = json.load(open(path))
    except:
        pass
    return res

def gib(url):
    r = requests.get(url, params={"access_token": token})
    return r.json()

def repo_name_arr(data):
    if not isinstance(data, list):
        return None
    return list(map(lambda d: d["name"], data))

def get_commits_thread(use_cached, user, repo):
    #  print("Thread spun up for {}/{}".format(user, repo))
    data = None
    repo_path = os.path.join(data_dir, user, "r-" + repo + ".json")
    if use_cached:
        data = cached(repo_path)
    if data == None:
        commits_url = api["commits"].format(user, repo)
        try:
            data = gib(commits_url)
        except:
            pass
        if data == None or "message" in data:
            sys.stderr.write("Warning! Couldn't fetch commit history for {}/{}\n"
                    .format(user, repo))
        with open(repo_path, 'w') as outfile:
            json.dump(data, outfile)
    return data

def prompt(p, d):
    s = p + (" [" + d + "]" if d != "" else d) + ": "
    res = input(s)
    return (d if res == '' else res)

def collect_commits(bar, user, data, repo, future):
    #  sys.stderr.write("repo\n")
    commits = future.result()
    for commit in commits:
        commit["repo"] = repo
    data.append(commits)
    bar.update(1)

def login():
    global token
    default_user = cached(user_path) or ''
    token_data = cached(token_path)
    if token_data == None:
        print("# Login to Github")
        user = prompt("Enter your Github username", default_user)
        with open(user_path, "w") as f:
            json.dump(user, f)
        password = getpass("Enter your Github password: ")
        token_data = requests.post("https://api.github.com/authorizations",
                auth=(user,password),
                json={"scopes":["repo", "gist"],"note":"shephero-github-v1"}).json()
        if not token in token_data:
            sys.stderr.write("Unable to authenticate with Github")
            sys.exit(0)
        with open(token_path, "w") as f:
            json.dump(token_data, f)
    token = token_data["token"]

def fetch_repo_names(user, path):
    print("Downloading list of repositories...")
    repos = gib(api["repos"].format(user))
    repo_names = repo_name_arr(repos)
    if repo_names == None:
        print("Cannot get repository list for user:", target, file=sys.stderr)
        sys.stderr.write(json.dumps(repos) + "\n")
        return 1
    with open(path, 'w') as outfile:
        json.dump(repo_names, outfile)
    return repo_names

def get_commits():
    default_target = cached(target_path) or ''
    target = prompt("Enter target Github username", default_target)
    with open(target_path, "w") as f:
        json.dump(target, f)
    user_dir = os.path.join(data_dir, target)
    repos_path = os.path.join(user_dir, "repos.json")
    repos = cached(repos_path)
    repo_names = repos
    use_cached = True
    if repos != None:
        use_cached = click.confirm("Use cached data?", default=True)
    if repos == None or not use_cached:
        repo_names = fetch_repo_names(target, repos_path)
    pp.pprint(repo_names)
    data = []
    print("Starting multithreaded commit fetcher...")
    with click.progressbar(length=len(repo_names),
                       label="Downloading commits") as bar:
        with ThreadPoolExecutor(max_workers=8) as pool:
            for ind, repo in enumerate(repo_names):
                future = pool.submit(get_commits_thread, use_cached, target, repo)
                future.add_done_callback(
                        partial(collect_commits, bar, target, data, repo))
    return [item for sublist in data for item in sublist]

def start():
    login()
    data = get_commits()
    print(data)

if __name__ == "__main__":
    start()
