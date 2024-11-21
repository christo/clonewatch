#!/usr/bin/env zsh

# using tmux session named cw
# start clonewatch with its logs tailing in two panes of a new tmux window
# if such a session exists, attach to it, otherwise create it

set -eu

if ( tmux has-session -t cw 2>/dev/null ); then
    tmux attach -t cw
else
    # create new session named cw
    # -u means utf8 -2 means 256 colour
    # -t foo:bar sets target session "foo" new window "bar"
    # -d start detached (will attach at end)
    tmux -u2 new-session -s cw -n clonewatch -d
    tmux select-window -t cw:clonewatch
    tmux send-keys -t cw:clonewatch "clonewatch.py" Enter
    # vertical split (top and bottom panes), new pane receives focus
    tmux split-window -v
    tmux send-keys -t cw "tail -f $(clonewatch.py -l)" Enter
    tmux select-layout even-vertical
    # now attach to it
    tmux -u2 attach -t cw
fi
