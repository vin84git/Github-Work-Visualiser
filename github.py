#!/usr/bin/env python3

import click
import dateutil.parser
import json
import math
import os
import pprint
import re
import requests
import sys
import time
from collections import Counter
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

def gib(url, params=dict()):
    params["access_token"] = token
    r = requests.get(url, params=params)
    res = r.json()
    if "Link" in r.headers:
        link = r.headers["Link"]
        for l in link.split(","):
            if re.search('rel=.next.', l) != None:
                res += gib(re.search('^<(.*)>', l).group(1))
    return res

def repo_name_arr(data):
    if not isinstance(data, list):
        return None
    return list(map(lambda d: d["name"], data))

def format_commits(user, repo, data):
    res = []
    for commit in data:
        ds = commit["commit"]["author"]["date"]
        res.append({"repo": repo, "date": ds})
    return res

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
        data = format_commits(user, repo, data)
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
        commit["date"] = dateutil.parser.parse(commit["date"])
    data += commits
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
        if not "token" in token_data:
            sys.stderr.write("Unable to authenticate with Github")
            sys.exit(0)
        with open(token_path, "w") as f:
            json.dump(token_data, f)
    token = token_data["token"]

def fetch_repo_names(user, path):
    print("Downloading list of repositories...")
    repos = gib(api["repos"].format(user), params={"type": "owner"})
    repos = list(filter(lambda a: not a["fork"], repos))
    repo_names = repo_name_arr(repos)
    if repo_names == None:
        print("Cannot get repository list for user:", user, file=sys.stderr)
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
    return data

def blank_mat(x, y):
    return [[' ' for x in range(w)] for y in range(h)]

def graph(keys, counts, totals, maxim):
    #  canvas = blank_mat(60, len(keys))
    res = ""
    for key in keys:
        k = key
        if len(key) > 14:
            k = k[:11] + "..."
        elif len(k) < 14:
            k += (14 - len(k)) * " "
        res += k + " |"
        res += math.ceil(counts[key] / maxim * 60) * "-"
        res += "\n"
    return res

def time_graph(commits):
    commits = sorted(commits, key=lambda a: a["date"])
    repo_commits = list(map(lambda d: d["repo"], commits))
    total_count = Counter(repo_commits)
    repos = set(repo_commits)
    maxim = total_count.most_common(1)[0][1]
    for i, c in enumerate(commits):
        count = Counter(repo_commits[0:i])
        g = graph(repos, count, total_count, maxim)
        click.clear()
        print(g)
        print("\n" + c["date"].strftime('%Y-%m-%d'))
        print("\n\n\n")
        time.sleep(0.05)

def start():
    login()
    commits = get_commits()
    with open("data.json", "w") as f:
        json.dump(list(map(lambda a: a["repo"], commits)), f)
    time_graph(commits)

if __name__ == "__main__":
    start()
