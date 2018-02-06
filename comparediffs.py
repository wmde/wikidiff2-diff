#!/usr/bin/python -u
# -*- coding: utf-8 -*-

# compare Autoimport/* pages in test wiki before and after wikidiff2 changes

import sys
import itertools
import re
import urllib2
from wikitools import wiki, api
import difflib

if __name__ == '__main__':
    testwikiurl_old= "http://wmde-wikidiff2-unpatched.wmflabs.org/core"
    testwikiurl_new= "http://wmde-wikidiff2-patched.wmflabs.org/core"
    wikiA= wiki.Wiki(testwikiurl_old + "/api.php") 
    wikiB= wiki.Wiki(testwikiurl_new + "/api.php")

    r= wikiA.login("Jkroll@importbot", open("importbot-password").read().strip(), force=True, verify=True)
    if not r:
        print(r)
        sys.exit(1)
    token= api.APIRequest(wikiA, { "action": "query", "meta": "tokens" }).query(querycontinue=False) ["query"]["tokens"]["csrftoken"]
    
    res= api.APIRequest(wikiA, { "action": "query", "prop": "info|revisions", "intoken": "edit", "titles": "Diffcompare" }).query(querycontinue=False) ["query"]["pages"]
    edittoken= res[res.keys()[0]]["edittoken"]

    req= api.APIRequest(wikiA, { "action": "query", "list": "prefixsearch", "pssearch": "Autoimport/" })
    res= req.queryGen()
    diffstotal= 0
    diffschanged= 0
    diffs= []
    #~ res= itertools.islice(res, 10/10)
    for chunk in res:
        for page in chunk["query"]["prefixsearch"]:
            print ("%60s" % page["title"]).encode("utf-8"),
            req= api.APIRequest(wikiA, { "action": "query", "prop": "revisions", "titles": page["title"], "rvprop": "ids", "rvlimit": "max" })
            res= req.query(querycontinue=False)
            revisions= res["query"]["pages"][str(page["pageid"])]["revisions"]
            if len(revisions) < 3:  # need 2 revisions to compare diffs, latest revision is generated when importing the page
                print "%30s" % "not enough revisions, skipping"
                continue
            diffstotal+= 1
            print "%30s" % ("comparing revs %d/%d" % (revisions[2]["revid"], revisions[1]["revid"])),
            params= { "action": "compare", "fromrev": revisions[2]["revid"], "torev": revisions[1]["revid"] }
            res= api.APIRequest(wikiA, params).query(querycontinue=False)
            diffA= res["compare"]["*"].encode("utf-8")
            res= api.APIRequest(wikiB, params).query(querycontinue=False)
            diffB= res["compare"]["*"].encode("utf-8")
            
            movedpara= False
            if diffA==diffB:
                print("[ ] no change")
                changed= False
            else:
                print("[x] change found")
                changed= True
                diffschanged+= 1
                diff= difflib.Differ().compare(diffA.split("\n"), diffB.split("\n"))
                for line in diff:
                    if line[0] in "-+?":
                        #~ print(line)
                        if 'class="mw-diff-movedpara' in line:
                            movedpara= True
            
            diffs.append({ "title": page["title"], "revs": [ revisions[2]["revid"], revisions[1]["revid"] ], "changed": changed, "movedpara": movedpara })
    
    summary= "%d of %d compared diff outputs differ (%.2f%%)." % (diffschanged, diffstotal, diffschanged*100.0/diffstotal)
    print(summary)
    
    wikitext= """
== comparison of diffs in randomly selected pages with and without the moved-paragraph patch and related changes to wikidiff2 ==

{| class="wikitable sortable"
|-
! title
! revs
! links
! changed
! movedpara
"""
    for d in diffs:
        t= page["title"].replace(' ', '_')
        d["links"]= "[%s/index.php?title=%s&diff=%s&oldid=%s old] / [%s/index.php?title=%s&diff=%s&oldid=%s new]" % (testwikiurl_old,t,d["revs"][1],d["revs"][0], testwikiurl_new,t,d["revs"][1],d["revs"][0])
        wikitext+= """
|-
| %(title)s
| %(revs)s
| %(links)s
| %(changed)s
| %(movedpara)s
""" % d
    wikitext+= "|}\n"
    wikitext+= summary
    
    req= api.APIRequest(wikiA, { "action": "edit", "title": "Diffcompare", "text": wikitext, "token": edittoken }, write=True)
    res= req.query(querycontinue=False)
    if res["edit"]["result"] != "Success":
        raise res
    print("list saved to %s/index.php?title=%s" % (testwikiurl_new, "Diffcompare"))
    