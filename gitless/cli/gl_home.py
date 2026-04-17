# -*- coding: utf-8 -*-
# Gitless - a version control system built on top of Git
# Licensed under MIT

"""gl home - List project readme, location to ground the user."""

from .. import Constants
import os
import json
from pathlib import Path

from . import helpers, pprint


def parser(subparsers, repo):
  desc = 'Lists the base location of the project on your system, display the project readme, list who is using the project and how you should work with the repository'
  permission_parser = subparsers.add_parser(
      'home', help=desc, description=(
        desc.capitalize()),
        aliases=['home'])
  permission_parser.set_defaults(func=main)


def main(args, repo):

    #list out the base path
    #the location of the config file
    #List the levels of people in the project
    #Print out the readme

    pprint.sep()

    print(f"Repo: {os.path.basename(repo.root)}, Location: {repo.root}")
    print(f"Current branch: {repo.current_branch}")
    print(f"Config file location: {str(Constants.CONFIG_PATH) + "/" + repo.root + ".json"}\n")

    pprint.sep()

    if Path(repo.root).exists():
        if Path(str(Path(repo.root))+"/readme.md").exists():
            name = "readme.md"
        elif Path(str(Path(repo.root))+"/Readme.md").exists():
            name = "Readme.md"
        elif Path(str(Path(repo.root))+"/README.md").exists():
            name = "README.md"
        elif Path(str(Path(repo.root))+"/readme.txt").exists():
            name = "readme.txt"
        elif Path(str(Path(repo.root))+"/Readme.txt").exists():
            name = "Readme.txt"
        elif Path(str(Path(repo.root))+"/README.txt").exists():
            name = "README.txt"
        else:
            pprint.err("You have no locatable readme at your project root, it is highly recommended you create this")
            name = ""

        if name != "": 
            with Path(str(Path(repo.root))+"/"+name).open("r", encoding='utf-8') as f:
                pprint.ok(f.read())
    
    pprint.sep()

    print("Who has access to this repo?\n")

    repo_name = os.path.basename(repo.root)
    json_path = str(Constants.CONFIG_PATH) + "/" + repo_name + ".json"
    Path(Constants.CONFIG_PATH).parent.mkdir(parents=True, exist_ok=True)

    if Path(Constants.CONFIG_PATH).exists():
        with Path(json_path).open("r", encoding='utf-8') as f:
            data = json.load(f)
            for u in data["settings"][0]["users"]:
                print(u.get("username") + " - " + Constants.Access_Type.Parse(u.get("account_type")))
                print("\n")
    else:
        pprint.err("An error occurred, I could not find your project config file!")

    pprint.sep()

    print(f"You are user: {Constants.username}, with access level: {Constants.Access_Type.ParseStr(Constants.access_level)}")

    pprint.sep()

    try:
        with Path(str(Constants.CONFIG_PATH) + "/" + os.path.basename(repo.root)+".json").open("r", encoding="utf-8") as f:
            d = json.load(f)
        try:
            w = d["settings"][0]["workflow"]
            print(f"Workflow designated by Admin:\n{w}")
        except Exception:
            pprint.err("Your admin hasn't designated as workflow description. This is key for advising New or Novice users on how to proceed about using the system.")
    except (FileNotFoundError):
        pprint.err("Could not locate your shared config file")

    pprint.sep()

    pprint.ok(Constants._run("git status -v", repo.root, capture=True).stdout)

    pprint.sep()

    return True