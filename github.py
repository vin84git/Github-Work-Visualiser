#!/usr/bin/env python3

import json
import os
import click
from pprint import pprint

#  home = os.path.expanduser("~")
#  conf_dir = os.path.join(home, ".github", "shephero")
#  os.makedirs(conf_dir, exist_ok=True)
#  conf_path = os.path.join(conf_dir, "config")
#  if os.path.isfile(conf_path):
#      conf = json.load(open(conf_path))
#  else:
#      conf = {}

def get_user():
    got = False
    user = ""
    while not got:
        user = input("Enter username: ")
        if click.confirm("User username: '{}'?".format(user), default=True):
            got = True
    return user

user = get_user()

