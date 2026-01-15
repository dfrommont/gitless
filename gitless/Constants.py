from pathlib import Path
from enum import Enum
import subprocess

CONFIG_PATH = Path("/home/vboxuser/DIT/Dit2.0_Config")
CONFIG_PATH_REPO_URL = "https://github.com/dfrommont/Dit2.0_Config"

username = ""
password = ""

class Access_Type(Enum):
  NONE = 0
  NEW = 1
  NOVICE = 2
  EXPERT = 3

  def Parse(t: str) -> Enum:
    if t == "New" or t == "NEW":
      return Access_Type.NEW
    elif t == "Novice" or t == "novice":
      return Access_Type.NOVICE
    elif t == "Expert" or t == "expert":
      return Access_Type.EXPERT
    else:
      return Access_Type.NONE 
    
  def Parse(i: int) -> Enum:
    if i == 1:
      return Access_Type.NEW
    elif i == 2:
      return Access_Type.NOVICE
    elif i == 3:
      return Access_Type.EXPERT
    else:
      return Access_Type.NONE 


access_level = Access_Type.NONE

def run(cmd, cwd=None):
  result = subprocess.run(
    cmd,
    cwd=cwd,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    shell=True
  )
  return result.returncode == 0

def sync_repo_permissions(repo_name) -> bool:
  if not CONFIG_PATH.exists() or not CONFIG_PATH.is_dir():
    print(f"Config path {CONFIG_PATH} does not exist or is not a directory!")

    if not run(f"git clone {CONFIG_PATH_REPO_URL} \"{CONFIG_PATH}\""):
      print("Failed to close config repository!")
      return False
  
  if not run("git fetch --quiet", cwd=CONFIG_PATH):
    print("Failed to fetch updates to config repository!")
    return False
  
  result = subprocess.run(
    f"git status --porcelain {repo_name}.json",
    cwd=CONFIG_PATH,
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    text=True
  )

  if result.stdout.strip():
    if not run(
      f"git add {repo_name}.json && git commit -m \"Update permissions\" --quiet",
      cwd=CONFIG_PATH
    ):
      print(f"Failed to commit changes to {repo_name}.json")
      return False
    
  result = subprocess.run(
    "git rev-list --left-reight --count HEAD..@{u}",
    cwd=CONFIG_PATH,
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    text=True
  )

  if result.returncode != 0:
    print("Failed to get git sync state!")
    return False
  
  behind, ahead = map(int, result.stdout.strip().split())

  if behind > 0:
    if not run("git pull --rebase --quiet", cwd=CONFIG_PATH):
      print("Failed to pull updates for config repository!")
      return False
    
  if ahead > 0:
    if not run("git push --quiet", cwd=CONFIG_PATH):
      print("Failed to push update for config repository!")
      return False
      
  return True