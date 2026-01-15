from pathlib import Path
from enum import Enum

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