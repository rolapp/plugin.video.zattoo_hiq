# -*- coding: utf-8 -*-
#
#    copyright (C) 2020 Steffen Rolapp (github@rolapp.de)
#
#    based on ZattooBoxExtended by Daniel Griner (griner.ch@gmail.com) License under GPL
#    based on ZattooBox by Pascal Nançoz (nancpasc@gmail.com) Licence under BSD 2 clause
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

import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import sys, urllib

from resources.lib.zattooDB import ZattooDB

_zattooDB_ = ZattooDB()
__addon__       = xbmcaddon.Addon()
__addonId__     =__addon__.getAddonInfo('id')
__addonname__   = __addon__.getAddonInfo('name')
__addondir__    = xbmc.translatePath( __addon__.getAddonInfo('profile') )
__addonhandle__ = int(sys.argv[1])
__addonuri__    = sys.argv[0]

ICON_PATH       = __addon__.getAddonInfo('path') + '/resources/icon.png'
STREAM_TYPE     = __addon__.getSetting('stream_type')
DOLBY           = __addon__.getSetting('dolby')
MAX_BANDWIDTH   = __addon__.getSetting('max_bandwidth')
DEBUG           = __addon__.getSetting('debug')

def debug(content):
    if DEBUG:log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 
    
    
class vod:
    def __init__(self):
        self.zapi = _zattooDB_.zapiSession()
        
    def main_menu(self):
        # get VoD Main Menu
        api = '/zapi/v2/cached/' + self.zapi.SessionData['session']['power_guide_hash'] + '/pages/vod_zattoo_webmobile?'
        vod_main = self.zapi.exec_zapiCall(api, None)
        if vod_main is None: return
        
        for main in vod_main['elements']:
            path = main['element_zapi_path']
            if 'avod' in path and not 'curated' in path:
                api = path +'?page=0&per_page=10'
                vod_sub = self.zapi.exec_zapiCall(api, None)

                xbmcplugin.addDirectoryItem(
                    handle = __addonhandle__,
                    url = __addonuri__+ '?' + urllib.urlencode({'mode': 'vod_sub', 'path': vod_sub['zapi_path'], 'total': vod_sub['teasers_total'], 'title': vod_sub['title']}),
                    listitem = xbmcgui.ListItem(vod_sub['title'] + ' [COLOR ff00ff00](' + str(vod_sub['teasers_total']) + ')[/COLOR]', iconImage = ICON_PATH),
                    isFolder = True,
                )

        xbmcplugin.endOfDirectory(__addonhandle__)

    def sub_menu(self, title, path, total):
        # get VoD Sub Menu

        xbmcplugin.addDirectoryItem(
			handle = __addonhandle__,
			isFolder = True,
			listitem = xbmcgui.ListItem('[COLOR blue]' + title + '[/COLOR]', iconImage = ICON_PATH),
		url = __addonuri__+ '?' + urllib.urlencode({'mode': 'vod_sub', 'path': path, 'title': title, 'total': total}),
        )
        listing = []
        for page in range (int(int(total)/10)+1):
            api = path + '?page=' + str(page) + '&per_page=10'
            vod_sub = self.zapi.exec_zapiCall(api, None)
            
            for data in vod_sub['teasers']:
                data = data['teasable']
                image_url = 'https://images.zattic.com/cms/' + data['image_token'] + '/format_480x360.jpg'
                meta = {
                        'title': data['title'],
                        'plot': data['description'],
                        'country': data['countries'],
                        'genre': data['genres'],
                        'year': data['year'],
                        'duration': data['duration']
                        }
                li = xbmcgui.ListItem(label=data['title'])
                li.setInfo('video', meta)
                li.setProperty('IsPlayable','true') 
                li.setArt({'thumb':image_url, 'fanart':image_url, 'landscape':image_url,'icon':image_url})
                url = __addonuri__ + '?' + urllib.urlencode({'mode': 'vod_watch','token': data['token']})
                isFolder = False
                listing.append((url, li, isFolder))
                
        xbmcplugin.addDirectoryItems(__addonhandle__, listing)
        xbmcplugin.setContent(__addonhandle__, 'movies')    
        xbmcplugin.endOfDirectory(__addonhandle__)
        
    def vod_watch(self, token):
        params = {'stream_type': STREAM_TYPE, 'maxrate': MAX_BANDWIDTH, 'enable_eac3': DOLBY}
        resultData = self.zapi.exec_zapiCall('/zapi/avod/videos/' + token + '/watch', params)
        debug ('ResultData: '+str(resultData))
        if resultData is not None:
            streams = resultData['stream']['watch_urls']
            
            if len(streams)==0:
                xbmcgui.Dialog().notification("ERROR", "NO STREAM FOUND, CHECK SETTINGS!", ICON_PATH, 5000, False)
                return
            elif len(streams) > 1 and  __addon__.getSetting('audio_stream') == 'B' and streams[1]['audio_channel'] == 'B': streamNr = 1
            else: streamNr = 0
            
        li = xbmcgui.ListItem(path=streams[streamNr]['url'])
        if STREAM_TYPE == 'dash':
            li.setProperty('inputstreamaddon', 'inputstream.adaptive')
            li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        if STREAM_TYPE == 'dash_widevine':
            li.setProperty('inputstreamaddon', 'inputstream.adaptive')
            li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            li.setProperty('inputstream.adaptive.license_key', streams[1]['license_url'] + "||a{SSM}|")
            li.setProperty('inputstream.adaptive.license_type', "com.widevine.alpha")
            
        xbmcplugin.setResolvedUrl(__addonhandle__, True, li)
        pos = 0
        player = xbmc.Player()
        while (player.isPlaying()):
            try: pos=player.getTime()
            except: pass
            xbmc.sleep(100)
    
    
                    
        
            
        
        
        
    
