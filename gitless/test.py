import pytest

import tempfile
import subprocess
import os
from pathlib import Path

from . import core
from . import Constants
from . import cli

test_directory = "/home/vboxuser/Documents/unit_tests"

@pytest.fixture(autouse=True)
def run_before_and_after_tests():
    if Path(test_directory).exists():
        os.rmdir(test_directory)
    os.mkdir(test_directory)
    core.init_repository(test_directory)
    print("I ran before")

    yield

def test_1():
    with tempfile.TemporaryDirectory() as tempdir:
        output = Constants._run("gl home", test_directory, True)
        stdout = output.stdout

        is_name_present = "Repo: " in stdout
        is_branch_present = "Current branch: " in stdout
        is_commit_count_present = "Your branch" in stdout and "origin" in stdout and "commit" in stdout
        is_user_present = "You are user" in stdout

        success = is_name_present and is_branch_present and is_commit_count_present and is_user_present

        assert success == True