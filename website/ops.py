#!/usr/bin/python3.10

import datetime
import json
import os
import os.path
import sqlite3
import hashlib
import random
import string
import smtplib, ssl
import urllib
import jwt
import shutil
import markdown
import re
import secrets
import pathlib
import subprocess
from collections import defaultdict
from icu import Locale, Collator
import requests
from nvh import nvh
from bottle import request
import sys
import tempfile
import glob
import dmlex2schema



currdir = os.path.dirname(os.path.abspath(__file__))
siteconfig = json.load(open(os.path.join(currdir, "siteconfig.json"), encoding="utf-8"))
for datadir in ["dicts", "uploads", "sqlite_tmp"]:
    pathlib.Path(os.path.join(siteconfig["dataDir"], datadir)).mkdir(parents=True, exist_ok=True)
os.environ["SQLITE_TMPDIR"] = os.path.join(siteconfig["dataDir"], "sqlite_tmp")

with open(os.path.join(currdir, 'version.txt')) as v_f:
    version = v_f.readline().strip()

DEFAULT_ENTRY_LIMIT = 5000
defaultDictConfig = {"editing": {},
                     "searchability": {"searchableElements": []},
                     "structure": {"nvhSchema": "", 'root': ''},
                     "titling": {"headwordAnnotations": []},
                     "flagging": {"flag_element": "", "flags": []},
                     "entry_count": 0}

prohibitedDictIDs = ["login", "logout", "make", "signup", "forgotpwd", "changepwd", "users", "dicts", "oneclick", "recoverpwd", "createaccount", "consent", "userprofile", "dictionaries", "about", "list", "lemma", "json", "ontolex", "tei"];

phases_re = re.compile('^#\s+phases\s*:\s*(.*?)$')

# db management
def getDB(dictID):
    if os.path.isfile(os.path.join(siteconfig["dataDir"], "dicts/"+dictID+".sqlite")):
        conn = sqlite3.connect(os.path.join(siteconfig["dataDir"], "dicts/"+dictID+".sqlite"))
        conn.row_factory = sqlite3.Row
        conn.executescript("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=on")
        return conn
    else:
        return None

def getMainDB():
    conn = sqlite3.connect(os.path.join(siteconfig["dataDir"], 'lexonomy.sqlite'))
    conn.row_factory = sqlite3.Row
    return conn

def getLinkDB():
    conn = sqlite3.connect(os.path.join(siteconfig["dataDir"], 'crossref.sqlite'))
    conn.row_factory = sqlite3.Row
    return conn

# SMTP
def sendmail(mailTo, mailSubject, mailText):
    try:
        if siteconfig["mailconfig"] and siteconfig["mailconfig"]["host"] and siteconfig["mailconfig"]["port"]:
            if siteconfig["mailconfig"]["secure"]:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(siteconfig["mailconfig"]["host"], siteconfig["mailconfig"]["port"], context=context)
            else:
                server = smtplib.SMTP(siteconfig["mailconfig"]["host"], siteconfig["mailconfig"]["port"])
            message = "Subject: " + mailSubject + "\n\n" + mailText
            server.sendmail(siteconfig["mailconfig"]["from"], mailTo, message.encode('utf-8'))
            server.quit()
    except smtplib.SMTPRecipientsRefused:
        return False

    return True

def sendFeedback(email_from, body_text):
    site_url = siteconfig.get('baseUrl', 'None')
    subject = "Lexonomy feedback from " + email_from
    mail_to = "support@sketchengine.eu"
    mail_text = body_text + "\n\nMAIL: " + email_from + "\n\nDomain: " + site_url
    sendmail(mail_to, subject, mail_text)
    mail_text_user = "Thank you for your feedback regarding Lexonomy. We will get back in touch as soon as possible. Here is the copy of your question:\n\n" + body_text
    sendmail(email_from, subject, mail_text_user)
    return True


# config
def readDictConfigs(dictDB):
    configs = {"siteconfig": siteconfig}

    c = dictDB.execute("select * from configs")
    for r in c.fetchall():
        configs[r["id"]] = json.loads(r["json"])

    # user access rights form 'user_dict' table
    configs['users'] = {}
    c1 = dictDB.execute("PRAGMA database_list")
    dictID = c1.fetchone()['file'].strip().split('/')[-1][:-7]

    conn = getMainDB()
    c2 = conn.execute("SELECT * FROM user_dict WHERE dict_id=?", (dictID,))
    for r in c2.fetchall():
        configs['users'][r['user_email']] = {"canEdit": 1 if r['can_edit'] else 0,
                                             "canView": 1 if r['can_view'] else 0,
                                             "canConfig": 1 if r['can_config'] else 0,
                                             "canDownload": 1 if r['can_download'] else 0,
                                             "canUpload": 1 if r['can_upload'] else 0}

    # alow access to all managers of project to all dicts that belong to the project
    c3 = conn.execute("SELECT DISTINCT u.user_email FROM user_projects AS u INNER JOIN project_dicts AS d ON u.project_id=d.project_id WHERE d.dict_id=? AND u.role=?", (dictID, 'manager'))
    for r2 in c3.fetchall():
        configs['users'][r2['user_email']] = {"canEdit": 1,
                                             "canView": 1,
                                             "canConfig": 1,
                                             "canDownload": 1,
                                             "canUpload": 1}


    # admin configs like dict limit form 'dicts' table
    c4 = conn.execute("SELECT configs FROM dicts WHERE id=?", (dictID,))
    r = c4.fetchone()
    if r:
        configs['dict_settings'] = json.loads(r["configs"])
    # if r:
    #     for key, value in json.loads(r["configs"]).items():
    #         configs[key] = value

    add_items = ["ident", "publico", "kontext", "titling", "flagging", "styles",
                 "searchability", "xampl", "thes", "collx", "defo", "structure",
                 "formatting", "editing", "download", "links", "gapi",
                 "metadata", "entry_count"]
    for conf in set(add_items):
        if not conf in configs:
            configs[conf] = defaultDictConfig.get(conf, {})

    # Default dict: return value for items not present in dict
    for key in configs.keys():
        if type(configs[key]) is dict:
            configs[key] = defaultdict(lambda: None, configs[key])

    return configs

"""
def addSubentryParentTags(db, entryID, xml):
    from xml.dom import minidom, Node
    doc = minidom.parseString(xml)
    els = []
    _els = doc.getElementsByTagName("*")
    els.append(_els[0])
    for i in range(1, len(_els)):
        if _els[i].getAttributeNS("http://www.lexonomy.eu/", "subentryID"):
            els.append(_els[i])
    for el in els:
        subentryID = el.getAttributeNS("http://www.lexonomy.eu/", "subentryID")
        if el.parentNode.nodeType != Node.ELEMENT_NODE:
            subentryID = entryID
        c = db.execute("select s.parent_id, e.title from sub as s inner join entries as e on e.id=s.parent_id where s.child_id=?", (subentryID,))
        for r in c.fetchall():
            pel = doc.createElementNS("http://www.lexonomy.eu/", "lxnm:subentryParent")
            pel.setAttribute("id", str(r["parent_id"]))
            pel.setAttribute("title", r["title"])
            el.appendChild(pel)
    return doc.toxml()

def removeSubentryParentTags(xml):
    return re.sub(r"<lxnm:subentryParent[^>]*>", "", xml)
"""

# auth
def verifyLogin(email, sessionkey):
    if "httpAuth" in siteconfig and siteconfig["httpAuth"] and request.auth and request.auth[0]:
        login_res = httpAuthLogin(request.auth[0])
        if login_res["success"]:
            email = request.auth[0]
            sessionkey = login_res["key"]
    if email == "" or sessionkey == "":
        return {"loggedin": False, "email": None}
    conn = getMainDB()
    now = datetime.datetime.utcnow()
    yesterday = now - datetime.timedelta(days=1)
    email = email.lower()
    c = conn.execute("select email, ske_apiKey, ske_username, apiKey, consent, is_manager from users where email=? and sessionKey=? and sessionLast>=?", 
                     (email, sessionkey, yesterday))
    user = c.fetchone()
    if not user:
        return {"loggedin": False, "email": None}
    conn.execute("update users set sessionLast=? where email=?", (now, email))
    conn.commit()
    return {"loggedin": True, "email": email, "isAdmin": email in siteconfig["admins"],
            "isProjectManager": user['is_manager'],
            "ske_username": user["ske_username"], "ske_apiKey": user["ske_apiKey"],
            "apiKey": user["apiKey"], "consent": user["consent"] == 1}

def verifyLoginAndDictAccess(email, sessionkey, dictDB):
    ret = verifyLogin(email, sessionkey)
    configs = readDictConfigs(dictDB)
    dictAccess = configs["users"].get(email)
    if ret["loggedin"] == False or (not dictAccess and not ret["isAdmin"]):
        return {"loggedin": ret["loggedin"], "email": email, "dictAccess": False, "isAdmin": False}, configs
    ret["dictAccess"] = dictAccess or {}
    for r in ["canEdit", "canConfig", "canDownload", "canUpload", "canView"]:
        ret[r] = ret.get("isAdmin") or (dictAccess and dictAccess[r])
        ret["dictAccess"][r] = ret[r]
    return ret, configs

def verifyLoginAndProjectAccess(email, sessionkey):
    ret = verifyLogin(email, sessionkey)
    if ret["loggedin"] == False or not ret["isAdmin"]:
        return {"loggedin": ret["loggedin"], "email": email, "isAdmin": False}

    configs = {'manager_of': [], 'annotator_of': []}
    conn = getMainDB()
    c = conn.execute('SELECT project_id, role FROM user_projects WHERE user_email=?', (email,))
    for r in c.fetchall():
        if r['role'] == 'manager':
            configs['manager_of'].append(r['project_id'])
        else:
            configs['annotator_of'].append(r['project_id'])
    return ret, configs

def getDmlLexSchemaItems(modules, xlingual_langs=[], linking_relations=[], etymology_langs=[]):
    with open(os.path.join(currdir, "dictTemplates/dmlex_modules.txt"), 'r') as f:
        result, desc_dict = dmlex2schema.get_dmlex_schema(f, "entry", modules, xlingual_langs, linking_relations, etymology_langs)
        schema = []
        used_modules = set()
        dmlex2schema.final_schema2str(result, schema, used_modules)
        return ''.join(schema), desc_dict, list(used_modules)


def deleteEntry(db, entryID, email):
    # tell my parents that they need a refresh:
    db.execute ("update entries set needs_refresh=1 where id in (select parent_id from sub where child_id=?)", (entryID,))
    # update completed:
    c = db.execute("SELECT id, nvh FROM entries WHERE id=?", (entryID, ))
    row = c.fetchone()
    c2 = db.execute("SELECT json FROM configs WHERE id='completed_entries'")
    r2 = c2.fetchone()
    if '__lexonomy__completed' in row['nvh']:
        db.execute("UPDATE configs SET json=? WHERE id=?", (int(r2['json']) - 1, 'completed_entries'))
    # delete me:
    db.execute ("delete from entries where id=?", (entryID,))
    # tell history that I have been deleted:
    db.execute ("insert into history(entry_id, action, [when], email, nvh) values(?,?,?,?,?)",
                (entryID, "delete", datetime.datetime.utcnow(), email, None))

    c2 = db.execute("SELECT json FROM configs WHERE id='entry_count'")
    r2 = c2.fetchone()
    db.execute("UPDATE configs SET json=? WHERE id=?", (int(r2['json']) - 1, 'entry_count'))
    db.commit()

def readEntry(db, configs, entryID):
    c = db.execute("select * from entries where id=?", (entryID,))
    row = c.fetchone()
    if not row:
        return 0, "", "", ""
    nvh = row["nvh"]
    if row["json"] != "":
        json = row["json"]
    else:
        json = nvh2jsonDump(nvh)
    """
    if configs["subbing"]:
        nvh = addSubentryParentTags(db, entryID, nvh)
    """
    return entryID, nvh, json, row["title"]

def createEntry(dictDB, configs, entryID, entryNvh, email, historiography):
    entryJson = nvh2jsonDump(entryNvh)
    nvhParsed = nvh.parse_string(entryNvh)
    title = getEntryTitle(nvhParsed, configs["titling"])
    sortkey = getSortTitle(nvhParsed, configs["titling"])
    needs_refresh = 1 if configs["searchability"].get("searchableElements") and len(configs["searchability"].get("searchableElements")) > 0 else 0
    # entry title already exists?
    c = dictDB.execute("SELECT id FROM entries WHERE title = ? AND id <> ?", (title, entryID))
    r = c.fetchone()
    feedback = {"type": "saveFeedbackHeadwordExists", "info": r["id"]} if r else None
    if entryID:
        sql = "INSERT INTO entries(id, nvh, title, sortkey, needs_refresh, json) VALUES (?, ?, ?, ?, ?, ?)"
        params = (entryID, entryNvh, title, sortkey, needs_refresh, entryJson)
    else:
        sql = "INSERT INTO entries(nvh, title, sortkey, needs_refresh, json) VALUES (?, ?, ?, ?, ?)"
        params = (entryNvh, title, sortkey, needs_refresh, entryJson)
    c = dictDB.execute(sql, params)
    entryID = c.lastrowid

    searchTitle = getEntryTitle(nvhParsed, configs["titling"], True)
    dictDB.execute("INSERT INTO searchables (entry_id, txt, level) VALUES (?, ?, ?)", (entryID, searchTitle, 1))

    rm_pos = re.match('(.*)-.*', searchTitle)
    if rm_pos:
        searchTitle_no_pos = rm_pos.group(1)
        dictDB.execute("INSERT INTO searchables(entry_id, txt, level) VALUES (?, ?, ?)", (entryID, searchTitle_no_pos, 1))

    dictDB.execute("INSERT INTO history (entry_id, action, [when], email, nvh, historiography) VALUES (?, ?, ?, ?, ?, ?)", (entryID, "create", str(datetime.datetime.utcnow()), email, entryNvh, json.dumps(historiography)))
    if configs["links"]:
        entryNvh = updateEntryLinkables(dictDB, entryID, nvhParsed, configs, False, False)

    c2 = dictDB.execute("SELECT json FROM configs WHERE id='entry_count'")
    r2 = c2.fetchone()
    dictDB.execute("UPDATE configs SET json=? WHERE id=?", (int(r2['json']) + 1, 'entry_count'))

    if '__lexonomy__completed' in entryNvh:
        c3 = dictDB.execute("SELECT json FROM configs WHERE id='completed_entries'")
        r3 = c3.fetchone()
        dictDB.execute("UPDATE configs SET json=? WHERE id=?", (int(r3['json']) + 1, 'completed_entries'))

    dictDB.commit()
    return entryID, entryNvh, feedback

def updateEntry(dictDB, configs, entryID, entryNvh, email, historiography):
    entryJson = nvh2jsonDump(entryNvh)
    c = dictDB.execute("SELECT id, nvh FROM entries WHERE id=?", (entryID, ))
    row = c.fetchone()
    if row["nvh"] == entryNvh:
        return entryID, entryNvh, False, None
    else:
        nvhParsed = nvh.parse_string(entryNvh)
        title = getEntryTitle(nvhParsed, configs["titling"]) # TODO move to front-end
        sortkey = getSortTitle(nvhParsed, configs["titling"])
        needs_refresh = 1 if configs["searchability"].get("searchableElements") and len(configs["searchability"].get("searchableElements")) > 0 else 0
        c2 = dictDB.execute("SELECT id FROM entries WHERE title = ? AND id <> ?", (title, entryID))
        r2 = c2.fetchone()
        feedback = {"type": "saveFeedbackHeadwordExists", "info": r2["id"]} if r2 else None
        dictDB.execute("UPDATE entries SET nvh=?, title=?, sortkey=?, needs_refresh=?, json=? WHERE id=?", (entryNvh, title, sortkey, needs_refresh, entryJson, entryID))
        dictDB.execute("UPDATE searchables SET txt=? WHERE entry_id=? AND level=1", (getEntryTitle(nvhParsed, configs["titling"], True), entryID))
        dictDB.execute("INSERT INTO history(entry_id, action, [when], email, nvh, historiography) values(?, ?, ?, ?, ?, ?)", (entryID, "update", str(datetime.datetime.utcnow()), email, entryNvh, json.dumps(historiography)))

        c3 = dictDB.execute("SELECT json FROM configs WHERE id='completed_entries'")
        r3 = c3.fetchone()
        if '__lexonomy__completed' not in row['nvh'] and '__lexonomy__completed' in entryNvh:
            dictDB.execute("UPDATE configs SET json=? WHERE id=?", (int(r3['json']) + 1, 'completed_entries'))
        elif '__lexonomy__completed' in row['nvh'] and '__lexonomy__completed' not in entryNvh:
            dictDB.execute("UPDATE configs SET json=? WHERE id=?", (int(r3['json']) - 1, 'completed_entries'))

        dictDB.commit()

        if configs["links"]:
            entryNvh = updateEntryLinkables(dictDB, entryID, nvhParsed, configs, True, True)
        return entryID, entryNvh, True, feedback

def getEntryTitle(nvhParsed, titling, plaintext=False):
    if titling.get("headwordAnnotationsType") == "advanced" and not plaintext:
        ret = titling["headwordAnnotationsAdvanced"]
        advancedUsed = False
        for el in re.findall(r"%\([^)]+\)", titling["headwordAnnotationsAdvanced"]):
            text = ""
            extract = extractText(nvhParsed, el[2:-1])
            if len(extract) > 0:
                text = extract[0]
                advancedUsed = True
            ret = ret.replace(el, text)
        if advancedUsed:
            return ret
    ret = getEntryHeadword(nvhParsed, titling.get("headword"))
    if not plaintext:
        ret = "<span class='headword'>" + ret + "</span>"
    if titling.get("headwordAnnotations"):
        for hw in titling.get("headwordAnnotations"):
            ret += " " if ret != "" else ""
            ret += " ".join(extractText(nvhParsed, hw))
    return ret

def getEntryTitleID(dictDB, configs, entry_id, plaintext=False):
    eid, nvh, json, title = readEntry(dictDB, configs, entry_id)
    return getEntryTitle(nvh2jsonDump(nvh), configs["titling"], plaintext)

def getEntryHeadword(nvhParsed, headword_elem):
    ret = "?"
    arr = extractText(nvhParsed, headword_elem)
    if len(arr)>0:
        ret = arr[0]
    else:
        ret = extractFirstText(nvhParsed)
    if len(ret) > 255:
        ret = ret[0:255]
    return ret

def getDoctype(nvhParsed):
    return nvhParsed.children[0].name

def getSortTitle(nvhParsed, titling):
    if titling.get("headwordSorting"):
        return getEntryHeadword(nvhParsed, titling.get("headwordSorting"))
    return getEntryHeadword(nvhParsed, titling.get("headword"))

def generateKey(size=32):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(size))

def generateDictId(size=8):
    return ''.join(random.choice("abcdefghijkmnpqrstuvwxy23456789") for _ in range(size))

def login(email, password):
    if siteconfig["readonly"]:
        return {"success": False}
    conn = getMainDB()
    passhash = hashlib.sha1(password.encode("utf-8")).hexdigest();
    c = conn.execute("select email, apiKey, ske_username, ske_apiKey, consent, is_manager from users where email=? and passwordHash=?", (email.lower(), passhash))
    user = c.fetchone()
    if not user:
        return {"success": False}
    key = generateKey()
    now = datetime.datetime.utcnow()
    conn.execute("update users set sessionKey=?, sessionLast=? where email=?", (key, now, email))
    conn.commit()
    return {"success": True, "email": user["email"], "key": key, "ske_username": user["ske_username"], "ske_apiKey": user["ske_apiKey"], "apiKey": user["apiKey"], "consent": user["consent"] == 1, "isAdmin": user["email"] in siteconfig["admins"], "isProjectManager": user["is_manager"]}

def httpAuthLogin(email):
    conn = getMainDB()
    c = conn.execute("select email, apiKey, ske_username, ske_apiKey, consent, is_manager from users where email=?", (email.lower(), ))
    user = c.fetchone()
    if not user:
        return {"success": False}
    key = generateKey()
    now = datetime.datetime.utcnow()
    conn.execute("update users set sessionKey=?, sessionLast=? where email=?", (key, now, email))
    conn.commit()
    return {"success": True, "email": user["email"], "key": key, "ske_username": user["ske_username"], "ske_apiKey": user["ske_apiKey"], "apiKey": user["apiKey"], "consent": user["consent"] == 1, "isAdmin": user["email"] in siteconfig["admins"], "isProjectManager": user["is_manager"]}

def logout(user):
    conn = getMainDB()
    conn.execute("update users set sessionKey='', sessionLast='' where email=?", (user["email"],))
    conn.commit()
    return True

def sendSignupToken(email, remoteip):
    if siteconfig["readonly"]:
        return False
    conn = getMainDB()
    c = conn.execute("select email from users where email=?", (email.lower(),))
    user = c.fetchone()
    if not user:
        token = secrets.token_hex()
        tokenurl = siteconfig["baseUrl"] + "#/createaccount/" + token
        expireDate = datetime.datetime.now() + datetime.timedelta(days=2)
        mailSubject = "Lexonomy signup"
        mailText = "Dear Lexonomy user,\n\n"
        mailText += "Somebody (hopefully you, from the address "+remoteip+") requested to create a new Lexonomy account. Please follow the link below to create your account:\n\n"
        mailText += tokenurl + "\n\n"
        mailText += "For security reasons this link is only valid for two days (until "+expireDate.isoformat()+"). If you did not request an account, you can safely ignore this message. \n\n"
        mailText += "Yours,\nThe Lexonomy team"
        conn.execute("insert into register_tokens (email, requestAddress, token, expiration) values (?, ?, ?, ?)", (email, remoteip, token, expireDate))
        conn.commit()
        return sendmail(email, mailSubject, mailText)
    else:
        return False

def sendToken(email, remoteip): # OK
    if siteconfig["readonly"]:
        return False
    conn = getMainDB()
    c = conn.execute("select email from users where email=?", (email.lower(),))
    user = c.fetchone()
    if user:
        token = secrets.token_hex()
        tokenurl = siteconfig["baseUrl"] + "#/recoverpwd/" + token
        expireDate = datetime.datetime.now() + datetime.timedelta(days=2)
        mailSubject = "Lexonomy password reset"
        mailText = "Dear Lexonomy user,\n\n"
        mailText += "Somebody (hopefully you, from the address "+remoteip+") requested a new password for the Lexonomy account "+email+". You can reset your password by clicking the link below:\n\n";
        mailText += tokenurl + "\n\n"
        mailText += "For security reasons this link is only valid for two days (until "+expireDate.isoformat()+"). If you did not request a password reset, you can safely ignore this message. \n\n"
        mailText += "Yours,\nThe Lexonomy team"
        conn.execute("insert into recovery_tokens (email, requestAddress, token, expiration) values (?, ?, ?, ?)", (email, remoteip, token, expireDate))
        conn.commit()
        return sendmail(email, mailSubject, mailText)
    else:
        return False

def verifyToken(token, tokenType):
    conn = getMainDB()
    c = conn.execute("select * from "+tokenType+"_tokens where token=? and expiration>=datetime('now') and usedDate is null", (token,))
    row = c.fetchone()
    if row:
        return True
    else:
        return False

def createAccount(token, password, remoteip):
    conn = getMainDB()
    c = conn.execute("select * from register_tokens where token=? and expiration>=datetime('now') and usedDate is null", (token,))
    row = c.fetchone()
    if row:
        c2 = conn.execute("select * from users where email=?", (row["email"],))
        row2 = c2.fetchone()
        if not row2:
            passhash = hashlib.sha1(password.encode("utf-8")).hexdigest();
            conn.execute("insert into users (email,passwordHash) values (?,?)", (row["email"], passhash))
            conn.execute("update register_tokens set usedDate=datetime('now'), usedAddress=? where token=?", (remoteip, token))
            conn.commit()
            # notify admins?
            if siteconfig.get('notifyRegister') == True:
                mailSubject = "Lexonomy, new user registered"
                mailText = "Hi,\n\n"
                mailText += "new user registered to Lexonomy at " + siteconfig["baseUrl"] + " :\n\n"
                mailText += "  " + row["email"]
                mailText += "\n\nYours,\nThe Lexonomy team"
                for adminMail in siteconfig["admins"]:
                    sendmail(adminMail, mailSubject, mailText)
            return True
        else:
            return False
    else:
        return False

def resetPwd(token, password, remoteip): # OK
    conn = getMainDB()
    c = conn.execute("select * from recovery_tokens where token=? and expiration>=datetime('now') and usedDate is null", (token,))
    row = c.fetchone()
    if row:
        passhash = hashlib.sha1(password.encode("utf-8")).hexdigest();
        conn.execute("update users set passwordHash=? where email=?", (passhash, row["email"]))
        conn.execute("update recovery_tokens set usedDate=datetime('now'), usedAddress=? where token=?", (remoteip, token))
        conn.commit()
        return True
    else:
        return False

def setConsent(email, consent):
    conn = getMainDB()
    conn.execute("update users set consent=? where email=?", (consent, email))
    conn.commit()
    return True

def changePwd(email, password):
    conn = getMainDB()
    passhash = hashlib.sha1(password.encode("utf-8")).hexdigest();
    conn.execute("update users set passwordHash=? where email=?", (passhash, email))
    conn.commit()
    return True

def changeSkeUserName(email, ske_userName):
    conn = getMainDB()
    conn.execute("update users set ske_username=? where email=?", (ske_userName, email))
    conn.commit()
    return True

def changeSkeApiKey(email, ske_apiKey):
    conn = getMainDB()
    conn.execute("update users set ske_apiKey=? where email=?", (ske_apiKey, email))
    conn.commit()
    return True

def updateUserApiKey(user, apiKey):
    conn = getMainDB()
    conn.execute("update users set apiKey=? where email=?", (apiKey, user["email"]))
    conn.commit()
    sendApiKeyToSke(user, apiKey)
    return True

def sendApiKeyToSke(user, apiKey):
    if user["ske_username"] and user["ske_apiKey"]:
        data = json.dumps({"options": {"settings_lexonomyApiKey": apiKey, "settings_lexonomyEmail": user["email"].lower()}})
        queryData = urllib.parse.urlencode({ "username": user["ske_username"], "api_key": user["ske_apiKey"], "json": data })
        url = "https://api.sketchengine.eu/bonito/run.cgi/set_user_options?" + queryData
        res = urllib.request.urlopen(url)
    return True

def prepareApiKeyForSke(email):
    conn = getMainDB()
    c = conn.execute("select * from users where email=?", (email,))
    row = c.fetchone()
    if row:
        if row["apiKey"] == None or row["apiKey"] == "":
            lexapi = generateKey()
            conn.execute("update users set apiKey=? where email=?", (lexapi, email))
            conn.commit()
        else:
            lexapi = row["apiKey"]
        sendApiKeyToSke(row, lexapi)
    return True


def processJWT(user, jwtdata):
    conn = getMainDB()
    c = conn.execute("select * from users where ske_id=?", (jwtdata["user"]["id"],))
    row = c.fetchone()
    key = generateKey()
    now = datetime.datetime.utcnow()
    if row:
        #if SkE ID in database = log in user
        conn.execute("update users set sessionKey=?, sessionLast=? where email=?", (key, now, row["email"]))
        conn.commit()
        prepareApiKeyForSke(row["email"])
        return {"success": True, "email": row["email"], "key": key}
    else:
        if user["loggedin"]:
            #user logged in = save SkE ID in database
            conn.execute("update users set ske_id=?, ske_username=?, ske_apiKey=?, sessionKey=?, sessionLast=? where email=?", (jwtdata["user"]["id"], jwtdata["user"]["username"], jwtdata["user"]["api_key"], key, now, user["email"]))
            conn.commit()
            prepareApiKeyForSke(user["email"])
            return {"success": True, "email": user["email"], "key": key}
        else:
            #user not logged in = register and log in
            email = jwtdata["user"]["email"].lower()
            c2 = conn.execute("select * from users where email=?", (email,))
            row2 = c2.fetchone()
            if not row2:
                lexapi = generateKey()
                conn.execute("insert into users (email, passwordHash, ske_id, ske_username, ske_apiKey, sessionKey, sessionLast, apiKey) values (?, null, ?, ?, ?, ?, ?, ?)", (email, jwtdata["user"]["id"], jwtdata["user"]["username"], jwtdata["user"]["api_key"], key, now, lexapi))
                conn.commit()
                prepareApiKeyForSke(email)
                return {"success": True, "email": email, "key": key}
            else:
                return {"success": False, "error": "user with email " + email + " already exists. Log-in and connect account to SkE."}


def dictExists(dictID):
    has_sql = os.path.isfile(os.path.join(siteconfig["dataDir"], "dicts/" + dictID + ".sqlite"))

    conn = getMainDB()
    c = conn.execute("SELECT id FROM dicts WHERE id=?", (dictID,))

    return has_sql or c.fetchone()

def suggestDictId():
    dictid = generateDictId()
    while dictid in prohibitedDictIDs or dictExists(dictid):
        dictid = generateDictId()
    return dictid

# def get_schema_elements(nvh_node, elements):
#     elements[nvh_node.name] = {
#         "type": "string",
#         "min": 0,
#         "max": 0,
#         "values": [],
#         "re": "",
#         "children": [child.name for child in nvh_node.children]
#     }
#     for child in nvh_node.children:
#         get_schema_elements(child, elements)

def checkDictExists(dictID):
    if dictID in prohibitedDictIDs or dictExists(dictID):
        return True
    return False

def initDict(dictID, title, lang, blurb, email, dmlex=False):
    if dmlex:
        with open(currdir + "/dictTemplates/dmlex.sqlite.schema", 'r') as f:
            sql_schema = f.read()
    else:
        with open(currdir + "/dictTemplates/general.sqlite.schema", 'r') as f:
            sql_schema = f.read()

    conn = sqlite3.connect("file:" + os.path.join(siteconfig["dataDir"], "dicts/" + dictID) + ".sqlite?modeof=" + os.path.join(siteconfig["dataDir"], "dicts/"), uri=True)
    conn.executescript(sql_schema)
    conn.commit()

    #update dictionary info
    dictDB = getDB(dictID)
    dictDB.execute("INSERT INTO configs (id, json) VALUES (?, ?)", ("metadata", json.dumps({"version": version, "creator": email})))

    ident = {"title": title, "blurb": blurb, "lang": lang}
    dictDB.execute("UPDATE configs SET json=? WHERE id=?", (json.dumps(ident), "ident"))

    dictDB.commit()

    return dictDB


def makeDict(dictID, structure_json, title, lang, blurb, email, dmlex=False, addExamples=False, deduplicate=False,
             bottle_files={}, hwNode=None, titling_node=None):
    if title == "":
        title = "?"
    if blurb == "":
        blurb = "Yet another Lexonomy dictionary."
    if dictID in prohibitedDictIDs:
        return {'url': dictID, 'success': False, 'error': "The entered name of the dictionary is prohibited"}
    if dictExists(dictID):
        return {'url': dictID, 'success': False, 'error': "The dict with the entered name already exists"}
    #init db schema
    dictDB = initDict(dictID, title, lang, blurb, email, dmlex)

    if not bottle_files:
        if structure_json.get('nvhSchema', False):
            # DICTIONARY STRUCTURE
            if not structure_json.get('root', False):
                structure_json['root'] = nvh.schema_get_root_name(structure_json['nvhSchema'])
            structure = structure_json
        else:
            raise Exception('No schema provided')

        dictDB.execute("INSERT INTO configs (id, json) VALUES (?, ?)", ("structure", json.dumps(structure)))

        schema_keys = nvh.schema_keys(structure_json['nvhSchema'])
        # DICTIONARY FORMATTING
        formatting = {}
        with open(currdir + "/dictTemplates/styles.json", 'r') as f:
            styles = json.loads(f.read())
            for key in schema_keys:
                if styles.get(key):
                    formatting[key] = styles[key]
                else:
                    formatting[key] = styles['__other__']
        dictDB.execute("INSERT INTO configs (id, json) VALUES (?, ?)", ("formatting", json.dumps(formatting)))

        # ADD EXAMPLES
        if dmlex and addExamples:
            with open("dictTemplates/dmlex.entry.example.nvh", 'r') as f:
                examples = filter_nodes(nvh2json(f.read()), schema_keys)
            for idx, example in enumerate(examples):
                dictDB.execute("INSERT INTO entries VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (idx + 1, example["nvh"], json.dumps(example['json']), example["title"], example["sortkey"], 0, 0, 0))
                dictDB.execute("INSERT INTO searchables (entry_id, txt, level) VALUES(?, ?, ?)", (idx + 1, example["sortkey"], 1))

            dictDB.execute("UPDATE configs SET json=? WHERE id=?", (len(examples), 'entry_count'))

    dictDB.commit()

    users = {email: {"canEdit": 1, "canConfig": 1, "canDownload": 1, "canUpload": 1, "canView": 1}}
    dict_config = {"limits": {"entries": DEFAULT_ENTRY_LIMIT}}
    attachDict(dictDB, dictID, users, dict_config)

    if bottle_files:
        err, import_message, upload_file_path = importfile(dictID, email, hwNode, deduplicate=deduplicate,
                                                           bottle_files=bottle_files, titling_node=titling_node)
        return {'url': dictID, 'success': True if not err else False, 'upload_error': err,
                'upload_file_path': upload_file_path, 'upload_message': import_message, 'error': ''}

    return {'url': dictID, 'success': True, 'error': ''}


def recur_filter(node, structure_nodes):
    for item in node:
        for key in list(item.keys()):
            if not key.startswith('_'):
                if item.get(key, False) and key not in structure_nodes:
                    del item[key]
                elif item.get(key, False):
                    recur_filter(item[key], structure_nodes)


def filter_nodes(examples_json, structure_nodes):
    result = []
    for entry in examples_json['entry']:
        for key in list(entry.keys()):
            if not key.startswith('_'):
                if entry.get(key, False) and key not in structure_nodes:
                    del entry[key]
                elif entry.get(key, False):
                    recur_filter(entry[key], structure_nodes)
        result.append({'json': {'entry': [entry], '_value': ''},
                       'nvh': json2nvh_str({'entry': [entry], '_value': ''}, paths=True),
                       "title": '<span class="headword">' + entry["_value"] + '</span>',
                       'sortkey': entry["_value"]})
    return result


def attachDict(dictDB, dictID, users, dict_config):
    configs = readDictConfigs(dictDB)

    conn = getMainDB()
    conn.execute("delete from dicts where id=?", (dictID,))
    conn.execute("delete from user_dict where dict_id=?", (dictID,))

    lang = ''
    title = configs["ident"]["title"]

    if configs["ident"].get("lang"):
        lang = configs["ident"]["lang"]
    conn.execute("insert into dicts (id, title, language, creator, configs) values (?, ?, ?, ?, ?)", (dictID, title, lang, configs["metadata"]["creator"], json.dumps(dict_config)))

    for email, access_rights in users.items():
        conn.execute("insert into user_dict (dict_id, user_email, can_view, can_edit, can_config, can_download, can_upload) values (?,?,?,?,?,?,?)",
                     (dictID, email.lower(), access_rights.get('canView', False), access_rights.get('canEdit', False), access_rights.get('canConfig', False),
                      access_rights.get('canDownload', False), access_rights.get('canUpload', False)))
    conn.commit()

def listDictUsers(dictID):
    users = {}
    conn = getMainDB()
    c = conn.execute("SELECT * FROM user_dict where dict_id=?", (dictID,))
    for r in c.fetchall():
        users[r['user_email']] = {"canEdit": bool(r['can_edit']), "canConfig": bool(r['can_config']),
                                  "canDownload": bool(r['can_download']), "canUpload": bool(r['can_upload']),
                                  "canView": bool(r['can_view'])}
    return users

def updateDictIdent(dictDB, dictID):
    configs = readDictConfigs(dictDB)

    conn = getMainDB()
    lang = configs["ident"].get("lang", '')
    title = configs["ident"].get("title", '')
    # blurb = data.get('blurb', configs["ident"].get("blurb", ''))

    conn.execute("UPDATE dicts SET title=?, language=? WHERE id=?", (title, lang, dictID))
    conn.commit()

    # dictDB.execute("UPDATE configs SET json=? WHERE id=ident", (json.dumps({"title": title, "blurb": blurb, "lang": lang})))
    # dictDB.commit()

def cloneDict(dictID, email):
    newID = suggestDictId()
    shutil.copy(os.path.join(siteconfig["dataDir"], "dicts/" + dictID + ".sqlite"), os.path.join(siteconfig["dataDir"], "dicts/" + newID + ".sqlite"))
    newDB = getDB(newID)
    cc = newDB.execute("select count(*) as total from entries")
    size = cc.fetchone()["total"]

    # Update tables for old dictionaries
    c = newDB.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='linkables'")
    if not c.fetchone():
        newDB.execute("CREATE TABLE linkables (id INTEGER PRIMARY KEY AUTOINCREMENT, entry_id INTEGER REFERENCES entries (id) ON DELETE CASCADE, txt TEXT, element TEXT, preview TEXT)")
        newDB.execute("CREATE INDEX link ON linkables (txt)")

    res = newDB.execute("select json from configs where id='ident'")
    row = res.fetchone()
    ident = {"title": "?", "blurb": "?"}
    if row:
        ident = json.loads(row["json"])
        ident["title"] = "Clone of " + ident["title"]
    newDB.execute("update configs set json=? where id='ident'", (json.dumps(ident),))
    newDB.commit()

    users = {email: {"canEdit": 1, "canConfig": 1, "canDownload": 1, "canUpload": 1, "canView": 1}}
    dict_config = {"limits": {"entries": DEFAULT_ENTRY_LIMIT if size < DEFAULT_ENTRY_LIMIT else size}}
    attachDict(newDB, newID,users, dict_config)

    return {"success": True, "dictID": newID, "title": ident["title"]}

def destroyDict(dictID):
    conn = getMainDB()
    conn.execute("delete from dicts where id=?", (dictID,))
    conn.execute("delete from user_dict where dict_id=?", (dictID,))
    conn.commit()
    os.remove(os.path.join(siteconfig["dataDir"], "dicts/" + dictID + ".sqlite"))
    if os.path.exists(os.path.join(siteconfig["dataDir"], "dicts/" + dictID + ".sqlite-wal")):
        os.remove(os.path.join(siteconfig["dataDir"], "dicts/" + dictID + ".sqlite-wal"))
    if os.path.exists(os.path.join(siteconfig["dataDir"], "dicts/" + dictID + ".sqlite-shm")):
        os.remove(os.path.join(siteconfig["dataDir"], "dicts/" + dictID + ".sqlite-shm"))
    return True

def moveDict(oldID, newID):
    if newID in prohibitedDictIDs or dictExists(newID):
        return False
    shutil.move(os.path.join(siteconfig["dataDir"], "dicts/" + oldID + ".sqlite"), os.path.join(siteconfig["dataDir"], "dicts/" + newID + ".sqlite"))
    if os.path.exists(os.path.join(siteconfig["dataDir"], "dicts/" + oldID + ".sqlite-wal")):
        os.remove(os.path.join(siteconfig["dataDir"], "dicts/" + oldID + ".sqlite-wal"))
    if os.path.exists(os.path.join(siteconfig["dataDir"], "dicts/" + oldID + ".sqlite-shm")):
        os.remove(os.path.join(siteconfig["dataDir"], "dicts/" + oldID + ".sqlite-shm"))

    conn = getMainDB()
    c = conn.execute("SELECT configs FROM dicts WHERE id=?", (oldID,))
    dict_config = json.loads(c.fetchone()['configs'])

    conn.execute("DELETE FROM dicts WHERE id=?", (oldID,))
    c2 = conn.execute("SELECT user_email, can_view, can_edit, can_config, can_download, can_upload FROM user_dict WHERE dict_id=?", (oldID,))

    users = {}
    for r in c2.fetchall():
        users[r['user_email']] = {"canEdit": r['can_edit'], "canConfig": r['can_config'], "canDownload": r['can_download'], "canUpload": r['can_upload'], "canView": r['can_view']}

    conn.execute("DELETE FROM user_dict WHERE dict_id=?", (oldID,))
    conn.commit()

    dictDB = getDB(newID)
    attachDict(dictDB, newID, users, dict_config)

    return True

def getDoc(docID):
    if os.path.isfile("docs/"+docID+".md"):
        doc = {"id": docID, "title":"", "html": ""}
        html = markdown.markdown(open("docs/"+docID+".md").read())
        title = re.search('<h1>([^<]*)</h1>', html)
        if title:
            doc["title"] = re.sub('<\/?h1>','', title.group(0))
        doc["html"] = html
        return doc
    else:
        return False

def getDictsByUser(email):
    dicts = []
    email = str(email).lower()
    conn = getMainDB()
    favs = []
    c = conn.execute("SELECT * FROM dict_fav WHERE user_email=?", (email,))
    for r in c.fetchall():
        favs.append(r['dict_id'])
    c = conn.execute("SELECT DISTINCT d.id, d.title FROM dicts AS d INNER JOIN user_dict AS ud ON ud.dict_id=d.id WHERE ud.user_email=? OR d.id IN (SELECT dict_id FROM dict_fav WHERE user_email=?) ORDER BY d.title", (email, email))
    for r in c.fetchall():
        info = {"id": r["id"], "title": r["title"], "hasLinks": False, "lang": "", "favorite": False, "owners": []}
        try:
            dictDB = getDB(r["id"])
            cc = dictDB.execute("select count(*) as total from entries")
            info["size"] = cc.fetchone()["total"]
            configs = readDictConfigs(dictDB)
            if configs["users"][email] and configs["users"][email]["canEdit"]:
                info["currentUserCanEdit"] = True
            if configs["users"][email] and configs["users"][email]["canConfig"]:
                info["currentUserCanDelete"] = True
            if configs["links"] and len(configs["links"])>0:
                info["hasLinks"] = True
            if configs["ident"] and configs["ident"]["lang"]:
                info["lang"] = configs["ident"]["lang"]
            if r["id"] in favs:
                info["favorite"] = True
            for user_email in configs["users"]:
                if configs["users"][user_email]["canEdit"] and configs["users"][user_email]["canConfig"]:
                    info["owners"].append(user_email)
        except:
            info["broken"] = True
        dicts.append(info)
    return dicts

def getPublicDicts():
    conn = getMainDB()
    c = conn.execute("select * from dicts order by title")
    dicts = []
    for r in c.fetchall():
        try:
            dictDB = getDB(r["id"])
            configs = readDictConfigs(dictDB)
        except:
            continue
        if configs["publico"]["public"]:
            cc = dictDB.execute("select count(*) as total from entries")
            size = cc.fetchone()["total"]
            configs = loadHandleMeta(configs)
            dictinfo = {"id": r["id"], "title": r["title"], "author": "", "lang": configs["ident"].get("lang"), "licence": configs["publico"]["licence"], "size": size}
            if len(list(configs["users"].keys())) > 0:
                dictinfo["author"] = re.sub(r"@.*","@...", list(configs["users"].keys())[0])
            if configs["metadata"].get("dc.title"):
                dictinfo["title"] = configs["metadata"]["dc.title"]
            if configs["metadata"].get("dc.language.iso") and len(configs["metadata"]["dc.language.iso"]) > 0:
                langs = [t['lang'] for t in get_iso639_1() if t['code3'] == configs["metadata"]["dc.language.iso"][0]]
                dictinfo["lang"] = langs[0] or dictinfo["lang"]
            if configs["metadata"].get("dc.rights") and configs["metadata"].get("dc.rights") != "":
                dictinfo["licence"] = configs["metadata"].get("dc.rights")
            if configs["metadata"].get("dc.contributor.author") and len(configs["metadata"].get("dc.contributor.author")) > 0:
                dictinfo["author"] = '; '.join(configs["metadata"].get("dc.contributor.author"))
            dicts.append(dictinfo)
    return dicts

def getLangList():
    langs = []
    codes = get_iso639_1()
    conn = getMainDB()
    c = conn.execute("SELECT DISTINCT language FROM dicts WHERE language!='' ORDER BY language")
    for r in c.fetchall():
        lang = next((item for item in codes if item["code"] == r["language"]), {})
        langs.append({"code": r["language"], "language": lang.get("lang")})
    return langs

def getDictList(lang, withLinks, loadHandle=False):
    dicts = []
    conn = getMainDB()
    if lang:
        c = conn.execute("SELECT * FROM dicts WHERE language=? ORDER BY title", (lang, ))
    else:
        c = conn.execute("SELECT * FROM dicts ORDER BY title")
    for r in c.fetchall():
        info = {"id": r["id"], "title": r["title"], "language": r["language"], "hasLinks": False}
        try:
            configs = readDictConfigs(getDB(r["id"]))
            if configs["links"] and len(configs["links"])>0:
                info["hasLinks"] = True
            if loadHandle:
                configs = loadHandleMeta(configs)
                if configs["metadata"].get("dc.title"):
                    info["title"] = configs["metadata"]["dc.title"]
        except:
            info["broken"] = True
        if not withLinks or (withLinks == True and info["hasLinks"] == True):
            dicts.append(info)
    return dicts

def getLinkList(headword, sourceLang, sourceDict, targetLang):
    links = []
    linkDB = getLinkDB()
    if sourceDict and sourceDict != "":
        dicts = [{"id": sourceDict}]
    else:
        dicts = getDictList(sourceLang, True)

    for d in dicts:
        dictDB = getDB(d["id"])
        if dictDB:
            query = "SELECT DISTINCT l.entry_id AS entry_id, l.txt AS link_id, l.element AS link_el, s.txt AS hw FROM searchables AS s, linkables AS l  WHERE s.entry_id=l.entry_id AND s.txt LIKE ? AND s.level=1"
            c = dictDB.execute(query, (headword+"%", ))
            for entry in c.fetchall():
                info0 = {"sourceDict": d["id"], "sourceHeadword": entry["hw"]}
                if entry["entry_id"] and entry["entry_id"] != "":
                    info0["sourceID"] = entry["entry_id"]
                if entry["link_el"] == "sense" and "_" in entry["link_id"]:
                    lia = entry["link_id"].split("_")
                    info0["sourceSense"] = lia[1]
                    if not info0["sourceID"]:
                        info0["sourceID"] = lia[0]
                info0["sourceURL"] = siteconfig["baseUrl"] + info0["sourceDict"] + "/" + str(info0["sourceID"])
                # first, find links with searched dict as source
                if targetLang:
                    targetDicts = []
                    for td in getDictList(targetLang, True):
                        targetDicts.append(td["id"])
                    query2 = "SELECT * FROM links WHERE source_dict=? AND source_id=? AND target_dict IN "+"('"+"','".join(targetDicts)+"')"
                else:
                    query2 = "SELECT * FROM links WHERE source_dict=? AND source_id=?"
                data2 = (d["id"], entry["link_id"])
                c2 = linkDB.execute(query2, data2)
                for r2 in c2.fetchall():
                    info = info0.copy()
                    info["targetDict"] = r2["target_dict"]
                    info["confidence"] = r2["confidence"]
                    targetDB = getDB(r2["target_dict"])
                    if targetDB:
                        info["targetLang"] = readDictConfigs(targetDB)['ident']['lang']
                        info["targetDictConcept"] = False
                        if r2["target_element"] == "sense" and "_" in r2["target_id"]:
                            lia = r2["target_id"].split("_")
                            info["targetSense"] = lia[1]
                        query3 = "SELECT DISTINCT l.entry_id AS entry_id, l.txt AS link_id, l.element AS link_el, s.txt AS hw FROM searchables AS s, linkables AS l  WHERE s.entry_id=l.entry_id AND l.txt=? AND s.level=1"
                        c3 = targetDB.execute(query3, (r2["target_id"],))
                        for r3 in c3.fetchall():
                            info["targetHeadword"] = r3["hw"]
                            info["targetID"] = r3["entry_id"]
                            info["targetURL"] = siteconfig["baseUrl"] + info["targetDict"] + "/" + str(info["targetID"])
                            links.append(info)
                    else:
                        info["targetHeadword"] = r2["target_id"]
                        info["targetID"] = r2["target_id"]
                        info["targetDictConcept"] = True
                        info["targetURL"] = ""
                        info["targetSense"] = ""
                        info["targetLang"] = ""
                        links.append(info)
                # second, find links with search dict as target
                if targetLang:
                    query2 = "SELECT * FROM links WHERE target_dict=? AND target_id=? AND source_dict IN "+"('"+"','".join(targetDicts)+"')"
                else:
                    query2 = "SELECT * FROM links WHERE target_dict=? AND target_id=?"
                data2 = (d["id"], entry["link_id"])
                c2 = linkDB.execute(query2, data2)
                for r2 in c2.fetchall():
                    info = info0.copy()
                    info["targetDict"] = r2["source_dict"]
                    info["confidence"] = r2["confidence"]
                    sourceDB = getDB(r2["source_dict"])
                    if sourceDB:
                        info["targetLang"] = readDictConfigs(sourceDB)['ident']['lang']
                        info["targetDictConcept"] = False
                        if r2["source_element"] == "sense" and "_" in r2["source_id"]:
                            lia = r2["source_id"].split("_")
                            info["targetSense"] = lia[1]
                        query3 = "SELECT DISTINCT l.entry_id AS entry_id, l.txt AS link_id, l.element AS link_el, s.txt AS hw FROM searchables AS s, linkables AS l  WHERE s.entry_id=l.entry_id AND l.txt=? AND s.level=1"
                        c3 = sourceDB.execute(query3, (r2["source_id"],))
                        for r3 in c3.fetchall():
                            info["targetHeadword"] = r3["hw"]
                            info["targetID"] = r3["entry_id"]
                            info["targetURL"] = siteconfig["baseUrl"] + info["targetDict"] + "/" + str(info["targetID"])
                            links.append(info)
                    else:
                        info["targetHeadword"] = r2["source_id"]
                        info["targetID"] = r2["source_id"]
                        info["targetDictConcept"] = True
                        info["targetURL"] = ""
                        info["targetSense"] = ""
                        info["targetLang"] = ""
                        links.append(info)
        else:
            # source dictionary is "concept", use headword as target_id
            info0 = {"sourceDict": d["id"], "sourceHeadword": headword, "sourceID": headword, "sourceDictConcept": True, "sourceURL": "", "sourceSense": ""}
            # first, find links with searched dict as source
            if targetLang:
                targetDicts = []
                for td in getDictList(targetLang, True):
                    targetDicts.append(td["id"])
                query2 = "SELECT * FROM links WHERE source_dict=? AND source_id=? AND target_dict IN "+"('"+"','".join(targetDicts)+"')"
            else:
                query2 = "SELECT * FROM links WHERE source_dict=? AND source_id=?"
            data2 = (d["id"], headword)
            c2 = linkDB.execute(query2, data2)
            for r2 in c2.fetchall():
                info = info0.copy()
                info["targetDict"] = r2["target_dict"]
                info["confidence"] = r2["confidence"]
                targetDB = getDB(r2["target_dict"])
                if targetDB:
                    info["targetLang"] = readDictConfigs(targetDB)['ident']['lang']
                    info["targetDictConcept"] = False
                    if r2["target_element"] == "sense" and "_" in r2["target_id"]:
                        lia = r2["target_id"].split("_")
                        info["targetSense"] = lia[1]
                    query3 = "SELECT DISTINCT l.entry_id AS entry_id, l.txt AS link_id, l.element AS link_el, s.txt AS hw FROM searchables AS s, linkables AS l  WHERE s.entry_id=l.entry_id AND l.txt=? AND s.level=1"
                    c3 = targetDB.execute(query3, (r2["target_id"],))
                    for r3 in c3.fetchall():
                        info["targetHeadword"] = r3["hw"]
                        info["targetID"] = r3["entry_id"]
                        info["targetURL"] = siteconfig["baseUrl"] + info["targetDict"] + "/" + str(info["targetID"])
                        links.append(info)
                else:
                    info["targetHeadword"] = r2["target_id"]
                    info["targetID"] = r2["target_id"]
                    info["targetDictConcept"] = True
                    info["targetURL"] = ""
                    info["targetSense"] = ""
                    info["targetLang"] = ""
                    links.append(info)
            # second, find links with search dict as target
            if targetLang:
                query2 = "SELECT * FROM links WHERE target_dict=? AND target_id=? AND source_dict IN "+"('"+"','".join(targetDicts)+"')"
            else:
                query2 = "SELECT * FROM links WHERE target_dict=? AND target_id=?"
            data2 = (d["id"], headword)
            c2 = linkDB.execute(query2, data2)
            for r2 in c2.fetchall():
                info = info0.copy()
                info["targetDict"] = r2["source_dict"]
                info["confidence"] = r2["confidence"]
                sourceDB = getDB(r2["source_dict"])
                if sourceDB:
                    info["targetLang"] = readDictConfigs(sourceDB)['ident']['lang']
                    info["targetDictConcept"] = False
                    if r2["source_element"] == "sense" and "_" in r2["source_id"]:
                        lia = r2["source_id"].split("_")
                        info["targetSense"] = lia[1]
                    query3 = "SELECT DISTINCT l.entry_id AS entry_id, l.txt AS link_id, l.element AS link_el, s.txt AS hw FROM searchables AS s, linkables AS l  WHERE s.entry_id=l.entry_id AND l.txt=? AND s.level=1"
                    c3 = sourceDB.execute(query3, (r2["source_id"],))
                    for r3 in c3.fetchall():
                        info["targetHeadword"] = r3["hw"]
                        info["targetID"] = r3["entry_id"]
                        info["targetURL"] = siteconfig["baseUrl"] + info["targetDict"] + "/" + str(info["targetID"])
                        links.append(info)
                else:
                    info["targetHeadword"] = r2["source_id"]
                    info["targetID"] = r2["source_id"]
                    info["targetDictConcept"] = True
                    info["targetURL"] = ""
                    info["targetSense"] = ""
                    info["targetLang"] = ""
                    links.append(info)

    # add dictionary titles
    dictUsed = {}
    for link in links:
        dictTitle = link["sourceDict"]
        if link["sourceDict"] in dictUsed:
            dictTitle = dictUsed[link["sourceDict"]]
        else:
            dictDB = getDB(link["sourceDict"])
            if dictDB:
                dictConf = readDictConfigs(dictDB)
                dictConf = loadHandleMeta(dictConf)
                if dictConf["metadata"].get("dc.title"):
                    dictTitle = dictConf["metadata"]["dc.title"]
                else:
                    dictTitle = dictConf["ident"]["title"]
                dictUsed[link["sourceDict"]] = dictTitle
        link["sourceDictTitle"] = dictTitle
        dictTitle = link["targetDict"]
        if link["targetDict"] in dictUsed:
            dictTitle = dictUsed[link["targetDict"]]
        else:
            dictDB = getDB(link["targetDict"])
            if dictDB:
                dictConf = readDictConfigs(dictDB)
                dictConf = loadHandleMeta(dictConf)
                if dictConf["metadata"].get("dc.title"):
                    dictTitle = dictConf["metadata"]["dc.title"]
                else:
                    dictTitle = dictConf["ident"]["title"]
                dictUsed[link["targetDict"]] = dictTitle
        link["targetDictTitle"] = dictTitle

    return links

def listUsers(searchtext, howmany):
    conn = getMainDB()
    users = []
    if searchtext and searchtext != "":
        c = conn.execute("select * from users where email like ? order by email limit ?", ("%"+searchtext+"%", howmany))
        for r in c.fetchall():
            users.append({"email": r["email"], "dictionaries": []})
        c = conn.execute("select count(*) as total from users where email like ?", ("%"+searchtext+"%", ))
        r = c.fetchone()
        total = r["total"]
    else:
        c = conn.execute("select * from users order by email")
        for r in c.fetchall():
            users.append({"email": r["email"], "dictionaries": []})
        total = len(users)
    for user in users:
        c = conn.execute("SELECT * FROM user_dict, dicts WHERE user_dict.dict_id=dicts.id AND user_email=? ORDER BY dicts.id", (user["email"],))
        for r in c.fetchall():
            user["dictionaries"].append({"id": r["dict_id"], "title": r["title"]})
    return {"entries":users, "total": total}

def createUser(email, user, manager=0):
    # TODO add manager and anotattor values to table and expand form in frontend
    import secrets
    passwd = secrets.token_urlsafe(8)
    passhash = hashlib.sha1(passwd.encode('utf-8')).hexdigest();
    conn = getMainDB()
    conn.execute("INSERT INTO users(email, passwordHash, created_by, is_manager) VALUES (?, ?, ?, ?)", (email.lower(), passhash, user['email'], manager))
    conn.commit()
    mailSubject = "New Lexonomy account"
    mailText = "Dear Lexonomy user,\n\n"
    mailText += "Welcome to the Lexonomy family. The user "+user['email']+" created a new Lexonomy account for you.\n"
    mailText += "Your new credentials:\n";
    mailText += "user: "+email+"\n";
    mailText += "password: "+passwd+"\n";
    mailText += "Please visit the " + siteconfig["baseUrl"] + " and change the generated password in your account settings.\n\n"
    mailText += "Yours,\nThe Lexonomy team"
    sendmail(email, mailSubject, mailText)

    return {"entryID": email}

def updateUser(email, pasword=''):
    if pasword:
        passhash = hashlib.sha1(pasword.encode("utf-8")).hexdigest();
        conn = getMainDB()
        conn.execute("update users set passwordHash=? where email=?", (passhash, email.lower()))
        conn.commit()
    return readUser(email)

def deleteUser(email):
    conn = getMainDB()
    conn.execute("DELETE FROM users WHERE email=?", (email.lower(),))
    c = conn.execute("SELECT * FROM user_dict WHERE user_email=?", (email.lower(),))
    for r in c.fetchall():
        dictDB = getDB(r["dict_id"])
        c2 = dictDB.execute("SELECT * FROM configs WHERE id='users'")
        for r2 in c2.fetchall():
            users = json.loads(r2["json"])
            del users[email.lower()]
            dictDB.execute("UPDATE configs SET json=? WHERE id=?", (json.dumps(users), 'users'))
            dictDB.commit()
    conn.execute("DELETE FROM user_dict WHERE user_email=?", (email.lower(),))
    conn.commit()
    return True

def readUser(email): # TODO load info about each dictionary, such as language, number of entries
    conn = getMainDB()
    c = conn.execute("select * from users where email=?", (email.lower(), ))
    r = c.fetchone()
    user_info = {}
    if r:
        if r["sessionLast"]:
            user_info['sessionLast'] = r["sessionLast"]

        c2 = conn.execute("select d.id, d.title from user_dict as ud inner join dicts as d on d.id=ud.dict_id  where ud.user_email=? order by d.title", (r["email"], ))
        user_info['dicts'] = []
        for r2 in c2.fetchall():
            user_info['dicts'].append((r2['id'], clean4xml(r2["title"])))
        return {"email": r["email"], "info": json.dumps(user_info)}
    else:
        return {"email":"", "info":""}


def listDicts(searchtext, howmany):
    conn = getMainDB()
    dicts = []
    if searchtext and searchtext != "":
        c = conn.execute("select * from dicts where id like ? or title like ? order by id limit ?", ("%"+searchtext+"%", "%"+searchtext+"%", howmany))
        for r in c.fetchall():
            dicts.append({"id": r["id"], "title": r["title"], "language": str(r["language"] or ""), "creator": str(r["creator"] or "")})
        c = conn.execute("select count(*) as total from dicts where id like ? or title like ?", ("%"+searchtext+"%", "%"+searchtext+"%"))
        r = c.fetchone()
        total = r["total"]
    else:
        c = conn.execute("select * from dicts order by id")
        for r in c.fetchall():
            dicts.append({"id": r["id"], "title": r["title"], "language": str(r["language"] or ""), "creator": str(r["creator"] or "")})
        total = len(dicts)
    return {"entries": dicts, "total": total}

def readDict(dictId):
    conn = getMainDB()
    c = conn.execute("select * from dicts where id=?", (dictId, ))
    r = c.fetchone()
    dict_info = {}
    if r:
        dict_info['id'] = clean4xml(r["id"])
        dict_info['title'] = clean4xml(r["title"])

        c2 = conn.execute("select u.email from user_dict as ud inner join users as u on u.email=ud.user_email where ud.dict_id=? order by u.email", (r["id"], ))
        dict_info['users'] = []
        for r2 in c2.fetchall():
            dict_info['users'].append(r2["email"])
        return {"id": r["id"], "dict_info": dict_info}
    else:
        return {"id":"", "dict_info":""}

def clean4xml(text):
    return text.replace("&", "&amp;").replace('"', "&quot;").replace("'", "&apos;").replace("<", "&lt;").replace(">", "&gt;");

def markdown_text(text):
    return markdown.markdown(text).replace("<a href=\"http", "<a target=\"_blank\" href=\"http")

# def cleanHousekeeping(xml):
#     xml = re.sub(r"^(<[^>\/]*)\s+xmlns:lxnm=['\"]http:\/\/www\.lexonomy\.eu\/[\"']", r"\1", xml)
#     xml = re.sub(r"^(<[^>\/]*)\s+lxnm:entryID=['\"][^\"\']*[\"']", r"\1", xml)
#     xml = re.sub(r"^(<[^>\/]*)\s+lxnm:subentryID=['\"][^\"\']*[\"']", r"\1", xml)
#     xml = re.sub(r"^(<[^>\/]*)\s+lxnm:linkable=['\"][^\"\']*[\"']", r"\1", xml)
#     return xml

# def exportEntryXml(dictDB, dictID, entryID, configs, baseUrl):
#     c = dictDB.execute("select * from entries where id=?", (entryID,))
#     row = c.fetchone()
#     if row:
#         xml = setHousekeepingAttributes(entryID, row["xml"], configs["subbing"])
#         attribs = " this=\"" + baseUrl + dictID + "/" + str(row["id"]) + ".xml\""
#         c2 = dictDB.execute("select e1.id, e1.title from entries as e1 where e1.sortkey<(select sortkey from entries where id=?) order by e1.sortkey desc limit 1", (entryID, ))
#         r2 = c2.fetchone()
#         if r2:
#             attribs += " previous=\"" + baseUrl + dictID + "/" + str(r2["id"]) + ".xml\""
#         c2 = dictDB.execute("select e1.id, e1.title from entries as e1 where e1.sortkey>(select sortkey from entries where id=?) order by e1.sortkey asc limit 1", (entryID, ))
#         r2 = c2.fetchone()
#         if r2:
#             attribs += " next=\"" + baseUrl + dictID + "/" + str(r2["id"]) + ".xml\""
#         xml = "<lexonomy" + attribs + ">" + xml + "</lexonomy>"
#         return {"entryID": row["id"], "xml": xml}
#     else:
#         return {"entryID": 0, "xml": ""}


def readRandoms(dictDB, limit=10): # OK
    configs = readDictConfigs(dictDB)
    more = False
    randoms = []
    c = dictDB.execute("SELECT id, title, sortkey, nvh FROM entries WHERE id IN (SELECT id FROM entries ORDER BY random() LIMIT ?)", (limit,))
    for r in c.fetchall():
        randoms.append({"id": r["id"], "title": r["title"], "sortkey": r["sortkey"], "titlePlain": getEntryTitle(nvh.parse_string(r["nvh"]), configs["titling"], True)})

    # sort by selected locale
    collator = Collator.createInstance(Locale(getLocale(configs)))
    randoms.sort(key=lambda x: collator.getSortKey(x['sortkey']))

    c = dictDB.execute("select count(*) as total from entries")
    r = c.fetchone()
    if r["total"] > limit:
        more = True
    return {"entries": randoms, "more": more}

def readRandomOne(dictDB, dictID, configs): # TODO
    c = dictDB.execute("SELECT id, title, nvh FROM entries WHERE id IN (SELECT id FROM entries ORDER BY random() LIMIT 1)")
    r = c.fetchone()
    if r:
        return {"id": r["id"], "title": r["title"], "nvh": r["nvh"]}
    else:
        return {"id": 0, "title": "", "nvh": ""}

def download_xslt(configs):
    if 'download' in configs and 'xslt' in configs['download'] and configs['download']['xslt'].strip != "" and len(configs['download']['xslt']) > 0 and configs['download']['xslt'][0] == "<":
        import lxml.etree as ET
        try:
            xslt_dom = ET.XML(configs["download"]["xslt"].encode("utf-8"))
            xslt = ET.XSLT(xslt_dom)
        except (ET.XSLTParseError, ET.XMLSyntaxError) as e:
            return "Failed to parse XSL: {}".format(e), False

        def transform(xml_txt):
            try:
                dom = ET.XML(xml_txt)
                xml_transformed_dom = xslt(dom)
                xml_transformed_byt = ET.tostring(xml_transformed_dom, xml_declaration=False, encoding="utf-8")
                xml_transformed = xml_transformed_byt.decode('utf-8')
                return xml_transformed, True
            except ET.XMLSyntaxError as e:
                return "Failed to parse content: {}".format(e), False
            except ET.XSLTParseError as e:
                return "Failed to use XSL: {}".format(e), False
    else:
        def transform(xml_text):
            return re.sub("><",">\n<",xml_text), True

    return transform


def download(dictDB, dictID, export_type):
    if export_type == 'nvh':
        c = dictDB.execute("select id, nvh from entries")
        for r in c.fetchall():
            yield r['nvh']

    elif export_type == 'xml':
        yield "<"+dictID+">\n"
        c = dictDB.execute("select id, nvh from entries")

        for r in c.fetchall():
            result_xml = []
            entry_nvh = nvh.parse_string(r['nvh'])
            entry_nvh.dump_xml(result_xml)
            yield '\n'.join(result_xml)
            yield "\n"

        yield "</"+dictID+">\n"

def purge(dictDB, email, historiography):
    dictDB.execute("insert into history(entry_id, action, [when], email, xml, historiography) select id, 'purge', ?, ?, xml, ? from entries", (str(datetime.datetime.utcnow()), email, json.dumps(historiography)))
    dictDB.execute("delete from entries")
    dictDB.commit()
    dictDB.execute("vacuum")
    dictDB.commit()
    return True

# def showImportErrors(filename, truncate):
#     with open(filename+".err", "r") as content_file:
#         content = content_file.read()
#     if (truncate):
#         content = content[0:truncate].replace("<", "&lt;")
#         return {"errorData": content, "truncated": truncate}
#     else:
#         return content

def getImportProgress(file_path):
    """
    return progress, finished status, error messages
    """
    done_re = re.compile(r'^INFO \[.*\]:\s*IMPORTED \(.*\):\s*PER:\s*(\d+)\s*,\s*COUNT:\s*(\d+)/(\d+)$')
    waring_re = re.compile(r'^WARNING(:|\s\[.*\]:)\s*(.+)$')
    err_re = re.compile(r'^ERROR(:|\s\[.*\]:)\s*(.*?)$')
    if os.path.isfile(os.path.join(file_path, "import_progress.log")):
        errors = []
        warnings = []
        progress = {}
        finished = False
        with open(os.path.join(file_path, "import_progress.log"), "r") as log_f:
            for line in log_f:
                prg = done_re.match(line)
                warn = waring_re.match(line)
                err = err_re.match(line)
                if prg:
                    progress = {'per': int(prg.group(1)), 'done': int(prg.group(2)), 'total': int(prg.group(3))}
                elif warn:
                    warnings.append(warn.group(2))
                elif err:
                    errors.append(err.group(2))

        if progress.get('per', 0) == 100:
            finished = True

        return progress, finished, errors, warnings, file_path
    else:
        return {'per': 0, 'done': 0, 'total': 0}, False, ['No log file found'], ['No log file found'], file_path


def importfile(dictID, email, hwNode, deduplicate=False, purge=False, purge_all=False, bottle_files={}, titling_node=None):
    """
    return progress, finished status, error messages
    """
    supported_formats = re.compile('^.*\.(xml|nvh)$', re.IGNORECASE)
    # XML file transforamtion
    if bottle_files.get("import_entires", False):
        if not supported_formats.match(bottle_files["import_entires"].filename):
            return 'Unsupported format for import file. An .xml or .nvh file are required.', '', ''

    save_path = os.path.join(siteconfig["dataDir"], "uploads", next(tempfile._get_candidate_names()))
    while os.path.exists(save_path):
        save_path = os.path.join(siteconfig["dataDir"], "uploads", next(tempfile._get_candidate_names()))

    os.makedirs(save_path)

    dbpath = os.path.join(siteconfig["dataDir"], "dicts/"+dictID+".sqlite")

    # ====================================
    # CONFIG
    # ====================================
    # safe all files as received
    for _, value in bottle_files.items():
        value.save(os.path.join(save_path, value.filename))

    entries_path = None
    if bottle_files.get('import_entires', False):
        entries_path = os.path.join(save_path, bottle_files.get('import_entires').filename)
        logfile_f = open(os.path.join(save_path, "import_progress.log"), "w")

    config = {'styles': {},
              'editting': {},
              'structure': {}}

    has_config = False
    # if config.json received rewrite the default one
    if bottle_files.get('config'): # Must be first !!!
        config = json.loads(bottle_files.get('config').file.read())
        if not config.get('styles', False):
            config['styles'] = {}
        if not config.get('editting', False):
            config['editting'] = {}
        if not config.get('structure', False):
            config['structure'] = {}
        has_config == True

    if bottle_files.get('ce_css'):
        config['editting']['css'] =  bottle_files.get('ce_css').file.read().decode('utf-8')
        has_config == True

    if bottle_files.get('ce_js'):
        config['editting']['js'] =  bottle_files.get('ce_js').file.read().decode('utf-8')
        has_config == True

    if bottle_files.get('structure'):
        config['structure']['nvhSchema'] = bottle_files.get('structure').file.read().decode('utf-8')
        has_config == True

    if bottle_files.get('styles'):
        config['styles']['css']= bottle_files.get('styles').file.read().decode('utf-8')
        has_config == True
    # ====================================

    params = []
    if deduplicate:
        params.append('-d')
    if purge:
        params.append('-p')
    if purge_all:
        params.append('-pp')
    if titling_node:
        params.append('-t')
        params.append(titling_node)
    if has_config:
        with open(os.path.join(save_path, "merged_config.json"), 'w') as f:
            json.dump(config, f, indent=4)
        params.append('--config')
        params.append(os.path.join(save_path, "merged_config.json"))

    if entries_path:
        subprocess.Popen([currdir + "/import2dict.py", dbpath, entries_path, email, hwNode] + params,
                        stdout=logfile_f, stderr=logfile_f, start_new_session=True, close_fds=True)
    else:
        return 'No entries', "", ""

    return '', "Import started. You may close the window, import will run in the background. Please wait...", save_path

def getLastEditedEntry(dictDB, email):
    c = dictDB.execute("select entry_id from history where email=? order by [when] desc limit 1", (email, ))
    r = c.fetchone()
    if r:
        return str(r["entry_id"])
    else:
        return ""

def listEntriesById(dictDB, entryID, configs):
    c = dictDB.execute("select e.id, e.title, e.nvh from entries as e where e.id=?", (entryID,))
    entries = []
    for r in c.fetchall():
        entries.append({"id": r["id"], "title": r["title"], "nvh": r["nvh"]})
    return entries

def listEntries(dictDB, dictID, configs, searchtext="", modifier="start", howmany=10, offset=0, sortdesc=False, reverse=False, fullNVH=False):
    collate = ""
    if "locale" in configs["titling"]:
        collator = Collator.createInstance(Locale(getLocale(configs)))
        dictDB.create_collation("custom", collator.compare)
        collate = "collate custom"
    if searchtext == "":
        cc = dictDB.execute("select count(*) as total from entries")
        rc = cc.fetchone()
        cf = dictDB.execute("select * from entries order by sortkey %s limit %s offset %s" % (collate, howmany, 0 if not offset else offset))
        entries = []
        for rf in cf.fetchall():
            item = {"id": rf["id"], "title": rf["title"], "sortkey": rf["sortkey"]}
            if configs["flagging"].get("flag_element"):
                item["flags"] = extractText(nvh.parse_string(rf["nvh"]), configs["flagging"]["flag_element"])
            entries.append(item)
        return rc["total"], entries, True

    lowertext = searchtext.lower()
    if type(sortdesc) == str:
        if sortdesc == "true":
            sortdesc = True
        else:
            sortdesc = False
    if "flag_element" in configs["flagging"] or fullNVH:
        entryNVH = ", e.nvh "
    else:
        entryNVH = ""
    if "headwordSortDesc" in configs["titling"]:
        reverse = configs["titling"]["headwordSortDesc"]
    if reverse:
        sortdesc = not sortdesc
    orderby = "ASC"
    if sortdesc:
        orderby = "DESC"
    if modifier == "start":
        sql1 = "SELECT s.txt, min(s.level) AS level, e.id, e.sortkey, e.title" + entryNVH + " FROM searchables AS s INNER JOIN entries AS e ON e.id=s.entry_id WHERE (LOWER(s.txt) LIKE ? OR s.txt LIKE ? OR e.sortkey LIKE ?) GROUP BY e.id ORDER BY s.level, e.sortkey %s %s LIMIT ? OFFSET ?" % (collate, orderby)
        params1 = (lowertext+"%", searchtext+"%", searchtext+"%", howmany, offset)
        sql2 = "SELECT COUNT(distinct s.entry_id) AS total FROM searchables AS s INNER JOIN entries AS e ON e.id=s.entry_id WHERE (LOWER(s.txt) LIKE ? OR s.txt LIKE ? OR e.sortkey LIKE ?)"
        params2 = (lowertext+"%", searchtext+"%", searchtext+"%")
    elif modifier == "wordstart":
        sql1 = "SELECT s.txt, min(s.level) AS level, e.id, e.sortkey, e.title" + entryNVH + " FROM searchables AS s INNER JOIN entries AS e ON e.id=s.entry_id WHERE (LOWER(s.txt) LIKE ? OR LOWER(s.txt) LIKE ? OR s.txt LIKE ? OR s.txt LIKE ?) GROUP BY e.id ORDER BY s.level, e.sortkey %s %s LIMIT ? OFFSET ?" % (collate, orderby)
        params1 = (lowertext + "%", "% " + lowertext + "%", searchtext + "%", "% " + searchtext + "%", howmany, offset)
        sql2 = "SELECT COUNT(distinct s.entry_id) AS total FROM searchables AS s INNER JOIN entries AS e ON e.id=s.entry_id WHERE (LOWER(s.txt) LIKE ? OR LOWER(s.txt) LIKE ? OR s.txt LIKE ? OR s.txt LIKE ?)"
        params2 = (lowertext + "%", "% " + lowertext + "%", searchtext + "%", "% " + searchtext + "%")
    elif modifier == "substring":
        sql1 = "SELECT s.txt, min(s.level) AS level, e.id, e.sortkey, e.title" + entryNVH + " FROM searchables AS s INNER JOIN entries AS e ON e.id=s.entry_id WHERE (LOWER(s.txt) LIKE ? OR s.txt LIKE ?) GROUP BY e.id ORDER BY s.level, e.sortkey %s %s LIMIT ? OFFSET ?" % (collate, orderby)
        params1 = ("%" + lowertext + "%", "%" + searchtext + "%", howmany, offset)
        sql2 = "SELECT COUNT(distinct s.entry_id) AS total FROM searchables AS s INNER JOIN entries AS e ON e.id=s.entry_id WHERE (LOWER(s.txt) LIKE ? OR s.txt LIKE ?)"
        params2 = ("%" + lowertext + "%", "%" + searchtext + "%")
    elif modifier == "exact":
        sql1 = "SELECT s.txt, min(s.level) AS level, e.id, e.sortkey, e.title" + entryNVH + " FROM searchables AS s INNER JOIN entries AS e ON e.id=s.entry_id WHERE s.txt LIKE ? GROUP BY e.id ORDER BY s.level, e.sortkey %s %s LIMIT ? OFFSET ?" % (collate, orderby)
        params1 = (searchtext, howmany, offset)
        sql2 = "SELECT COUNT(distinct s.entry_id) AS total FROM searchables AS s INNER JOIN entries AS e ON e.id=s.entry_id WHERE s.txt LIKE ?"
        params2 = (searchtext)
    c1 = dictDB.execute(sql1, params1)
    entries = []
    for r1 in c1.fetchall():
        item = {"id": r1["id"], "title": r1["title"], "sortkey": r1["sortkey"]}
        if configs["flagging"].get("flag_element"):
            item["flags"] = extractText(nvh.parse_string(r1["nvh"]), configs["flagging"]["flag_element"])
        if fullNVH:
            item["nvh"] = r1["nvh"]
        if r1["level"] > 1:
            item["title"] += " ← <span class='redirector'>" + r1["txt"] + "</span>"
        entries.append(item)

    c2 = dictDB.execute(sql2, params2)
    r2 = c2.fetchone()
    total = r2["total"]
    return total, entries, False

def listEntriesPublic(dictDB, dictID, configs, searchtext):
    howmany = 100
    sql_list = "select s.txt, min(s.level) as level, e.id, e.title, e.sortkey, case when s.txt=? then 1 else 2 end as priority from searchables as s inner join entries as e on e.id=s.entry_id where s.txt like ? group by e.id order by priority, level, s.level"
    c1 = dictDB.execute(sql_list, ("%"+searchtext+"%", "%"+searchtext+"%"))
    entries = []
    for r1 in c1.fetchall():
        item = {"id": r1["id"], "title": r1["title"], "sortkey": r1["sortkey"], "exactMatch": (r1["level"] == 1 and r1["priority"] == 1)}
        if r1["level"] > 1:
            item["title"] += " ← <span class='redirector'>" + r1["txt"] + "</span>"
        entries.append(item)

    # sort by selected locale
    collator = Collator.createInstance(Locale(getLocale(configs)))
    entries.sort(key=lambda x: collator.getSortKey(x['sortkey']))
    # and limit
    entries = entries[0:int(howmany)]

    return entries

def extractText(nvhParsed, elName):
    if not elName:
        return []
    return extractElementText(nvhParsed, elName, [])

def extractElementText(nvh_parsed, elName, textAr):
    nvh_parsed.filter_entries([elName], [elName])
    nvh_parsed.path2value(textAr)
    return textAr

def extractFirstText(nvhParsed):
    return extractFirstElementText(nvhParsed) or ""

def extractFirstElementText(nvhChild):
    if nvhChild.value != "":
        return nvhChild.value
    else:
        for c in nvhChild.children:
            return extractFirstElementText(c)

def getDictStats(dictDB):
    res = {"entryCount": 0, "needResave": 0}
    c = dictDB.execute("select count(*) as entryCount from entries")
    r = c.fetchone()
    res["entryCount"] = r["entryCount"]
    c = dictDB.execute("select count(*) as needResave from entries where needs_resave=1 or needs_refresh=1 or needs_refac=1")
    r = c.fetchone()
    res["needResave"] = r["needResave"]
    return res

def combine_dmlex_schemas(old_sch_nvh, new_sch_nvh):
    """Find all custom nodes in old dmlex schema and add it to new dmlex schema if perents exists"""
    stadard_dmlex_schema, _, _ = getDmlLexSchemaItems(['all'])
    removed_nodes = {}
    stadard_dmlex_nodes_keys = nvh.schema_keys(stadard_dmlex_schema)
    old_sch_json = nvh.schema_nvh2json(old_sch_nvh)
    new_sch_json = nvh.schema_nvh2json(new_sch_nvh)

    for old_node, old_value in old_sch_json.items():
        if old_node not in new_sch_json.keys():
            if True in [True if re.fullmatch(x, old_node) else False for x in stadard_dmlex_nodes_keys]:
                removed_nodes[old_node] = old_value
            elif old_value['parent'] in new_sch_json.keys():
                new_sch_json[old_node] = old_value
                if old_node not in new_sch_json[old_value['parent']]['children']:
                    new_sch_json[old_value['parent']]['children'].append(old_node)
            else:
                removed_nodes[old_node] = old_value

    return removed_nodes, nvh.schema_json2nvh(new_sch_json)


def updateDmLexSchema(current_schema, requested_modules, xlingual_langs, linking_relations, etymology_langs):
    new_schema, desc_dict, used_modules = getDmlLexSchemaItems(requested_modules, xlingual_langs, linking_relations, etymology_langs)

    if sorted(current_schema.get('modules', [])) != sorted(requested_modules):
        removed_nodes, final_schema = combine_dmlex_schemas(current_schema['nvhSchema'], new_schema)
    else:
        final_schema = current_schema['nvhSchema']

    return final_schema, desc_dict, used_modules, removed_nodes


def updateDictConfig(dictDB, dictID, configID, content):
    if configID == 'structure':
        value = content
        if not content.get('nvhSchema', False):
            old_strucure_json = json.loads(dictDB.execute("SELECT json FROM configs WHERE id='structure'").fetchone()['json'])
            if old_strucure_json and old_strucure_json.get('nvhSchema', False):
                value['nvhSchema'] = old_strucure_json['nvhSchema']
        if value.get('root', False):
            value['root'] = nvh.schema_get_root_name(content['nvhSchema'])

    else:
        value = content

    dictDB.execute("DELETE FROM configs WHERE id=?", (configID, ))
    dictDB.execute("INSERT INTO configs(id, json) VALUES (?, ?)", (configID, json.dumps(value)))
    dictDB.commit()

    if configID == "ident":
        updateDictIdent(dictDB, dictID)
        return content, False
    elif configID == "titling" or configID == "searchability":
        resaveNeeded = flagForResave(dictDB)
        return content, resaveNeeded
    elif configID == "links":
        resaveNeeded = flagForResave(dictDB)
        c = dictDB.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='linkables'")
        if not c.fetchone():
            dictDB.execute("CREATE TABLE linkables (id INTEGER PRIMARY KEY AUTOINCREMENT, entry_id INTEGER REFERENCES entries (id) ON DELETE CASCADE, txt TEXT, element TEXT, preview TEXT)")
            dictDB.execute("CREATE INDEX link ON linkables (txt)")
            dictDB.commit()
        return content, resaveNeeded
    else:
        return content, False

def addFlagToStructure(dictDB, content):
    deleteFlagFromStructure(dictDB)
    c = dictDB.execute("SELECT json FROM configs WHERE id=?", ('structure',))
    structure = json.loads(c.fetchone()['json'])
    flag_element = content["flag_element"]
    flag_name = 'lexonomy_flag'
    structure['elements'][flag_name] = {'type': 'string', 'min': 1, 'max': 1, 'values': [x['name'] for x in content['flags']], 're': '', 'children': []}
    if structure['elements'][flag_element].get('children', False):
        structure['elements'][flag_element]['children'].append(flag_name)
    else:
        structure['elements'][flag_element]['children'] = [flag_name]

    dictDB.execute("UPDATE configs SET json=? WHERE id=?", (json.dumps(structure), 'structure'))
    dictDB.commit()

def deleteFlagFromStructure(dictDB):
    c = dictDB.execute("SELECT json FROM configs WHERE id=?", ('structure',))
    structure = json.loads(c.fetchone()['json'])
    flag_name = 'lexonomy_flag'
    if flag_name in structure['elements']:
        structure['elements'].pop(flag_name)
        for e in structure['elements']:
            if flag_name in structure['elements'][e]['children']:
                idx = structure['elements'][e]['children'].index(flag_name)
                structure['elements'][e]['children'].pop(idx)
        dictDB.execute("UPDATE configs SET json=? WHERE id=?", (json.dumps(structure), 'structure'))
        dictDB.commit()

def updateDictAccess(dictID, users):
    conn = getMainDB()
    c = conn.execute("SELECT * FROM user_dict WHERE dict_id=?", (dictID,))
    old_users = {}
    for r in c.fetchall():
        old_users[r['user_email']] = {'canView': r['can_view'], 'canEdit': r['can_edit'],
                                      'canConfig': r['can_config'], 'canDownload': r['can_download'],
                                      'canUpload': r['can_upload']}

    conn.execute("DELETE FROM user_dict WHERE dict_id=?", (dictID,))

    for user, rights in users.items():
        conn.execute("INSERT INTO user_dict(dict_id, user_email, can_view, can_edit, can_config, can_download, can_upload) VALUES (?, ?, ?, ?, ?, ?, ?)",
                     (dictID, user, rights['canView'], rights['canEdit'], rights['canConfig'], rights['canDownload'], rights['canUpload']))
    conn.commit()

    return old_users

def updateDictSettings(dictID, settings_config):
    conn = getMainDB()
    conn.execute("UPDATE dicts SET configs=? WHERE id=?", (settings_config, dictID))
    conn.commit()

def flagForResave(dictDB):
    c = dictDB.execute("update entries set needs_resave=1")
    dictDB.commit()
    return (c.rowcount > 0)

"""
def flagForRefac(dictDB):
    c = dictDB.execute("update entries set needs_refac=1")
    dictDB.commit()
    return (c.rowcount > 0)
"""

def makeQuery(lemma):
    words = []
    for w in lemma.split(" "):
        if w != "":
            words.append('[lc="'+w+'"|lemma_lc="'+w+'"]')
    ret = "aword," + "".join(words)
    return ret

def clearRefac(dictDB):
    dictDB.execute("update entries set needs_refac=0, needs_refresh=0")
    dictDB.commit()

def resave(dictDB, dictID, configs):
    c = dictDB.execute("select id, nvh from entries where needs_resave=1")
    entry_updates = []
    ids = []
    searchable_updates = []
    for r in c.fetchall():
        entryID = r["id"]
        nvhParsed = nvh.parse_string(r["nvh"])
        entryTitle = getEntryTitle(nvhParsed, configs["titling"])
        entryTitle_plaintext = getEntryTitle(nvhParsed, configs["titling"], True)
        sortTitle = getSortTitle(nvhParsed, configs["titling"])
        entry_updates.append((entryTitle, sortTitle, entryID))
        ids.append(entryID)
        searchable_updates.append((entryID, entryTitle_plaintext, 1))
        searchable_updates.append((entryID, entryTitle_plaintext.lower(), 1))
        headword = getEntryHeadword(nvhParsed, configs["titling"].get("headword"))
        for searchable in getEntrySearchables(nvhParsed, configs):
            if searchable != headword:
                searchable_updates.append((entryID, searchable, 2))
        if configs["links"]:
            updateEntryLinkables(dictDB, entryID, nvhParsed, configs, True, True)
    dictDB.executemany("update entries set needs_resave=0, title=?, sortkey=? where id=?", entry_updates)
    dictDB.execute("delete from searchables where entry_id in (%s)" % (",".join(map(str, ids))))
    dictDB.executemany("insert into searchables(entry_id, txt, level) values(?, ?, ?)", searchable_updates)
    dictDB.commit()
    return True

def getEntryLinks(dictDB, dictID, entryID):
    ret = {"out": [], "in": []}
    cl = dictDB.execute("SELECT count(*) as count FROM sqlite_master WHERE type='table' and name='linkables'")
    rl = cl.fetchone()
    if rl['count'] > 0:
        c = dictDB.execute("SELECT * FROM linkables WHERE entry_id=?", (entryID,))
        conn = getLinkDB()
        for r in c.fetchall():
            lout = []
            lin = []
            for lr in links_get(dictID, r["element"], r["txt"], "", "", ""):
                lr['source_preview'] = r['preview']
                lout.append(lr)
            for lr in links_get("", "", "", dictID, r["element"], r["txt"]):
                lr['target_preview'] = r['preview']
                lin.append(lr)
            ret["out"] = ret["out"] + lout
            ret["in"] = ret["in"] + lin
    return ret

def updateEntryLinkables(dictDB, entryID, nvhParsed, configs, save=True, save_xml=True):
    linkableAr = []
    for linkref in configs["links"].values():
        nvhParsed, linkableAr = updateLinkablesLevel(nvhParsed, linkref, nvhParsed, linkableAr)
    if save:
        dictDB.execute("DELETE FROM linkables WHERE entry_id=?", (entryID,))
        for linkable in configs["links"].values():
            dictDB.execute("INSERT INTO linkables (entry_id, txt, element, preview) VALUES (?,?,?,?)", (entryID, linkable["identifier"], linkable["linkElement"], linkable["preview"]))
    if save_xml and len(configs["links"].values())>0:
        dictDB.execute("UPDATE entries SET nvh=? WHERE id=?", (nvhParsed.dump_string(), entryID))
    dictDB.commit()
    return nvhParsed.dump_string()

def updateLinkablesLevel(nvhNode, linkinfo, entryNvh, linkableAr):
    if nvhNode.name == linkinfo['linkElement']:
        # remove existing linkables
        nvhNode.children = [c for c in nvhNode.children if c.name != "__lexonomy__linkable"]

        # add new linkable identifier
        identifier = linkinfo["identifier"]
        for pattern in re.findall(r"%\([^)]+\)", linkinfo["identifier"]):
            text = ""
            extract = extractText(nvhNode, pattern[2:-1])
            extractfull = extractText(entryNvh, pattern[2:-1])
            if len(extract) > 0:
                text = extract[0]
            elif len(extractfull) > 0:
                text = extractfull[0]
            identifier = identifier.replace(pattern, text)
        if nvhNode.children:
            nvhNode.children.append(nvh(nvhNode, nvhNode.children[0].indent, "__lexonomy__linkable", identifier, []))
        else:
            ind_step = nvhNode.indent[len(nvhNode.parent.indent):]
            indent = nvhNode.indent + ind_step
            nvhNode.children.append(nvh(nvhNode, indent, "__lexonomy__linkable", identifier, []))

        # add preview
        preview = linkinfo["preview"]
        for pattern in re.findall(r"%\([^)]+\)", linkinfo["preview"]):
            text = ""
            extract = extractText(nvhNode, pattern[2:-1])
            extractfull = extractText(entryNvh, pattern[2:-1])
            if len(extract) > 0:
                text = extract[0]
            elif len(extractfull) > 0:
                text = extractfull[0]
            preview = preview.replace(pattern, text)
        linkableAr.append({'element': linkinfo["linkElement"], "identifier": identifier, "preview": preview})

    for c in nvhNode.children:
        if c.name != "__lexonomy__linkable":
            c, linkableAr = updateLinkablesLevel(c, linkinfo, entryNvh, linkableAr)

    return nvhNode, linkableAr

def getEntrySearchables(nvhParsed, configs): # TODO search
    ret = []
    ret.append(getEntryHeadword(nvhParsed, configs["titling"].get("headword")))
    if configs["searchability"].get("searchableElements"):
        for sel in configs["searchability"].get("searchableElements"):
            for txt in extractText(nvhParsed, sel):
                if txt != "" and txt not in ret:
                    ret.append(txt)
    return ret

def flagEntry(dictDB, configs, entryID, flags, email, historiography):
    c = dictDB.execute("select id, nvh from entries where id=?", (entryID,))
    row = c.fetchone()
    nvhParsed = nvh.parse_string(row["nvh"])
    while deleteNode(nvhParsed, configs["flagging"]["flag_element"].strip().split('.')):
        pass
    success = True
    error = ""

    schema_json = nvh.schema_nvh2json(configs["structure"]["nvhSchema"])
    for flag in flags:
        s, error = addNode(nvhParsed, flag, configs["flagging"]["flag_element"], schema_json)
        success = success and s
    dictDB.execute("UPDATE entries SET nvh=?, json=?, title=?, sortkey=?, needs_resave=?, needs_refresh=?, needs_refac=? where id=?", (nvhParsed.dump_string(),
                                                                                                                                       nvh2jsonDump(nvhParsed),
                                                                                                                                       getEntryTitle(nvhParsed, configs["titling"]),
                                                                                                                                       getSortTitle(nvhParsed, configs["titling"]),
                                                                                                                                       0, 0, 0, entryID))

    dictDB.execute("insert into history(entry_id, action, [when], email, nvh, historiography) values(?, ?, ?, ?, ?, ?)", (entryID, "update", str(datetime.datetime.utcnow()), email, nvhParsed.dump_string(), json.dumps(historiography)))
    dictDB.commit()
    return success, error


def addNode(nvhParsed, node_value, node_name, structure):
    parent_name = ''
    for name, params in structure.items():
        if node_name in params.get('children',[]):
            parent_name = name

    nvh_path = node_name.strip().split('.')
    if not parent_name:
        return False, 'Flagging elemennt no present in strucure'
    else:
        addNodeRecursive(nvhParsed, node_value, nvh_path)
        return True, ''


def addNodeRecursive(nvhNode, node_value, nvh_path):
    if len(nvh_path) == 2:
        if nvhNode.name == nvh_path[0]:
            ind_step = nvhNode.indent[len(nvhNode.parent.indent):]
            indent = nvhNode.indent + ind_step
            nvhNode.children.append(nvh(nvhNode, indent, nvh_path[1], node_value, []))
        else:
            for c in nvhNode.children:
                addNodeRecursive(c, node_value, nvh_path)
    else:
        for c in nvhNode.children:
            if c.name == nvh_path[0]:
                addNodeRecursive(c, node_value, nvh_path[1:])


def deleteNode(nvhNode, nvh_path):
    success = False
    if len(nvh_path) == 2:
        if nvhNode.name == nvh_path[0]:
            for idx, c in enumerate(nvhNode.children):
                if c.name == nvh_path[1]:
                    nvhNode.children.pop(idx)
                    success = True
        else:
            for c in nvhNode.children:
                success = success or deleteNode(c, nvh_path)
    else:
        for c in nvhNode.children:
            if c.name == nvh_path[0]:
                success = success or deleteNode(c, nvh_path[1:])
    return success


def getFlagElementInString(path, xml):
    start_out, end_out = 0, len(xml)
    start_in, end_in = 0, len(xml)

    # find each element in path to flag element, start with outmost one
    for path_element in path:
        regex = re.compile("<{}[^>]*>([\s\S]*?)</{}>".format(path_element, path_element))
        match = regex.search(xml, start_in, end_in)

        # we can not find the element, just return to the beginning of outer element
        if match is None:
            return (start_in, start_in)

        start_out = match.start(0)
        end_out = match.end(0)
        start_in = match.start(1)
        end_in = match.end(1)

    # we found it! Return the span where flag element exists in xml
    return (start_out, end_out)


def readDictHistory(dictDB, dictID, configs, entryID):
    history = []
    c = dictDB.execute("select * from history where entry_id=? order by [when] desc", (entryID,))
    for row in c.fetchall():
        """
        xml = row["xml"]
        if row["xml"]:
            xml = setHousekeepingAttributes(entryID, row["xml"], configs["subbing"])
        """
        history.append({"entry_id": row["entry_id"], "revision_id": row["id"], "content": row["nvh"], "action": row["action"], "when": row["when"], "email": row["email"] or "", "historiography": json.loads(row["historiography"])})
    return history

def verifyUserApiKey(email, apikey):
    conn = getMainDB()
    if email == '':
        c = conn.execute("select email from users where apiKey=?", (apikey,))
        row = c.fetchone()
    else:
        c = conn.execute("select email from users where email=? and apiKey=?", (email, apikey))
        row = c.fetchone()
    if not row or siteconfig["readonly"]:
        return {"valid": False}
    else:
        return {"valid": True, "email": email or ""}

def links_add(source_dict, source_el, source_id, target_dict, target_el, target_id, confidence=0, conn=None):
    if not conn:
        conn = getLinkDB()
    c = conn.execute("SELECT * FROM links WHERE source_dict=? AND source_element=? AND source_id=? AND target_dict=? AND target_element=? AND target_id=?", (source_dict, source_el, source_id, target_dict, target_el, target_id))
    row = c.fetchone()
    if not row:
        conn.execute("INSERT INTO links (source_dict, source_element, source_id, target_dict, target_element, target_id, confidence) VALUES (?,?,?,?,?,?,?)", (source_dict, source_el, source_id, target_dict, target_el, target_id, confidence))
        conn.commit()
    c = conn.execute("SELECT * FROM links WHERE source_dict=? AND source_element=? AND source_id=? AND target_dict=? AND target_element=? AND target_id=?", (source_dict, source_el, source_id, target_dict, target_el, target_id))
    row = c.fetchone()
    return {"link_id": row["link_id"], "source_dict": row["source_dict"], "source_el": row["source_element"], "source_id": row["source_id"], "target_dict": row["target_dict"], "target_el": row["target_element"], "target_id": row["target_id"], "confidence": row["confidence"]}

def links_delete(dictID, linkID):
    conn = getLinkDB()
    conn.execute("DELETE FROM links WHERE source_dict=? AND link_id=?", (dictID, linkID))
    conn.commit()
    c = conn.execute("select * from links where link_id=?", (linkID, ))
    if len(c.fetchall()) > 0:
        return False
    else:
        return True

def links_get(source_dict, source_el, source_id, target_dict, target_el, target_id):
    params = []
    where = []
    if source_dict != "":
        where.append("source_dict=?")
        params.append(source_dict)
    if source_el != "":
        where.append("source_element=?")
        params.append(source_el)
    if source_id != "":
        where.append("source_id=?")
        params.append(source_id)
    if target_dict != "":
        where.append("target_dict=?")
        params.append(target_dict)
    if target_el != "":
        where.append("target_element=?")
        params.append(target_el)
    if target_id != "":
        where.append("target_id=?")
        params.append(target_id)
    query = "SELECT * FROM links"
    if len(where) > 0:
        query += " WHERE " + " AND ".join(where)
    conn = getLinkDB()
    c = conn.execute(query, tuple(params))
    res = []
    #first, get all dictionaries in results
    dbs = {}
    dbconfigs = {}
    for row in c.fetchall():
        if not row["source_dict"] in dbs:
            dbs[row["source_dict"]] = getDB(row["source_dict"])
            dbconfigs[row["source_dict"]] = readDictConfigs(dbs[row["source_dict"]])
        if not row["target_dict"] in dbs:
            try:
                dbs[row["target_dict"]] = getDB(row["target_dict"])
                dbconfigs[row["target_dict"]] = readDictConfigs(dbs[row["target_dict"]])
            except:
                dbconfigs[row["target_dict"]] = None
    #now the actual results
    c = conn.execute(query, tuple(params))
    for row in c.fetchall():
        sourceDB = dbs[row["source_dict"]]
        sourceConfig = dbconfigs[row["source_dict"]]
        targetDB = dbs[row["target_dict"]]
        targetConfig = dbconfigs[row["target_dict"]]
        source_entry = ""
        source_hw = ""
        try:
            # test if source DB has linkables tables
            ress = sourceDB.execute("SELECT entry_id FROM linkables WHERE txt=?", (row["source_id"],))
            rows = ress.fetchone()
            if rows:
                source_entry = rows["entry_id"]
        except:
            source_entry = ""
        # fallback for ontolex ids
        if source_entry == "" and re.match(r"^[0-9]+_[0-9]+$", row["source_id"]):
            source_entry = row["source_id"].split("_")[0]
        if source_entry != "":
            source_hw = getEntryTitleID(sourceDB, sourceConfig, source_entry, True)
        target_entry = ""
        target_hw = ""
        try:
            # test if target DB has linkables tables
            rest = targetDB.execute("SELECT entry_id FROM linkables WHERE txt=?", (row["target_id"],))
            rowt = rest.fetchone()
            if rowt:
                target_entry = rowt["entry_id"]
        except:
            target_entry = ""
        # fallback for ontolex ids and CILI
        if target_entry == "" and re.match(r"^[0-9]+_[0-9]+$", row["target_id"]):
            target_entry = row["target_id"].split("_")[0]
        if target_entry != "":
            target_hw = getEntryTitleID(targetDB, targetConfig, target_entry, True)
        if target_dict == "CILI":
            target_entry = row["target_id"]
            target_hw = row["target_id"]

        res.append({"link_id": row["link_id"], "source_dict": row["source_dict"], "source_entry": str(source_entry), "source_hw": source_hw, "source_el": row["source_element"], "source_id": row["source_id"], "target_dict": row["target_dict"], "target_entry": str(target_entry), "target_hw": target_hw, "target_el": row["target_element"], "target_id": row["target_id"], "confidence": row["confidence"]})
    return res

def getDictLinkables(dictDB):
    ret = []
    cl = dictDB.execute("SELECT count(*) as count FROM sqlite_master WHERE type='table' and name='linkables'")
    rl = cl.fetchone()
    if rl['count'] > 0:
        c = dictDB.execute("SELECT * FROM linkables ORDER BY entry_id, element, txt")
        for r in c.fetchall():
            ret.append({"element": r["element"], "link": r["txt"], "entry": r["entry_id"], "preview": r["preview"]})
    return ret

def isrunning(dictDB, bgjob, pid=None):
    if not pid:
        c = dictDB.execute("SELECT pid FROM bgjobs WHERE id=?", (bgjob,))
        job = c.fetchone()
        if not job:
            return False
        pid = job["pid"]
    if pid < 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True

def autoImage(dictDB, dictID, configs, addElem, addNumber):
    import subprocess
    res = isAutoImage(dictDB)
    if res["bgjob"] and res["bgjob"] > 0:
        return res
    c = dictDB.execute("INSERT INTO bgjobs (type, data) VALUES ('autoimage', 'autoimage')")
    dictDB.commit()
    jobid = c.lastrowid
    errfile = open("/tmp/autoImage-%s.err" % (dictID), "w")
    outfile = open("/tmp/autoImage-%s.out" % (dictID), "w")
    bgjob = subprocess.Popen(['adminscripts/autoImage.py', siteconfig["dataDir"], dictID, addElem, str(addNumber), str(jobid)],
        start_new_session=True, close_fds=True, stderr=errfile, stdout=outfile, stdin=subprocess.DEVNULL)
    dictDB.execute("UPDATE bgjobs SET pid=? WHERE id=?", (bgjob.pid, jobid))
    dictDB.commit()
    return {"bgjob": jobid}

def isLinking(dictDB):
    c = dictDB.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bgjobs'")
    if not c.fetchone():
        dictDB.execute("CREATE TABLE bgjobs (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, data TEXT, finished INTEGER DEFAULT -1, pid DEFAULT -1)")
        dictDB.commit()
    c = dictDB.execute("SELECT * FROM bgjobs WHERE finished=-1")
    job = c.fetchone()
    if job:
        pid = job["pid"]
        if isrunning(dictDB, job["id"], pid):
            return {"bgjob": job["id"], "otherdictID": job["data"]}
        else: # mark as dead
            c = dictDB.execute("UPDATE bgjobs SET finished=-2 WHERE pid=?", (pid,))
    return {"bgjob": -1}

def isAutoImage(dictDB):
    c = dictDB.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bgjobs'")
    if not c.fetchone():
        dictDB.execute("CREATE TABLE bgjobs (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, data TEXT, finished INTEGER DEFAULT -1, pid DEFAULT -1)")
        dictDB.commit()
    c = dictDB.execute("SELECT * FROM bgjobs WHERE finished=-1 AND data='autoimage'")
    job = c.fetchone()
    if job:
        pid = job["pid"]
        if isrunning(dictDB, job["id"], pid):
            return {"bgjob": job["id"]}
        else: # mark as dead
            c = dictDB.execute("UPDATE bgjobs SET finished=-2 WHERE pid=?", (pid,))
    return {"bgjob": -1}

def autoImageStatus(dictDB, dictID, bgjob):
    try:
        out = open("/tmp/autoImage-%s.out" % (dictID))
    except:
        return None
    if "COMPLETED\n" in out.readlines():
        return {"status": "finished"}
    if isrunning(dictDB, bgjob):
        return {"status": "working"}
    else:
        return {"status": "failed"}

def notifyUsers(configOld, configNew, dictInfo, dictID):
    for user in configNew:
        if not configOld.get(user, ''):
            mailSubject = "Lexonomy, added to the dictionary"
            mailText = "Dear Lexonomy user,\n\n"
            mailText += "you are now able to access the following dictionary:\n"
            mailText += "  " + dictInfo['title'] + "\n\n"
            mailText += "You have the following permissions:\n"
            if configNew[user]['canEdit']:
                mailText += " * edit\n"
            if configNew[user]['canConfig']:
                mailText += " * configure\n"
            if configNew[user]['canDownload']:
                mailText += " * download\n"
            if configNew[user]['canUpload']:
                mailText += " * upload\n"
            mailText += "\nYou can access the dictionary at the following address:\n"
            mailText += siteconfig['baseUrl'] + "#/" + dictID
            mailText += "\n\nYours,\nThe Lexonomy team"
            sendmail(user, mailSubject, mailText)

def changeFavDict(userEmail, dictID, status):
    if userEmail != '' and dictID != '':
        conn = getMainDB()
        conn.execute("DELETE FROM dict_fav WHERE user_email=? AND dict_id=?", (userEmail, dictID))
        if status == 'true':
            conn.execute("INSERT INTO dict_fav VALUES (?, ?)", (dictID, userEmail))
        conn.commit()
    return True

def get_iso639_1():
    codes = []
    for line in open("libs/iso-639-3.tab").readlines():
        la = line.split("\t")
        if la[3] != "" and la[3] != "Part1":
            codes.append({'code':la[3], 'code3':la[1], 'lang':la[6]})
    return codes

def get_locales():
    codes = []
    for code in Locale().getAvailableLocales():
        codes.append({'code': code, 'lang': Locale(code).getDisplayName()})
    return codes

def getLocale(configs):
    locale = 'en'
    if "locale" in configs["titling"] and configs["titling"]["locale"] != "":
        locale = configs["titling"]["locale"]
    return locale

def preprocessLex0(entryXml):
    from xml.dom import minidom, Node
    doc = minidom.parseString(entryXml)
    headword = None
    for el in doc.getElementsByTagName("form"):
        if el.getAttribute("type") == "lemma":
            for el2 in el.getElementsByTagName("orth"):
                headword = el2.firstChild.nodeValue
    if headword and headword != "":
        he = doc.createElement("headword")
        het = doc.createTextNode(headword)
        doc.documentElement.appendChild(he)
        he.appendChild(het)
    return doc.toxml().replace('<?xml version="1.0" ?>', '').strip()


def elexisDictAbout(dictID):
    dictDB = getDB(dictID)
    if dictDB:
        info = {"id": dictID}
        configs = readDictConfigs(dictDB)
        configs = loadHandleMeta(configs)
        if configs["metadata"].get("dc.language.iso") and len(configs["metadata"]["dc.language.iso"]) > 0:
            info["sourceLanguage"] = configs["metadata"]["dc.language.iso"][0]
            info["targetLanguage"] = configs["metadata"]["dc.language.iso"]
        elif configs['ident'].get('lang'):
            info["sourceLanguage"] = configs['ident'].get('lang')
            info["targetLanguage"] = [configs['ident'].get('lang')]
        else:
            info["sourceLanguage"] = 'en'
            info["targetLanguage"] = ['en']
        if configs["metadata"].get("dc.rights"):
            if configs["metadata"].get("dc.rights.label") == "PUB":
                info["release"] = "PUBLIC"
                if configs["metadata"].get("dc.rights.uri") != "":
                    info["license"] = configs["metadata"].get("dc.rights.uri")
                else:
                    info["license"] = configs["metadata"].get("dc.rights")
            else:
                info["release"] = "PRIVATE"
                info["license"] = ""
        else:
            if configs["publico"]["public"]:
                info["release"] = "PUBLIC"
                info["license"] = configs["publico"]["licence"]
                if siteconfig["licences"][configs["publico"]["licence"]]:
                    info["license"] = siteconfig["licences"][configs["publico"]["licence"]]["url"]
            else:
                info["release"] = "PRIVATE"
        info["creator"] = []
        info["publisher"] = []
        if configs["metadata"].get("dc.contributor.author"):
            for auth in configs["metadata"]["dc.contributor.author"]:
                info["creator"].append({"name": auth})
        else:
            for user in configs["users"]:
                info["creator"].append({"email": user})
        if configs["metadata"].get("dc.publisher"):
            info["publisher"] = [{"name": configs["metadata"]["dc.publisher"]}]
        if configs["metadata"].get("dc.title"):
            info["title"] = configs["metadata"]["dc.title"]
        else:
            info["title"] = configs["ident"]["title"]
        if configs["metadata"].get("dc.description"):
            info["abstract"] = configs["metadata"]["dc.description"]
        else:
            info["abstract"] = configs["ident"]["blurb"]
        if configs["metadata"].get("dc.date.issued"):
            info["issued"] = configs["metadata"]["dc.date.issued"]
        info["genre"] = ["gen"]
        if configs["metadata"].get("dc.subject"):
            info["subject"] = '; '.join(configs["metadata"]["dc.subject"])
            if "terminolog" in info["subject"]:
                info["genre"].append("trm")
            if "etymolog" in info["subject"]:
                info["genre"].append("ety")
            if "historical" in info["subject"]:
                info["genre"].append("his")
        c = dictDB.execute("select count(*) as total from entries")
        r = c.fetchone()
        info["entryCount"] = r['total']
        return info
    else:
        return None

# def elexisLemmaList(dictID, limit=None, offset=0):
#     dictDB = getDB(dictID)
#     if dictDB:
#         info = {"language": "en", "release": "PRIVATE"}
#         configs = readDictConfigs(dictDB)
#         configs = loadHandleMeta(configs)
#         if configs["metadata"].get("dc.language.iso") and len(configs["metadata"]["dc.language.iso"]) > 0:
#             info["language"] = configs["metadata"]["dc.language.iso"][0]
#         elif configs['ident'].get('lang'):
#             info["language"] = configs['ident'].get('lang')
#         if configs["metadata"].get("dc.rights"):
#             if configs["metadata"].get("dc.rights.label") == "PUB":
#                 info["release"] = "PUBLIC"
#             else:
#                 info["release"] = "PRIVATE"
#         else:
#             if configs["publico"]["public"]:
#                 info["release"] = "PUBLIC"
#             else:
#                 info["release"] = "PRIVATE"
#         lemmas = []
#         query = "SELECT id, xml FROM entries"
#         if limit != None and limit != "":
#             query += " LIMIT "+str(int(limit))
#         if offset != "" and int(offset) > 0:
#             query += " OFFSET "+str(int(offset))
#         c = dictDB.execute(query)
#         formats = []
#         firstentry = True
#         for r in c.fetchall():
#             if firstentry:
#                 firstentry = False
#                 jsonentry = elexisConvertTei(r["xml"])
#                 if jsonentry != None:
#                     formats = ["tei", "json"]
#             lemma = {"release": info["release"], "language": info["language"], "formats": formats}
#             lemma["id"] = str(r["id"])
#             lemma["lemma"] = getEntryHeadword(r["xml"], configs["titling"].get("headword"))
#             pos = elexisGuessPOS(r["xml"])
#             if pos != "":
#                 lemma["partOfSpeech"] = [pos]
#             lemmas.append(lemma)
#         return lemmas
#     else:
#         return None


# def elexisGuessPOS(xml):
#     # try to guess frequent PoS element
#     pos = ""
#     if "</pos>" in xml:
#         arr = extractText(xml, "pos")
#         if arr[0] and arr[0] != "":
#             pos = arr[0]
#     if "<partOfSpeech>" in xml:
#         arr = extractText(xml, "partOfSpeech")
#         if arr[0] and arr[0] != "":
#             pos = arr[0]
#     if 'type="pos"' in xml:
#         pat = r'<gram[^>]*type="pos"[^>]*>([^<]*)</gram>'
#         arr = re.findall(pat, xml)
#         if arr and arr[0] and arr[0] != "":
#             pos = arr[0]
#     return pos

def getEntry(dictID, entryID, out_format):
    dictDB = getDB(dictID)
    if dictDB:
        query = "SELECT id, %s FROM entries WHERE id=?" % (out_format)
        c = dictDB.execute(query, (entryID, ))
        r = c.fetchone()
        if not r:
            return None
        else:
            return r[out_format]
    else:
        return None

def loadHandleMeta(configs):
    configs["metadata"] = {}
    if configs["ident"].get("handle") and "hdl.handle.net" in configs["ident"].get("handle"):

        handle = configs["ident"].get("handle").replace("hdl.handle.net", "hdl.handle.net/api/handles")
        res = requests.get(handle)
        data = res.json()
        if data.get('values') and data["values"][0] and data["values"][0]["type"] == "URL":
            repourl = data["values"][0]["data"]["value"].replace("xmlui", "rest")
            res2 = requests.get(repourl)
            data2 = res2.json()
            if data2.get("id") != "":
                urlparsed = urllib.parse.urlparse(repourl)
                repourl2 = urlparsed.scheme + "://" + urlparsed.hostname + "/repository/rest/items/" + str(data2["id"]) + "/metadata"
                res3 = requests.get(repourl2)
                data3 = res3.json()
                for item in data3:
                    if item["key"] == "dc.contributor.author" or item["key"] == "dc.subject" or item["key"] == "dc.language.iso":
                        if not configs["metadata"].get(item["key"]):
                            configs["metadata"][item["key"]] = []
                        configs["metadata"][item["key"]].append(item["value"])
                    else:
                        configs["metadata"][item["key"]] = item["value"]
    return configs

def elexisConvertTei(xml_entry):
    """Convert a TEI entry into Json, return None if not TEI
    xml_entry: The entry as a string"""
    from io import BytesIO
    from lxml import etree as ET

    try:
        # strip NS
        it = ET.iterparse(BytesIO(xml_entry.encode("UTF-8")), recover=True)
        for _, el in it:
            _, _, el.tag = el.tag.rpartition('}')
        doc = it.root

        entry = {}
        for form_elem in doc.iter("form"):
            if form_elem.attrib["type"] == "lemma":
                for orth_elem in form_elem.iter("orth"):
                    if "canonicalForm" not in entry:
                        entry["canonicalForm"] = {"writtenRep": orth_elem.text}
        for gramgrp_elem in doc.iter("gramGrp"):
            for gram in gramgrp_elem.iter("gram"):
                if gram.attrib["type"] == "pos":
                    if "norm" in gram.attrib:
                        entry["partOfSpeech"] = elexisNormalisePos(gram.attrib["norm"])
                    else:
                        entry["partOfSpeech"] = elexisNormalisePos(gram.text)

        entry["senses"] = []
        for sense_elem in doc.iter("sense"):
            sense = {}
            for defn in sense_elem.iter("def"):
                sense["definition"] = defn.text
            entry["senses"].append(sense)
        if "canonicalForm" in entry:
            return entry
        else:
            return None
    except Exception as e:
        return None

def elexisNormalisePos(pos):
    if pos in ["adjective", "adposition", "adverb", "auxiliary",
            "coordinatingConjunction", "determiner", "interjection",
            "commonNoun", "numeral", "particle", "pronoun", "properNoun",
            "punctuation", "subordinatingConjunction", "symbol", "verb",
            "other"]:
        return pos
    pos = pos.upper().strip(' .')
    if pos == "ADJ":
        return "adjective"
    elif pos == "ADP":
        return "adposition"
    elif pos == "ADV":
        return "adverb"
    elif pos == "AUX" :
        return "auxiliary"
    elif pos == "CCONJ" :
        return "coordinatingConjunction"
    elif pos == "DET":
        return "determiner"
    elif pos == "INTJ" :
        return "interjection"
    elif pos == "NN":
        return "commonNoun"
    elif pos == "NOUN":
        return "commonNoun"
    elif pos == "NUM":
        return "numeral"
    elif pos == "PART":
        return "particle"
    elif pos == "PRON":
        return "pronoun"
    elif pos == "PROPN":
        return "properNoun"
    elif pos == "PUNCT":
        return "punctuation"
    elif pos == "SCONJ":
        return "subordinatingConjunction"
    elif pos == "SYM":
        return "symbol"
    elif pos == "VB":
        return "verb"
    elif pos == "VERB":
        return "verb"
    elif pos == "X":
        return "other"
    else:
        return "other"

def replaceN(some_str, original, replacement, n):
    all_replaced = some_str.replace(original, replacement)
    for i in range(n):
        first_originals_back = all_replaced.replace(replacement, original, i)
    return first_originals_back

def dql2sqliteToken(token):
    match token:
        case _ if '!=' in token:
            # !=
            parts = token.split('!=')
            operator = '!='
            path = parts[0]
            value = parts[1]
        case _ if '~=' in token:
            #regex
            parts = token.split('~=')
            operator = '~='
            path = parts[0]
            value = parts[1]
        case _ if '#=' in token:
            #count
            parts = token.split('#=')
            operator = '#='
            path = parts[0]
            value = parts[1]
        case _ if '#>' in token:
            #count
            parts = token.split('#>')
            operator = '#>'
            path = parts[0]
            value = parts[1]
        case _ if '=' in token:
            # =
            parts = token.split('=')
            operator = '='
            path = parts[0]
            value = parts[1]
        case _:
            operator = 'exist'
            path = token.strip()
            value = ''

    fullpath = replaceN(path, '.', '[%]%', 2)
    fullpathval = '$.' + fullpath + '[%]."_val"'

    sql = ''
    match operator:
        case '=':
            sql = "(json_tree.key='_val' AND json_tree.value = '" + value + "' AND json_tree.fullkey LIKE '" + fullpathval + "')"
        case '!=':
            sql = "(json_tree.key='_val' AND json_tree.value != '" + value + "' AND json_tree.fullkey LIKE '" + fullpathval + "')"
        case 'exist':
            sql = "(json_tree.fullkey LIKE '$." + fullpath + "[%]')"
        case '~=':
            sql = "(json_tree.key='_val' AND json_tree.value REGEXP '" + value + "' AND json_tree.fullkey LIKE '" + fullpathval + "')"
        case '#=':
            sql = "(entries.id IN (SELECT entries.id FROM entries,json_tree(entries.entry_data) WHERE json_tree.fullkey LIKE '$." + fullpath + "[%]' GROUP BY entries.id HAVING COUNT(json_tree.key)=" + value + "))"
        case '#>':
            sql = "(entries.id IN (SELECT entries.id FROM entries,json_tree(entries.entry_data) WHERE json_tree.fullkey LIKE '$." + fullpath + "[%]' GROUP BY entries.id HAVING COUNT(json_tree.key)>" + value + "))"

    return sql

def parse_nested(text, left=r'[(]', right=r'[)]', sep=r' '):
    pat = r'({}|{}|{})'.format(left, right, sep)
    tokens = re.split(pat, text)
    stack = [[]]
    for x in tokens:
        if not x or re.match(sep, x): continue
        if re.match(left, x):
            stack[-1].append([])
            stack.append(stack[-1][-1])
        elif re.match(right, x):
            stack.pop()
            if not stack:
                raise ValueError('error: opening bracket is missing')
        else:
            stack[-1].append(x)
    if len(stack) > 1:
        print(stack)
        raise ValueError('error: closing bracket is missing')
    return stack.pop()

def parse_level(query_list):
    result_list = []
    for token in query_list:
        if type(token) == list:
            result_list.append(parse_level(token))
        else:
            if token == 'and' or token == 'or':
                result_list.append(token)
            else:
                result_list.append(dql2sqliteToken(token))
    return '(' + ' '.join(result_list) + ')'

def dql2sqlite(query): # TODO search
    parsed_query = parse_nested(query)
    sql = "select distinct json_extract(entries.entry_data,'$.hw.lemma') from entries, json_tree(entries.entry_data) where " + parse_level(parsed_query) + " limit 10;"
    return sql

def nvh2jsonDump(entryNvh):
    if type(entryNvh) == str:
        entryNvh = nvh.parse_string(entryNvh)
    else:
        entryNvh = nvh.parse_string(entryNvh.dump_string())
    jsonEntry = nvh2jsonNode(entryNvh)
    return json.dumps(jsonEntry)

def nvh2json(entryNvh):
    if type(entryNvh) == str:
        entryNvh = nvh.parse_string(entryNvh)
    else:
        entryNvh = nvh.parse_string(entryNvh.dump_string())
    jsonEntry = nvh2jsonNode(entryNvh)
    return jsonEntry

def nvh2jsonNode(nvhNode):
    data_obj = {}

    p = nvhNode.parent
    curr_path = [nvhNode.name]
    while p and p.name!='':
        curr_path.insert(0, p.name)
        p = p.parent
    parent_name = '.'.join(curr_path)
    data_obj['_name'] = nvhNode.name

    if nvhNode.value:
        data_obj['_value'] = nvhNode.value
    for c in nvhNode.children:
        path = parent_name + '.' if parent_name else ''
        if not data_obj.get(path + c.name):
            data_obj[path + c.name] = []
        data_obj[path + c.name].append(nvh2jsonNode(c))
    return data_obj

def json2nvhLevel(jsonNode, nvhParent, paths=False):
    for key, val in jsonNode.items():
        if key != "_value" and key != "_name":
            if paths:
                new_key = key.strip().split('.')[-1]
            else:
                new_key = key
            for item in val:
                indent = nvhParent.indent+"  " if nvhParent.parent else ""
                value = item["_value"] if item.get("_value") else ""
                newNode = json2nvhLevel(item, nvh(nvhParent, indent, new_key, value), paths)
                nvhParent.children.append(newNode)
    return nvhParent

def json2nvh_str(jsonEntry, paths=False):
    if type(jsonEntry) == str:
        jsonEntry = json.loads(jsonEntry)
    entryNvh = json2nvhLevel(jsonEntry,nvh(None), paths)
    nvh_str = entryNvh.dump_string()
    return nvh_str

def json2nvh(jsonEntry, paths=False):
    if type(jsonEntry) == str:
        jsonEntry = json.loads(jsonEntry, paths)
    return json2nvhLevel(jsonEntry,nvh(None))
