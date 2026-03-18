# -*- coding: utf-8 -*-
# Gitless - a version control system built on top of Git
# Licensed under MIT

"""gl publish - Publish commits upstream."""


from . import helpers, pprint
from .. import core


def parser(subparsers, _):
  """Adds the publish parser to the given subparsers object."""
  desc = 'publish commits upstream'
  publish_parser = subparsers.add_parser(
      'publish', help=desc, description=desc.capitalize(), aliases=['pb'])
  publish_parser.add_argument(
      'dst', nargs='?', help='the branch where to publish commits')
  publish_parser.set_defaults(func=main)


def main(args, repo):
  if core.Constants.Access_Type.ParseStr(core.Constants.access_level) == core.Constants.Access_Type.NEW:
    if core.Constants.verbose_conf_dialog(repo.current_branch, "publish", args, repo.git_repo.lookup_branch(repo.git_repo.head.shorthand, core.pygit2.GIT_BRANCH_LOCAL).upstream.name):
        pprint.ok("Command confirmed, continuing...")
    else:
        pprint.err("Command aborted, ending...")
    return False

  current_b = repo.current_branch
  dst_b = helpers.get_branch_or_use_upstream(args.dst, 'dst', repo)
  current_b.publish(dst_b)
  pprint.ok(
      'Publish of commits from branch {0} to branch {1} succeeded'.format(
        current_b, dst_b))
  return True
