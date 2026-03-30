# -*- coding: utf-8 -*-
# Gitless - a version control system built on top of Git
# Licensed under MIT

"""gl - Main Gitless's command. Dispatcher to the other cmds."""


import sys
import argparse
import argcomplete
import traceback
import pygit2
import os
import json

from pathlib import Path
from subprocess import CalledProcessError

from gitless import core

from . import (
    gl_track, gl_untrack, gl_status, gl_diff, gl_commit, gl_branch, gl_tag,
    gl_checkout, gl_merge, gl_resolve, gl_fuse, gl_remote, gl_publish,
    gl_switch, gl_init, gl_history, gl_permission, gl_undo, gl_home, gl_runrepo)
from . import pprint
from . import helpers
from enum import Enum

from .. import Constants


SUCCESS = 0
ERRORS_FOUND = 1
# 2 is used by argparse to indicate cmd syntax errors.
INTERNAL_ERROR = 3
NOT_IN_GL_REPO = 4

__version__ = '0.8.8'
URL = 'http://gitless.com'

repo = None
try:
  repo = core.Repository()
  try:
    pprint.DISABLE_COLOR = not repo.config.get_bool('color.ui')
  except pygit2.GitError:
    pprint.DISABLE_COLOR = (
        repo.config['color.ui'] in ['no', 'never'])
except (core.NotInRepoError, KeyError):
  pass

def print_help(parser):
  pprint.sep()
  """print help for humans"""
  print(parser.description)
  print('\ncommands:\n')

  # https://stackoverflow.com/questions/20094215/argparse-subparser-monolithic-help-output
  # retrieve subparsers from parser
  subparsers_actions = [
      action for action in parser._actions
      if isinstance(action, argparse._SubParsersAction)]
  # there will probably only be one subparser_action,
  # but better safe than sorry
  for subparsers_action in subparsers_actions:
      # get all subparsers and print help
      for choice in subparsers_action._choices_actions:
          print('    {:<19} {}'.format(choice.dest, choice.help))
  pprint.sep()
  if not repo:
    pprint.err("Cannot show repo-specific information as you are not in a known gitless repo")
  else:
    try:
      with Path(str(Constants.CONFIG_PATH) + "/" + os.path.basename(repo.root)+".json").open("r", encoding="utf-8") as f:
        d = json.load(f)
        try:
          w = d["settings"][0]["workflow"]
          print(f"Workflow designated by Admin:\n{w}")
        except Exception:
          pprint("Your admin hasn't designated as workflow description. This is key for advising New or Novice users on how to proceed about using the system.")
    except (FileNotFoundError):
      pprint.err("Could not locate your shared config file")

def build_parser(subcommands, repo):
  l = ""
  if Path(Constants.CONFIG_PATH).exists():
    try:
      with Path(str(Constants.CONFIG_PATH) + "/" + os.path.basename(repo.root) + ".json").open("r", encoding='utf-8') as f:
          data = json.load(f)
          for u in data["settings"][0]["users"]:
              l = l + u.get("username") + " - " + Constants.Access_Type.Parse(u.get("account_type")) + "\n"
    except Exception:
      pprint.err("This repository is missing some key files for dfrommont's version of Gitless..., it may need to be reinitialised")
  if repo:
    parser = argparse.ArgumentParser(
        description=(
            f'Gitless: a version control system built on top of Git.\nMore info, downloads and documentation at {URL}\n\n################################################################################\nWho has access to this repo?\n{l}\n################################################################################\n'),
        formatter_class=argparse.RawDescriptionHelpFormatter)
  else:
        parser = argparse.ArgumentParser(
        description=(
            f'Gitless: a version control system built on top of Git.\nMore info, downloads and documentation at {URL}\n\n'),
        formatter_class=argparse.RawDescriptionHelpFormatter)
  if sys.version_info[0] < 3:
      parser.register('action', 'parsers', helpers.AliasedSubParsersAction)
  parser.add_argument(
      '--version', action='version', version=(
         'GL Version: {0}\nYou can check if there\'s a new version of Gitless '
         'available at {1}'.format(__version__, URL)))
  subparsers = parser.add_subparsers(title='subcommands', dest='subcmd_name')
  subparsers.required = True

  for sub_cmd in subcommands:
    sub_cmd.parser(subparsers, repo)

  return parser

def setup_windows_console():
  if sys.platform == 'win32':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

def verify_access(json_path: Path, permission_file_name: str, username: str) -> Constants.Access_Type:
  with Path(json_path).open("r", encoding='utf-8') as f:
    data = json.load(f)
    for repo in data.get("settings", []):
      if repo.get("repo_name") != permission_file_name:
        continue
      for user in repo.get("users", []):
        if user.get("username") == username:
          return Constants.Access_Type.Parse(user.get("account_type"))
      pprint.err("Could not find given user in config file")
      return Constants.Access_Type.NONE
    return Constants.Access_Type.NONE

def main():
  #grab username from config.json in /.git

  try:
    with Path(repo.path + "/dit_config.json").open("r", encoding='utf-8') as f:
      d = json.load(f)
      u = d["this_user"]
      m = d["this_machine"]
      Constants.username = u.get("username")
      Constants.access_level = Constants.Access_Type.Parse(u.get("account_type"))
      Constants.CONFIG_PATH = m.get("CONFIG_PATH")
      Constants.CONFIG_PATH_REPO_URL = m.get("CONFIG_PATH_REPO_URL")
  except Exception:
    pprint.err("This repository is missing.../.git/dit_config.json, it may need to be reinitialised")
    
  sub_cmds = [
      gl_track, gl_untrack, gl_status, gl_diff, gl_commit, gl_branch, gl_tag,
      gl_checkout, gl_merge, gl_resolve, gl_fuse, gl_remote, gl_publish,
      gl_switch, gl_init, gl_history, gl_permission, gl_undo, gl_home, gl_runrepo]

  parser = build_parser(sub_cmds, repo)
  argcomplete.autocomplete(parser)
  if len(sys.argv) == 1:
    print_help(parser)
    return SUCCESS

  args = parser.parse_args()
  try:
    if args.subcmd_name != 'init' and repo:

      permission_file_name = os.path.basename(repo.root)+".json"
      if not Constants.sync_repo_permissions(permission_file_name):
        print("The repo failed to update it's permissions from the config server!")
        quit()
      else:
        Constants.access_level = verify_access(str(Constants.CONFIG_PATH)+ "/" + permission_file_name, os.path.basename(repo.root), Constants.username)
        if Constants.access_level == Constants.Access_Type.NONE:
          print("You do not have permission to access this repo!")
          quit()
    if args.subcmd_name != 'init' and not repo:
      raise core.NotInRepoError('You are not in a Gitless\'s repository')

    setup_windows_console()
    return SUCCESS if args.func(args, repo) else ERRORS_FOUND
  except KeyboardInterrupt:
    pprint.puts('\n')
    pprint.msg('Keyboard interrupt detected, operation aborted')
    return SUCCESS
  except core.NotInRepoError as e:
    pprint.err(e)
    pprint.err_exp('do gl init to turn this directory into an empty repository')
    pprint.err_exp('do gl init remote_repo to clone an existing repository')
    return NOT_IN_GL_REPO
  except (ValueError, pygit2.GitError, core.GlError) as e:
    pprint.err(e)
    return ERRORS_FOUND
  except CalledProcessError as e:
    pprint.err(e.stderr)
    return ERRORS_FOUND
  except:
    pprint.err('Some internal error occurred')
    pprint.err_exp(
        'If you want to help, see {0} for info on how to report bugs and '
        'include the following information:\n\n{1}\n\n{2}'.format(
            URL, __version__, traceback.format_exc()))
    return INTERNAL_ERROR
