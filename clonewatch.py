#!/usr/bin/env python3.10

# python3.10 used because current python3 is python3.12 
# which seems to suddenly be managed by brew on my machine
# after latest upgrade
# requires pyperclip: pip install pyperclip

# continuously watches the system clipboard, aka pastebuffer for git repos
# and automatically clones them into a specific location
# if the repo already exists, does a git pull

from os.path import expanduser
from subprocess import Popen, PIPE, DEVNULL
import logging
import os
import pyperclip
import re
import sys
import time

# TODO add ThreadPoolExecutor concurrency from concurrent.futures see: 
#  https://docs.python.org/dev/library/concurrent.futures.html#threadpoolexecutor-example
# TODO update repos based on time since latest update being greater than average past few updates
#  (need last pulled data, maybe a poop file?)
# TODO browser extension integration instead of clipboard transport

# time in seconds between clipboard checks
INTERVAL = 1.5
# root of all checkouts
REPO_HOME = expanduser("~/src/other/")
LOG = os.path.join(REPO_HOME, "clonewatch.log")


# e.g. github, gitlab etc.
# enables parsing various urls and specifying the root clone dir
class RepoParser:
    def __init__(self, dirname, regex):
        self.dirname = dirname
        self.regex = regex

    # returns (user, url) tuple if parsed, otherwise None
    def parse(self, s):
        return re.search(self.regex, s)


ALL_PARSERS = [
    (RepoParser("github.com", r'^(?:https://|git@)github\.com:([^/]+)/(.*?)(\.git)?$')),
    (RepoParser("gitlab.com", r'^(?:https://|git@)gitlab\.com:([^/]+)/(.*?)(\.git)?$')),
    (RepoParser("bitbucket.org", r'^(?:git clone )?(?:git@bitbucket.org:)([^/]+)/([^/]+).git$')),
    (RepoParser("git.sr.ht", r'(?:https://git\.sr\.ht/|git@git\.sr\.ht:)~([^/]+)/([^/]+)')),
    (RepoParser("github.com", r'^https://github\.com/([^/]+)/([^/?]+)'))
]


# Attempts parsing s using each parser in turn.
# returns a tuple of dirname, parsed where both are None if parsing failed
# dirname is equal to hostname, a root dir for that repo host's local repos.
# parsed is a tuple of user, repourl where user is the account name on the repo hosting site
def detect(s):
    detected = False
    i = 0
    parsed = None
    while not detected and ++i < len(ALL_PARSERS):
        parsed = ALL_PARSERS[i].parse(s)
        if parsed is None:
            i += 1
        else:
            detected = True
    if parsed is not None:
        return ALL_PARSERS[i].dirname, parsed
    else:
        return None, parsed


# constructs a github git repo URL from user and reponame
def github_repo(user, reponame):
    return "git@github.com:{}/{}.git".format(user, reponame)


def update_console(num_running, latest_repo):
    print("\x1b[1F   downloads active: {}             ".format(num_running), end='\n')
    print("   latest: {}/{}             ".format(latest_repo[0], latest_repo[1]), end='\r')


def git_pull(repo_dir):
    return Popen(["git", "-C", repo_dir, "pull", "-q", "--recurse-submodules"], stdout=DEVNULL, stderr=DEVNULL)


def git_clone(url, repo_dir):
    return Popen(["git", "clone", "-q", "--recurse-submodules", url, repo_dir], stdout=DEVNULL, stderr=DEVNULL)


def main():
    # only one optional arg supported:
    # -l means print the name of the log file and exit
    if len(sys.argv) > 1 and sys.argv[1] == '-l':
        print("%s\n" % LOG)
        return

    print("check log file at {}\n".format(LOG))
    logging.basicConfig(filename=LOG, format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
    logging.info("startup")
    previous_clipboard = ""
    gits = []
    latest = ("?", "?")
    while True:
        url = pyperclip.paste().strip()
        if len(url) > 0 and url != previous_clipboard:
            previous_clipboard = url
            subdir, parsed = detect(url)
            if parsed is not None:
                user, repo = parsed.group(1, 2)
                latest = (user, repo)
                # the following can fail, but we probably want to die in that case
                user_basedir = os.path.join(os.path.join(REPO_HOME, subdir), user)
                os.makedirs(name=user_basedir, mode=0o755, exist_ok=True)
                repo_dir = os.path.join(user_basedir, repo)
                if os.path.exists(repo_dir):
                    logging.info("pull existing {} assuming {}".format(repo_dir, url))
                    # maybe check this ^ with git remote -v
                    gits.append(git_pull(repo_dir))
                else:
                    gits.append(git_clone(url, repo_dir))
                    logging.info("cloning {} by {}: {}".format(repo, user, url))

        time.sleep(INTERVAL)
        # TODO fix race condition
        finished = (x for x in gits if not x.poll() is None)
        for x in finished:
            if x.poll() == 0:
                logging.info("completed {}".format(x.args))
            else:
                logging.info("fail code {} for {}".format(x.poll(), x.args))
        # remove completed processes
        gits = [x for x in gits if x.poll() == None]
        update_console(len(gits), latest)


if __name__ == "__main__":
    main()
