# -*- coding: utf-8 -*-
# Gitless - a version control system built on top of Git
# Licensed under MIT

"""gl permission - List, add, edit or delete permissions for your current repository."""

import Constants
import os
import json

from gitless import core

from . import helpers, pprint


def parser(subparsers, repo):
  desc = 'add, edit or delete permissions for your current repository'
  permission_parser = subparsers.add_parser(
      'permission', help=desc, description=(
        desc.capitalize() + '. ' +
        'Use the -a to add new users by username, -e to edit the access level of a username and -d to remove users from the repository'),
        aliases=['fs'])
  permission_parser.add_argument(
    '-a', '--add', nargs='+', help=('add new user by username to the repository (access level defaults to NEW) - format username/password')
  )
  permission_parser.add_argument(
    'e', '--edit', nargs='+', help=('set the access level of a given username to a new value')
  )
  permission_parser.add_argument(
    '-d', '--delete', nargs='+', help=('remove a username from the respository')
  )
  permission_parser.set_defaults(func=main)


def main(args, repo):
    #this is external to git
    #make the requested changes to the JSON
    #call the sync command we defined for the main program to push the changes up and out

    json_path = Constants.CONFIG_PATH + "/" + os.path.basename(repo.path) + ".json"
    repo_name = os.path.basename(repo.path)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    if json_path.exists():
        with json_path.open("r", encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {"settings": []}

    for r in data["settings"]:
        if r.get("repo_name") == repo_name:
            if args.add:
                add = frozenset(args.add)
                creds = [tuple(entry.split('/', 1)) for entry in add]
                users = [(u.get("username"), u.get("password")) for u in r["users"]]
                to_add = list(set(creds) - set(users))
                for username, password in to_add:
                    r["users"].append(
                        {
                            "username": username,
                            "password": password,
                            "account_type": Constants.Access_Type.NEW
                        }
                    )

            if args.edit:
                edit = frozenset(args.edit)
                updates = [tuple(entry.split('/', 1)) for entry in edit]
                for username, new_level in updates:
                    for user in r['users']:
                        if user.get("username") == username:
                            user["account_type"] = new_level

            if args.delete:
                delete = frozenset(args.delete)
                r["users"] = [u for u in r["users"] if u.get("username") not in delete]

            with json_path.open("w", encoding='utf-8') as f:
                json.dump(data, f, indent=2, sort_keys=True)

            break

    return Constants.sync_repo_permissions(repo_name)


