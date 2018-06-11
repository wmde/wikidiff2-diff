#!/usr/bin/python -u
import re

with open("/tmp/old-list") as old, open("/tmp/new-list") as new:
    syms= {}
    for line in old:
        m= re.match("\| \[([0-9]+), ([0-9]+)\]", line)
        if m:
            revs= m.group(1), m.group(2)
        elif line.startswith("| ") and len(line)==4:
            syms[revs]= line
    
    for line in new:
        m= re.match("\| \[([0-9]+), ([0-9]+)\]", line)
        if m:
            revs= m.group(1), m.group(2)
        elif line.startswith("|") and len(line)==2 and revs in syms:
            line= syms[revs]
        print(line.strip())
