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
    gl_switch, gl_init, gl_history, gl_permission)
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

def build_parser(subcommands, repo):
  parser = argparse.ArgumentParser(
      description=(
          'Gitless: a version control system built on top of Git.\nMore info, '
          'downloads and documentation at {0}'.format(URL)),
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

def verify_access(json_path: Path, permission_file_name: str, username: str, password: str) -> Constants.Access_Type:
  with json_path.open("r", encoding='utf-8') as f:
    data = json.load(f)
    for repo in data.get("settings", []):
      if repo.get("repo_name") != permission_file_name:
        continue
      for user in repo.get("users", []):
        if user.get("username") != username:
          continue
        if user.get("password") == password:
          return Constants.Access_Type.Parse(user.get("account_type"))
        return Constants.Access_Type.NONE
      return Constants.Access_Type.NONE
    return Constants.Access_Type.NONE

def main():
  #first things first, go off and get the permissions file
  #have them log in
  #boom we have username, permission and repo

  if repo:
    permission_file_name = os.path.basename(repo.root)+".json"
    if not Constants.sync_repo_permissions(permission_file_name):
      print("The repo failed to update it's permissions from the config server!")
      quit()
    else:
      Constants.username = input("Username: ")
      Constants.password = input("Password: ")
      Constants.access_level = verify_access(str(Constants.CONFIG_PATH)+ "/" + permission_file_name, permission_file_name, Constants.username, Constants.password)
      if Constants.access_level == Constants.Access_Type.NONE:
        print("You do not have permission to access this repo!")
        quit()
    
  sub_cmds = [
      gl_track, gl_untrack, gl_status, gl_diff, gl_commit, gl_branch, gl_tag,
      gl_checkout, gl_merge, gl_resolve, gl_fuse, gl_remote, gl_publish,
      gl_switch, gl_init, gl_history, gl_permission]

  parser = build_parser(sub_cmds, repo)
  argcomplete.autocomplete(parser)
  if len(sys.argv) == 1:
    print_help(parser)
    return SUCCESS

  args = parser.parse_args()
  try:
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
