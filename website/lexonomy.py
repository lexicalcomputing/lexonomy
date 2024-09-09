#!/usr/bin/python3.10

import os
import sys
import functools
import ops
import project
import advance_search
import re
import jwt
import json
from nvh import nvh
import urllib.request
from ops import siteconfig
import media
import bottle
from bottle import (hook, route, get, post, run, template, error, request,
                    response, static_file, abort, redirect, install)

# configuration
application = app = bottle.default_app()
app.config['autojson'] = True
bottle.BaseRequest.MEMFILE_MAX = 10 * 1024 * 1024 #10MB upload
my_url = siteconfig["baseUrl"].split("://")[1].rstrip("/")
cgi = False
if "SERVER_NAME" in os.environ and "SERVER_PORT" in os.environ:
    my_url = os.environ["SERVER_NAME"] + ":" + os.environ["SERVER_PORT"]
    cgi = True
if "HTTPS" in os.environ and os.environ["HTTPS"] == "on":
    my_base_url = "https://" + my_url + "/"
else:
    my_base_url = "http://" + my_url + "/"

# command-line arguments (unless CGI)
if not cgi and len(sys.argv) > 1:
    if sys.argv[1] in ["-h", "--help"] or len(sys.argv) != 2:
        print("Usage: %s SERVER:PORT, which default to %s" % (sys.argv[0], my_url), file=sys.stderr)
        print(sys.argv, file=sys.stderr)
        sys.exit(1)
    my_url = sys.argv[1]

currdir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(currdir, 'version.txt')) as v_f:
    version = v_f.readline().strip()

# serve static files
@route('/<path:re:(furniture|customization|libs|index.*\.html|config\.js|bundle\.js|bundle\.static\.js|bundle\.css|riot|img|js|css|docs|version\.txt).*>')
def server_static(path):
    return static_file(path, root="./")

# ignore trailing slashes, urldecode cookies
@hook('before_request')
def strip_path():
    request.environ['PATH_INFO'] = request.environ['PATH_INFO'].rstrip('/')
    from urllib.parse import unquote
    for c in request.cookies:
        request.cookies[c] = unquote(request.cookies[c])

# profiler
def profiler(callback):
    def wrapper(*args, **kwargs):
        if request.query.prof:
            import cProfile, pstats, io
            profile = cProfile.Profile()
            profile.enable()
        body = callback(*args, **kwargs)
        if request.query.prof:
            profile.disable()
            output = io.StringIO()
            profstats = pstats.Stats(profile, stream=output)
            output.write("<pre>")
            profstats.sort_stats('time','calls').print_stats(50)
            profstats.sort_stats('cumulative').print_stats(50)
            output.write("</pre>")
            return output.getvalue()
        return body
    return wrapper
install(profiler)

# authentication decorator
# use @authDict(["canEdit", "canConfig", "canUpload", "canDownload"]) before any handler
# to ensure that user has appropriate access to the dictionary. Empty list checks read access only.
# assumes <dictID> in route and "dictID", "user", "dictDB", "configs" as parameters in the decorated function
# <dictID> gets open and passed as dictDB alongside the configs
def authDict(checkRights, errorRedirect=False):
    def wrap(func):
        @functools.wraps(func)
        def wrapper_verifyLoginAndDictAccess(*args, **kwargs):
            try:
                conn = ops.getDB(kwargs["dictID"])
            except IOError:
                abort(404, "No such dictionary")
            res, configs = ops.verifyLoginAndDictAccess(request.cookies.email, request.cookies.sessionkey, conn)
            for r in checkRights:
                if not res.get(r, False):
                    if errorRedirect:
                        redirect("/#"+kwargs["dictID"])
                    else:
                        return res
            kwargs["user"] = res
            kwargs["dictDB"] = conn
            kwargs["configs"] = configs
            return func(*args, **kwargs)
        return wrapper_verifyLoginAndDictAccess
    return wrap

# authentication decorator
# use @auth to check that user is authenticated
# assumes that the decorated function has a "user" parameter which is used to pass the user info
def auth(func, errorRedirect=False):
    @functools.wraps(func)
    def wrapper_verifyLogin(*args, **kwargs):
        res = ops.verifyLogin(request.cookies.email, request.cookies.sessionkey)
        if not res["loggedin"]:
            if errorRedirect:
                redirect("/")
            else:
                return res
        kwargs["user"] = res
        return func(*args, **kwargs)
    return wrapper_verifyLogin

# authentication decorator
# use @authProject to check that user is authenticated and have access to certain projects
# assumes that the decorated function has a "user" parameter which is used to pass the user info
def authProject(func):
    @functools.wraps(func)
    def wrapper_verifyProject(*args, **kwargs):
        res, configs = ops.verifyLoginAndProjectAccess(request.cookies.email, request.cookies.sessionkey)
        if not res["loggedin"]:
            redirect("/")
        kwargs["user"] = res
        kwargs["configs"] = configs
        return func(*args, **kwargs)
    return wrapper_verifyProject


# admin authentication decorator
# use @auth to check that user is authenticated and admin
# assumes that the decorated function has a "user" parameter which is used to pass the user info
def authAdmin(func):
    @functools.wraps(func)
    def wrapper_verifyLoginAdmin(*args, **kwargs):
        res = ops.verifyLogin(request.cookies.email, request.cookies.sessionkey)
        if not res["loggedin"] or not res["isAdmin"]:
            redirect("/")
        kwargs["user"] = res
        return func(*args, **kwargs)
    return wrapper_verifyLoginAdmin

#homepage
@get(siteconfig["rootPath"])
def home():
    return static_file("/index.html", root="./")

@get(siteconfig["rootPath"] + "siteconfigread.json") # OK
def lexonomyconfig():
    configData = {
        "licences": siteconfig['licences'],
        "baseUrl": siteconfig['baseUrl'],
        "ske_url": siteconfig['ske_url'],
        "api_url": siteconfig['api_url'],
        "langs": ops.get_iso639_1(),
        "version": version,
        "customStyle": siteconfig.get("customStyle"),
        "disableRegistration": siteconfig.get("disableRegistration", False),
        "sketchengineLoginPage": siteconfig.get("sketchengineLoginPage"),
        "showDictionaryNameInPageTitle": siteconfig.get("showDictionaryNameInPageTitle"),
        "notification": siteconfig.get("notification"),
        "homepage": siteconfig.get("homepage")
    }
    if "consent" in siteconfig and siteconfig["consent"].get("terms") != "":
        configData["consent"] = siteconfig["consent"]
    return configData

@post(siteconfig["rootPath"]+"feedback.json")
def sendfeedback():
    if request.forms.email != "" and request.forms.text != "":
        ops.sendFeedback(request.forms.email, request.forms.text)
        return {"success": True}
    else:
        return {"success": False, "error": "missing parameters"}

@get(siteconfig["rootPath"] + "schemaitems.json") # OK
def schemaitems():
    return {"items": ops.getSchemaItems()}

@post(siteconfig["rootPath"] + "schemafinal.json") # OK
def schemafinal():
    return {"schemafinal": ops.mergeSchemaItems(json.loads(request.forms.schema_items))}

@post(siteconfig["rootPath"] + "schema_to_json.json") # OK
def schema_to_json():
    schema = nvh.parse_string(json.loads(request.forms.schema))
    schema_dict: dict = {}
    schema.build_json(schema_dict)
    return {"schemajson": json.dumps(schema_dict)}

@get(siteconfig["rootPath"] + "userdicts.json")
@auth
def listuserdicts(user):
    dicts = ops.getDictsByUser(user["email"])
    return {"dicts": dicts}

@post(siteconfig["rootPath"] + "<dictID>/entrydelete.json")
@authDict(["canEdit"])
def entrydelete(dictID, user, dictDB, configs):
    ops.deleteEntry(dictDB, request.forms.id, user["email"])
    return {"success": True, "id": request.forms.id}

@post(siteconfig["rootPath"]+"<dictID>/entryread.json")
@authDict([])
def entryread(dictID, user, dictDB, configs):
    adjustedEntryID, nvh, json, _title = ops.readEntry(dictDB, configs, request.forms.id)
    adjustedEntryID = int(adjustedEntryID)
    return {"success": (adjustedEntryID > 0), "id": adjustedEntryID, "nvh": nvh, "json": json}

@post(siteconfig["rootPath"]+"<dictID>/entryupdate.json")
@authDict(["canEdit"])
def entryupdate(dictID, user, dictDB, configs):
    adjustedEntryID, adjustedNvh, changed, feedback = ops.updateEntry(dictDB, configs, request.forms.id, request.forms.nvh, user["email"], {})
    result = {"success": True, "id": adjustedEntryID, "content": adjustedNvh}
    if feedback:
        result["feedback"] = feedback
    return result

@post(siteconfig["rootPath"]+"<dictID>/entrycreate.json")
@authDict(["canEdit"])
def entrycreate(dictID, user, dictDB, configs):
    adjustedEntryID, adjustedNvh, feedback = ops.createEntry(dictDB, configs, None, request.forms.nvh, request.forms.json, user["email"], {})
    result = {"success": True, "id": adjustedEntryID, "content": adjustedNvh}
    if feedback:
        result["feedback"] = feedback
    return result

@post(siteconfig["rootPath"]+"<dictID>/entryflag.json")
@authDict(["canEdit"])
def entryflag(dictID, user, dictDB, configs):
    success, error = ops.flagEntry(dictDB, configs, request.forms.id, json.loads(request.forms.flags), user["email"], {})
    return {"success": success, "id": request.forms.id, 'error': error}

@get(siteconfig["rootPath"]+"<dictID>/subget")
@authDict(["canEdit"])
def subget(dictID, user, dictDB, configs):
    total, entries, first = ops.listEntries(dictDB, dictID, configs, request.query.doctype, request.query.lemma, "wordstart", 100, 0, False, False, True)
    return {"success": True, "total": total, "entries": entries}

@post(siteconfig["rootPath"]+"<dictID>/history.json")
def history(dictID):
    if not ops.dictExists(dictID):
        return redirect("/")
    user, configs = ops.verifyLoginAndDictAccess(request.cookies.email, request.cookies.sessionkey, ops.getDB(dictID))
    history = ops.readDictHistory(ops.getDB(dictID), dictID, configs, request.forms.id)
    res_history = []
    for item in history:
        res_history.append(item)
    return {"history":res_history}

@post(siteconfig["rootPath"] + "consent.json")
@auth
def save_consent(user):
    res = ops.setConsent(user["email"], request.forms.consent)
    return {"success": res}

@get(siteconfig["rootPath"] + "<dictID>/getmedia/<query>")
@authDict(["canEdit"])
def getmedia(dictID, query, user, dictDB, configs):
    res = media.get_images(configs, query)
    return {"images": res}

@get(siteconfig["rootPath"] + "<dictID>/skeget/corpora") # TODO fix for referene corpora for projects
@authDict([])
def skeget_corpora(dictID, user, dictDB, configs):
    import base64
    apiurl = "https://api.sketchengine.eu/"
    if configs.get("ske") and configs["ske"].get("apiurl") != "":
        apiurl = configs["ske"].get("apiurl").replace("bonito/run.cgi", "")
    req = urllib.request.Request(apiurl + "/ca/api/corpora",
                                  headers = {"Authorization": "Basic " + base64.b64encode(str.encode(str(user['ske_username'])+':'+str(user['ske_apiKey']))).decode('ascii')})
    ske_response = urllib.request.urlopen(req)
    response.headers['Content-Type'] = ske_response.getheader('Content-Type')
    return ske_response

@get(siteconfig["rootPath"] + "user_corpora.json")
@auth
def user_corpora(user):
    import base64
    apiurl = siteconfig["api_url"].replace("bonito/run.cgi", "")
    req = urllib.request.Request(apiurl + "/ca/api/corpora",
                                  headers = {"Authorization": "Basic " + base64.b64encode(str.encode(str(user['ske_username'])+':'+str(user['ske_apiKey']))).decode('ascii')})
    ske_response = urllib.request.urlopen(req)
    response.headers['Content-Type'] = ske_response.getheader('Content-Type')
    return ske_response

@get(siteconfig["rootPath"] + "<dictID>/skeget/examples")
@authDict(["canEdit"])
def skeget_xampl(dictID, user, dictDB, configs):
    url = request.query.url
    url += "/view"
    url += "?corpname=" + urllib.parse.quote_plus(request.query.corpus)
    url += "&username=" + request.query.username
    url += "&api_key=" + request.query.apikey
    url += "&format=json"
    if request.query.querytype == "skesimple":
        url += "&q=q[lemma=\"" + urllib.parse.quote_plus(request.query.query) + "\"]"
    else:
        url += "&q=q" + urllib.parse.quote_plus(request.query.query)
    url += "&viewmode=sen"
    url += "&q=e500"
    url += "&async=0"
    if request.query.fromp:
        url += "&" + request.query.fromp
    req = urllib.request.Request(url, headers = {"Authorization": "Bearer " + request.query.apikey})
    res = urllib.request.urlopen(req)
    data = json.loads(res.read())
    return data

@get(siteconfig["rootPath"] + "<dictID>/skeget/thesaurus")
@authDict(["canEdit"])
def skeget_thes(dictID, user, dictDB, configs):
    url = request.query.url
    url += "/thes"
    url += "?corpname=" + urllib.parse.quote_plus(request.query.corpus)
    url += "&username=" + request.query.username
    url += "&api_key=" + request.query.apikey
    url += "&format=json"
    url += "&lemma=" + urllib.parse.quote_plus(request.query.lemma)
    if request.query.fromp:
        url += "&" + request.query.fromp
    req = urllib.request.Request(url, headers = {"Authorization": "Bearer " + request.query.apikey})
    res = urllib.request.urlopen(req)
    data = json.loads(res.read())
    return data

@get(siteconfig["rootPath"] + "<dictID>/skeget/collocations")
@authDict(["canEdit"])
def skeget_collx(dictID, user, dictDB, configs):
    url = request.query.url
    url += "/wsketch"
    url += "?corpname=" + urllib.parse.quote_plus(request.query.corpus)
    url += "&username=" + request.query.username
    url += "&api_key=" + request.query.apikey
    url += "&format=json"
    url += "&lemma=" + urllib.parse.quote_plus(request.query.lemma)
    url += "&structured=0"
    if request.query.fromp:
        url += "&" + request.query.fromp
    req = urllib.request.Request(url, headers = {"Authorization": "Bearer " + request.query.apikey})
    res = urllib.request.urlopen(req)
    data = json.loads(res.read())
    return data

@get(siteconfig["rootPath"] + "<dictID>/skeget/definitions")
@authDict(["canEdit"])
def skeget_defo(dictID, user, dictDB, configs):
    url = request.query.url
    url += "/view"
    url += "?corpname=" + urllib.parse.quote_plus(request.query.corpus)
    url += "&username=" + request.query.username
    url += "&api_key=" + request.query.apikey
    url += "&format=json"
    url += "&q=" + urllib.parse.quote_plus(ops.makeQuery(request.query.lemma))
    url += "&q=p+0+0>0+1+[ws(\".*\",\"definitions\",\".*\")]"
    url += "&viewmode=sen"
    if request.query.fromp:
        url += "&" + request.query.fromp
    req = urllib.request.Request(url, headers = {"Authorization": "Bearer " + request.query.apikey})
    res = urllib.request.urlopen(req)
    data = json.loads(res.read())
    return data

@get(siteconfig["rootPath"] + "<dictID>/kontext/corpora")
@authDict([])
def kontext_corpora(dictID, user, dictDB, configs):
    kontexturl = "https://www.clarin.si/kontext/"
    if configs.get("kontext") and configs["kontext"].get("url") != "":
        kontexturl = configs["kontext"].get("url")
    kontexturl += "corpora/ajax_list_corpora?requestable=1"
    requrl = kontexturl
    loadmore = True
    corpus_list = []
    while loadmore:
        res = urllib.request.urlopen(requrl)
        data = json.loads(res.read())
        if data["nextOffset"] != None:
            requrl = kontexturl + "&offset=" + str(data["nextOffset"])
            corpus_list += data["rows"]
        else:
            loadmore = False
    return {"corpus_list": corpus_list}

@get(siteconfig["rootPath"] + "<dictID>/kontext/conc")
@authDict([])
def kontext_xampl(dictID, user, dictDB, configs):
    kontexturl = configs["kontext"].get("url") + "query_submit?format=json"
    corpus = configs["kontext"].get("corpus")
    if request.query.querytype == "kontextcql":
        cql = urllib.parse.quote_plus(request.query.query)
    else:
        cql = '[word=\"' + urllib.parse.quote_plus(request.query.query) + '\"]'
    request_data = {
        "type": "concQueryArgs",
        "maincorp": configs["kontext"].get("corpus"),
        "viewmode": "sen",
        "pagesize": 40,
        "fromp": 0,
        "queries": [{
            "qtype": "advanced",
            "corpname": configs["kontext"].get("corpus"),
            "query": cql,
            "pcq_pos_neg": "pos",
            "include_empty": False,
            "default_attr":"word"
        }],
        "text_types": {},
        "context":  {
            "fc_lemword_wsize": [-5, 5],
            "fc_lemword": "",
            "fc_lemword_type": "all",
            "fc_pos_wsize": [-5, 5],
            "fc_pos": [],
            "fc_pos_type": "all"
        },
        "async": False
    }
    if request.query.fromp:
        request_data['fromp'] = int(request.query.fromp)
    req = urllib.request.Request(kontexturl)
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    jsondata = json.dumps(request_data)
    jsondataasbytes = jsondata.encode('utf-8')
    req.add_header('Content-Length', len(jsondataasbytes))
    res = urllib.request.urlopen(req, jsondataasbytes)
    data = json.loads(res.read())
    concurl = configs["kontext"].get("url") + 'view?corpname=' + configs["kontext"].get("corpus") + '&viewmode=sen&q=' + data['Q'][0]
    if request.query.fromp:
        concurl += '&fromp=' + request.query.fromp
    if request.query.redir and request.query.redir == '1':
        return redirect(concurl)
    concurl += '&format=json'
    res = urllib.request.urlopen(concurl)
    data = json.loads(res.read())
    return data

@post(siteconfig["rootPath"] + "login.json")
def check_login():
    if request.forms.email != "" and request.forms.password != "":
        res = ops.login(request.forms.email, request.forms.password)
        if res["success"]:
            #response.set_cookie("email", res["email"], path="/")
            #response.set_cookie("sessionkey", res["key"], path="/")
            response.add_header('Set-Cookie', "email=\""+res["email"]+"\"; Path=/; SameSite=None; Secure")
            response.add_header('Set-Cookie', "sessionkey="+res["key"]+"; Path=/; SameSite=None; Secure")
            return {"success": True, "email": res["email"], "sessionkey": res["key"], "ske_username": res["ske_username"], "ske_apiKey": res["ske_apiKey"], "apiKey": res["apiKey"], "consent": res["consent"], "isAdmin": res["isAdmin"], "isProjectManager": res["isProjectManager"]}
    res = ops.verifyLogin(request.cookies.email, request.cookies.sessionkey)
    if res["loggedin"]:
        return {"success": True, "email": res["email"], "sessionkey": request.cookies.sessionkey, "ske_username": res["ske_username"], "ske_apiKey": res["ske_apiKey"], "apiKey": res["apiKey"], "consent": res["consent"], "isAdmin": res["isAdmin"], "isProjectManager": res["isProjectManager"]}
    return {"success": False}

@post(siteconfig["rootPath"] + "logout.json")
@auth
def do_logout(user):
    ops.logout(user)
    response.delete_cookie("email", path="/")
    response.delete_cookie("sessionkey", path="/")
    return {"success": False}

@get(siteconfig["rootPath"] + "logout")
@auth
def logout(user):
    ops.logout(user)
    if not "Referer" in request.headers:
        referer = "/"
    elif re.search(r"/logout/$",request.headers["Referer"]):
        referer = "/"
    else:
        referer = request.headers["Referer"]
    response.delete_cookie("email", path="/")
    response.delete_cookie("sessionkey", path="/")
    return redirect(referer)

@post(siteconfig["rootPath"] + "verifytoken.json")
def verify_token():
    valid = ops.verifyToken(request.forms.token, request.forms.type)
    return {"success": valid}

@post(siteconfig["rootPath"] + "signup.json")
def send_signup():
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
    res = ops.sendSignupToken(request.forms.email, client_ip)
    return {"success": res}

@post(siteconfig["rootPath"] + "createaccount.json")
def do_create_account():
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
    res = ops.createAccount(request.forms.token, request.forms.password, client_ip)
    return {"success": res}

@post(siteconfig["rootPath"] + "forgotpwd.json")
def forgotpwd(): # OK
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
    res = ops.sendToken(request.forms.email, client_ip)
    return {"success": res}

@post(siteconfig["rootPath"] + "recoverpwd.json")
def do_recover_pwd(): #OK
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
    res = ops.resetPwd(request.forms.token, request.forms.password, client_ip)
    return {"success": res}

@get(siteconfig["rootPath"] + "makesuggest.json")
@auth
def makedict(user):
    return {"baseUrl": siteconfig['baseUrl'], "suggested": ops.suggestDictId()}

@post(siteconfig["rootPath"] + "make.json")
@auth
def makedictjson(user):
    if request.files.get('filename'):
        upload = request.files.get("filename")
        supported_formats = re.compile('^.*\.(xml|nvh)$', re.IGNORECASE)
        if supported_formats.match(upload.filename):
            res = ops.makeDict(request.forms.url, None, None, request.forms.title,
                               request.forms.language, "", user["email"],
                               addExamples=False,
                               deduplicate=True if request.forms.deduplicate=='true' else False,
                               clean=True if request.forms.clean=='true' else False,
                               bottle_file_object=upload, hwNode=request.forms.hwNode)
        else:
            return{"success": False, "url": request.forms.url,
                   "error": 'Unsupported format for import file. An .xml or .nvh file are required.', 'msg': ''}
    else:
        res = ops.makeDict(request.forms.url, request.forms.nvhSchema, json.loads(request.forms.schemaKeys),
                           request.forms.title, request.forms.language, "", user["email"],
                           addExamples=request.forms.addExamples=="true",
                           deduplicate=False, clean=False, bottle_file_object=None, hwNode=None)
    return res

@post(siteconfig["rootPath"]+"<dictID>/clone.json")
@authDict(["canView"])
def clonedict(dictID, user, dictDB, configs):
    res = ops.cloneDict(dictID, user["email"])
    res["dicts"] = ops.getDictsByUser(user["email"])
    return res

@post(siteconfig["rootPath"]+"<dictID>/destroy.json")
@authDict(["canConfig"])
def destroydict(dictID, user, dictDB, configs):
    res = ops.destroyDict(dictID)
    return {"success": res, "dicts": ops.getDictsByUser(user["email"])}

@post(siteconfig["rootPath"]+"<dictID>/move.json")
@authDict(["canConfig"])
def movedict(dictID, user, dictDB, configs):
    res = ops.moveDict(dictID, request.forms.url)
    return {"success": res}

@post(siteconfig["rootPath"]+"exists.json")
@auth
def movedict(user):
    res = ops.checkDictExists(request.forms.url)
    return {"success": res}

@post(siteconfig["rootPath"] + "changepwd.json")
@auth
def changepwd(user):
    res = ops.changePwd(user["email"], request.forms.password)
    return {"success": res}

@post(siteconfig["rootPath"] + "changeskeusername.json")
@auth
def changeskeusername(user):
    res = ops.changeSkeUserName(user["email"], request.forms.ske_userName)
    return {"success": res}

@post(siteconfig["rootPath"] + "changeskeapi.json")
@auth
def changeskeapi(user):
    res = ops.changeSkeApiKey(user["email"], request.forms.ske_apiKey)
    return {"success": res}

@post(siteconfig["rootPath"] + "changeoneclickapi.json")
@auth
def changeoneclickapi(user):
    res = ops.updateUserApiKey(user, request.forms.apiKey)
    return {"success": res}

@get(siteconfig["rootPath"] + "skelogin.json/<token>")
def skelogin(token):
    secret = siteconfig["sketchengineKey"]
    try:
        jwtdata = jwt.decode(token, secret, audience="lexonomy.eu", algorithms="HS256")
        user = ops.verifyLogin(request.cookies.email, request.cookies.sessionkey)
        res = ops.processJWT(user, jwtdata)
        if res["success"]:
            response.set_cookie("email", res["email"].lower(), path="/")
            response.set_cookie("sessionkey", res["key"], path="/")
            if request.query.lexonomynext and request.query.lexonomynext != "":
                redirurl = request.query.lexonomynext
            else:
                redirurl = "/"
            return redirect(redirurl)
        else:
            response.set_cookie("jwt_error", str(res["error"]), path="/")
            return redirect("/")
    except Exception as e:
        return redirect("/")

@post(siteconfig["rootPath"] + "users/userlist.json") # OK
@authAdmin
def userelist(user):
    res = ops.listUsers(request.forms.searchtext, request.forms.howmany)
    return {"success": True, "entries": res["entries"], "total": res["total"]}

@post(siteconfig["rootPath"] + "users/userupdate.json") # TODO front-end
@authAdmin
def userupdate(user):
    res = ops.updateUser(request.forms.email, request.forms.password)
    return {"success": True, "id": res["email"], "content": res["info"]}

@post(siteconfig["rootPath"] + "users/usercreate.json") # TODO frontend create user add option for manager
@authAdmin
def usercreate(user):
    res = ops.createUser(request.forms.id, user, manager=request.forms.manager)
    return {"success": True, "id": res["entryID"]}

@post(siteconfig["rootPath"] + "users/userdelete.json") # OK
@authAdmin
def userdelete(user):
    res = ops.deleteUser(request.forms.id)
    return {"success": True, "id": request.forms.id}

@post(siteconfig["rootPath"] + "users/userread.json") # TODO front-end
@authAdmin
def userread(user):
    res = ops.readUser(request.forms.id)
    if res["email"] == "":
        return {"success": False}
    else:
        return {"success": True, "id": res["email"], "content": res["info"]}

# TODO project logging

@get(siteconfig["rootPath"] + "projects/suggestid.json") # OK
@auth
def project_suggestid(user):
    return {"suggested": project.suggestProjectId()}

@get(siteconfig["rootPath"] + "projects/list.json") # OK
@auth
def project_list(user):
    return project.getProjectsByUser(user)

@post(siteconfig["rootPath"] + "projects/create.json") # OK
@auth
def project_create(user):
    if user['isProjectManager'] or user['isAdmin']:
        res = project.createProject(request.forms.id, request.forms.name, request.forms.description, json.loads(request.forms.annotators),
                                    json.loads(request.forms.managers), request.forms.ref_corpus, request.forms.source_dict_id,
                                    request.forms.workflow, request.forms.language, user)
        return res
    return {"success": False, "projectID": request.forms.id, 'error': 'User is not a manager. Can not create project.'}

@post(siteconfig["rootPath"] + "projects/<projectID>/update.json")
@authProject
def project_update(projectID, user, configs):
    if projectID in configs["manager_of"] or user['isAdmin']:
        res = project.editProject(projectID, request.forms.name, request.forms.description, json.loads(request.forms.annotators),
                                  json.loads(request.forms.managers), user)
        return res
    return {"success": False, "projectID": projectID, 'error': 'User is not a manager. Can not create project.'}

@post(siteconfig["rootPath"] + "projects/<projectID>/update_source_dict.json") # OK
@authProject
def project_update_source(projectID, user, configs):
    if projectID in configs["manager_of"] or user['isAdmin']:
        res = project.update_project_source_dict(projectID, request.forms.source_dict_id)
        return res
    return {"success": False, "projectID": projectID, 'error': 'User is not a manager. Can not update project source dict.'}

@get(siteconfig["rootPath"] + "projects/<projectID>/project.json") # OK
@authProject
def project_get(projectID, user, configs):
    if project.projectExists(projectID):
        if projectID in configs["manager_of"] or user['isAdmin']:
            res = project.getProject(projectID)
            return res
        return {"success": False, "projectID": projectID, 'error': 'User is not a manager. Can not create project.'}
    return {"success": False, "projectID": projectID, 'error': 'Project does not exists'}

@post(siteconfig["rootPath"] + "projects/<projectID>/archive.json") # OK
@authProject
def project_archive(projectID, user, configs):
    if projectID in configs["manager_of"] or user['isAdmin']:
        res = project.archiveProject(projectID)
        return res
    return {"success": False, "projectID": projectID, 'error': 'User is not a manager. Can not create project.'}

@post(siteconfig["rootPath"] + "projects/<projectID>/delete.json") # OK
@authProject
def project_delete(projectID, user, configs):
    if projectID in configs["manager_of"] or user['isAdmin']:
        res = project.deleteProject(projectID)
        return res
    return {"success": False, "projectID": projectID, 'error': 'User is not a manager. Can not create project.'}

@post(siteconfig["rootPath"] + "projects/<projectID>/create_batch.json") # OK
@authProject
def create_batch(projectID, user, configs):
    if projectID in configs["manager_of"] or user['isAdmin']:
        res = project.createBatch(projectID, request.forms.stage, request.forms.size, request.forms.batch_number, user['email'])
        return res
    return {"success": False, "projectID": projectID, 'error': 'User is not a manager. Can not make batch in project.'}

@post(siteconfig["rootPath"] + "projects/<projectID>/make_stage.json") # OK
@authProject
def makeStage(projectID, user, configs):
    if projectID in configs["manager_of"] or user['isAdmin']: # TODO maybe should be alowed only to manegers by default
        res = project.makeStage(projectID, request.forms.stage, user['email'])
        return res
    return {"success": False, "projectID": projectID, 'error': 'User is not a manager. Can not make batch in project.'}

@post(siteconfig["rootPath"]+"projects/<projectID>/assign_batch.json") # OK
@authProject
def assignProjectDict(projectID, user, configs):
    if projectID in configs["manager_of"] or user['isAdmin']:
        ret = project.assignProjectDict(projectID, json.loads(request.forms.assignees))
        return ret
    return {"success": False, "projectID": projectID, 'error': 'User is not a manager. Can not make batch in project.'}


@post(siteconfig["rootPath"] + "projects/<projectID>/accept_batch.json") # OK
@authProject
def accept_batch(projectID, user, configs):
    if projectID in configs["manager_of"] or user['isAdmin']:
        res = project.acceptBatch(projectID, json.loads(request.forms.dictID_list))
        return res
    return {"success": False, "projectID": projectID, 'error': 'User is not a manager. Can not make batch in project.'}

@post(siteconfig["rootPath"] + "projects/<projectID>/reject_batch.json") # OK
@authProject
def reject_batch(projectID, user, configs):
    if projectID in configs["manager_of"] or user['isAdmin']: # TODO maybe should be alowed only to manegers by default
        res = project.rejectBatch(projectID, json.loads(request.forms.dictID_list))
        return res
    return {"success": False, "projectID": projectID, 'error': 'User is not a manager. Can not reject batch in project.'}

@post(siteconfig["rootPath"] + "projects/<projectID>/delete_batch.json") # OK
@authProject
def delete_batch(projectID, user, configs):
    if projectID in configs["manager_of"] or user['isAdmin']: # TODO maybe should be alowed only to manegers by default
        res = project.deleteBatch(projectID, json.loads(request.forms.dictID_list))
        return res
    return {"success": False, "projectID": projectID, 'error': 'User is not a manager. Can not delete batch in project.'}

@get(siteconfig["rootPath"] + "wokflows/list.json")
@auth
def workflow_list(user):
    try:
        return project.getWokflows()
    except Exception as e:
        return {"success": False, "exception": str(e)}


@post(siteconfig["rootPath"] + "dicts/dictlist.json")
@authAdmin
def dictlist(user):
    res = ops.listDicts(request.forms.searchtext, request.forms.howmany)
    return {"success": True, "entries": res["entries"], "total": res["total"]}

@post(siteconfig["rootPath"] + "dicts/dictread.json") # TODO front-end
@authAdmin
def dictread(user):
    res = ops.readDict(request.forms.id)
    if res["id"] == "":
        return {"success": False}
    else:
        return {"success": True, "id": res["id"], "content": res["dict_info"]}

@get(siteconfig["rootPath"]+"<dictID>/config.json")
def dictconfig(dictID):
    if not ops.dictExists(dictID):
        return {"success": False}
    else:
        user, configs = ops.verifyLoginAndDictAccess(request.cookies.email, request.cookies.sessionkey, ops.getDB(dictID))
        doctypes = [configs["structure"]["root"]]
        doctypes = list(set(doctypes))

        # WARNING consider if new config item does show personal data, than add to this list
        hide_items = ["siteconfig", "download", "autonumber", "users"]
        for item in hide_items:
            configs.pop(item)

        res = {"success": True, "publicInfo": {**configs["ident"], **configs["publico"]},
               "userAccess": user["dictAccess"], "configs": configs,
               "doctype": configs["structure"]["root"], "doctypes": doctypes}

        res["publicInfo"]["blurb"] = ops.markdown_text(str(configs["ident"]["blurb"] or ""))
        return res

@get(siteconfig["rootPath"]+"<dictID>/doctype.json")
def dictconfig(dictID):
    if not ops.dictExists(dictID):
        return {"success": False}
    else:
        user, configs = ops.verifyLoginAndDictAccess(request.cookies.email, request.cookies.sessionkey, ops.getDB(dictID))
        doctypes = [configs["structure"]["root"]]
        doctypes = list(set(doctypes))
        res = {"success": True, "doctype": configs["structure"]["root"], "doctypes": doctypes, "userAccess": user["dictAccess"]}
        return res

@get(siteconfig["rootPath"]+"<dictID>/<entryID:re:\d+>/nabes.json")
def publicentrynabes(dictID, entryID):
    dictDB = ops.getDB(dictID)
    user, configs = ops.verifyLoginAndDictAccess(request.cookies.email, request.cookies.sessionkey, dictDB)
    nabes = ops.readNabesByEntryID(dictDB, dictID, entryID, configs)
    return {"nabes": nabes}


@post(siteconfig["rootPath"]+"<dictID>/random.json") # OK
def publicrandom(dictID):
    if not ops.dictExists(dictID):
        return redirect("/")
    dictDB = ops.getDB(dictID)
    return ops.readRandoms(dictDB, int(request.query.limit) if request.query.limit else 10)

@post(siteconfig["rootPath"]+"<dictID>/exportconfigs.json")
@authDict(["canConfig"])
def exportconfigs(dictID, user, dictDB, configs):
    output = {}
    for configid in request.forms.configs.split(','):
        if configid == 'ske':
            output['ske'] = configs['ske']
        elif configid == 'users':
            output['users'] = ops.listDictUsers(dictID)
        else:
            output[configid] = configs[configid]
    response.set_header("Content-Disposition", "attachment; filename="+dictID+"-configs.json")
    return output

@post(siteconfig["rootPath"]+"<dictID>/importconfigs.json")
@authDict(["canConfig"])
def importconfigs(dictID, user, dictDB, configs):
    if not request.files.get("myfile"):
        return {"success": False}
    else:
        upload = request.files.get("myfile")
        # try:
        data = json.loads(upload.file.read().decode())
        resaveNeeded = False
        for key in data:
            if key == 'ske':
                adjustedJson = {}
                adjustedJson['ske'], resaveNeeded = ops.updateDictConfig(dictDB, dictID, 'ske', data['ske'])
                resaveNeeded = False
            elif key == 'users':
                # raise Exception(type(data[key]))
                old_users = ops.updateDictAccess(dictID, data[key])
                ops.notifyUsers(old_users, data[key], configs['ident'], dictID)
            elif key == 'dict_settings':
                ops.updateDictSettings(dictID, json.dumps(data[key]))
            else:
                adjustedJson, resaveNeeded = ops.updateDictConfig(dictDB, dictID, key, data[key])

        if resaveNeeded:
            configs = ops.readDictConfigs(dictDB)
            ops.resave(dictDB, dictID, configs)

        return {"success": True}
        # except:
            # return {"success": False}

@get(siteconfig["rootPath"]+"<dictID>/download.json") # OK
@authDict(["canDownload"], True)
def download(dictID, user, dictDB, configs):
    if request.query.format == 'xml':
        response.content_type = "text/xml; charset=utf-8"
        response.set_header("Content-Disposition", "attachment; filename="+dictID+".xml")
        return ops.download(dictDB, dictID, 'xml')
    elif request.query.format == 'nvh':
        response.content_type = "text/xml; charset=utf-8"
        response.set_header("Content-Disposition", "attachment; filename="+dictID+".nvh")
        return ops.download(dictDB, dictID, 'nvh')
    else:
        return {'error': 'Unsupported export type.'}

@post(siteconfig["rootPath"]+"<dictID>/import.json") # OK
@authDict(["canUpload"])
def importjson(dictID, user, dictDB, configs):
    err, msg, upload_file_path = ops.importfile(dictID, user["email"], configs['structure']['root'],
                                                deduplicate=True if request.forms.deduplicate.lower()=='true' else False,
                                                clean=True if request.forms.clean.lower()=='true' else False,
                                                purge=True if request.forms.purge.lower()=='true' else False,
                                                purge_all=True if request.forms.purge_all.lower()=='true' else False,
                                                bottle_upload_obj=request.files.get("filename"))
    return{"error": err, 'msg': msg, 'upload_file_path': upload_file_path}


@post(siteconfig["rootPath"]+"<dictID>/getImportProgress.json") # OK
@authDict(["canUpload"])
def getImportProgress(dictID, user, dictDB, configs):
    progress, finished, err, warns, upload_file_path = ops.getImportProgress(request.forms.upload_file_path)
    return{"finished": finished, "progress": progress, "error": err, "warnings": warns, 'upload_file_path': upload_file_path}


@post(siteconfig["rootPath"]+"<dictID>/<doctype>/entrylist.json") # OK
@authDict(["canEdit"])
def entrylist(dictID, doctype, user, dictDB, configs):
    if request.forms.id:
        if request.forms.id == "last":
            entryID = ops.getLastEditedEntry(dictDB, user["email"])
            return {"success": True, "entryID": entryID}
        else:
            entries = ops.listEntriesById(dictDB, request.forms.id, configs)
            return {"success": True, "entries": entries}
    elif request.forms.advance_query:
        try:
            total, entries, first = advance_search.getEntries(dictDB, configs, request.forms.advance_query, request.forms.howmany, request.forms.offset, request.forms.sortdesc, False, False)
        except ValueError as e:
            return {"success": False, "entries": [], "total": 0, "firstRun": False, "error": e}

        return {"success": True, "entries": entries, "total": total, "firstRun": first}
    else:
        total, entries, first = ops.listEntries(dictDB, dictID, configs, doctype, request.forms.searchtext, request.forms.modifier, request.forms.howmany, request.forms.offset, request.forms.sortdesc, False)
        return {"success": True, "entries": entries, "total": total, "firstRun": first}

@post(siteconfig["rootPath"]+"<dictID>/search.json")
def publicsearch(dictID):
    dictDB = ops.getDB(dictID)
    configs = ops.readDictConfigs(dictDB)
    modifier = request.forms.modifier or "start"
    howmany = request.forms.howmany or 100
    if not configs["publico"]["public"]:
        return {"success": False}
    else:
        total, entries, first = ops.listEntries(dictDB, dictID, configs, configs['structure']['root'], request.forms.searchtext, modifier, howmany, request.forms.offset)
        return {"success": True, "entries": entries, "total": total}

@post(siteconfig["rootPath"]+"<dictID>/configread.json")
@authDict(["canConfig"])
def configread(dictID, user, dictDB, configs):
    if request.forms.id == 'ske':
        config_data = configs.get('ske', None)
    else:
        if request.forms.id == 'structure' and 'structure' not in configs:
            config_data = configs['structure']
        else:
            config_data = configs[request.forms.id]
    if request.forms.id == 'ident':
        config_data['langs'] = ops.get_iso639_1()
    if request.forms.id == 'titling':
        config_data['locales'] = ops.get_locales()
    return {"success": True, "id": request.forms.id, "content": config_data}

@post(siteconfig["rootPath"]+"<dictID>/dictconfigupdate.json")
@authDict(["canConfig"])
def configupdate(dictID, user, dictDB, configs):
    if request.forms.id == 'ske':
        adjustedJson, resaveNeeded = ops.updateDictConfig(dictDB, dictID, 'ske', json.loads(request.forms.content))
    else:
        adjustedJson, resaveNeeded = ops.updateDictConfig(dictDB, dictID, request.forms.id, json.loads(request.forms.content))

    if resaveNeeded:
        configs = ops.readDictConfigs(dictDB)
        ops.resave(dictDB, dictID, configs)

    return {"success": True, "id": request.forms.id, "content": adjustedJson}

@post(siteconfig["rootPath"]+"<dictID>/dictaccessupdate.json")
@authDict(["canConfig"])
def dict_access_update(dictID, user, dictDB, configs):
    old_users = ops.updateDictAccess(dictID, json.loads(request.forms.users))
    ops.notifyUsers(old_users, json.loads(request.forms.users), configs['ident'], dictID)
    return {"success": True}

@post(siteconfig["rootPath"]+"<dictID>/dictsettingsupdate.json")
@authAdmin
def dict_settings_update(dictID, user):
    ops.updateDictSettings(dictID, request.forms.configs)
    return {"success": True}

@post(siteconfig["rootPath"]+"<dictID>/autonumber.json")
@authDict(["canConfig"])
def autonumber(dictID, user, dictDB, configs):
    process = ops.addAutoNumbers(dictDB, dictID, request.forms.countElem, request.forms.storeElem)
    return {"success": True, "processed": process}

@post(siteconfig["rootPath"]+"<dictID>/autoimage.json")
@authDict(["canEdit"])
def autoimage(dictID, user, dictDB, configs):
    res = ops.autoImage(dictDB, dictID, configs, request.forms.addElem, request.forms.addNumber)
    return res

@get(siteconfig["rootPath"]+"<dictID>/autoimageprogress.json")
@authDict([])
def autoimagestatus(dictID, user, dictDB, configs):
    res = ops.autoImageStatus(dictDB, dictID, request.query.jobid)
    if not res:
        abort(400, "Invalid job")
    return res

@post(siteconfig["rootPath"]+"<dictID>/resave.json")
@authDict(["canEdit","canConfig","canUpload"])
def resavejson(dictID, user, dictDB, configs):
    count = 0
    stats = ops.getDictStats(dictDB)
    while stats["needResave"] and count <= 127:
        """
        if len(configs['subbing']) > 0:
            ops.refac(dictDB, dictID, configs)
            ops.refresh(dictDB, dictID, configs)
        """
        ops.resave(dictDB, dictID, configs)
        stats = ops.getDictStats(dictDB)
        count += 1
    return {"todo": stats["needResave"]}

@post(siteconfig["rootPath"] + "<dictID>/<doctype>/ontolex.api")
def ontolex(dictID, doctype):
    data = json.loads(request.body.getvalue().decode('utf-8'))
    if not data.get("email") or not data.get("apikey"):
        return {"success": False, "message": "missing email or api key"}
    user = ops.verifyUserApiKey(data["email"], data["apikey"])
    if not user["valid"]:
        return {"success": False}
    else:
        if data.get("search"):
            search = data["search"]
        else:
            search = ""
        dictDB = ops.getDB(dictID)
        configs = ops.readDictConfigs(dictDB)
        dictAccess = configs["users"].get(user["email"]) or user["email"] in siteconfig["admins"]
        if not dictAccess:
            return {"success": False}
        else:
            response.headers['Content-Type'] = "text/plain; charset=utf-8"
            return ops.listOntolexEntries(dictDB, dictID, configs, doctype, search)

@get(siteconfig["rootPath"] + "api")
def apitest():
    return redirect("/#/api")

@post(siteconfig["rootPath"] + "api/listLang")
def apilistlang():
    data = json.loads(request.body.getvalue().decode('utf-8'))
    user = ops.verifyUserApiKey(data["email"], data["apikey"])
    if not user["valid"]:
        return {"success": False}
    else:
        langs = ops.getLangList()
        return {"languages": langs, "success": True}

@post(siteconfig["rootPath"] + "api/listDict")
def apilistdict():
    data = json.loads(request.body.getvalue().decode('utf-8'))
    user = ops.verifyUserApiKey(data["email"], data["apikey"])
    if not user["valid"]:
        return {"success": False}
    else:
        dicts = ops.getDictList(data.get('lang'), data.get('withLinks'), True)
        return {"dictionaries": dicts, "success": True}

@post(siteconfig["rootPath"] + "api/listLinks")
def apilistlink():
    data = json.loads(request.body.getvalue().decode('utf-8'))
    user = ops.verifyUserApiKey(data["email"], data["apikey"])
    if not user["valid"]:
        return {"success": False, "msg": "invalid user"}
    else:
        if data.get('headword') and (data.get('sourceLanguage') or data.get('sourceDict')):
            dicts = ops.getLinkList(data.get('headword'), data.get('sourceLanguage'), data.get('sourceDict'), data.get('targetLanguage'))
            return {"links": dicts, "success": True}
        else:
            return {"success": False, "msg": "missing parameters"}

@get(siteconfig["rootPath"] + "push.api")
def pushtest():
    return redirect("/#/api")

@app.route(siteconfig["rootPath"] + "push.api", 'OPTIONS')
def pushapioptions():
    return {}

# @post(siteconfig["rootPath"] + "push.api") TODO FIX
# def pushapi():
#     data = json.loads(request.body.getvalue().decode('utf-8'))
#     user = ops.verifyUserApiKey(data["email"], data["apikey"])
#     if not user["valid"]:
#         return {"success": False}
#     else:
#         if data["command"] == "makeDict":
#             dictID = ops.suggestDictId()
#             dictTitle = re.sub(r"^\s+", "", data["dictTitle"])
#             if dictTitle == "":
#                 dictTitle = dictID
#             dictBlurb = data["dictBlurb"]
#             addExamples = data["addExamples"]
#             poses = []
#             labels = []
#             if "poses" in data:
#                 poses = data["poses"]
#             if "labels" in data:
#                 labels = data["labels"]
#             if data.get("format") == "teilex0":
#                 dictFormat = "teilex0"
#             else:
#                 dictFormat = "push"
#             res, error = ops.makeDict(dictID, dictFormat, dictTitle, dictBlurb, user["email"], addExamples)
#             if not res:
#                 return {"success": False, "error": error}
#             else:
#                 if dictFormat == "push":
#                     dictDB = ops.getDB(dictID)
#                     configs = ops.readDictConfigs(dictDB)
#                     if configs["structure"]["elements"].get("partOfSpeech"):
#                         for pos in poses:
#                             configs["structure"]["elements"]["partOfSpeech"]["values"].append({"value": pos, "caption": ""})
#                     if configs["structure"]["elements"].get("collocatePartOfSpeech"):
#                         for pos in poses:
#                             configs["structure"]["elements"]["collocatePartOfSpeech"]["values"].append({"value": pos, "caption":""})
#                     if configs["structure"]["elements"].get("label"):
#                         for label in labels:
#                             configs["structure"]["elements"]["label"]["values"].append({"value":label, "caption": ""})
#                     ops.updateDictConfig(dictDB, dictID, "structure", configs["structure"])
#                 return {"success": True, "dictID": dictID}
#         elif data["command"] == "listDicts":
#             dicts = ops.getDictsByUser(user["email"])
#             return {"entries": dicts, "success": True}
#         elif data["command"] == "createEntries":
#             dictID = data["dictID"]
#             entryXmls = data["entryXmls"]
#             dictDB = ops.getDB(dictID)
#             configs = ops.readDictConfigs(dictDB)
#             dictAccess = configs["users"].get(user["email"])
#             if dictAccess and (dictAccess["canEdit"] or dictAccess["canUpload"]):
#                 for entry in entryXmls:
#                     if data.get("format") == "teilex0":
#                         entry = ops.preprocessLex0(entry)
#                     ops.createEntry(dictDB, configs, None, entry, user["email"], {"apikey": data["apikey"]})
#                 return {"success": True}
#             else:
#                 return {"success": False}
#         else:
#             return {"success": False}

@get(siteconfig["rootPath"]+"publicdicts.json")
def publicdicts():
    dicts = ops.getPublicDicts()
    user = ops.verifyLogin(request.cookies.email, request.cookies.sessionkey)
    if user["loggedin"] and user["isAdmin"]:
        [dic.update({'isAdmin': True}) for dic in dicts]
    return {"entries": dicts, "success": True}

@get(siteconfig["rootPath"] + "<dictID>/links/add")
@authDict(["canEdit"])
def linksadd(dictID, user, dictDB, configs):
    source_dict = dictID
    source_el = request.query.source_el
    source_id = request.query.source_id
    target_dict = request.query.target_dict
    target_el = request.query.target_el
    target_id = request.query.target_id
    confidence = request.query.confidence
    if source_dict == "" or source_id == "" or target_dict == "" or target_id == "" or source_el == "" or target_el == "":
        return {"success": False, "error": "missing parameters"}
    else:
        res = ops.links_add(source_dict, source_el, source_id, target_dict, target_el, target_id, confidence)
        return {"success": True, "links": res}

@get(siteconfig["rootPath"] + "<dictID>/links/delete/<linkID>")
@authDict(["canEdit"])
def linksdelete(dictID, linkID, user, dictDB, configs):
    res = ops.links_delete(dictID, linkID)
    return {"success": res}

@get(siteconfig["rootPath"] + "<dictID>/links.json")
@authDict([])
def linksdict(dictID, user, dictDB, configs):
    resto = ops.links_get(dictID, '', '', '', '', '')
    resfrom = ops.links_get('', '', '', dictID, '', '')
    return {"links": {"to": resto, "from": resfrom}}

@get(siteconfig["rootPath"] + "<dictID>/links/from")
@authDict([])
def linksfrom(dictID, user, dictDB, configs):
    source_el = request.query.source_el
    source_id = request.query.source_id
    target_dict = request.query.target_dict
    target_el = request.query.target_el
    target_id = request.query.target_id
    res = ops.links_get(dictID, source_el, source_id, target_dict, target_el, target_id)
    return {"links": res}

@get(siteconfig["rootPath"] + "<dictID>/links/to")
@authDict([])
def linksto(dictID, user, dictDB, configs):
    source_dict = request.query.source_dict
    source_el = request.query.source_el
    source_id = request.query.source_id
    target_el = request.query.target_el
    target_id = request.query.target_id
    res = ops.links_get(source_dict, source_el, source_id, dictID, target_el, target_id)
    return {"links": res}

@get(siteconfig["rootPath"]+"<dictID>/linkablelist.json")
@authDict([])
def linkablelist(dictID, user, dictDB, configs):
    res = ops.getDictLinkables(dictDB)
    return {"links": res}

@get(siteconfig["rootPath"]+"<dictID>/linknaisc.json")
@authDict([])
def linkNaisc(dictID, user, dictDB, configs):
    otherdictID = request.query.otherdictID
    if dictID == otherdictID:
        abort(400, "Linking dictionary to the same dictionary does not make any sense")
    try:
        otherconn = ops.getDB(otherdictID)
    except IOError:
        abort(404, "No such dictionary")
    _res, otherconfigs = ops.verifyLoginAndDictAccess(request.cookies.email, request.cookies.sessionkey, otherconn)
    res = ops.linkNAISC(dictDB, dictID, configs, otherconn, otherdictID, otherconfigs)
    return res

@get(siteconfig["rootPath"]+"<dictID>/naiscprogress.json")
@authDict([])
def checkNaisc(dictID, user, dictDB, configs):
    res = ops.getNAISCstatus(dictDB, dictID, request.query.otherdictID, request.query.jobid)
    if not res:
        abort(400, "Invalid job")
    return res

@get(siteconfig["rootPath"]+"<dictID>/linking.json")
@authDict([])
def linking(dictID, user, dictDB, configs):
    return ops.isLinking(dictDB)

@get(siteconfig["rootPath"]+"<dictID>/entrylinks.json")
@authDict([])
def entrylinks(dictID, user, dictDB, configs):
    res = ops.getEntryLinks(dictDB, dictID, request.query.id)
    return {"links": res}

@post(siteconfig["rootPath"] + "changefavdict.json")
@auth
def changefavdict(user):
    res = ops.changeFavDict(user['email'], request.forms.dictId, request.forms.status)
    return {"success": res}

@get(siteconfig["rootPath"]+"<dictID>")
def publicdict(dictID):
    if ops.dictExists(dictID):
        return redirect("/#" + dictID)
    else:
        return redirect("/")

@get(siteconfig["rootPath"]+"<dictID>/<entryID:re:\d+>")
def publicentry(dictID, entryID):
    if ops.dictExists(dictID):
        return redirect("/#" + dictID + '/' + entryID)
    else:
        return redirect("/")

@get(siteconfig["rootPath"]+"<dictID>/edit")
def dictedit(dictID):
    if ops.dictExists(dictID):
        return redirect("/#" + dictID + '/edit')
    else:
        return redirect("/")

@get(siteconfig["rootPath"]+"<dictID>/edit/<doctype>")
def dicteditdoc(dictID, doctype):
    if ops.dictExists(dictID):
        return redirect("/#" + dictID + '/edit/' + doctype)
    else:
        return redirect("/")

@get(siteconfig["rootPath"]+"docs/intro")
def docintro():
    return redirect("/#docs/intro")

# ELEXIS REST API https://elexis-eu.github.io/elexis-rest/
@get(siteconfig["rootPath"] + "dictionaries")
def elexlistdict():
    apikey = request.headers["X-API-KEY"]
    user = ops.verifyUserApiKey("", apikey)
    if not user["valid"]:
        abort(403, "Forbidden (API key not specified or not valid")
    else:
        dicts = list(map(lambda h: h['id'], ops.getDictList(None, None)))
        return {"dictionaries": dicts}

@get(siteconfig["rootPath"] + "about/<dictID>")
def elexaboutdict(dictID):
    apikey = request.headers["X-API-KEY"]
    user = ops.verifyUserApiKey("", apikey)
    if not user["valid"]:
        abort(403, "Forbidden (API key not specified or not valid")
    dictinfo = ops.elexisDictAbout(dictID)
    if dictinfo is None:
        abort(404, "Dictionary not found (identifier not known)")
    else:
        return dictinfo

@get(siteconfig["rootPath"] + "list/<dictID>")
def elexlistlemma(dictID):
    apikey = request.headers["X-API-KEY"]
    user = ops.verifyUserApiKey("", apikey)
    if not user["valid"]:
        abort(403, "Forbidden (API key not specified or not valid")
    lemmalist = ops.elexisLemmaList(dictID, request.query.limit, request.query.offset)
    if lemmalist is None:
        abort(404, "Dictionary not found (identifier not known)")
    else:
        return json.dumps(lemmalist)

@get(siteconfig["rootPath"] + "lemma/<dictID>/<headword>")
def elexgetlemma(dictID, headword):
    apikey = request.headers["X-API-KEY"]
    user = ops.verifyUserApiKey("", apikey)
    if not user["valid"]:
        abort(403, "Forbidden (API key not specified or not valid")
    lemmalist = ops.elexisGetLemma(dictID, headword, request.query.limit, request.query.offset)
    if lemmalist is None:
        abort(404, "Dictionary not found (identifier not known)")
    else:
        return json.dumps(lemmalist)

@get(siteconfig["rootPath"] + "<dictID>/<entryID>.nvh") # OK
@authDict([])
def getentrynvh(dictID, user, dictDB, configs, entryID):
    entry = ops.getEntry(dictID, entryID, 'nvh')
    if entry is None:
        abort(404, "No Entry Available")
    else:
        response.content_type = "text/plain; charset=utf-8"
        return entry

@get(siteconfig["rootPath"] + "<dictID>/<entryID>.json") # OK
@authDict([])
def getentryjson(dictID, user, dictDB, configs, entryID):
    entry = ops.getEntry(dictID, entryID, 'json')
    if entry is None:
        abort(404, "No Entry Available")
    else:
        return entry

@get(siteconfig["rootPath"] + "api/<dictID>/<entryID>.nvh") # OK
def getentryapinvh(dictID, entryID):
    apikey = request.headers["X-API-KEY"]
    user = ops.verifyUserApiKey("", apikey)
    if not user["valid"]:
        abort(403, "Forbidden (API key not specified or not valid")
    entry = ops.getEntry(dictID, entryID, 'nvh')
    if entry is None:
        abort(404, "No Entry Available")
    else:
        response.content_type = "text/plain; charset=utf-8"
        return entry

@get(siteconfig["rootPath"] + "api/<dictID>/<entryID>.json") # OK
def getentryapijson(dictID, entryID):
    apikey = request.headers["X-API-KEY"]
    user = ops.verifyUserApiKey("", apikey)
    if not user["valid"]:
        abort(403, "Forbidden (API key not specified or not valid")
    entry = ops.getEntry(dictID, entryID, 'json')
    if entry is None:
        abort(404, "No Entry Available")
    else:
        return entry

@error(404)
def error404(error):
    if request.path.startswith("/about/") or request.path.startswith("/list/") or request.path.startswith("/lemma/") or request.path.startswith("/tei/") or request.path.startswith("/json/"):
        return error.body
    else:
        return redirect("/#/e404")

# deployment
debug=True
if "DEBUG" in os.environ:
    debug=True
if ":" in my_url:
    host, port = my_url.split(":")
elif siteconfig.get("port") and siteconfig["port"] > 0:
    host = my_url
    port = siteconfig["port"]
else:
    host = my_url
    port = 3000
if cgi: # we are called as CGI script
    run(host=host, port=port, debug=debug, server="cgi")
elif "httpd" not in os.environ["HOME"]: # very poor mod_wsgi detection; else run a standalone server, prefer the paste server if available over the builtin one
    try:
        import paste
        run(host=host, port=port, debug=debug, reloader=debug, server='paste', interval=0.1)
    except ImportError:
        run(host=host, port=port, debug=debug, reloader=debug, interval=0.1)

