# coding=utf-8
#
#
#    ZapiSession
#   (c) 2014 Pascal Nançoz
#   modified by Daniel Griner
#

import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
import os, re, base64,sys
import datetime
import urllib.request, urllib.parse, urllib.error
import json
from http.client import BadStatusLine
from uuid import uuid4

__addon__ = xbmcaddon.Addon()
__addonId__=__addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__addonVersion__ = __addon__.getAddonInfo('version')
profilePath = xbmcvfs.translatePath(__addon__.getAddonInfo('profile'))
local = xbmc.getLocalizedString
KODIVERSION = xbmc.getInfoLabel( "System.BuildVersion" ).split()[0]
DEBUG = __addon__.getSetting('debug')

#USERAGENT = 'Kodi-'+str(KODIVERSION)+' '+str(__addonname__)+'-'+str(__addonVersion__)+' (Kodi Video Addon)'
USERAGENT = 'Kodi-'+str(KODIVERSION)+' '+str(__addonname__)+'-'+str(__addonVersion__)+' (Kodi Video Addon)'
#USERAGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36'

def debug(content):
    if DEBUG:log(content, xbmc.LOGDEBUG)

def notice(content):
    log(content, xbmc.LOGINFO)

def log(msg, level=xbmc.LOGINFO):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level)

if sys.version_info > (2, 7, 9):
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context

class ZapiSession:

    ZAPIUrl = None
    DATA_FOLDER = None
    COOKIE_FILE = None
    PZUID_FILE = None
    SESSION_FILE = None
    ACCOUNT_FILE = None
    HttpHandler = None
    Username = None
    Password = None
    SessionData = None
    AccountData = None

    def __init__(self, dataFolder):
        self.DATA_FOLDER = dataFolder
        self.COOKIE_FILE = os.path.join(dataFolder, 'cookie.cache')
        self.SESSION_FILE = os.path.join(dataFolder, 'session.cache')
        self.PZUID_FILE = os.path.join(dataFolder,'pzuid.cache')
        self.ACCOUNT_FILE = os.path.join(dataFolder, 'account.cache')
        self.APICALL_FILE = os.path.join(dataFolder, 'apicall.cache')
        self.SESSION_TXT = os.path.join(dataFolder, 'session.txt')
        self.ACCOUNT_TXT = os.path.join(dataFolder, 'account.txt')
        self.COOKIE_TXT = os.path.join(dataFolder, 'cookie.txt')
        self.HttpHandler = urllib.request.build_opener()
        #self.HttpHandler.addheaders = [('User-Agent', USERAGENT), ('Content-type', 'application/x-www-form-urlencoded'), ('Accept', 'application/json')]
        self.HttpHandler.addheaders = [
                ('User-Agent', USERAGENT),
                ('Content-type', 'application/x-www-form-urlencoded'),
                ('Accept', 'application/json'),
                #('sec-ch-ua-platform', '"Windows"'),
                ('pragma', 'no-cache'),
                ('dnt', '1'),
                ('sec-fetch-dest', 'empty'),
                ('sec-fetch-site', 'same-origin'),
                ('sec-fetch-mode', 'same-origin'),
                ('sec-ch-ua', '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"')

                ]
                
    def init_session(self, username, password, api_url="https://zattoo.com"):
        self.Username = username
        self.Password = password
        self.ZAPIUrl = api_url
        if os.path.isfile(self.COOKIE_FILE):
            mtime = os.path.getmtime(self.COOKIE_FILE)
            today = datetime.datetime.now()
            yesterday = today - datetime.timedelta(days=1)
            if mtime < yesterday.timestamp():
                return self.renew_session()
        if self.restore_session():
            #debug ('Restore = '+str(self.restore_session()))
            return self.restore_session()
        else: return self.renew_session()

    def restore_session(self):
        if os.path.isfile(self.PZUID_FILE) and os.path.isfile(self.ACCOUNT_FILE) and os.path.isfile(self.SESSION_FILE):
        #if os.path.isfile(self.COOKIE_FILE) and os.path.isfile(self.ACCOUNT_FILE):
            with open(self.ACCOUNT_FILE, 'r') as f:
                accountData = json.loads(base64.b64decode(f.readline()))
            try:
                if accountData['active'] == True:
                    self.AccountData = accountData
                    with open(self.COOKIE_FILE, 'r') as f:
                        self.set_cookie(base64.b64decode(f.readline()).decode('utf-8'))
                    with open(self.PZUID_FILE, 'r') as f:
                        self.set_pzuid(base64.b64decode(f.readline()).decode('utf-8'))
                    with open(self.SESSION_FILE, 'r') as f:
                        self.SessionData = json.loads(base64.b64decode(f.readline()))
                    return True
            except: 
                # profilePath = xbmcvfs.translatePath(__addon__.getAddonInfo('profile'))
                # if os.path.isfile(os.path.join(profilePath, 'session.cache')):
                    # os.remove(os.path.join(profilePath, 'session.cache'))
                # if os.path.isfile(os.path.join(profilePath, 'account.cache')):
                    # os.remove(os.path.join(profilePath, 'account.cache'))
                self.renew_session()
            
        return False

    def extract_sessionId(self, cookieContent):
        if cookieContent is not None:
            ID = re.search("beaker\.session\.id\s*=\s*([^\s;]*)", str(cookieContent))
            if ID is None: return None
            return re.search("beaker\.session\.id\s*=\s*([^\s;]*)", str(cookieContent)).group(1)
        return None
        
    def extract_pzuid(self, cookieContent):
        if cookieContent is not None:
            PZUID = re.search("pzuid\s*=\s*([^\s;]*)", str(cookieContent))
            if PZUID is None: return None
            PZUID = re.search("pzuid\s*=\s*([^\s;]*)", str(cookieContent)).group(1)
            return PZUID
        return None
            
    def get_accountData(self):
        accountData={}
        if os.path.isfile(self.ACCOUNT_FILE):
            with open(self.ACCOUNT_FILE, 'r') as f:
                accountData = json.loads(base64.b64decode(f.readline()))
        return accountData

    def persist_accountData(self, accountData):
        with open(self.ACCOUNT_FILE, 'wb') as f:
            f.write(base64.b64encode(json.dumps(accountData).encode('utf-8')))

    def persist_sessionId(self, sessionId):
        with open(self.COOKIE_FILE, 'wb') as f:
            f.write(base64.b64encode(sessionId.encode('utf-8')))
    
    def persist_pzuid(self, pzuid):
        with open(self.PZUID_FILE, 'wb') as f:
            f.write(base64.b64encode(pzuid.encode('utf-8')))

    def persist_sessionData(self, sessionData):
        with open(self.SESSION_FILE, 'wb') as f:
            f.write(base64.b64encode(json.dumps(sessionData).encode('utf-8')))

    def set_cookie(self, sessionId):
        self.HttpHandler.addheaders.append(('Cookie', 'beaker.session.id=' + sessionId))

    def set_pzuid(self, pzuid):
        self.HttpHandler.addheaders.append(('Cookie', 'pzuid=' + pzuid))

    def request_url(self, url, params):

        try:

            if params is not None:
                f = urllib.parse.urlencode(params)
                f = f.encode('utf-8')
            #debug(params)
            response = self.HttpHandler.open(url,f if params is not None else None, timeout=60)
            #debug(response)
            if response is not None:
                sessionId = self.extract_sessionId(response.info())
                pzuid = self.extract_pzuid(response.info())
                if sessionId is not None:
                    self.set_cookie(sessionId)
                    self.persist_sessionId(sessionId)
                if pzuid is not None:
                    self.set_pzuid(pzuid)
                    self.persist_pzuid(pzuid)
                #debug(response.read().decode('utf-8'))
                return response.read().decode('utf-8')
        except Exception as e:
            debug(str(e))
            if '403' in str(e) or '400' in str(e):
                xbmcgui.Dialog().ok(__addon__.getAddonInfo('name'), str(e))
                xbmcgui.Dialog().ok(__addon__.getAddonInfo('name'), __addon__.getLocalizedString(31902))
                sys.exit()
                
        except BadStatusLine:
            pass

        return None

    # zapiCall with params=None creates GET request otherwise POST

    def exec_zapiCall(self, api, params, context='default'):
        #url = self.ZAPIAuthUrl + api if context == 'session' else self.ZAPIUrl + api
        url = self.ZAPIUrl + api
        #debug( "ZapiCall  " + str(url)+'  '+str(params))
        content = self.request_url(url, params)
        debug(content)
        x=2
        while x < 4:
            if content is None:# and self.renew_session():
                xbmc.sleep(2000)
                debug(str(x) + '. Versuch')
                content = self.request_url(url, params)
                debug(content)
            elif content == '403':
                #xbmcgui.Dialog().ok(__addon__.getAddonInfo('name'), __addon__.getLocalizedString(31902))
                self.session()
                content = self.request_url(url, params)
                break
            x = x+1
    
        if content is None:
            return None
        #try:
        resultData = json.loads(content)
        #debug(resultData)
        return resultData

        # except Exception:
           # pass
        # return None

    def fetch_appToken(self):
        handle = urllib.request.urlopen(self.ZAPIUrl + '/login')
        html = str(handle.read())
        #appversion = re.search("<!--(.+?)-v(.+?)-", html).group(2)
        js = re.search(r"\/app-\w+\.js", html).group(0)
        handle = urllib.request.urlopen(self.ZAPIUrl + js)
        html = str(handle.read())
        try:
            token_js = re.search(r"token-(.+?)\.json", html).group(0)
        except AttributeError:
            token_js = 'token.json'
        #debug(token_js)
        handle = urllib.request.urlopen(self.ZAPIUrl + '/' + token_js)
        htmlJson = json.loads(handle.read())                        
        return htmlJson['session_token']
                
    def fetch_appVersion(self):
        handle = urllib.request.urlopen(self.ZAPIUrl + '/login')
        html = str(handle.read())
        return re.search("<!--(.+?)-v(.+?)-", html).group(2)

    def session(self):
        api = '/zapi/v3/session/hello'
        if __addon__.getSetting('smarttv'):            
            params = {"uuid"    : str(uuid4()),
                      "app_version" : '2.2409.1',
                      "app_tid" : "01054a65-1f0d-4a00-a441-44c2ec5fa357",
                      "device_type" : 'android_bigscreen 30/zattoo_2.2409.1/NVIDIA/SHIELD Android TV/mdarcy/1920x1080',    
                      "format"  : "json",
                      }
        else:
            params = {"client_app_token" : self.fetch_appToken(),
                      "uuid"    : str(uuid4()),
                      "app_version" : '3.2315.0',
                      "format"  : "json",
                      }
            
        sessionData = self.exec_zapiCall(api, params, 'session')

        debug('SessionData: '+str(sessionData))
        if sessionData is not None:
            self.SessionData = sessionData
            self.persist_sessionData(sessionData)
            return True
        return False

    def login(self):
        api = '/zapi/v3/account/login'
        params = {"login": self.Username, "password" : self.Password, "remember": True}
        accountData = self.exec_zapiCall(api, params, 'session')
        debug ('Login: '+str(accountData))
        if accountData is not None:
            self.AccountData = accountData
            self.persist_accountData(accountData)
            return True
        return False

    def renew_session(self):
        return self.session() and self.login()
        #return self.login() and self.session()
