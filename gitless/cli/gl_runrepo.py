# -*- coding: utf-8 -*-
# Gitless - a version control system built on top of Git
# Licensed under MIT

"""gl runrepo - Communicate with server over HTTP to control running of remote repositories on server."""

from .. import Constants
import os
import json
from pathlib import Path
import subprocess

from gitless import core
from . import Client

from . import helpers, pprint

def parser(subparsers, repo):
    desc = 'control repositories running on the server'
    runrepo_parser = subparsers.add_parser(
        'runrepo', help=desc, description=desc.capitalize(), aliases=['rr'])
    group = runrepo_parser.add_mutually_exclusive_group()
    group.add_argument(
        '-a', '--abort', help='abort your repository currently running', action='store_true')
    group.add_argument(
        '-r', '--repo', help='Pass repo name that the commit ID will be searched for in to be run'
    )
    group.add_argument(
        '-c', '--commit', help='Pass commit ID to be unpacked and run by the server'
    )
    group.add_argument(
        '-id', '--jobID', help='Job ID on server of repo being run'
    )
    runrepo_parser.set_defaults(func=main)

def main(args, repo):
    try:
        repo_name = Path(repo.path).parent.name
        with Path(repo.path.parent + f"/../.git/{repo_name}.json").open("w", encoding='utf-8') as f:
            data = json.load(f)
            server = data["this_server"]["ip"]
            port = data["this_server"]["port"]
        if args.abort:
            print(Client.abort(server, port, Constants.username))
        if args.jobID:
            print(Client.query(server, port, Constants.username))
        else:
            if not args.commit and args.repo:
                raise Exception("you must provide both a repo name and commit ID for the server to run")
            print(Client.run(server, port, args.repo, args.commit, Constants.username))
        return True
    except Exception as e:
        print(f"Run repo command failed, Error: {e}")
        return False