from pathlib import Path
from enum import Enum
import subprocess

CONFIG_PATH = Path("/home/vboxuser/DIT/Dit2.0_Config")
CONFIG_PATH_REPO_URL = "https://github.com/dfrommont/Dit2.0_Config"

username = ""

class Access_Type(Enum):
  NONE = 0
  NEW = 1
  NOVICE = 2
  EXPERT = 3

  @staticmethod
  def Parse(t: str) -> "Access_Type":
    if t == "New" or t == "NEW":
      return Access_Type.NEW
    elif t == "Novice" or t == "novice":
      return Access_Type.NOVICE
    elif t == "Expert" or t == "expert":
      return Access_Type.EXPERT
    else:
      return Access_Type.NONE 
    
  @staticmethod 
  def Parse(i: int) -> "Access_Type":
    if i == 1:
      return Access_Type.NEW
    elif i == 2:
      return Access_Type.NOVICE
    elif i == 3:
      return Access_Type.EXPERT
    else:
      return Access_Type.NONE 
    
  @staticmethod 
  def Serialise(self) -> int:
      return self.value

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
    if not CONFIG_PATH.exists() or not CONFIG_PATH.is_dir():
        print(f"Config path {CONFIG_PATH} does not exist or is not a directory!")

        if not run(f"git clone {CONFIG_PATH_REPO_URL} \"{CONFIG_PATH}\"", cwd=None, capture=True):
            print("Failed to clone config repository!")
            return False

    if not run("git fetch --quiet", cwd=CONFIG_PATH, capture=True):
        print("Failed to fetch updates for config repository!")
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
            f"git add {file_name} && git commit -m \"Updated permissions\"",
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