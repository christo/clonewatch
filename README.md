# Clonewatch

Ever wanted to easily clone a bunch of git repositories in one session without having to organise
them into a directory structure by hand?

A background script for monitoring the system clipboard for urls recognisable as git repo urls 
and automatically cloning that repo into a preconfigured directory tree. Each repo host has
a root directory under which account name dirs are created with their cloned repos inside.

Currently supports the following repo hosts:

* https://github.com
* https://gitlab.com
* https://bitbucket.org
* Source Hut https://git.sr.ht

Add your own as required and send me a pull request to add it.

* Converts github.com web urls into git repo urls
* Performs clones concurrently across spawned child processes.
* Only clones if the clipboard changes
* Performs a pull if the repo already exists
* Tested on Linux and MacOS

## Requirements

Uses the python library pyperclilp:

`pip install pyperclip`

## Usage

* Edit the `REPO_HOME` location to the root directory of these clones. 
* Set the `INTERVAL` to a number of seconds for polling the clipboard.

The following prints the location of the log file so it can be tailed. This makes it easy
to set this up as two panes in a tmux session.

`clonewatch.py -l`

## Known Bugs

* [ ] There is a potential race condition which basically never happens for me so I haven't bothered
to fix it.