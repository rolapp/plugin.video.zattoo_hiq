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

import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
import sys, urllib.parse, urllib.request, urllib.error
import ast
from resources.lib.zattooDB import ZattooDB
_zattooDB_ = ZattooDB()

__addon__       = xbmcaddon.Addon()
__addonId__     =__addon__.getAddonInfo('id')
__addonname__   = __addon__.getAddonInfo('name')
__addondir__    = xbmcvfs.translatePath( __addon__.getAddonInfo('profile') )
#__addonhandle__ = int(sys.argv[1])
__addonuri__    = sys.argv[0]

ICON_PATH       = __addon__.getAddonInfo('path') + '/resources/icon.png'
STREAM_TYPE     = "dash"
DOLBY           = __addon__.getSetting('dolby')
MAX_BANDWIDTH   = __addon__.getSetting('max_bandwidth')
DEBUG           = __addon__.getSetting('debug')
YPIN		 = __addon__.getSetting('ypin')

def debug(content):
    if DEBUG:log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGINFO)

def log(msg, level=xbmc.LOGINFO):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 
    
    
class vod:
    def __init__(self):
        self.zapi = _zattooDB_.zapiSession()
        self.watchlist = self.get_watchlist()
        self.wl = False
        
    def subscription(self):
        # get VoD Subscription
        api = '/zapi/vod/subscriptions'
        subscription = self.zapi.exec_zapiCall(api, None)
        for i in subscription:
            debug('Subscription: ' + str(i))
        return subscription
        
    def main_menu(self, __addonhandle__, page='vod_zattoo_webmobile'):
        
        if 'subscriptions' not in locals():
            subscription = self.subscription()
        
        # get VoD Main Menu
        api = '/zapi/v2/cached/' + self.zapi.AccountData['power_guide_hash'] + '/pages/' + page +'?'
        vod_main = self.zapi.exec_zapiCall(api, None)
        debug(vod_main)
        if vod_main is None: return

        for main in vod_main['elements']:
            path = main['element_zapi_path']
            api = path +'?page=0&per_page=10'
            vod_sub = self.zapi.exec_zapiCall(api, None)
            debug(vod_sub)
            if not vod_sub: continue
            if main["element_content_id"] == "de_replay_all": continue
            if vod_sub['teasers_total'] == 0: continue
            #for teasers in vod_sub['teasers']:
                        
            if vod_sub['teasers'][0]['teasable_type'] == 'Vod::Series': continue
            if vod_sub['teasers'][0]['teasable_type'] == 'Vod::Movie':
                sub = vod_sub['teasers'][0]['teasable']['terms_catalog'][0]['terms'][0]['subscription_sku']
                debug(sub)
                if sub not in subscription: continue
                
            li = xbmcgui.ListItem(vod_sub['title'] + ' [COLOR ff00ff00](' + str(vod_sub['teasers_total']) + ')[/COLOR]')
            if vod_sub['logo_token']:
                li.setArt({'icon': 'https://logos.zattic.com/logos/' + vod_sub['logo_token'] + '/black/140x80.png'})
            else: li.setArt({'icon': ICON_PATH})
            xbmcplugin.addDirectoryItem(
                handle = __addonhandle__,
                url = __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'vod_sub', 'path': vod_sub['zapi_path'], 'total': vod_sub['teasers_total'], 'title': vod_sub['title']}),
                listitem = li,
                isFolder = True,
            )

        xbmcplugin.endOfDirectory(__addonhandle__, succeeded=True, updateListing=True, cacheToDisc=False)

    def sub_menu(self, __addonhandle__, title, path, total):
        # get VoD Sub Menu
        
        xbmcplugin.addDirectoryItem(
            handle = __addonhandle__,
            isFolder = True,
            listitem = xbmcgui.ListItem('[COLOR blue]' + title + '[/COLOR]'),
            url = __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'vod_sub', 'path': path, 'title': title, 'total': total}),
        )
        listing = []
        pfad=''
        token=''
        t_type=''
        t_id=''
        token = ''
        s_id=''
        
        for page in range (int(int(total)/10)+1):
            api = path + '?page=' + str(page) + '&per_page=10'
            vod_sub = self.zapi.exec_zapiCall(api, None)
            debug('sub' + str(vod_sub))
            if vod_sub['page_public_id']: self.main_menu(vod_sub['page_public_id'])
               
            for teasers in vod_sub['teasers']:

                t_type = teasers['teasable_type']
                t_id = teasers['teasable_id']
                data = teasers['teasable']
                if t_id in self.watchlist: self.wl = True
                else: self.wl = False
                    
                try:
                    s_id = teasers['teasable']['current_season']['id']
                except: pass
                episode = ''
                director = []
                cast = []
                if t_type == 'Avod::Video': 
                    pfad ='avod/videos/' + data['token'] + '/watch'
                    params = {
                            'stream_type': STREAM_TYPE,
                            'youth_protection_pin': YPIN
                            }
                elif t_type == 'Vod::Video': 
                    pfad = '/zapi/watch/vod/video'
                    try:
                        token = data['terms_catalog'][0]['terms'][0]['token']
                    except:
                        token = data['current_season']['terms_catalog'][0]['terms'][0]['token']
                    params = {
                            'term_token': str(token),
                            'teasable_id': str(t_id),
                            'teasable_type': t_type,
                            'stream_type': STREAM_TYPE,
                            'youth_protection_pin': YPIN
                            }
                    if data['credits'] != []:
                        if 'directors' in data['credits']:
                            for name in data['credits']['directors']:
                                director.append(name['name'])
                        if 'actors' in data['credits']:
                            for name in data['credits']['actors']:
                                cast.append(name['name'])
                    try:
                        year = data['year']
                    except:
                        year = ''
                    try:
                        duration = data['duration']   
                    except:
                        duration = data['runtime'] * 60
    
                    if data['subtitle']: episode = ' - ' + data['subtitle']
                    image_url = 'https://images.zattic.com/cms/' + data['image_token'] + '/format_480x360.jpg'
                    if self.wl:
                        title = '[COLOR gold]' + data['title'] + episode + '[/COLOR]'
                    else:
                        title = data['title'] + episode
                    meta = {
                            'title': title,
                            'plot': data['description'],
                            #'country': data['countries'],
                            'genre': data['genres'],
                            'year': year,
                            'duration': duration,
                            'director': director,
                            'cast': cast
                            }
                        
                elif t_type == 'Vod::Movie': 
                    pfad = '/zapi/watch/vod/video'
                    try:
                        token = data['terms_catalog'][0]['terms'][0]['token']
                    except:
                        token = data['current_season']['terms_catalog'][0]['terms'][0]['token']
                    params = {
                            'term_token': str(token),
                            'teasable_id': str(t_id),
                            'teasable_type': t_type,
                            'stream_type': STREAM_TYPE,
                            'youth_protection_pin': YPIN
                            }
                            
                    if data['credits'] != []:
                        if 'directors' in data['credits']:
                            for name in data['credits']['directors']:
                                director.append(name['name'])
                        if 'actors' in data['credits']:
                            for name in data['credits']['actors']:
                                cast.append(name['name'])
                    try:
                        year = data['year']
                    except:
                        year = ''
                    try:
                        duration = data['duration']   
                    except:
                        duration = data['runtime'] * 60
    
                    if data['subtitle']: episode = ' - ' + data['subtitle']
                    image_url = 'https://images.zattic.com/cms/' + data['image_token'] + '/format_480x360.jpg'
                    if self.wl:
                        title = '[COLOR gold]' + data['title'] + episode + '[/COLOR]'
                    else:
                        title = data['title'] + episode
                    meta = {
                            'title': title,
                            'plot': data['description'],
                            #'country': data['countries'],
                            'genre': data['genres'],
                            'year': year,
                            'duration': duration,
                            'director': director,
                            'cast': cast
                            }
                            
                elif t_type == 'Tv::Broadcast': 
                    pfad = '/v3/watch/replay/' + data['cid'] + '/' + str(data['id'])
                    
                    # try:
                        # token = data['terms_catalog'][0]['terms'][0]['token']
                    # except:
                        # token = data['current_season']['terms_catalog'][0]['terms'][0]['token']
                    params = {
                            #'term_token': str(token),
                            #'teasable_id': str(t_id),
                            #'teasable_type': t_type,
                            'stream_type': 'dash_widevine',
                            'youth_protection_pin': YPIN,
                            'max_drm_lvl': '1'
                            }
                            
                    if data['cr'] != []:
                        if 'director' in data['cr']:
                            for name in data['cr']['director']:
                                director.append(name)
                        if 'actor' in data['cr']:
                            for name in data['cr']['actor']:
                                cast.append(name)
                                
                    if data['g']:
                        for genre in data['g']:
                            director.append(genre)
                    try:
                        year = data['year']
                    except:
                        year = ''
                    #try:
                        #duration = data['duration']   
                    #except:
                        #duration = data['runtime'] * 60
    
                    if data['et']: episode = ' - ' + data['et']
                    if data['i_t']: image_url = 'https://images.zattic.com/cms/' + data['i_t'] + '/format_480x360.jpg'
                    if self.wl:
                        title = '[COLOR gold]' + data['t'] + episode + '[/COLOR]'
                    else:
                        title = data['t'] + episode
                    meta = {
                            'title': title,
                            'plot': data['d'],
                            #'country': data['countries'],
                            #'genre': data['g'],
                            'year': year,
                            #'duration': duration,
                            'director': director,
                            'cast': cast
                            }
                            
                li = xbmcgui.ListItem(label=title)
                li.setInfo('video', meta)
                li.setProperty('IsPlayable','true') 
                li.setArt({'thumb':image_url, 'fanart':image_url, 'landscape':image_url,'icon':image_url})
                url = __addonuri__ + '?' + urllib.parse.urlencode({'mode': 'vod_watch','pfad': pfad, 'params':params})

                debug(url)
                isFolder = False
                listing.append((url, li, isFolder))
                contextMenuItems = []
                contextMenuItems.append(('Info', 'Action(Info)'))
                if t_type == 'Vod::Movie':
                    para = {'teasable_id': t_id, 'teasable_type': t_type}
                    if self.wl:
                        contextMenuItems.append(('Remove from Watchlist', 'RunPlugin("plugin://'+__addonId__+'/?mode=remove_wl&params='+str(para)+'")',))
                    else:
                        contextMenuItems.append(('Add to Watchlist', 'RunPlugin("plugin://'+__addonId__+'/?mode=add_wl&params='+str(para)+'")',))
                li.addContextMenuItems(contextMenuItems, replaceItems=True) 
                       
        xbmcplugin.addDirectoryItems(__addonhandle__, listing)
        xbmcplugin.setContent(__addonhandle__, 'movies')
        xbmcplugin.addSortMethod(__addonhandle__, xbmcplugin.SORT_METHOD_LABEL )    
        xbmcplugin.endOfDirectory(__addonhandle__,  succeeded=True, updateListing=False, cacheToDisc=False)
        
    
    def vod_watch(self, __addonhandle__, pfad, params):
        params = ast.literal_eval(params)
        debug (type(params))
        resultData = self.zapi.exec_zapiCall(pfad , params)
        debug ('ResultData: '+str(resultData))
        if resultData is not None:
            streams = resultData['stream'][ "watch_urls"]
            
            if len(streams)==0:
                xbmcgui.Dialog().notification("ERROR", "NO STREAM FOUND, CHECK SETTINGS!", ICON_PATH, 5000, False)
                return
            elif len(streams) > 1 and  __addon__.getSetting('audio_stream') == 'B' and streams[1]['audio_channel'] == 'B': streamNr = 1
            else: streamNr = 0
            
        li = xbmcgui.ListItem(path=streams[0]['url'])
        if STREAM_TYPE == 'dash':
            li.setProperty('inputstream', 'inputstream.adaptive')
            li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        elif STREAM_TYPE == 'dash_widevine':
            li.setProperty('inputstream', 'inputstream.adaptive')
            li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            li.setProperty('inputstream.adaptive.license_key', streams[0]['license_url'] + "||a{SSM}|")
            li.setProperty('inputstream.adaptive.license_type', "com.widevine.alpha")
        elif STREAM_TYPE == 'hls7':
            li.setProperty('inputstream', 'inputstream.adaptive')
            li.setProperty('inputstream.adaptive.manifest_type', 'hls')

            
        xbmcplugin.setResolvedUrl(__addonhandle__, True, li)
        pos = 0
        player = xbmc.Player()
        while (player.isPlaying()):
            try: pos=player.getTime()
            except: pass
            xbmc.sleep(100)
    
    def get_watchlist(self):
        # get watchlist
        api = '/zapi/v2/cached/' + self.zapi.AccountData['power_guide_hash'] + '/teaser_collections/ptc_vod_watchlist_movies_landscape'
        vod_wl = self.zapi.exec_zapiCall(api, None)
        watchlist = []
        if not vod_wl: return None
        for teasers in vod_wl['teasers']:
            watchlist.append(teasers['teasable_id'])
        debug(watchlist)
        return watchlist
                
    def add_watchlist(self, params):
        debug('vod_add')
        params = ast.literal_eval(params)
        api = "/zapi/v2/vod/watch_list/add"
        vod_add = self.zapi.exec_zapiCall(api, params)
        debug(vod_add)
        self.watchlist = self.get_watchlist()
        xbmc.executebuiltin('Container.Refresh')
        debug(xbmc.getInfoLabel('Container.FolderPath'))
        
    def remove_watchlist(self, params):
        debug('vod_remove')
        params = ast.literal_eval(params)
        debug(type(params))
        api = "/zapi/v2/vod/watch_list/remove"
        vod_remove = self.zapi.exec_zapiCall(api, params)
        debug(vod_remove)
        self.watchlist = self.get_watchlist()
        xbmc.executebuiltin('Container.Refresh')
        
                    
        
            
        
        
        
    
