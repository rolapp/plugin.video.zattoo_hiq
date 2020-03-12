# # -*- coding: utf-8 -*-
#
#    copyright (C) 2017 Steffen Rolapp (github@rolapp.de)
#
#    based on ZattooBoxExtended by Daniel Griner (griner.ch@gmail.com) license under GPL
#
#    This file is part of ZattooHiQ
#
#    zattooHiQ is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    zattooHiQ is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with zattooHiQ.  If not, see <http://www.gnu.org/licenses/>.
#

import xbmc, xbmcgui, xbmcaddon, os, xbmcplugin, datetime, time
import json
from resources.lib.zapisession import ZapiSession
import sqlite3
import sys
import importlib
importlib.reload(sys)
#sys.setdefaultencoding('utf8')


__addon__ = xbmcaddon.Addon()
_listMode_ = __addon__.getSetting('channellist')
_channelList_=[]
localString = __addon__.getLocalizedString
local = xbmc.getLocalizedString
DEBUG = __addon__.getSetting('debug')
_umlaut_ = {ord('ä'): 'ae', ord('ö'): 'oe', ord('ü'): 'ue', ord('ß'): 'ss'}


def debug(content):
    if DEBUG:log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 
    
class reloadDB(xbmcgui.WindowXMLDialog):

  def __init__(self, xmlFile, scriptPath):
    xbmcgui.Window(10000).setProperty('reloadDB', 'True')
    news = __addon__.getAddonInfo('path')+'/resources/media/news.png'
    if os.path.isfile(news): 
        self.wartungImg =xbmcgui.ControlImage(50, 50, 1180, 596,__addon__.getAddonInfo('path') + '/resources/media/news.png'  , aspectRatio=0)
    else:
        self.wartungImg =xbmcgui.ControlImage(50, 50, 1180, 596,__addon__.getAddonInfo('path') + '/resources/media/wartung.png'  , aspectRatio=0)
    self.addControl(self.wartungImg)
    self.show()
    
  def reloadDB(self, cache=False):
    debug('ReloadDB')
    from resources.lib.library import library
    _library_ = library()
    DB = ZattooDB()
    news = __addon__.getAddonInfo('path')+'/resources/media/news.png'        
    xbmc.executebuiltin("ActivateWindow(busydialog)")
    #delete zapi files to force new login    
    profilePath = xbmc.translatePath(__addon__.getAddonInfo('profile'))
    if os.path.isfile(news): 
        try:
            os.remove(os.path.join(xbmc.translatePath(__addon__.getAddonInfo('path') + '/resources/media/'), 'news.png'))
        except:
            pass
    if cache:
        try:
            os.remove(os.path.join(profilePath, 'cookie.cache'))
            os.remove(os.path.join(profilePath, 'session.cache'))
            os.remove(os.path.join(profilePath, 'account.cache'))
            #os.remove(os.path.join(profilePath, 'apicall.cache'))
            DB.zapiSession()
            DB._createTables()
            #xbmcgui.Dialog().ok(__addon__.getAddonInfo('name'), local(24074))
            
        except:
            pass
    #DB.zapi.AccountData = None
    
    DB._createTables()
    time.sleep(5)
    xbmcgui.Dialog().notification(localString(31916), localString(30110),  __addon__.getAddonInfo('path') + '/resources/icon.png', 3000, False)
    DB.updateChannels(True)
    #time.sleep(2)
    DB.updateProgram(datetime.datetime.now(), True)
    
    try: 
        tomorrow = datetime.datetime.today() + datetime.timedelta(days=1)
        DB.updateProgram(tomorrow)
    except:pass
    
    startTime=datetime.datetime.now()#-datetime.timedelta(minutes = 60)
    endTime=datetime.datetime.now()+datetime.timedelta(minutes = 20)
    #time.sleep(2)
    DB.getProgInfo(True, startTime, endTime)
   
    
    xbmcgui.Dialog().notification(localString(31106), localString(31915),  __addon__.getAddonInfo('path') + '/resources/icon.png', 3000, False)
    _library_.make_library()
    xbmc.executebuiltin("Dialog.Close(busydialog)")
    
    self.close()
    
  def close(self):
    #self.wartungImg.setVisible(False)    
    xbmcgui.Window(10000).setProperty('reloadDB', 'False')
    super(reloadDB, self).close()
   
class ZattooDB(object):
  def __init__(self):
    self.conn = None
    profilePath = xbmc.translatePath(__addon__.getAddonInfo('profile'))
    if not os.path.exists(profilePath): os.makedirs(profilePath)
    self.databasePath = os.path.join(profilePath, "zattoo.db")
    self.connectSQL()
    self.zapi=self.zapiSession()

  def zapiSession(self):
    zapiSession   = ZapiSession(xbmc.translatePath(__addon__.getAddonInfo('profile')))
    PROVIDER = __addon__.getSetting('provider')
    #debug('Provider '+str(PROVIDER))
    if PROVIDER == "0": ZAPIUrl = "https://zattoo.com"
    elif PROVIDER == "1": ZAPIUrl = "https://www.netplus.tv"
    elif PROVIDER == "2": ZAPIUrl = "https://mobiltv.quickline.com"
    elif PROVIDER == "3": ZAPIUrl = "https://tvplus.m-net.de"
    elif PROVIDER == "4": ZAPIUrl = "https://player.waly.tv"
    elif PROVIDER == "5": ZAPIUrl = "https://www.meinewelt.cc"
    elif PROVIDER == "6": ZAPIUrl = "https://www.bbv-tv.net"
    elif PROVIDER == "7": ZAPIUrl = "https://www.vtxtv.ch"
    elif PROVIDER == "8": ZAPIUrl = "https://www.myvisiontv.ch"
    elif PROVIDER == "9": ZAPIUrl = "https://iptv.glattvision.ch"
    elif PROVIDER == "10": ZAPIUrl = "https://www.saktv.ch"
    elif PROVIDER == "11": ZAPIUrl = "https://nettv.netcologne.de"
    elif PROVIDER == "12": ZAPIUrl = "https://tvonline.ewe.de"
    elif PROVIDER == "13": ZAPIUrl = "https://www.quantum-tv.com"
    elif PROVIDER == "14": ZAPIUrl = "https://tv.salt.ch"
    elif PROVIDER == "15": ZAPIUrl = "https://www.1und1.tv"
    
    if zapiSession.init_session(__addon__.getSetting('username'), __addon__.getSetting('password'), ZAPIUrl):                                
      return zapiSession

    else:
      # show home window, zattooHiQ settings and quit
      xbmc.executebuiltin('ActivateWindow(10000)')
      xbmcgui.Dialog().ok(__addon__.getAddonInfo('name'), __addon__.getLocalizedString(31902))
      __addon__.openSettings()
      zapiSession.renew_session()
      xbmcgui.Dialog().ok(__addon__.getAddonInfo('name'), local(24074))
      
      import sys
      sys.exit()

  @staticmethod
  def adapt_datetime(ts):
    # http://docs.python.org/2/library/sqlite3.html#registering-an-adapter-callable
    return time.mktime(ts.timetuple())

  @staticmethod
  def convert_datetime(ts):
    try:
        return datetime.datetime.fromtimestamp(float(ts))
    except ValueError:
        return None

  def connectSQL(self):
    import sqlite3

    sqlite3.register_adapter(datetime.datetime, self.adapt_datetime)
    sqlite3.register_converter('timestamp', self.convert_datetime)

    self.conn = sqlite3.connect(self.databasePath, detect_types=sqlite3.PARSE_DECLTYPES)
    self.conn.execute('PRAGMA foreign_keys = ON')
    self.conn.row_factory = sqlite3.Row

    # check if DB exists
    c = self.conn.cursor()
    try: 
        c.execute('SELECT * FROM showinfos')
    except: 
        self._createTables()
    c.close()

  def _createTables(self):
    import sqlite3
    c = self.conn.cursor()
   
    try: 
        c.execute('DROP TABLE channels')
        debug('Delete Channels')
    except: pass
    try: 
        c.execute('DROP TABLE programs')
        debug('Delete program')
    except: pass
    try: c.execute('DROP TABLE updates')
    except: pass
    try: c.execute('DROP TABLE playing')
    except: pass
    try: c.execute('DROP TABLE showinfos')
    except: pass
    self.conn.commit()
    c.close()
    
    try:
      c = self.conn.cursor()
      c.execute('CREATE TABLE channels(id TEXT, title TEXT, logo TEXT, weight INTEGER, favourite BOOLEAN, PRIMARY KEY (id) )')
      c.execute('CREATE TABLE programs(showID TEXT, title TEXT, channel TEXT, start_date TIMESTAMP, end_date TIMESTAMP, restart BOOLEAN, series BOOLEAN, record BOOLEAN, description TEXT, description_long TEXT, year TEXT, country TEXT, genre TEXT, category TEXT, image_small TEXT, credits TEXT, PRIMARY KEY (showID), FOREIGN KEY(channel) REFERENCES channels(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED)')

      c.execute('CREATE INDEX program_list_idx ON programs(channel, start_date, end_date)')
      c.execute('CREATE INDEX start_date_idx ON programs(start_date)')
      c.execute('CREATE INDEX end_date_idx ON programs(end_date)')
      
      c.execute('CREATE TABLE updates(id INTEGER, date TIMESTAMP, type TEXT, PRIMARY KEY (id) )')
      #c.execute('CREATE TABLE playing(channel TEXT, start_date TIMESTAMP, action_time TIMESTAMP, current_stream INTEGER, streams TEXT, PRIMARY KEY (channel))')
      c.execute('CREATE TABLE showinfos(showID INTEGER, info TEXT, PRIMARY KEY (showID))')
      c.execute('CREATE TABLE playing(channel TEXT, showID TEXT, current_stream INTEGER, streams TEXT, PRIMARY KEY (channel))')
      c.execute('CREATE TABLE version(version TEXT, PRIMARY KEY (version))')
      c.execute('CREATE TABLE search(search TEXT, PRIMARY KEY (search))')
    
   
      self.conn.commit()
      c.close()

    except sqlite3.OperationalError as ex:
      pass
    VERSION = __addon__.getAddonInfo('version')
    self.set_version(VERSION)
    
    
  def updateChannels(self, rebuild=False):
    c = self.conn.cursor()

    if rebuild == False:
      #date = datetime.date.today().strftime('%Y-%m-%d')
      date = datetime.date.today()
      #debug ("date: "+str(date))
      c.execute('SELECT * FROM updates WHERE date=? AND type=? ', [date, 'channels'])
      if len(c.fetchall())>0:
        c.close()
        return

    # always clear db on update
    if rebuild: c.execute('DELETE FROM channels')
    

    api = '/zapi/v2/cached/channels/' + self.zapi.AccountData['session']['power_guide_hash'] + '?details=False'
    channelsData = self.zapi.exec_zapiCall(api, None)
    if channelsData == None:
        channelsData = self.zapi.exec_zapiCall(api, None)
    debug("channels: " +str(channelsData))
    #time.sleep(5)
    api = '/zapi/channels/favorites'
    favoritesData = self.zapi.exec_zapiCall(api, None)
    debug (str(favoritesData))
    if favoritesData == None: 
        debug('favourites = None')
        time.sleep(5)
        favoritesData = self.zapi.exec_zapiCall(api, None)
    debug (str(favoritesData))
    
    nr = 0
    for group in channelsData['channel_groups']:
      for channel in group['channels']:
        if channel['qualities'][0]['availability'] == 'subscribable': 
            try:
                if channel['qualities'][1]['availability'] == 'subscribable': continue
                #else: debug(str(channel['title'].encode('utf-8')+"  "+channel['qualities'][1]['availability'].encode('utf-8')))
            except: continue
        #else: debug(str(channel['title'].encode('utf-8')+"  "+channel['qualities'][0]['availability'].encode('utf-8')))
        
        logo = 'http://logos.zattic.com' + channel['qualities'][0]['logo_black_84'].replace('/images/channels', '')
        try:
          favouritePos = favoritesData['favorites'].index(channel['id'])
          weight = favouritePos
          favourite = True
        except:
          weight = 1000 + nr
          favourite = False

        c.execute('INSERT OR IGNORE INTO channels(id, title, logo, weight, favourite) VALUES(?, ?, ?, ?, ?)',
            [channel['id'], channel['title'], logo, weight, favourite])
        if not c.rowcount:
          c.execute('UPDATE channels SET title=?, logo=?, weight=?, favourite=? WHERE id=?',
              [channel['title'], logo, weight, favourite, channel['id']])
        nr += 1
    if nr>0: c.execute('INSERT INTO updates(date, type) VALUES(?, ?)', [datetime.date.today(), 'channels'])
    self.conn.commit()
    c.close()
    return

  def updateProgram(self, date=None, rebuild=False):
    if date is None: date = datetime.date.today()
    else: date = date.date()

    c = self.conn.cursor()

    # if rebuild:
      # c.execute('DELETE FROM programs')
      # self.conn.commit()

    # get whole day
    fromTime = int(time.mktime(date.timetuple()))  # UTC time for zattoo
    
    # get the first channel
    c.execute('SELECT * FROM channels ORDER BY weight ASC LIMIT 1')
    row = c.fetchone()
    firstchan = row['id']
    
    #try:
    c.execute('SELECT * FROM programs WHERE start_date > ? AND end_date < ?', [fromTime+18000, fromTime+25200,]) #get shows between 05:00 and 07:00
    #except:pass
    count = c.fetchall()

    if len(count)>0:
        c.close()
        return
    

    xbmcgui.Dialog().notification(__addon__.getLocalizedString(31917), self.formatDate(date), __addon__.getAddonInfo('path') + '/resources/icon.png', 5000, False)
    #xbmc.executebuiltin("ActivateWindow(busydialog)")
    debug('update Program')
    #update 09.02.2018: zattoo only sends max 5h (6h?) of programdata -> load 6*4h
    for nr in range(0, 6):
        api = '/zapi/v2/cached/program/power_guide/' + self.zapi.AccountData['session']['power_guide_hash'] + '?end=' + str(fromTime+14400) + '&start=' + str(fromTime)
        fromTime+=14400

        #print "apiData   "+api
        programData = self.zapi.exec_zapiCall(api, None)
        debug ('ProgrammData: '+str(programData))
        count=0
        for channel in programData['channels']:
            cid = channel['cid']
            c.execute('SELECT * FROM channels WHERE id==?', [cid])
            countt=c.fetchall()
            if len(countt)==0:
                 #debug('Sender nicht im Abo: '+str(cid))
                continue
            if cid == firstchan and not channel['programs']:
                xbmcgui.Dialog().notification('Update Program', 'No Data',  __addon__.getAddonInfo('path') + '/resources/icon.png', 3000, False)
                #c.close()
                continue
           
            for program in channel['programs']:
                count+=1
                #debug ('Programm: '+str(cid)+' '+str(program))
       
                if program['i'] != None:
                  image = "https://images.zattic.com/cms/" + program['i_t'] + "/format_480x360.jpg"
                  #https://images.zattic.com/cms/64ab6db7f62b325f4148/original.jpg
                  #http://images.zattic.com/system/images/6dcc/8817/50d1/dfab/f21c/format_480x360.jpg
                else: image = ""
                
                c.execute('INSERT OR IGNORE INTO programs(channel, title, start_date, end_date, description,  genre, image_small, showID, category) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    [cid, program['t'], program['s'], program['e'], program['et'], ', '.join(program['g']), image, program['id'], ', '.join(program['c']) ])
           

    if count>0:
      c.execute('INSERT into updates(date, type) VALUES(?, ?)', [date, 'program'])

    try:
        self.conn.commit()
    except:
        print('IntegrityError: FOREIGN KEY constraint failed zattooDB 232')
    #xbmc.executebuiltin("Dialog.Close(busydialog)")
    c.close()
    return

  def getChannelList(self, favourites=True):
    #self.updateChannels()
    c = self.conn.cursor()
    if favourites: c.execute('SELECT * FROM channels WHERE favourite=1 ORDER BY weight')
    else: c.execute('SELECT * FROM channels ORDER BY weight')
    channelList = {'index':[]}
    nr=0
    for row in c:
      channelList[row['id']]={
        'id': str(row['id']),
        'title': row['title'],
        'logo': row['logo'],
        'weight': row['weight'],
        'favourite': row['favourite'],
        'nr':nr
      }
      channelList['index'].append(str(row['id']))
      nr+=1
    c.close()
    return channelList

  def get_channelInfo(self, channel_id):
    c = self.conn.cursor()
    c.execute('SELECT * FROM channels WHERE id=?', [channel_id])
    row = c.fetchone()
    channel = {
         'id':row['id'],
         'title':row['title'],
         'logo':row['logo'],
         'weight':row['weight'],
         'favourite':row['favourite']
    }
    c.close()
    return channel

  def getPopularList(self):
    channels=self.getChannelList(False)
    popularList = {'index':[]}
    nr=0
    #max 10 items per request -> request 3times for 30 items
    for page in range(3):
          api = '/zapi/v2/cached/' + self.zapi.SessionData['session']['power_guide_hash'] + '/teaser_collections/most_watched_live_now_de?page='+str(page)+'&per_page=10'
          #api = '/zapi/v2/cached/' + self.zapi.SessionData['session']['power_guide_hash'] + '/teaser_collections/avod_highlights_page?page='+str(page)+'&per_page=10'
          mostWatched = self.zapi.exec_zapiCall(api, None)
          debug('Popular '+str(mostWatched))
          if mostWatched is None: continue
          for data in mostWatched['teasers']:
              data=data['teasable']
              popularList[data['cid']]={
                  'id': str(data['cid']),
                  'title': data['t'],
                  'logo': channels[data['cid']]['logo'],
                  'nr':nr
              }
              popularList['index'].append(str(data['cid']))
              nr+=1
              debug(popularList)
    return popularList

  def getPrograms(self, channels, get_long_description=False, startTime=datetime.datetime.now(), endTime=datetime.datetime.now()):
    import urllib.request, urllib.parse, urllib.error
    c = self.conn.cursor()
    programList = []

    for chan in channels['index']:
      try:
        c.execute('SELECT * FROM programs WHERE channel = ? AND start_date < ? AND end_date > ?', [chan, endTime, startTime])
      except:pass
      
      r = c.fetchall()

      for row in r:
        description_long = row['description_long']
        #debug(str(row['channel'])+' '+str(description_long))
        year = row['year']
        country = row['country']
        if get_long_description and description_long is None:
            #description_long = self.getShowInfo(row["showID"],'description')
            info = self.getShowLongDescription(row['showID'])
            #print 'ProgINFO  ' + str(type(info)) + ' ' + str(row['showID'])+ '  ' + str(info)
            if type(info) == dict:
                description_long = info.get('description','')
                year = info.get('year',' ')
                country = info.get('country','')
                category = info.get('category','')
        programList.append({
            'channel': row['channel'],
            'showID' : row['showID'],
            'title' : row['title'],
            'description' : row['description'],
            'description_long' : description_long,
            'year': row['year'],
            'genre': row['genre'],
            'country': row['country'],
            'category': row['category'],
            'start_date' : row['start_date'],
            'end_date' : row['end_date'],
            'image_small' : row['image_small'],
            'credits' : row['credits'],
            'restart': row['restart']
           
            })

    c.close()
    
    return programList

  def getShowLongDescription(self, showID):
        info = self.conn.cursor()
        try:
            info.execute('SELECT * FROM programs WHERE showID= ? ', [showID])
        except:
            info.close()
            return None
            
        show = info.fetchone()
        info.close()
        if show is None:
            info.close()
            longDesc=''
            year=''
            category=''
            country=''
            genre =''
            cred=''

            return {'description':longDesc, 'year':year, 'country':country, 'category':category, 'genre':genre, 'credits':cred}
        longDesc = show['description_long']
        year = show['year']
        country = show['country']
        category = show ['category']
        series = show['series']
        restart = show['restart']
        genre = show['genre']
        cred = show['credits']
        if longDesc is None:
            import json
            
            profilePath = xbmc.translatePath(__addon__.getAddonInfo('profile'))
            while os.path.exists(profilePath+"/zattoo.db-journal"):
                debug('Database is locked')
                time.sleep(1)
            #api = '/zapi/program/details?program_id=' + showID + '&complete=True'
            api = '/zapi/v2/cached/program/power_details/'+ self.zapi.AccountData['session']['power_guide_hash'] + '?program_ids='+str(showID)
            showInfo = self.zapiSession().exec_zapiCall(api, None)
            #infoall = showInfo['program']
            
            #info.execute('UPDATE programs SET info=? WHERE showID=?',[json.dumps(infoall), showID ])
            
            #debug ('Showinfo  ' + str(showInfo))
            
            if showInfo is None:
                longDesc=''
                year=''
                category=''
                country=''
                info.close()
                return {'description':longDesc, 'year':year, 'country':country, 'category':category}
                
            if len(showInfo['programs']) == 0:
                 longDesc=''
                 year=''
                 category=''
                 country=''
                 info.close()
                 return {'description':longDesc, 'year':year, 'country':country, 'category':category}
            info = self.conn.cursor()     
            longDesc = showInfo['programs'][0]['d']
            info.execute('UPDATE programs SET description_long=? WHERE showID=?', [longDesc, showID ])
            year = showInfo['programs'][0]['year']
            if year is None: year=''
            info.execute('UPDATE programs SET year=? WHERE showID=?', [year, showID ])
            category = ', '.join(showInfo['programs'][0]['c'])
            info.execute('UPDATE programs SET category=? WHERE showID=?', [category, showID ])
            country = showInfo['programs'][0]['country']
            country = country.replace('|',', ')
            info.execute('UPDATE programs SET country=? WHERE showID=?', [country, showID ])
            series = showInfo['programs'][0]['ser_e']
            info.execute('UPDATE programs SET series=? WHERE showID=?', [series, showID])
            cred = showInfo['programs'][0]['cr']

            info.execute('UPDATE programs SET credits=? WHERE showID=?', [json.dumps(cred), showID])
            try:
                restart = showInfo['programs'][0]['sr_u']
                info.execute('UPDATE programs SET restart=? WHERE showID=?', [True, showID])
            except:
                info.execute('UPDATE programs SET restart=? WHERE showID=?', [False, showID])
                
           
            record = showInfo['programs'][0]['r_e']
            info.execute('UPDATE programs SET record=? WHERE showID=?', [record, showID])

        try:
            self.conn.commit()
        except:
            print('IntegrityError: FOREIGN KEY constraint failed zattooDB 355')
        info.close()
        return {'description':longDesc, 'year':year, 'country':country, 'category':category, 'genre':genre, 'credits':cred}
        
  def getShowInfo(self, showID, field='all'):
        if field!='all':
            #api = '/zapi/program/details?program_id=' + str(showID) + '&complete=True'
            #showInfo = self.zapi.exec_zapiCall(api, None)
            showInfo = self.getShowLongDescription(showID)
            #return showInfo['program'].get(field, " ")
            return showInfo[field]

        #save information for recordings
        import json
        c = self.conn.cursor()
        c.execute('SELECT * FROM showinfos WHERE showID= ? ', [int(showID)])
        row = c.fetchone()
        if row is not None:
            showInfoJson=row['info']
            showInfo=json.loads(showInfoJson)
        else:
            #api = '/zapi/program/details?program_id=' + str(showID) + '&complete=True'
            api = '/zapi/v2/cached/program/power_details/' + self.zapi.AccountData['session']['power_guide_hash']+'?program_ids='+str(showID)
            debug(api)
            showInfo = self.zapi.exec_zapiCall(api, None)
            if showInfo is None:
                c.close()
                return "NONE"
            showInfo = showInfo['programs']
            try: c.execute('INSERT INTO showinfos(showID, info) VALUES(?, ?)',(int(showID), json.dumps(showInfo)))
            except: pass
        self.conn.commit()
        c.close()
        return showInfo
        
  def setProgram(self, showID):
       
    c = self.conn.cursor()
    
    #api = '/zapi/program/details?program_id=' + str(showID) + '&complete=True'
    api = '/zapi/v2/cached/program/power_details/' + self.zapi.AccountData['session']['power_guide_hash'] + '?program_ids='+str(showID)
    showInfo = self.zapi.exec_zapiCall(api, None)
    debug(showInfo)
    if showInfo is None:
        c.close()
        return "NONE"
    if not showInfo['programs']:
        debug('Liste ist leer')
        c.close()
        return "NONE"
        
    title = showInfo['programs'][0]['t']
    channel = showInfo['programs'][0]['cid']
    start = showInfo['programs'][0]['s']
    end = showInfo['programs'][0]['e']
    genre = showInfo['programs'][0]['g']
    year = showInfo['programs'][0]['year']
    country = showInfo['programs'][0]['country']
    description = showInfo['programs'][0]['d']
    cred = showInfo['programs'][0]['cr']
                
    c.execute('INSERT OR IGNORE INTO programs(showID, title, channel, start_date, end_date, genre, year, country, description_long, credits) VALUES(?,?,?,?,?,?,?,?,?,?)', [showID, title, channel, start, end, ', '.join(genre) ,year, country, description, json.dumps(cred)])
    
    self.conn.commit()
    c.close()
    return {'description':description, 'year':year, 'country':country, 'title':title, 'genre':genre, 'credits':cred}



  def set_playing(self, channel=None, showID='', streams=None, streamNr=0):
    c = self.conn.cursor()
    c.execute('DELETE FROM playing')
    #c.execute('INSERT INTO playing(channel, start_date, action_time, current_stream,  streams) VALUES(?, ?, ?, ?, ?)', [channel, start, datetime.datetime.now(), streamNr, streams])
    c.execute('INSERT INTO playing(channel, showID, current_stream,  streams) VALUES(?, ?, ?, ?)', [channel, showID, streamNr, streams])    
    self.conn.commit()
    c.close()
    

  def get_playing(self):
    c = self.conn.cursor()
    c.execute('SELECT * FROM playing')
    row = c.fetchone()
    #debug('print row:'+str(row))
    if row is not None:
      playing = {'channel':row['channel'], 'current_stream':row['current_stream'], 'streams':row['streams'], 'showID':row['showID']}
    else:
      c.execute('SELECT * FROM channels ORDER BY weight ASC LIMIT 1')
      row = c.fetchone()
      playing = {'channel':row['id'], 'start':datetime.datetime.now(), 'action_time':datetime.datetime.now()}
    c.close()
    #debug( "now playing" +str(playing))
    return playing
  
  def get_showID(self, showID):
        c = self.conn.cursor()
        programList = []
        try:
            c.execute('SELECT * FROM programs WHERE showID = ? ', [showID])
            #debug(showID)
        except:pass
        row = c.fetchone()
        programList.append({
            'channel': row['channel'],
            'showID' : row['showID'],
            'title' : row['title'],
            'description' : row['description'],
            'year': row['year'],
            'genre': row['genre'],
            'country': row['country'],
            'category': row['category'],
            'start_date' : row['start_date'],
            'end_date' : row['end_date'],
            'image_small' : row['image_small'],
            'credits' : row['credits'],
            'restart': row['restart']
           
            })
        c.close
        return programList
        
  def set_currentStream(self, nr):
    c = self.conn.cursor()
    c.execute('UPDATE playing SET current_stream=?', [nr])
    self.conn.commit()
    c.close()

  def reloadDB(self, cache=False):
    gui = reloadDB("wartung.xml", __addon__.getAddonInfo('path'))
    gui.reloadDB(cache)
    gui.show()
    del gui
    
  def get_channeltitle(self, channelid):
    c = self.conn.cursor()
    c.execute('SELECT * FROM channels WHERE id= ? ', [channelid])
    row = c.fetchone()
    if row:
      channeltitle=row['title']
    self.conn.commit()
    c.close()
    return channeltitle

  def get_channelid(self, channeltitle):
    c = self.conn.cursor()
    c.execute('SELECT * FROM channels WHERE title= ? ', [channeltitle])
    row = c.fetchone()
    #print 'Title ' +str(channeltitle)
    if row:
      channelid=row['id']
    self.conn.commit()
    c.close()
    return channelid

  def get_channelweight(self, weight):
    c = self.conn.cursor()
    c.execute('SELECT * FROM channels WHERE weight= ? ', [weight])
    row = c.fetchone()
    if row:
      channelid=row['id']
    self.conn.commit()
    c.close()
    return channelid

  def getProgInfo(self, notify=False, startTime=datetime.datetime.now(), endTime=datetime.datetime.now(), chan='fav'):
        import urllib.request, urllib.parse, urllib.error
        fav = False
        if __addon__.getSetting('onlyfav') == 'true': fav = True
        if chan == 'all': fav = False
        channels = self.getChannelList(fav)
        
        c = self.conn.cursor()
        #print 'START Programm'
        # for startup-notify
        if notify:
            #xbmc.executebuiltin("ActivateWindow(busydialog)")
            #c = self.conn.cursor()
            PopUp = xbmcgui.DialogProgressBG()
            #counter = len(channels)
            counter = 0
            for chan in channels['index']:
                #debug( str(chan) + ' - ' + str(startTime) + str(endTime))
                c.execute('SELECT * FROM programs WHERE channel = ? AND start_date < ? AND end_date > ?', [chan, endTime, startTime])
                d=c.fetchall()
                for nr in d:
                    counter += 1
               
            bar = 0         # Progressbar (Null Prozent)
            PopUp.create('zattooHiQ lade Programm Informationen ...', '')
            PopUp.update(bar)
            #c.close
        for chan in channels['index']:
            #if DEBUG: print str(chan) + ' - ' + str(startTime) + str(endTime)
            
            try:
                c.execute('SELECT * FROM programs WHERE channel = ? AND start_date < ? AND end_date > ?', [chan, endTime, startTime])
            except:pass
            
            f=c.fetchall()
            
            for row in f:
       
                description_long = row['description_long']
                #debug(str(row['channel'])+' ' +str(row['description_long']))
                if notify:
                    bar += 1
                    percent = int(bar * 100 / counter)
                
                if description_long is None:
                    #debug (str(row['channel'])+' ' +str(row["showID"]))
                    if notify:
                        PopUp.update(percent,localString(31922), localString(31923) + str(row['channel']))
                    description_long = self.getShowLongDescription(row["showID"])
                    
        c.close()
        if notify:
            PopUp.close()
            #xbmc.executebuiltin("Dialog.Close(busydialog)")
        return
  def dummy(self, notify=False, startTime=datetime.datetime.now(), endTime=datetime.datetime.now()):
        import urllib.request, urllib.parse, urllib.error
        fav = False
        if __addon__.getSetting('onlyfav') == 'true': fav = True
        channels = self.getChannelList(fav)
        
        c = self.conn.cursor()
        c.execute('SELECT * FROM channels ORDER BY weight ASC LIMIT 1')
        chan = c.fetchone()

        #if DEBUG: print str(chan) + ' - ' + str(startTime) + str(endTime)
        
        try:
            c.execute('SELECT * FROM programs WHERE channel = ? AND start_date < ? AND end_date > ?', [row['id'], endTime, startTime])
        except:pass
        
        f=c.fetchall()
        
        for row in f:
            debug(row[0])
            description_long = row['description_long']
            debug(str(row['channel'])+' ' +str(row['description_long']))
            # if notify:
                # bar += 1
                # percent = int(bar * 100 / counter)
            
            if description_long is None:
                debug ('LoadLongDescription '+str(description_long)+' ' + str(row['channel'])+' ' +str(row["showID"]))
                # if notify:
                    # PopUp.update(percent,localString(31922), localString(31923) + str(row['channel']))
                description_long = self.getShowLongDescription(row["showID"])
                
        c.close()

        return

  def cleanProg(self, silent=False):
        d = (datetime.datetime.today() - datetime.timedelta(days=8))
        midnight = datetime.time(0)
        datelow = datetime.datetime.combine(d, midnight)
        #print 'CleanUp  ' + str(datelow)
        try:
            c = self.conn.cursor()
            c.execute('SELECT * FROM programs WHERE start_date < ?', [datelow])
            r=c.fetchall()
        except:
            c.close
            return

        if len(r)>0:
            #print 'Anzahl Records  ' + str(len(r))
            dialog = xbmcgui.Dialog()
            if (silent or  dialog.yesno(localString(31918), str(len(r)) + ' ' + localString(31920), '', '',local(106),local(107))):
                count=len(r)
                bar = 0         # Progressbar (Null Prozent)
                if (not silent):
                  PopUp = xbmcgui.DialogProgress()
                  PopUp.create(localString(31913), '')
                  PopUp.update(bar)

                for row in r:
                    c.execute('DELETE FROM programs WHERE showID = ?', (row['showID'],))
                    if (not silent):
                      bar += 1
                      PopUp.update(int(bar * 100 / count),  str(count-bar) + localString(31914))
                      if (PopUp.iscanceled()):
                          c.close
                          return

                if (not silent): PopUp.close()

        self.conn.commit()
        
        date = datetime.date.today()
        try:
            c = self.conn.cursor()
            c.execute('DELETE FROM updates WHERE date < ?', [date])
            r=c.fetchall()
        except:
            c.close
            return
        
        self.conn.commit()
        c.close()
        return

  def formatDate(self, timestamp):
        if timestamp:
            format = xbmc.getRegion('datelong')
            date = timestamp.strftime(format)
            date = date.replace('Monday', local(11))
            date = date.replace('Tuesday', local(12))
            date = date.replace('Wednesday', local(13))
            date = date.replace('Thursday', local(14))
            date = date.replace('Friday', local(15))
            date = date.replace('Saturday', local(16))
            date = date.replace('Sunday', local(17))
            date = date.replace('January', local(21))
            date = date.replace('February', local(22))
            date = date.replace('March', local(23))
            date = date.replace('April', local(24))
            date = date.replace('May', local(25))
            date = date.replace('June', local(26))
            date = date.replace('July', local(27))
            date = date.replace('August', local(28))
            date = date.replace('September', local(29))
            date = date.replace('October', local(30))
            date = date.replace('November', local(31))
            date = date.replace('December', local(32))
            return date
        else:
            return ''

  def getSeries(self, showID):
        c = self.conn.cursor()
        c.execute('SELECT series FROM programs WHERE showID = ?', [showID])
        series = c.fetchone()
        #print str(showID)+'  '+str(series['series'])
        c.close()
        return series['series']
  
  def getRestart(self, showID):
        
        c = self.conn.cursor()
        c.execute('SELECT restart FROM programs WHERE showID = ?', [showID])
        restart = c.fetchone()
        if restart is None:
            api = '/zapi/program/details?program_id=' + showID + '&complete=True'
            showInfo = self.zapiSession().exec_zapiCall(api, None)
            #debug("ShowInfo :" + str(showInfo))
            try:
                restart = showInfo['program']['selective_recall_until']
                c.execute('UPDATE programs SET restart=? WHERE showID=?', [True, showID])
                #print 'Restart  ' +str(showID) + '  ' + str(restart)
            except:
                debug('No Restart')
                c.execute('UPDATE programs SET restart=? WHERE showID=?', [False, showID])
            self.conn.commit()
            
        c.close()
        return restart['restart']

  def get_version(self, version):
        try:
            c = self.conn.cursor()
            c.execute('SELECT version FROM version')
            row = c.fetchone()
            version = row['version']
            c.close
            #debug('Version:'+str(version))
            return version
        except:
            self._createTables()
            self.set_version(version)
            
  def get_search(self):
        
    c = self.conn.cursor()
    c.execute('SELECT * FROM search')
    searchList = {'index':[]}

    for row in c:
        searchList[row['search']]={
        'id': str(row['search'])
        }
        searchList['index'].append(str(row['search']))
  
    c.close()
    return searchList
    
            
  def set_search(self,search):
    c = self.conn.cursor()
    try:
        c.execute('INSERT INTO search(search) VALUES(?)', [search])
    except:pass
    self.conn.commit()
    #c.execute("SELECT Count(*) FROM `search`")
    # for res in c:
        # debug(res[0])
        # if res[0] > 10:
            # debug(res[0])
            # c.execute('delete  from search limit 1')
    c.close()
   
  def del_search(self,al=False,search=''): 
    debug('DEl-Search ' + str(al)+' ' +str(search))
    c = self.conn.cursor()    
    if al == 'True':
        c.execute('DELETE FROM search')
        debug('True')
    else:
        c.execute('DELETE FROM search WHERE search=?', [search])
    self.conn.commit()
    c.close()
    
  def edit_search(self,search):
    
    item = xbmcgui.Dialog().input(__addon__.getLocalizedString(31200), defaultt=search, type=xbmcgui.INPUT_ALPHANUM)
    if item == "": return
    c = self.conn.cursor()
    try:
       c.execute('UPDATE search SET search=? WHERE search=?', [item, search])
    except:pass
    self.conn.commit()  
    c.close()
    return item
    
  def set_version(self, version):
    c = self.conn.cursor()
    c.execute('DELETE FROM version')
    c.execute('INSERT INTO version(version) VALUES(?)', [version])
    self.conn.commit()
    c.close()
    

  def set_category(self):
    channels = self.getChannelList(False)
    chan = repr(channels['index']).replace('[','(').replace(']',')') 
    #debug ('Channels: '+str(chan))
    time=datetime.datetime.now()
    c = self.conn.cursor()
    #c.execute('DELETE FROM programs WHERE showID IN (SELECT showID FROM programs GROUP by showID HAVING (COUNT(*) > 1 ))')
    #self.conn.commit()
    c.execute('SELECT category FROM programs WHERE channel IN %s GROUP by category' % chan)
    row = c.fetchall()
    cat=[]
    for category in row:
        
        gen = category['category']
        #debug ('Kat:' +str(gen))
        if gen == None: continue
        c.execute('SELECT category FROM programs WHERE channel IN (SELECT id FROM channels) AND category = ? AND start_date < ? AND end_date > ?', [gen, time, time])
        r = c.fetchall()
        
        for g in r:
            count = len(r)
        c.execute('SELECT category FROM programs WHERE channel IN (SELECT id FROM channels) AND category = ? AND start_date < ? AND end_date > ? GROUP by category', [gen, time, time])
        rb = c.fetchall()
        
        for a in rb:
            ge = a['category']
            if ge =='':continue
            debug('Kategorien:'+str(count)+' '+str(ge))
            cat.append({
            'category': ge,
            'len': count})
        
    c.close()
    return cat
    
  def get_category(self, cat, get_long_description=False, startTime=datetime.datetime.now(), endTime=datetime.datetime.now()):
         
    c = self.conn.cursor()

    c.execute('SELECT * FROM programs INNER JOIN channels ON programs.channel = channels.id AND category = ? AND start_date < ? AND end_date > ? ORDER by channels.weight', [cat, startTime, endTime])
    
    r = c.fetchall()
    programList = {'index':[]}
    
    for row in r:
        description_long = row['description_long']
        year = row['year']
        country = row['country']
        category =row['category']
        if get_long_description and description_long is None:
            #description_long = self.getShowInfo(row["showID"],'description')
            info = self.getShowLongDescription(row['showID'])
            #print 'ProgINFO  ' + str(type(info)) + ' ' + str(row['showID'])+ '  ' + str(info)
            if type(info) == dict:
                description_long = info.get('description','')
                year = info.get('year',' ')
                country = info.get('country','')
                category = info.get('category','')
        
        programList[row['channel']]={
            'channel': row['channel'],
            'showID' : row['showID'],
            'title' : row['title'],
            'description' : row['description'],
            'description_long' : description_long,
            'year': year, #row['year'],
            'genre': row['genre'],
            'country': country, #row['country'],
            'category': category, #row['category'],
            'start_date' : row['start_date'],
            'end_date' : row['end_date'],
            'image_small' : row['image_small'],
            'credits': row['credits']
        }
        programList['index'].append(str(row['channel']))
    c.close()
    debug ('Kategorien: '+str(programList))
    return programList
