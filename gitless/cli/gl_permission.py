# -*- coding: utf-8 -*-
# Gitless - a version control system built on top of Git
# Licensed under MIT

"""gl permission - List, add, edit or delete permissions for your current repository."""

from .. import Constants
import os
import json
from pathlib import Path

from gitless import core

from . import helpers, pprint


def parser(subparsers, repo):
  desc = 'List, add, edit or delete permissions for your current repository'
  permission_parser = subparsers.add_parser(
      'permission', help=desc, description=(
        desc.capitalize() + '. ' +
        f'Use the -a to add new users by username, -e to edit the access level of a username and -d to remove users from the repository. Access Levels: {Constants.Access_Type.GetAccessTypes()}'),
        aliases=['perm'])
  permission_parser.add_argument(
    '-a', '--add', nargs='+', help=('add new user by username to the repository (access level defaults to NEW) - format username/access_level')
  )
  permission_parser.add_argument(
    '-e', '--edit', nargs='+', help=('set the access level of a given username to a new value - format username/new_access_level')
  )
  permission_parser.add_argument(
    '-d', '--delete', nargs='+', help=('remove a username from the respository')
  )
  permission_parser.set_defaults(func=main)


def main(args, repo):
    #this is external to git
    #make the requested changes to the JSON
    #call the sync command we defined for the main program to push the changes up and out

    if core.Constants.Access_Type.ParseStr(core.Constants.access_level) == core.Constants.Access_Type.NEW:
        if core.Constants.verbose_conf_dialog(repo.current_branch, "permission", args, repo.git_repo.lookup_branch(repo.git_repo.head.shorthand, core.pygit2.GIT_BRANCH_LOCAL).upstream.name):
            pprint.ok("Command confirmed, continuing...")
        else:
            pprint.err("Command aborted, ending...")
        return False

    repo_name = os.path.basename(repo.root)
    json_path = str(Constants.CONFIG_PATH) + "/" + repo_name + ".json"
    print(json_path)
    Constants.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    if Constants.CONFIG_PATH.exists():
        with Path(json_path).open("r", encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {"settings": []}

    for r in data["settings"]:
        if r.get("repo_name") == repo_name:
            if args.add:
                add = frozenset(args.add)
                print(add)
                creds = [tuple(entry.split('/', 1)) for entry in add]
                print(creds)
                users = [(u.get("username"), u.get("account_type")) for u in r["users"]]
                print(users)
                to_add = list(set(creds) - set(users))
                print(to_add)
                print("3")
                for username, access_level in to_add:
                    r["users"].append(
                        {
                            "username": username,
                            "account_type": Constants.Access_Type.Serialise(access_level)
                        }
                    )

            if args.edit:
                edit = frozenset(args.edit)
                updates = [tuple(entry.split('/', 1)) for entry in edit]
                for username, new_level in updates:
                    for user in r['users']:
                        if user.get("username") == username:
                            if isinstance(new_level, int):
                                user["account_type"] = new_level
                            else:
                                user["account_type"] = Constants.Access_Type.Serialise(new_level)

            if args.delete:
                delete = frozenset(args.delete)
                r["users"] = [u for u in r["users"] if u.get("username") not in delete]

            with Path(json_path).open("w", encoding='utf-8') as f:
                json.dump(data, f, indent=2, sort_keys=True)

            break

    return Constants.sync_repo_permissions(repo_name + ".json")


