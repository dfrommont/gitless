from pathlib import Path
from enum import Enum
import subprocess
import datetime
import sys
import os

testing = True

CONFIG_PATH = str(os.path.expanduser("~"))+"/.config/Dit2.0_Config"
CONFIG_PATH_REPO_URL = "" #Set by local config.json in .../.git

RED = '\033[31m'
CLEAR = '\033[0m'
def should_color():
  # We only output colored lines if the coloring is enabled and we are not being
  # piped or redirected
  return not False and sys.stdout.isatty()
def _color(color_code, text):
  return '{0}{1}{2}'.format(color_code, text, CLEAR) if should_color() else text
def red(text):
  return _color(RED, text)
def puts(s='', newline=True, stream=sys.stdout.write):
  if newline:
    s = s + '\n'
  stream(s)
def err(text):
  puts(red('✘ {0}'.format(text)), stream=sys.stderr.write)

username = ""

class Access_Type(Enum):
  NONE = 0
  NEW = 1
  NOVICE = 2
  EXPERT = 3

  @staticmethod
  def ParseStr(t: str) -> "Access_Type":
    if t == "New" or t == "NEW":
      return Access_Type.NEW
    elif t == "Novice" or t == "novice":
      return Access_Type.NOVICE
    elif t == "Expert" or t == "expert":
      return Access_Type.EXPERT
    else:
      return Access_Type.NONE 
    
  @staticmethod 
  def ParseInt(i: int) -> "Access_Type":
    if i == 1:
      return Access_Type.NEW
    elif i == 2:
      return Access_Type.NOVICE
    elif i == 3:
      return Access_Type.EXPERT
    else:
      return Access_Type.NONE 
        
  @staticmethod 
  def Parse(i: int) -> str:
    if i == 1:
      return "NEW"
    elif i == 2:
      return "NOVICE"
    elif i == 3:
      return "EXPERT"
    else:
      return "NONE"
    
  @staticmethod 
  def Serialise(self) -> int:
      return self.value
  
  @staticmethod 
  def GetAccessTypes() -> str:
    return "Expert - 3, Novice - 2, New - 1"

access_level = Access_Type.NONE

def run(cmd, cwd=None, capture=False):
  result = subprocess.run(
    cmd,
    cwd=cwd,
    stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
    stderr=subprocess.PIPE if capture else subprocess.DEVNULL,
    shell=True,
    text=True
  )
  return result.returncode == 0

def _run(cmd, cwd=None, capture=False):
  return subprocess.run(
    cmd,
    cwd=cwd,
    stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
    stderr=subprocess.PIPE if capture else subprocess.DEVNULL,
    shell=True,
    text=True
  )

def sync_repo_permissions(file_name: str) -> bool:
    if not Path(CONFIG_PATH+"/.git").exists() or not Path(CONFIG_PATH+"/.git").is_dir():
        print(f"Config path {CONFIG_PATH}/.git does not exist or is not a directory!")

        if not run(f"sudo git clone {CONFIG_PATH_REPO_URL} \"{CONFIG_PATH}\"", cwd=None, capture=True):
            print("Failed to clone config repository!")
            return False

    if not run("sudo git fetch --quiet", cwd=CONFIG_PATH, capture=True):
        print("Failed to fetch updates for config repository!")
        return False
    
    if file_name == "":
       print("aborting after clone/fetch for blank file name/initial call")
       return False

    result = subprocess.run(
        f"git status --porcelain {file_name}",
        cwd=CONFIG_PATH,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.stdout.strip():
        if not run(
            f"git add {file_name} && git commit -m \"{str(datetime.datetime.now())} {username}\"",
            cwd=CONFIG_PATH, capture=True
        ):
            print("Failed to commit changes!")
            return False

    upstream = subprocess.run(
        "git rev-parse --abbrev-ref --symbolic-full-name @{u}",
        cwd=CONFIG_PATH,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if upstream.returncode != 0:
        if not run("git push -u origin HEAD", cwd=CONFIG_PATH):
            print("Failed to set upstream branch!")
            return False
        return True

    result = subprocess.run(
        "git rev-list --left-right --count HEAD...@{u}",
        cwd=CONFIG_PATH,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    ahead, behind = map(int, result.stdout.strip().split())

    if behind > 0:
        if not run("git pull --rebase --quiet", cwd=CONFIG_PATH):
            print("Failed to pull updates!")
            return False

    if ahead > 0:
        if not run("git push --quiet", cwd=CONFIG_PATH):
            print("Failed to push updates!")
            return False

    return True

def verbose_conf_dialog(branch_name, cmd_type, args, upstream) -> bool:
  if testing:
     return True
  print('\n################################################################################')
  speech = []
  match cmd_type:
    case "branch":
      speech.append("You called a branch command attempting the following:\n")
      if args.remote: speech.append("-r or --remote -> List list remote branches in addition to local branches\n")
      if args.verbose: speech.append("-v or --verbose -> Make this command output verbose, i.e. include more detail and process visiability\n")
      if args.create_b: speech.append(f"-cp or --create-branch {args.create_b} -> Create the following new branch(es) {args.create_b}\n")
      if args.dp: speech.append(f"-dp or --divergent-point {args.dp} -> Create the new branch(es) diverging from this commit; otherswise use default point HEAD\n")
      if args.delete_b:
        s = f"-d or --delete-branch {args.delete_b} -> Delete the following branch(es): "
        speech.append(s + f"{', '.join(args.delete_b)}\n" if args.delete_b else "")
      if args.new_head: speech.append(f"-sh or --set-head {args.new_head or "HEAD"} -> set the head of the current branch ({branch_name}) to be this new commit: {args.new_head or "HEAD"}. Default if no commit_id given is HEAD\n")
      if args.upstream_b: speech.append(f"-su or --set-upstream {args.upstream_b} -> set the upstream branch of the current branch ({branch_name}) to the new branch {args.upstream_b}\n")
      if args.unset_upstream: speech.append(f"-uu or --unset-upstream: unset the upstream branch of the current branch ({branch_name})\n")
      if args.rename_b:
        if len(args.rename_b) == 1:
          speech.append(f"-rn or --rename-branch {args.rename_b} -> Rename the current branch ({branch_name}) to {args.rename_b}\n")
        elif len(args.rename_b) == 2:
           speech.append(f"-rn or --rename-branch {args.rename_b[0]} {args.rename_b[1]} -> Rename the specified branch {args.rename_b[0]} to {args.rename_b[1]}\n")
    case "checkout":
      speech.append("You are initiating a checkout of committed files\n")
      speech.append(f"{args.files} -> You are viewing the following file(s): ".join(args.files))
      speech.append("\n")
      if args.cp: speech.append("-cp or --commit-point {args.cp} -> You are viewing the above files at this commit point\n")
    case "commit":
      speech.append("You are making a commit - Save changes to the local repository. By default all tracked modified files are committed. To customize the set of files to be committed use the only, exclude, and include flags\n")
      if args.only: 
        s = f"-o or --only {args.only} -> Include only the following file(s) in the commit: "
        speech.append(s + f"{', '.join(args.only)}\n" if args.only else "")
      if args.p: speech.append("-p or --partial -> you want to interactively select segments of files to commit\n")
      if args.m: speech.append(f"-m or --message -> this commit will include the following message: {str(args.m)}\n")
      if args.exclude:
        s = f"-e or --exclude {args.delete_b} -> Exclude the following file(s) from the commit: "
        speech.append(s + f"{', '.join(args.exclude)}\n" if args.exclude else "")
      if args.include:
        s = f"-e or --exclude {args.delete_b} -> Include the following file(s) from the commit: "
        speech.append(s + f"{', '.join(args.include)}\n" if args.include else "")
    case "diff":
      speech.append("You are attempting to view changes made to files\n")
      if args.only: speech.append(f"{args.only} -> create the commit using only these files, note they must be \"tracked modified\" or \"untracked\" \n")
      if args.exclude:
        s = f"-e or --exclude {args.delete_b} -> Exclude the following file(s) from the commit: "
        speech.append(s + f"{', '.join(args.exclude)}\n" if args.exclude else "")
      if args.include:
        s = f"-i or --include {args.delete_b} -> Include the following file(s) from the commit: "
        speech.append(s + f"{', '.join(args.include)}\n" if args.include else "")
    case "fuse":
      speech.append("Fuse the divergent changes of a branch onto the current branch. By default all divergent changes from the given source branch are fused. To customize the set of commits to fuse use the only and exclude flags\n")
      if args.src: speech.append(f"Source branch: {args.src} -> {"This branch will be used to merge in to the current branch ({branch_name})" if args.src else "You have not given a source branch so {upstream} will be used"}\n")
      if args.only: 
        s = f"-o or --only {args.only} -> Fuse only these given commits: "
        speech.append(s + f"{', '.join(args.only)}\n" if args.only else "")
      if args.exclude:
        s = f"-e or --exclude {args.delete_b} -> Exclude the following file(s) from the commit: "
        speech.append(s + f"{', '.join(args.exclude)}\n" if args.exclude else "")
      if args.insertion_point: speech.append(f"-ip or --insertion-point {args.insertion_point or ""} -> Fuse from the insertion point or if none given, the divergent point between the current branch ({branch_name}) and incoming branch ({args.insertion_point if args.insertion_point else (args.src if args.src else upstream)}))\n")
      if args.abort: speech.append("-a or --abort -> The inclusion of this tags voids any other arguments given to this command and aborts the fuse that is in progress\n")
    case "history":
        speech.append("The history command will display the history of your repo or a branch of your repo\n")
        if args.b: speech.append(f"-b or --branch {"[args.b]" if args.b else ""} -> {f"view the history of the branch {args.b}\n" if args.b else f"You gave no branch so the default value of the current branch ({branch_name} will be used)"}\n")
        if args.limit: speech.append(f"-l or --limit {args.limit} -> display the history of only the first {args.limit} {"commit" if args.limit == 1 else "commits"}\n")
        if args.compact: speech.append("-c or --compact -> display the history in a compact format\n")
        if args.verbose: speech.append("-v or --verbose -> display the history verbosely including the diffs between each commit\n")
    case "home": speech.append("The home command is designed to groun you - it will list the base location of the project on your system, display the project readme, list who is using the project and how you should work with the repository\n")
    case "init":
      speech.append("Create an empty git repository or clone remote\n")
      if args.repo: 
        speech.append(f"Source remote repository: {args.repo} -> The remote ({args.repo}) will be copied and initialised as a new local repository\n")
      else:
         speech.append(f"Source: Not Given -> If a source remote repository is not given, a default empty repository will be created\n")
      if args.only: 
        s = f"-o or --only {args.only} -> Use only the given branch(es): "
        speech.append(s + f"{', '.join(args.only)}\n" if args.only else "\n")
      if args.exclude:
        s = f"-e or --exclude {args.delete_b} -> Exclude the following branch(s) from the commit: "
        speech.append(s + f"{', '.join(args.exclude)}\n" if args.exclude else "\n")
    case "merge":      
      speech.append("Merge the divergent changes of one branch onto another\n")
      if args.src: 
        speech.append(f"Source remote repository: {args.src} -> The branch ({args.src}) will be merged into the current branch ({branch_name})\n")
      else:
         speech.append(f"Source: Not Given -> If a source branch is not given, the upstream ({upstream}) will be used\n")
      if args.abort: speech.append("-a or --abort -> The inclusion of this tags voids any other arguments given to this command and aborts the merge that is in progress\n")
    case "permission":
        speech.append(f'Use the -a to add new users by username, -e to edit the access level of a username and -d to remove users from the repository. Access Levels: {Access_Type.GetAccessTypes()}')
        if args.add:
          s = f"-a or --add [...] -> Add the following users with an access level (respectively)\n"
          creds = [tuple(entry.split('/', 1)) for entry in args.add]
          speech.append(s + " " + ", ".join(f"{name}:{level}\n" for name, level in creds) if args.add else "\n")
        if args.edit:
          s = f"-e or --edit [...] -> Edit the following users to have a new access level (respectfully)\n"
          creds = [tuple(entry.split('/', 1)) for entry in args.edit]
          speech.append(s + " " + ", ".join(f"{name}:{level}\n" for name, level in creds) if args.edit else "\n")
        if args.delete:
          s = f"-d or --delete [...] -> Delete the following users from the access level configs\n"
          speech.append(s + " " + ", ".join(f"{name}\n" for name in args.delete) if args.delete else "\n")
    case "publish":
      if args.dst: 
        speech.append(f"Destination: {args.dst} -> Commits will be published upstream to the desintation\n")
      else:
         speech.append(f"Source: Not Given -> Commits till be published to the defeault upstream ({upstream})\n")
    case "remote":
      speech.append("List, create, edit or delete remotes\n")
      if args.remote_url:
        speech.append(f"Remote Url: {args.remote_url} -> Including this remote url means a new remote has been generated that you are linking to\n")
      if args.remote_name: speech.append(f"-c or --create {args.remote_name} -> You are creating a new remote called {args.remote_name}\n")
      if args.delete_r:
        s = f"-d or --delete [...] -> Delete the following remote(s)"
        speech.append(s + f"{', '.join(args.delete_r) if args.delete_r else ""}\n")
      if args.rename_r: 
        s = f"-rn or --rename [...] -> Rename the following remotes to the paired name: "
        speech.append(s + f"{", ".join([f"{a} becomes {b}" for a, b in zip(args.rename_r[::2], args.rename_r[1::2])])}\n")
    case "resolve":
        s = "Mark the following file(s) with conflicts as resolved:"
        speech.append(s + f"{", ".join(args.files) if args.files else ""}\n")
    case "status":
        speech.append("View the status of the repo or a subset of it\n")
        if args.paths:
          s = "Query the status of the following files"
          speech.append(s + f"{", ".join(args.paths) if args.paths else ""}\n")
    case "switch":
        speech.append("Switch branches\n")
        speech.append(f"Destination: {args.branch}\n")
        if args.move_over:
          speech.append(f"-mo or --move-over -> brining uncommitted changes to the current branch {branch_name} over to the new branch {args.branch}\n")
        if args.move_ignored:
          if args.move_over:
            speech.append("-mi or --move-ignored -> this has been ignored as you have already set -mo or --move-over, ignored files will not be moved across from {branch_name} to {args.branch}\n")
          else :
            speech.append(f"-mi or --move-ignored -> move over all ignored files from the current branch {branch_name} to the new branch {args.branch}\n")
    case "tag":
        speech.append("List, create, or delete tags - simple text flags against a commit or action to identify them\n")
        if args.remote:
          speech.append("-r or --remote -> List remote tags alongside local tags\n")
        if args.create_t:
          s = f"-c or --create -> Create the following tag(s): "
          speech.append(s + f"{", ".join(args.create_t) if args.create_t else ""}\n")
        if args.ci:
          speech.append(f"-ci or --commit {args.ci if args.ci else "HEAD"} -> tag the commit {args.ci if args.ci else "HEAD"} with the new tag {frozenset(args.create_t)[0]}\n")
        if args.delete_t:
          s = f"-d or --delete -> Delete the following tag(s): "
          speech.append(s + f"{", ".join(args.delete_t) if args.delete_t else ""}\n")
    case "track":
        s = "Start tracking changes to the following file(s):\n"
        speech.append(s + f"{", ".join(args.files) if args.files else ""}\n")
    case "undo":
        speech.append("Undo local commits that contain mistakes or you do not want to be pushed tothe remote. Use -l LIMIT to control how many commits are to be undone (default1). Commits will be undone until either the limit, there are no more local-only commits or a merge commit is reached\n")
        if args.limit:
           speech.append(f"-l or --limit -> This will try to delete the top {args.limit} commit(s) starting with the HEAD of the current branch {branch_name}\n")
        else:
           speech.append("This will try to revert only the top commit (HEAD) of the current branch {branch_name}\n")
    case "untrack":
        s = "Stop tracking changes to the following file(s)"
        speech.append(s + f"{", ".join(args.files) if args.files else ""}\n")
    case _:
        err("Some internal error occurred, confirm dialog was called on an unknown command!\n")

  [print(s) for s in speech]
         
  print('{0} -> Do you wish to continue? (y/N)'.format(cmd_type))
  user_input = input()
  print('\n################################################################################')
  return user_input and user_input[0].lower() == 'y'

def try_get_upstream(repo, local):
  #local -> core.pygit2.GIT_BRANCH_LOCAL
  r = repo.git_repo.lookup_branch(repo.git_repo.head.shorthand, local)
  u, n = "", ""
  try:
    u = r.upstream
    try:
      n = u.name
    except:
      n = ""
  except:
    u = ""
  if u == "" or n == "":
    return "NO_UPSTREAM"
  else:
    return n