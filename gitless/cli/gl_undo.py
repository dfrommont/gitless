# -*- coding: utf-8 -*-
# Gitless - a version control system built on top of Git
# Licensed under MIT

"""gl permission - Undo local commits that contain mistakes or you don't want to be pushed to the remote."""

from .. import Constants
import os
import json
from pathlib import Path
import subprocess

from gitless import core

from . import helpers, pprint


def parser(subparsers, repo):
  desc = 'Undo local commits that contain mistakes or you do not want to be pushed to the remote'
  undo_parser = subparsers.add_parser(
      'undo', help=desc, description=(
        desc.capitalize() + '. ' +
        'Use -l LIMIT to control how many commits are to be undone (default 1). Commits will be undone until either the limit, there are no more local-only commits or a merge commit is reached'),
        aliases=['undo'])
  undo_parser.add_argument(
    '-l', '--limit', help='number of potential commits to be undone', type=int
  )
  undo_parser.set_defaults(func=main)


def main(args, repo):
    #this gets called to do any pre-processing but we should hand over to the the core to handle the actual undo
    #an undo should query the git state for committed local changes on the current branch
    #if these changes exist, it must backtrack through them up until the LIMIT or the last commit to be pushed (whichever comes first)

    if not args.limit:
        limit = 1
    else:
        limit = args.limit
    print(limit)
    count = 0
    while count < limit:

        count = count + 1

        if not Path(repo.root + "/.git").exists():
            print("Not in a git repository!")
            return False
        
        head = Constants._run("git rev-parse HEAD", repo.root, capture=True)
        if head.returncode != 0:
            print("No commits exist!")
            return False
        
        parents = Constants._run("git rev-list --parents -n 1 HEAD", repo.root, capture=True)
        p = parents.stdout.strip().split()
        if len(p) != 2:
            print("Cannot undo merge commits")
            return False
        
        upstream = Constants._run("git rev-parse --abbrev-ref --symbolic-full-name @{u}", repo.root, capture=True)
        if upstream.returncode == 0:
            counts = Constants._run("git rev-list --left-right --count HEAD...@{u}", repo.root, capture=True)

            if counts.returncode != 0:
                print("Failed to determine sync state")
                return False
            ahead, behind = map(int, counts.stdout.strip().split())

            if ahead == 0:
                print("Commit has already been pushed, undo not allowed")
                return False
            
        reset = Constants._run("git reset --mixed HEAD~1", repo.root, capture=True)
        if reset.returncode != 0:
            print("Failed to undo commit")
            return False
    
    return True