# coding=utf-8
#
#    copyright (C) 2017 Steffen Rolapp (github@rolapp.de)
#
#    This file is part of zattooHiQ
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

import xbmc, xbmcgui, xbmcaddon, datetime, time
import os, urlparse
from resources.lib.library import library
from resources.lib.zattooDB import ZattooDB
from resources.lib.zapisession import ZapiSession

_zattooDB_ = ZattooDB()
__addon__ = xbmcaddon.Addon()
__addondir__  = xbmc.translatePath( __addon__.getAddonInfo('profile') ) 

_library_=library()
localString = __addon__.getLocalizedString

DEBUG = __addon__.getSetting('debug')

VERSION = __addon__.getAddonInfo('version')
OLDVERSION = _zattooDB_.get_version(VERSION)

def debug(content):
    if DEBUG:log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 
    
def refreshProg():
    import urllib
    monitor = xbmc.Monitor()
    while not monitor.abortRequested():
        if monitor.waitForAbort(600): break
        from resources.lib.zattooDB import ZattooDB
        _zattooDB_ = ZattooDB()
        #update programInfo
        startTime=datetime.datetime.now()
        endTime=datetime.datetime.now()+datetime.timedelta(minutes = 120)

        try:
            getProgNextDay()
            _zattooDB_.getProgInfo(False, startTime, endTime,'all')
        except:
            pass

def recInfo():
    import urllib
    from resources.lib.zattooDB import ZattooDB
    _zattooDB_ = ZattooDB()

    resultData = _zattooDB_.zapi.exec_zapiCall('/zapi/playlist', None)
    if resultData is None: return
    for record in resultData['recordings']:
        _zattooDB_.getShowInfo(record['program_id'])

def start():
    player=myPlayer()

    if OLDVERSION != VERSION:
        #_zattooDB_.reloadDB(True)
        _zattooDB_.set_version(VERSION)
        
    
    import urllib
    #xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
    #re-import ZattooDB to prevent "convert_timestamp" error
    from resources.lib.zattooDB import ZattooDB
    _zattooDB_ = ZattooDB()
    _zattooDB_.cleanProg(True)
    
    #re-import ZattooDB to prevent "convert_timestamp" error
    from resources.lib.zattooDB import ZattooDB
    _zattooDB_ = ZattooDB()
    _zattooDB_.updateChannels()
    
    #re-import ZattooDB to prevent "convert_timestamp" error
    from resources.lib.zattooDB import ZattooDB
    _zattooDB_ = ZattooDB()
    _zattooDB_.updateProgram()
    
    try: 
        tomorrow = datetime.datetime.today() + datetime.timedelta(days=1)
        _zattooDB_.updateProgram(tomorrow)
    except:pass


    startTime=datetime.datetime.now()#-datetime.timedelta(minutes = 60)
    endTime=datetime.datetime.now()+datetime.timedelta(minutes = 20)
    
    #re-import ZattooDB to prevent "convert_timestamp" error
    from resources.lib.zattooDB import ZattooDB
    _zattooDB_ = ZattooDB()
    #xbmcgui.Dialog().notification(localString(31916), localString(30110),  __addon__.getAddonInfo('path') + '/icon.png', 3000, False)
    
    if __addon__.getSetting('dbonstart') == 'true':
        _zattooDB_.getProgInfo(True, startTime, endTime)
        recInfo()
        _library_.delete_library() # add by samoth
        _library_.make_library()
  
    #xbmcgui.Dialog().notification(localString(31106), localString(31915),  __addon__.getAddonInfo('path') + '/icon.png', 3000, False)
    refreshProg()



def getProgNextDay():
    from resources.lib.zattooDB import ZattooDB
    _zattooDB_ = ZattooDB()

    start = datetime.time(14, 0, 0)
    now = datetime.datetime.now().time()
    tomorrow = datetime.datetime.today() + datetime.timedelta(days=1)

    if now > start:
        #debug('NextDay ' + str(start) + ' - ' + str(now) + ' - ' + str(tomorrow))
        _zattooDB_.updateProgram(tomorrow)


# start
class myPlayer(xbmc.Player):
    
    def __init__(self, skip=0):
      self.skip=skip
      self.startTime=0
      self.playing=True
      
      
    def onPlayBackStarted(self):
      #self.loadKeymap()
      if (self.skip>0):
        self.seekTime(self.skip)
        self.startTime=self.startTime-datetime.timedelta(seconds=self.skip)
      xbmc.sleep(200)
      playingFile=xbmc.getInfoLabel('Player.Filenameandpath')
      #print("playingfile: " + str(playingFile))
      if playingFile.find('dash-live')>-1 or playingFile.find('hls-live')>-1 or playingFile.find('dashenc-live')>-1:
            self.loadKeymap()
     
      else: #start recall while playing -> unload keymap
        self.unloadKeymap()
        
    #def onPlayBackSeek(self, time, seekOffset):
    #  if self.startTime+datetime.timedelta(milliseconds=time) > datetime.datetime.now():
    #    channel=_zattooDB_.get_playing()['channel']
        #_zattooDB_.set_playing() #clear setplaying to start channel in watch_channel
     #   self.playing=False
     #   xbmc.executebuiltin('RunPlugin("plugin://'+__addonId__+'/?mode=watch_c&id='+channel+'&showOSD=1")')
        
        
    def onPlayBackStopped(self):
      self.unloadKeymap()        
      self.playing=False;
      
    def onPlayBackEnded(self): 
      self.unloadKeymap()          
      self.playing=False;
     
        
    def loadKeymap(self):
            
      source = __addondir__ + '/zattooKeymap.xml'
      dest = xbmc.translatePath('special://profile/keymaps/zattooKeymap.xml')
      if os.path.isfile(dest): return
      with open(source, 'r') as file: content = file.read()
      with open(dest, 'w') as file: file.write(content)
      xbmc.sleep(200)
      xbmc.executebuiltin('XBMC.Action(reloadkeymaps)')

    def unloadKeymap(self):
      
      path=xbmc.translatePath('special://profile/keymaps/zattooKeymap.xml')
      if os.path.isfile(path):
        try:
          os.remove(path)
          xbmc.sleep(200)
          xbmc.executebuiltin('XBMC.Action(reloadkeymaps)')
        except:pass



