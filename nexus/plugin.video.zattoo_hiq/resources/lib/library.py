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

import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
import sys, urllib.parse
import  time, datetime, threading
import io
from resources.lib.zattooDB import ZattooDB

__addon__ = xbmcaddon.Addon()
__addonId__=__addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
_zattooDB_ = ZattooDB()

_timezone_ = int(__addon__.getSetting('time_offset'))*60*-60 #-time.altzone

DEBUG = __addon__.getSetting('debug')

def debug(s):
	if DEBUG: xbmc.log(str(s), xbmc.LOGDEBUG)

class library:
  
  def make_library(self):
    folder=__addon__.getSetting('library_dir')
    if folder == '': return
    import os
    libraryPath = xbmcvfs.translatePath(folder)
    if not os.path.exists(libraryPath): os.makedirs(libraryPath)
    
    resultData = _zattooDB_.zapi.exec_zapiCall('/zapi/playlist', None)
    debug('Resultdata:'+str(resultData))
    if resultData is None: return
    for record in resultData['recordings']:
      showInfo=_zattooDB_.getShowInfo(record['program_id'])
      #debug(str(showInfo))
      start = int(time.mktime(time.strptime(record['start'], "%Y-%m-%dT%H:%M:%SZ"))) + _timezone_  # local timestamp
      if showInfo == "NONE": continue
      if not showInfo: continue
      if showInfo[0]['et']: name=showInfo[0]['t']+'-'+showInfo[0]['et']
      else: name=showInfo[0]['t']
  
      fileName=slugify(name)
      strmFile=os.path.join(libraryPath, fileName+"/"+fileName+".strm")
      if os.path.exists(os.path.dirname(strmFile)):continue
      strmFile=str(strmFile).encode('utf-8')
      try:
        if not os.path.exists(os.path.dirname(strmFile)):
            os.makedirs(os.path.dirname(strmFile))
      except OSError as err:
        print(err)      
    
      with open(strmFile, 'w', encoding="utf-8", errors='namereplace') as f:
        f.write('plugin://'+__addonId__+'/?mode=watch_r&id='+str(record['id'])+'&start='+str(start))

      
      out='<?xml version="1.0" encoding="UTF-8" standalone="yes" ?><movie>'
      out+='<title>'+name+' [COLOR red]ZBE[/COLOR]</title>'
      out+='<year>'+str(showInfo[0]['year'])+'</year>'
      out+='<plot>'+showInfo[0]['d']+'</plot>'
      out+='<thumb>'+showInfo[0]['i_url']+'</thumb>'
      out+='<fanart><thumb>'+showInfo[0]['i_url']+'</thumb></fanart>'
      out+='<genre clear="true>'+str(showInfo[0]['g'])+'</genre>'
      # for actor in showInfo[0]['cr']['actor']:
        # out+='<actor><name>'+actor+'</name></actor>'
      #out+='<actor>'+str(showInfo[0]['cr']['actor'])+'</actor>'

      out+='</movie>'
      
      nfoFile=os.path.join(libraryPath, fileName+"/"+fileName+".nfo")
      nfoFile=str(nfoFile).encode('utf-8')
      debug(nfoFile)
      with open(nfoFile,"w", encoding='utf-8') as f:
        f.write(out)
    
      
      max_bandwidth = __addon__.getSetting('max_bandwidth')
      params = {'recording_id': record['id'], 'stream_type': 'hls', 'maxrate': max_bandwidth}
      Data = _zattooDB_.zapi.exec_zapiCall('/zapi/watch', params)
      #debug('resultdata'+str(Data)+'  '+str(record['id']))
      if Data is not None:
        streams = Data['stream']['watch_urls']
        debug('resultData:'+str(streams))
        if len(streams)==0:
          xbmcgui.Dialog().notification("ERROR", "NO STREAM FOUND, CHECK SETTINGS!", channelInfo['logo'], 500, False)
          return
        elif len(streams) > 1 and  __addon__.getSetting('audio_stream') == 'B' and streams[1]['audio_channel'] == 'B': streamNr = 1
        else: streamNr = 0
        dlFile=os.path.join(libraryPath, fileName+"/"+fileName+".dl")
        dlFile=str(dlFile).encode('utf-8')
        with open(dlFile,"w", encoding='utf-8') as f:
            f.write(streams[streamNr]['url'])

    xbmcgui.Dialog().notification('Ordner für Filme aktualisiert', __addon__.getLocalizedString(31251),  __addon__.getAddonInfo('path') + '/resources/icon.png', 500, False)    
      #xbmcgui.Dialog().notification(localString(31106), localString(31915),  __addon__.getAddonInfo('path') + '/icon.png', 3000, False) 
      
# added - by Samoth  
  def delete_library(self): 
    folder=__addon__.getSetting('library_dir') 
    if not folder: return 
    import os, shutil 
    libraryPath = xbmcvfs.translatePath(folder) 
    if os.path.exists(libraryPath) and libraryPath != "": 
      shutil.rmtree(libraryPath)  
      
# added - by Samoth
  def delete_entry_from_library(self, recording_id): 
    import os, shutil 
    folder=__addon__.getSetting('library_dir') 
    if not folder: return 
    libraryPath = xbmcvfs.translatePath(folder)
    resultData = _zattooDB_.zapi.exec_zapiCall('/zapi/playlist', None) 
    for record in resultData['recordings']: 
      if recording_id == str(record['id']): 
        showInfo=_zattooDB_.getShowInfo(record['program_id']) 
        if showInfo == "NONE": continue 
        
        if showInfo[0]['et']: name=showInfo[0]['t']+'-'+showInfo[0]['et'] 
        else: name=showInfo[0]['t'] 
  
        fileName=slugify(name) 
        strmDir=os.path.join(libraryPath, fileName) 
        if os.path.exists(os.path.dirname(strmDir)): 
         shutil.rmtree(strmDir) 
        continue 
        
        
def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    import re, unicodedata
    #value = unicodedata.normalize('NFKD', value).encode('utf-8', 'ignore')
    value = str(re.sub('[^\w\s-]', '', value).strip().lower())
    value = str(re.sub('[-\s]+', '-', value))
    return value
  
