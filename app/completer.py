#!/usr/bin/env python3
import sys
import os

# Your shell passes: arg1 = base_cmd, arg2 = current_word, arg3 = prev_word
cmd = sys.argv[1] if len(sys.argv) > 1 else ""
curr_word = sys.argv[2] if len(sys.argv) > 2 else ""
prev_word = sys.argv[3] if len(sys.argv) > 3 else ""

# Available completion candidates
subcommands = ["status", "commit", "checkout", "clone", "push", "pull", "branch"]

# Filter candidates matching what the user typed so far
matches = [s for s in subcommands if s.startswith(curr_word)]

# Output candidates one per line
for match in matches:
    print(match)