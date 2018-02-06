#!/usr/bin/python -u
# -*- coding: utf-8 -*-

# this is a one-off script for importing random pages to wikidiff2 test wikis

import sys
import itertools
import re
import urllib2
from wikitools import wiki, api

srcwikilang= "en"

if __name__ == "__main__":
    srcwiki= wiki.Wiki("https://%s.wikipedia.org/w/api.php" % srcwikilang) 
    dstwiki= wiki.Wiki("http://wmde-wikidiff2-patched.wmflabs.org/core/api.php") 
    # normal accounts don't work anymore. instead, there are "bot passwords" now which refer to accounts with special 
    # rights management. the set of possible rights for these non-accounts doesn't include importing, forcing me to 
    # hack the mediawiki rights checking stuff on the test machine just so that i can import some pages for testing. 
    # you can't make this stuff up.
    #~ r= dstwiki.login("importbot", <password>, force=True, verify=True)
    r= dstwiki.login("Jkroll@importbot", open("importbot-password").read(), force=True, verify=True)
    print "login returns %s" % r
    if not r:
        sys.exit(1)
    
    token= api.APIRequest(dstwiki, { "action": "query", "meta": "tokens" }).query(querycontinue=False) ["query"]["tokens"]["csrftoken"]
    print("token: %s\n" % token)

    rgen= api.APIRequest(srcwiki, { "action": "query", "list": "random", "rnlimit": 10, "rnnamespace": 0 }).queryGen()
    pages= itertools.islice(rgen, 100/10)
    for chunk in pages:
        for page in chunk["query"]["random"]:
################### instead of using the export API, use the Special:Export API which is not part of the API. this is the only method which seems to work. go figure.
            title= page["title"].replace(" ", "_").encode("utf-8")
            print("page: '%s'" % title)
            params= "&pages=%s&offset=1&limit=10&action=submit" % title
            f= urllib2.urlopen("https://en.wikipedia.org/w/index.php?title=Special:Export", params)
            page_xml= f.read()
            page_xml= re.sub("<title>", "<title>Autoimport/", page_xml)
            req= api.APIRequest(dstwiki, { "action": "import", "format": "xml", "xml": page_xml, "token": token, "interwikiprefix": "en" }, write=True, multipart=True)
            # need to fiddle with this and then run the request manually, because the API desperately NEEDS the filename parameter even though it isn't used anywhere, and wikitools doesn't set it.
            req.encodeddata= re.sub('name="xml"', 'name="xml"; filename="broomstick.xml"', req.encodeddata)
            req.request = urllib2.Request(req.wiki.apibase, req.encodeddata, req.headers)
            try:
                res= req.query(querycontinue=False)
            except api.APIError as ex:
                if "databaseerror-text" in str(ex):
                    print ex
                    # for whatever reason, this "database query error" happens regularly every couple pages. 
                    # in this case, a kind of "limbo" page with no revisions attached is SOMETIMES left in the target wiki.
                    # just delete the page and move on. 

                    # ...but... attempting to delete the page results in another "database query error". :-)
                    # better just manually "DELETE FROM page WHERE page_latest=0;" after running this script, which seems to fix the problem.
                    
                    #~ res= api.APIRequest(dstwiki, { "action": "delete", "title": "Autoimport/%s" % title, "token": token }, write=True).query(querycontinue=False)
                    #~ printf("delete result: %s" % res)
                    

################### transwiki import: 'Unrecognized value for parameter "interwikisource"' for "wikipedia", "en", "enwiki" etc. checked $wgImportSources and interwiki table, everything should work. giving up.
            #~ req= api.APIRequest(srcwiki, { "action": "import", "interwikisource": "wikipedia", "interwikipage": page["title"], "fullhistory": True, "token": token }, write=True)
            #~ print req.encodeddata
            #~ res= req.query(querycontinue=False)
            #~ print(res)
            #~ red= api.APIRequest(srcwiki, { "action": "move", "from": page["title"], "to": "Autoimport/%s" % page["title"], "token": token, "noredirect": True }, write=True).query(querycontinue=False)
            #~ print res



################### after hacking post-2016 mediawiki to let bots import stuff again, this *** STILL DOESN'T WORK BECAUSE  E X P O R T  doesn't  E X P O R T  R E V I S I O N  H I S T O R I E S
            #~ r= api.APIRequest(srcwiki, { "action": "query", "export": 1, "pageids": page["id"], "format": "xml", "curonly": False, "history": True, "fullhistory": True }).query(querycontinue=False)
            #~ page_xml= r["query"]["export"]["*"]
            #~ page_xml= re.sub("<title>", "<title>Autoimport/", page_xml)
            #~ req= api.APIRequest(dstwiki, { "action": "import", "format": "xml", "xml": page_xml.encode('utf-8'), "token": token, "interwikiprefix": "en" }, write=True, multipart=True)
            #~ req.encodeddata= re.sub('name="xml"', 'name="xml"; filename="meinefresse.xml"', req.encodeddata)
            #~ req.request = urllib2.Request(req.wiki.apibase, req.encodeddata, req.headers)
            #~ try:
                #~ res= req.query(querycontinue=False)
                #~ print res
            #~ except api.APIError as ex:
                #~ if "databaseerror-text" in str(ex):
                    #~ print ex
                    #~ print "continuing..."





