# coding=utf-8
#
#    copyright (C) 2020 Steffen Rolapp (github@rolapp.de)
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

#print 'ZattooHiq-Service started'

import xbmc, xbmcgui, xbmcaddon, datetime, time, xbmcvfs
import os, urllib.parse

from resources.lib.library import library
from resources.lib.zattooDB import ZattooDB
from resources.lib.zapisession import ZapiSession

#import web_pdb;

global player

_zattooDB_ = ZattooDB()
__addon__ = xbmcaddon.Addon()
__addondir__  = xbmcvfs.translatePath( __addon__.getAddonInfo('profile') )
__addonId__=__addon__.getAddonInfo('id')

_library_=library()
localString = __addon__.getLocalizedString

DEBUG = __addon__.getSetting('debug')
accountData=_zattooDB_.zapi.get_accountData()

def debug(content):
    if DEBUG:log(content, xbmc.LOGDEBUG)

def notice(content):
    log(content, xbmc.LOGINFO)

def log(msg, level=xbmc.LOGINFO):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level)

def script_chk(script_name):
    return xbmc.getCondVisibility('System.AddonIsEnabeled(%s)' % script_name)

def refreshProg():
    import urllib.request, urllib.parse, urllib.error
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
    import urllib.request, urllib.parse, urllib.error
    from resources.lib.zattooDB import ZattooDB
    _zattooDB_ = ZattooDB()
    try:
        if accountData['nonlive']['recording_number_limit'] > 0:
            resultData = _zattooDB_.zapi.exec_zapiCall('/zapi/playlist', None)
            if resultData is None: return
            for record in resultData['recordings']:
                _zattooDB_.getShowInfo(record['program_id'])
            _library_.delete_library() # add by samoth
            _library_.make_library()
    except: return
    
def start():
    from resources.lib.zattooDB import ZattooDB
    _zattooDB_ = ZattooDB()
    
	# reload Account
    # xbmcgui.Dialog().notification(localString(30104), localString(31024),  __addon__.getAddonInfo('path') + '/resources/icon.png', 500, False)
    # profilePath = xbmcvfs.translatePath(__addon__.getAddonInfo('profile'))
    # os.remove(os.path.join(profilePath, 'cookie.cache'))
    # os.remove(os.path.join(profilePath, 'session.cache'))
    # os.remove(os.path.join(profilePath, 'account.cache'))
    _zattooDB_.zapiSession()

    player=myPlayer()
    VERSION = __addon__.getAddonInfo('version')
    OLDVERSION = _zattooDB_.get_version(VERSION)

    if OLDVERSION != VERSION:
    
        # reload DB
        #_zattooDB_.reloadDB()
        # set Version
        _zattooDB_.set_version(VERSION)

    import urllib.request, urllib.parse, urllib.error
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

    def __init__( self, skip=0, *args):
      
      self.skip=skip
      self.startTime=0
      self.playing=True
      self.playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
      
    def onPlayBackStarted(self):
        from resources.lib.zattooDB import ZattooDB
        _zattooDB_ = ZattooDB()
        live = 'false'
        streams = xbmc.getInfoLabel('Player.Filenameandpath')
        showID = xbmc.getInfoLabel('VideoPlayer.Writer')
        channel = xbmc.getInfoLabel('VideoPlayer.Director')
        _zattooDB_.set_playing(channel, showID, streams, 0)
        
        # load Keymap for liveTV
        if streams.find('dash-live')>-1 or streams.find('hls5-live')>-1 or streams.find('dashenc-live')>-1 or streams.find('hls7-live')>-1:
            live = 'true'
            self.loadKeymap()
        else: 
            self.unloadKeymap()
            

    def onPlayBackStopped(self):
      self.unloadKeymap()
      self.playing=False
      self.playlist.clear()

    def onPlayBackEnded(self):
      playing = _zattooDB_.get_playing()
      if playing['channel'] != '': 
          ret = xbmcgui.Window(12005).getProperty('after_recall')
          #GreenAir: switch to live
          if ret == "1":
            playing = _zattooDB_.get_playing()
            xbmc.executebuiltin('RunPlugin("plugin://'+__addonId__+'/?mode=watch_c&id='+playing['channel'] +'")')
          #GreenAir: continue with next recall
          elif ret == "2":
            playing = _zattooDB_.get_playing()
            program = _zattooDB_.get_showID(playing['showID'])[0]
            nextprog = _zattooDB_.getPrograms({'index':[program['channel']]}, True, program['end_date']+datetime.timedelta(seconds=20), program['end_date']+datetime.timedelta(seconds=50))[0]
    
            xbmc.executebuiltin('RunPlugin("plugin://'+__addonId__+'/?mode=watch_c&id='+nextprog['channel'] + '&showID=' + nextprog['showID'] +'&restart=true")')
    
            notice ('continueRecall program:'+str(program))
            notice ('continueRecall nextprog:'+str(nextprog))

            
    def loadKeymap(self):

      source = __addondir__ + '/zattooKeymap.xml'
      dest = xbmcvfs.translatePath('special://profile/keymaps/zattooKeymap.xml')
      if os.path.isfile(dest): return
      with open(source, 'r') as file: content = file.read()
      with open(dest, 'w') as file: file.write(content)
      xbmc.sleep(200)
      xbmc.executebuiltin('Action(reloadkeymaps)')

    def unloadKeymap(self):

      path=xbmcvfs.translatePath('special://profile/keymaps/zattooKeymap.xml')
      if os.path.isfile(path):
        try:
          os.remove(path)
          xbmc.sleep(200)
          xbmc.executebuiltin('Action(reloadkeymaps)')
        except:pass


