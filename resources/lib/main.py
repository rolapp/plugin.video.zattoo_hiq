# -*- coding: utf-8 -*-
#
#    copyright (C) 2017 Steffen Rolapp (github@rolapp.de)
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
import sys, urllib.parse,  os, json
import time, datetime, threading
import _strptime
    
from resources.lib.zattooDB import ZattooDB
from resources.lib.library import library
from resources.lib.guiactions import *
from resources.lib.keymap import KeyMap
from resources.lib.helpmy import helpmy


__addon__ = xbmcaddon.Addon()
__addonId__=__addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__addondir__  = xbmc.translatePath( __addon__.getAddonInfo('profile') )


_timezone_ = int(__addon__.getSetting('time_offset'))*60*-60 #-time.altzone

if __addon__.getSetting('show_favourites')=='true':_listMode_ ='favourites'
else: _listMode_ ='all'

_channelList_=[]
_zattooDB_=ZattooDB()
_library_=library()
_keymap_=KeyMap()
_helpmy_=helpmy()

global lastplaying
_umlaut_ = {ord('ä'): 'ae', ord('ö'): 'oe', ord('ü'): 'ue', ord('ß'): 'ss'}

localString = __addon__.getLocalizedString
local = xbmc.getLocalizedString
DEBUG = __addon__.getSetting('debug')

def debug(content):
    if DEBUG:log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level)

# get Timezone Offset
from tzlocal import get_localzone
#import resources.lib.pytz
try:
  tz = get_localzone()
  offset=tz.utcoffset(datetime.datetime.now()).total_seconds()
  _timezone_=int(offset)
except:pass

def convert_date(date):
  try:
      res = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
  except TypeError:
      res = datetime.datetime(*(time.strptime(date, "%Y-%m-%dT%H:%M:%SZ")[0:6]))
  res += datetime.timedelta(seconds=_timezone_)
  return str(res.strftime('%A,%d.%B %Y %H:%M'))

def formatTime(timestamp):
  if timestamp:
      format = xbmc.getRegion('time').replace(':%S', '').replace('%H%H', '%H')
      return timestamp.strftime(format)
  else:
      return ''
# This is a throwaway variable to deal with a python bug
#throwaway = datetime.datetime.strptime('20110101','%Y%m%d')
  
### Account Data ###

accountData=_zattooDB_.zapi.get_accountData()
premiumUser=accountData['session']['user']['subscriptions']!=[]

RECALL=accountData['session']['recall_eligible']
try:
  RESTART=accountData['session']['selective_recall_eligible']
except KeyError:RESTART = False

try:
  SERIE=accountData['session']['series_recording_eligible']
except KeyError:SERIE = False

RECORD=accountData['session']['recording_eligible']
if RECALL:
  __addon__.setSetting('recall', 'recall')
elif RESTART:
  __addon__.setSetting('recall', 'selectiv_recall')
else:
  __addon__.setSetting('recall', '')
try:
  country=accountData['session']['service_region_country']
  __addon__.setSetting('country', country)
except: pass

dateregistered=accountData['session']['user']['dateregistered']
__addon__.setSetting('dateregistered',convert_date(dateregistered))

if premiumUser:
  product=accountData['session']['user']['products'][0]['name']
  __addon__.setSetting('product', product)
  
  cost=accountData['session']['user']['products'][0]['cost']
  if cost != 0:
    currency=accountData['session']['user']['products'][0]['currency']
    price = str(float(cost)/100)
    __addon__.setSetting('price', price+' '+currency)
  else:
    __addon__.setSetting('price', '')
    
  expiration=accountData['session']['user']['subscriptions'][0]['expiration']
  if expiration is not None:
    __addon__.setSetting('expiration', convert_date(expiration))
  else:
    __addon__.setSetting('expiration', '')
  
  if accountData['session']['user']['subscriptions'][0]['autorenewing']:
    renewal_date=accountData['session']['user']['subscriptions'][0]['renewal_date']
    if expiration is not None:
      __addon__.setSetting('renewal_date', convert_date(renewal_date))
  else:
    __addon__.setSetting('renewal_date', '')
    
  if accountData['session']['user']['products'][0]['currency'] == 'CHF':
    __addon__.setSetting('country', 'CH')
    
else:
  __addon__.setSetting('product', '')
  __addon__.setSetting('price', '')
  __addon__.setSetting('expiration', '')
  __addon__.setSetting('renewal_date', '')
 
if __addon__.getSetting('country') == 'CH': SWISS = True
else: SWISS = False


stream_type = __addon__.getSetting('stream_type')
RECREADY = __addon__.getSetting('rec_ready')
RECNOW = __addon__.getSetting('rec_now')
VERSION = __addon__.getAddonInfo('version')
DOLBY = __addon__.getSetting('dolby')
KEYMAP = __addon__.getSetting('keymap')
   
if premiumUser or SWISS:
  xbmc.executebuiltin( "Skin.SetBool(%s)" %'record')
else: 
  xbmc.executebuiltin( "Skin.Reset(%s)" %'record')
  
if RECALL:
  xbmc.executebuiltin( "Skin.SetBool(%s)" %'restart')
else:
  xbmc.executebuiltin( "Skin.Reset(%s)" %'restart')
  
def build_directoryContent(content, __addonhandle__, cache=True, root=False, con='movies'):
  fanart=__addon__.getAddonInfo('path') + '/fanart.jpg'
  xbmcplugin.setContent(__addonhandle__, con)
  xbmcplugin.setPluginFanart(__addonhandle__, fanart)
  #debug('Liste: '+str(content))
  for record in content:
    rec = dict(record)
    record['thumbnail'] = record.get('thumbnail', fanart)
    record['image'] = record.get('image', "")
    record['selected'] = record.get('selected', False)
    record['url2']=record.get('url2', '')
    record['isFolder']=rec['isFolder']
    
    # remove not existing labels
    try:del rec['image']
    except:pass
    try:del rec['selected']
    except:pass
    try:del rec['thumbnail']
    except:pass
    try:del rec['url']
    except:pass
    try:del rec['url2']
    except:pass
    try:del rec['isFolder']
    except:pass
    
    li = xbmcgui.ListItem(record['title'], iconImage=record['image'])
    li.setInfo(type='Video', infoLabels = rec)
    li.setArt({'icon': record['image'], 'thumb': record['image'], 'poster': record['thumbnail'], 'banner': record['thumbnail']})
    li.setProperty('Fanart_Image', record['thumbnail'])
    li.select(record['selected'])
    
    # context menu
    contextMenuItems = []
    contextMenuItems.append(('Info', 'Action(Info)'))
    if record['url2'] !='':
       contextMenuItems.append((localString(31301), 'RunPlugin('+str(record['url2'])+')') )
    li.addContextMenuItems(contextMenuItems, replaceItems=True)

    xbmcplugin.addDirectoryItem(handle=int(__addonhandle__), url=record['url'], listitem=li, isFolder=record['isFolder'])
    
  #xbmcplugin.addSortMethod(__addonhandle__, xbmcplugin.SORT_METHOD_GENRE)
  # if con == 'movies':
      # xbmc.executebuiltin('Container.SetViewMode(%s)' % '504')
  xbmcplugin.endOfDirectory(__addonhandle__, True, root, cache)


def build_root(__addonuri__, __addonhandle__):
  import urllib.request, urllib.parse, urllib.error

  # check if settings are set
  name = __addon__.getSetting('username')
  if name == '':
    # show home window, zattooHiQ settings and quit
    xbmc.executebuiltin('ActivateWindow(10000)')
    xbmcgui.Dialog().ok(__addonname__, localString(31902))
    __addon__.openSettings()
    sys.exit()

  #play channel on open addon
  if ((xbmcgui.Window(10000).getProperty('ZBEplayOnStart')!='false') and (not xbmc.Player().isPlaying()) and (__addon__.getSetting('start_liveTV')=='true')):
    channeltitle = __addon__.getSetting('start_channel')
    if channeltitle=="lastChannel": channelid=_zattooDB_.get_playing()['channel']
    else: channelid = _zattooDB_.get_channelid(channeltitle)
    resultData = _zattooDB_.zapi.exec_zapiCall('/zapi/watch', {'cid': channelid, 'stream_type': 'hls', 'maxrate':__addon__.getSetting('max_bandwidth')})
    xbmc.Player().play(resultData['stream']['watch_urls'][0]['url'])
    streamsList = []
    for stream in resultData['stream']['watch_urls']: streamsList.append(stream['url'])
    streamsList = '|'.join(streamsList)
    _zattooDB_.set_playing(channelid, streamsList, 0)

    xbmcgui.Window(10000).setProperty('ZBEplayOnStart', 'false')


  iconPath = __addon__.getAddonInfo('path') + '/resources/icon.png'
#  if _listMode_ == 'all': listTitle = localString(31100)
#  else: listTitle = localString(31101)

  content = [
    
    {'title': '[COLOR ff00ff00]'+localString(31099)+'[/COLOR]', 'image': iconPath, 'isFolder': False, 'url': __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'popular'})},
    {'title': localString(31103), 'image': iconPath, 'isFolder': False, 'url': __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'preview'})},
    {'title': localString(31104), 'image': iconPath, 'isFolder': False, 'url': __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'epg'})},
    {'title': localString(31102), 'image': iconPath, 'isFolder': True, 'url': __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'channellist'})},
    {'title': localString(31105), 'image': iconPath, 'isFolder': True, 'url': __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'searchlist', })},
    
  ]
  if RECORD:
    content.append({'title': localString(31106), 'image': iconPath, 'isFolder': True, 'url': __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'recordings'})},)
  content.append({'title': localString(31108), 'image': iconPath, 'isFolder': True, 'url': __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'category'})},)

  if __addon__.getSetting('help') == "true":
    content.append({'title': '[COLOR yellow]'+local(10043)+'[/COLOR]', 'image': iconPath, 'isFolder': True, 'url': __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'showhelp'})})
  if __addon__.getSetting('settings') == "true":
    content.append({'title': '[COLOR yellow]'+localString(31107)+' '+__addonname__+' - v.'+VERSION+'[/COLOR]', 'image': iconPath, 'isFolder': False, 'url': __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'show_settings'})})
  
  build_directoryContent(content, __addonhandle__, True, False, 'files')
  
  #update db
  #_zattooDB_.updateChannels()
  #_zattooDB_.updateProgram()
  
  #_zattooDB_.getProgInfo(True, datetime.datetime.now(), datetime.datetime.now()+datetime.timedelta(minutes = 20))
 
def build_searchList():
  import urllib.request, urllib.parse, urllib.error
  __addonuri__= sys.argv[0]
  __addonhandle__ = int(sys.argv[1])
  search = _zattooDB_.get_search()
  debug('Search '+str(search))
  
  
  if search is not None:
        xbmcplugin.addDirectoryItem(
          handle=__addonhandle__,
          url=__addonuri__+ '?' + urllib.parse.urlencode({'mode': 'inputsearch'}),
          listitem=xbmcgui.ListItem('[B][COLOR blue]' + localString(320000) +'[/B][/COLOR]'),
          isFolder=True
        )
        xbmcplugin.addDirectoryItem(
          handle=__addonhandle__,
          url=__addonuri__+ '?' + urllib.parse.urlencode({'mode': 'deletesearch', 'al': True, 'search': '_'}),
          listitem=xbmcgui.ListItem('[B][COLOR blue]' + localString(320001) +'[/B][/COLOR]'),
          isFolder=True
        )
        for chan in search['index']:
            li = xbmcgui.ListItem(search[chan]['id'])
            contextMenuItems = []
            contextMenuItems.append((localString(320002), 'RunPlugin("plugin://'+__addonId__+'/?mode=deletesearch&al=False&search='+str(chan)+'")'))
            contextMenuItems.append((localString(320003), 'RunPlugin("plugin://'+__addonId__+'/?mode=editsearch&search='+str(chan)+'")'))
            li.addContextMenuItems(contextMenuItems, replaceItems=True)
            xbmcplugin.addDirectoryItem(
              handle=__addonhandle__,
              url=__addonuri__+ '?' + urllib.parse.urlencode({'mode': 'search', 'id': search[chan]['id']}),
              listitem=li,
              isFolder=True
            )
            
            
  xbmcplugin.setContent(__addonhandle__, 'movie')
  xbmcplugin.addSortMethod(__addonhandle__, xbmcplugin.SORT_METHOD_LABEL)
  xbmcplugin.endOfDirectory(__addonhandle__)
  
  
def build_channelsList(__addonuri__, __addonhandle__):
  import urllib.request, urllib.parse, urllib.error
  channels = _zattooDB_.getChannelList(_listMode_ == 'favourites')
  li = False
  nr=0
  for chan in channels['index']:
    nr+=1
  if channels is not None:
    # get currently playing shows
    if __addon__.getSetting('dbonstart') == 'true': li = True
    program = _zattooDB_.getPrograms(channels, li)
    content = []
    # time of chanellist creation
    if _listMode_ == 'favourites':
      content.append({'title': '[B][COLOR blue]' + 'Favourites ('+str(nr)+')' +'[/B][/COLOR]', 'isFolder': False, 'url': __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'switchlist'})})
    else:
      content.append({'title': '[B][COLOR blue]' + 'All ('+str(nr)+')' +'[/B][/COLOR]', 'isFolder': False, 'url':__addonuri__+ '?' + urllib.parse.urlencode({'mode': 'switchlist'})})

    # get last watched channel
    playing = _zattooDB_.get_playing()

    nr=1
    for chan in channels['index']:
      #prog=program[chan]
      prog = {}
      for search in program:
        if search['channel'] == chan:
          prog = search
          break
      try:
        start = prog.get('start_date','').strftime('%H:%M')
        end = prog.get('end_date','').strftime('%H:%M')
        startend = '[COLOR yellow]'+start+"-"+end+'[/COLOR]'
        zstart = int(time.mktime(prog.get('start_date', '').timetuple()))
        zend = int(time.mktime(prog.get('end_date', '').timetuple()))
      except AttributeError:
        startend = ''
      if len(str(nr)) == 1:
        chnr = '  '+str(nr)
      else: chnr = str(nr)
      yy = prog.get('year','')
      
      cred=''
      director=[]
      cast=[]      
      credjson = prog.get('credits','')
      if credjson is not None:
        try:
          cred = json.loads(credjson)
          debug (cred)       
          director=cred['director']
          cast=cred['actor']
        except:pass
      #debug(str(prog))
      if RECALL: 
        url2 = "plugin://"+__addonId__+"/?mode=watch_c&id=" + prog.get('channel', '') +'&showID=' + prog.get('showID','') + "&start=" + str(zstart+300) + "&end=" + str(zend)
      elif RESTART:
        url2 = "plugin://"+__addonId__+"/?mode=watch_c&id=" + prog.get('channel', '') +'&showID=' + prog.get('showID', '') + '&restart=true' + "&start=" + str(zstart+300) + "&end=" + str(zend)
      else: url2=''
        
      content.append({
        'title': '[COLOR lime]'+chnr+'[/COLOR]'+'  '+channels[chan]['title'] + ' - ' + prog.get('title', '')+ '  '+startend,
        'image': channels[chan]['logo'],
        'thumbnail': prog.get('image_small', ''),
        'genre': prog.get('genre',''),
        'director':director,
        'cast': cast,
        'plot':  prog.get('description_long', ''),
        'year': yy,
        'country': prog.get('country',''),
        'isFolder': False,
        'url': __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'watch_c', 'id': channels[chan]['id'], 'showID': prog.get('showID', '')}),
        'url2': url2,
        'selected' : channels[chan]['id'] == playing['channel']
      })
      nr+=1
  
  build_directoryContent(content, __addonhandle__, False)

def build_category(__addonuri__, __addonhandle__, cat):
  import urllib.request, urllib.parse, urllib.error
  
  #li = False
  program = _zattooDB_.get_category(cat)
  #debug('Progkategorien: '+str(program))
  if program is not None:
    channels = _zattooDB_.getChannelList(False)
    #debug('KatChannels: '+str(channels))
    content = []
    # time of chanellist creation
    content.append({'title': '[B][COLOR blue]' + cat +'[/B][/COLOR]', 'isFolder': True, 'url':__addonuri__+ '?' + urllib.parse.urlencode({'mode': 'category'})})

    # get last watched channel
    playing = _zattooDB_.get_playing()

    nr=1
    for chan in program['index']:
      #prog=program[chan]
      prog = {}
      for search in channels['index']:
        if search == chan:
          prog = search
          break
      #debug(str(program[chan]))
      try:
        start = program[chan]['start_date'].strftime('%H:%M')
        end = program[chan]['end_date'].strftime('%H:%M')
        startend = '[COLOR yellow]'+start+"-"+end+'[/COLOR]'
        zend = int(program[chan]['end_date'].strftime('%S'))
        zstart = int(program[chan]['start_date'].strftime('%S'))
        
      except AttributeError:
        startend = ''
      if len(str(nr)) == 1:
        chnr = '  '+str(nr)
      else: chnr = str(nr)
      yy = program[chan]['year']
      cred=''
      director=[]
      cast=[]
      credjson = program[chan]['credits']
    
      if credjson is not None:
        try:
          cred = json.loads(credjson)
          director=cred['director']
          cast=cred['actor']          
        except:pass

        
        
      if RECALL: 
        url2 = "plugin://"+__addonId__+"/?mode=watch_c&id=" + channels[prog]['id'] + "&start=" + str(zstart+300) + "&end=" + str(zend)
      elif RESTART:
        url2 = "plugin://"+__addonId__+"/?mode=watch_c&id=" + channels[prog]['id'] +'&showID=' + program[chan]['showID'] + '&restart=true' + "&start=" + str(zstart+300) + "&end=" + str(zend)
      else: url2=''

      content.append({
        'title': '[COLOR green]'+chnr+'[/COLOR]'+'  '+channels[prog]['title'] + ' - ' + program[chan]['title']+ '  '+startend,
        'image': channels[prog]['logo'],
        'thumbnail': program[chan]['image_small'],
        'genre': program[chan]['genre'],
        'plot':  program[chan]['description_long'],
        'year': yy,
        'director':director,
        'cast': cast,
        'country': program[chan]['country'],
        'isFolder': False,
        'url': __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'watch_c', 'id': channels[prog]['id']}),
        'url2': url2,
        'selected' : channels[prog]['id'] == playing['channel']
      })
      nr+=1
  
  build_directoryContent(content, __addonhandle__, False)

def build_recordingsList(__addonuri__, __addonhandle__):
  import urllib.request, urllib.parse, urllib.error
  
  resultData = _zattooDB_.zapi.exec_zapiCall('/zapi/playlist', None)
  debug('recordliste: '+str(resultData))
  if resultData is None: return
  
  for record in resultData['recordings']:
    showInfo=_zattooDB_.getShowInfo(record['program_id'])
    if not showInfo: continue
    if showInfo == "NONE": continue
    #mark if show is future, running or finished

    start = int(time.mktime(time.strptime(record['start'], "%Y-%m-%dT%H:%M:%SZ"))) + _timezone_  # local timestamp
    end = int(time.mktime(time.strptime(record['end'], "%Y-%m-%dT%H:%M:%SZ"))) + _timezone_  # local timestamp
    position = int(time.mktime(time.strptime(record['position'], "%Y-%m-%dT%H:%M:%SZ"))) + _timezone_  # local timestamp
    st = showInfo[0]['s']
    
    now = time.time()
    duration = end - start
    color='crimson'
  
    if (now>start): color='gold'
    if (now>end): color='lime'
    
    if RECREADY == "true":
        if RECNOW == "false":
          if color == "gold": continue
        if color == "crimson": continue
        
    if __addon__.getSetting('rec_name') == '0':
        label=datetime.datetime.fromtimestamp(st).strftime('%Y.%m.%d. %H:%M')+' '
    elif __addon__.getSetting('rec_name') == '1':
        label=datetime.datetime.fromtimestamp(st).strftime('%a %d.%m.%Y. %H:%M')+' '
    if record['episode_title']:
      label+='[COLOR '+color+']'+record['title']+'[/COLOR]: '+record['episode_title']
      title=record['title']+': '+record['episode_title']
      meta = {'title':record['episode_title'], 'season':1, 'episode':1, 'tvshowtitle':record['title']}
    else:
      label+='[COLOR '+color+']'+record['title']+'[/COLOR]'
      title=record['title']
      meta = {'title':record['title']}
    if showInfo == "NONE": continue
    label+=' ('+showInfo[0]['channel_name']+')'
    
    director = []
    cast = []

    if showInfo[0]['cr'] != []:
        director = showInfo[0]['cr']['director']
        cast = showInfo[0]['cr']['actor']

    date = datetime.datetime.fromtimestamp(start).strftime('%d.%m.%Y')
    meta.update({'title':label,'date':date,'year':showInfo[0]['year'], 'plot':showInfo[0]['d'], 'country':showInfo[0]['country'],'director':director, 'cast':cast, 'genre':', '.join(showInfo[0]['g'])  })
    meta.update({'sorttitle':record['title']})
    '''
    #mark watched
    if (position>end-660):  #10min padding from zattoo +1min safety margin
        meta.update({'overlay':7, 'playcount':12})
    '''
    
    li = xbmcgui.ListItem(label)
    li.setInfo('video',meta)
    if record['image_token'] is not None:
      image_url = 'https://images.zattic.com/cms/' + record['image_token'] + '/format_480x360.jpg'
      li.setThumbnailImage(image_url)
      li.setArt({'thumb':image_url, 'fanart':image_url, 'landscape':image_url})
    li.setProperty('IsPlayable', 'true')
    
    li.setProperty("TotalTime", str(end-start))
    li.setProperty("ResumeTime", str(position-start+300)) #skip 5min zattoo padding
    li.setProperty('zStartTime', str(start))
    
    try:
      series=record['tv_series_id']
    except:
      seriesrec = 'None'
    
    try:
      if resultData['recorded_tv_series']:
        for ser in resultData['recorded_tv_series']:
          if series == ser['tv_series_id']:
            seriesrec = 'true'
            #debug('SeriesID '+str(series))
            break
          else:
            seriesrec = 'None'
    except:
      seriesrec = 'None'
  
    contextMenuItems = []
    contextMenuItems.append(('Info', 'Action(Info)'))
    contextMenuItems.append((localString(31926), 'Action(ToggleWatched)'))
    if seriesrec == 'true':
      contextMenuItems.append((localString(31925),'RunPlugin("plugin://'+__addonId__+'/?mode=remove_series&recording_id='+str(record['id'])+'&series='+str(series)+'")',))
    contextMenuItems.append((localString(31921), 'RunPlugin("plugin://'+__addonId__+'/?mode=remove_recording&recording_id='+str(record['id'])+'&title='+str(title)+'")'))
    li.addContextMenuItems(contextMenuItems, replaceItems=True)

    xbmcplugin.addDirectoryItem(
      handle=__addonhandle__,
      url=__addonuri__+ '?' + urllib.parse.urlencode({'mode': 'watch_r', 'id': record['id'], 'start': start}),
      listitem=li,
      isFolder=False
    )
  
  xbmcplugin.setContent(__addonhandle__, 'movies')
  xbmcplugin.addSortMethod(__addonhandle__, xbmcplugin.SORT_METHOD_LABEL)
  xbmcplugin.addSortMethod(__addonhandle__, xbmcplugin.SORT_METHOD_DATE)
  xbmcplugin.addSortMethod(__addonhandle__, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)
  xbmcplugin.addSortMethod(__addonhandle__, xbmcplugin.SORT_METHOD_GENRE)
  xbmcplugin.endOfDirectory(__addonhandle__)

def watch_recording(__addonuri__, __addonhandle__, recording_id, start=0):
  #if xbmc.Player().isPlaying(): return
  
  if start == 0:
    startTime=int(xbmc.getInfoLabel('ListItem.Property(zStartTime)'))
    
  else:
    startTime=int(start)
 
  max_bandwidth = __addon__.getSetting('max_bandwidth')
  #if DASH: stream_type='dash'
  #else: stream_type='hls'

  #params = {'recording_id': recording_id, 'stream_type': stream_type, 'maxrate':max_bandwidth}
  params = {'stream_type': stream_type, 'maxrate':max_bandwidth, 'enable_eac3':DOLBY}
  resultData = _zattooDB_.zapi.exec_zapiCall('/zapi/watch/recording/' + recording_id, params)
  #debug ('ResultData: '+str(resultData))
  if resultData is not None:
    streams = resultData['stream']['watch_urls']
    
    if len(streams)==0:
      xbmcgui.Dialog().notification("ERROR", "NO STREAM FOUND, CHECK SETTINGS!", channelInfo['logo'], 5000, False)
      return
    elif len(streams) > 1 and  __addon__.getSetting('audio_stream') == 'B' and streams[1]['audio_channel'] == 'B': streamNr = 1
    else: streamNr = 0
    
    li = xbmcgui.ListItem(path=streams[streamNr]['url'])
    if stream_type == 'dash':
        li.setProperty('inputstreamaddon', 'inputstream.adaptive')
        li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
    if stream_type == 'dash_widevine':
        li.setProperty('inputstreamaddon', 'inputstream.adaptive')
        li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        li.setProperty('inputstream.adaptive.license_key', streams[1]['license_url'] + "||a{SSM}|")
        li.setProperty('inputstream.adaptive.license_type', "com.widevine.alpha")

    xbmcplugin.setResolvedUrl(__addonhandle__, True, li)
    pos=0
    xbmc.sleep(2000)
    player=xbmc.Player()
    while (player.isPlaying()):
        try: pos=player.getTime()
        except: pass
        xbmc.sleep(100)

    #send watched position to zattoo
    #zStoptime=datetime.datetime.fromtimestamp(startTime+round(pos)-300).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    zStoptime=datetime.datetime.fromtimestamp(startTime+round(pos)-300 - _timezone_ ).strftime("%Y-%m-%dT%H:%M:%SZ")
    resultData = _zattooDB_.zapi.exec_zapiCall('/zapi/playlist/recording', {'recording_id': recording_id, 'position': zStoptime})
    xbmc.executebuiltin('Container.Refresh')
    debug(resultData)

def setup_recording(program_id):
  #print('RECORDING: '+program_id)
  params = {'program_id': program_id}
  # test ob Aufnahme existiert
  playlist = _zattooDB_.zapi.exec_zapiCall('/zapi/playlist', None)
  for record in playlist['recordings']:
      if int(params['program_id']) == int(record['program_id']):
          xbmcgui.Dialog().ok(__addonname__, __addon__.getLocalizedString(31906))
          return
       
  resultData = _zattooDB_.zapi.exec_zapiCall('/zapi/playlist/program', params)
  
  debug('Recording: '+str(params)+'  '+str(resultData))

  if resultData is not None:
    xbmcgui.Dialog().ok(__addonname__, __addon__.getLocalizedString(31903), __addon__.getLocalizedString(31904))
  else:
    xbmcgui.Dialog().ok(__addonname__, __addon__.getLocalizedString(31905))
  
  _library_.make_library()  # NEW added - by Samoth


def delete_recording(recording_id, title):
  dialog = xbmcgui.Dialog()
  ret = dialog.yesno(local(19112), str(title), '[COLOR gold]'+localString(32025)+'[/COLOR]', localString(32026),'','[COLOR red]'+local(19291)+'[/COLOR]')
  if ret ==1:
    params = {'recording_id': recording_id}
    folder=__addon__.getSetting('library_dir') # NEW added - by Samoth
    if folder: # NEW added - by Samoth
      _library_.delete_entry_from_library(str(recording_id)) # NEW added - by Samoth
    resultData = _zattooDB_.zapi.exec_zapiCall('/zapi/playlist/remove', params)
    xbmc.executebuiltin('Container.Refresh')
# times in local timestamps

def delete_series(recording_id, series):
  dialog = xbmcgui.Dialog()
  params = {'recording_id': recording_id, 'tv_series_id':series, 'remove_recording':'true'}
  folder=__addon__.getSetting('library_dir') # NEW added - by Samoth
  if folder: # NEW added - by Samoth
    _library_.delete_entry_from_library(str(recording_id)) # NEW added - by Samoth
  resultData = _zattooDB_.zapi.exec_zapiCall('/zapi/series_recording/remove', params)
  xbmc.executebuiltin('Container.Refresh')

def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    import re, unicodedata
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = str(re.sub('[^\w\s-]', '', value).strip().lower())
    value = str(re.sub('[-\s]+', '-', value))
    return value


def watch_channel(channel_id, start, end, showID="", restart=False, showOSD=False):
  #print('WATCH: '+channel_id+' st:'+str(start)+' en:'+str(end))
  #new ZattooDB instance because this is called from thread-timer on channel-nr input (sql connection doesn't work)
  _zattooDB_=ZattooDB()

  #selected currently playing live TV
  playing = _zattooDB_.get_playing()
   
  #lastplaying = playing['channel']
  xbmcgui.Window(10000).setProperty('lastChannel', playing['channel'])
  #debug('last play Channel '+str(xbmcgui.Window(10000).getProperty('lastChannel')))
  if (xbmc.Player().isPlaying() and channel_id == playing['channel'] and start=='0'):
    xbmc.executebuiltin("Action(FullScreen)")

    return

  # (64 150 300) 600 900 1500 3000 5000
  max_bandwidth = __addon__.getSetting('max_bandwidth')

  #if DASH: stream_type='dash_widevine'
  #else:  stream_type='hls'
  

  if restart:
    startTime = datetime.datetime.fromtimestamp(int(start))
    endTime = datetime.datetime.fromtimestamp(int(end))
    params = {'stream_type': stream_type, 'maxrate':max_bandwidth, 'enable_eac3':DOLBY}
    resultData = _zattooDB_.zapi.exec_zapiCall('/zapi/watch/selective_recall/'+channel_id+'/'+showID, params)
  elif start == '0':
    startTime = datetime.datetime.now()
    endTime = datetime.datetime.now()
    #params = {'cid': channel_id, 'stream_type': stream_type, 'maxrate':max_bandwidth, 'enable_eac3':'true'}
    params = {'stream_type': stream_type, 'maxrate':max_bandwidth, 'enable_eac3':DOLBY, 'timeshift':'10800', 'https_watch_urls': 'true'}
    resultData = _zattooDB_.zapi.exec_zapiCall('/zapi/watch/live/' + channel_id, params)
  else:
    startTime = datetime.datetime.fromtimestamp(int(start))
    endTime = datetime.datetime.fromtimestamp(int(end))
    #zStart = datetime.datetime.fromtimestamp(int(start) - _timezone_ ).strftime("%Y-%m-%dT%H:%M:%SZ") #5min zattoo skips back
    #zEnd = datetime.datetime.fromtimestamp(int(end) - _timezone_ ).strftime("%Y-%m-%dT%H:%M:%SZ")
    #params = {'cid': channel_id, 'stream_type': stream_type, 'start':zStart, 'end':zEnd, 'maxrate':max_bandwidth }
    params = {'stream_type': stream_type, 'maxrate':max_bandwidth, 'enable_eac3':DOLBY}
    resultData = _zattooDB_.zapi.exec_zapiCall('/zapi/watch/recall/' + channel_id + '/' + showID, params)
    
  channelInfo = _zattooDB_.get_channelInfo(channel_id)

  #if restart: resultData = _zattooDB_.zapi.exec_zapiCall('/zapi/watch/selective_recall/'+channel_id+'/'+showID, params)
  #else: resultData = _zattooDB_.zapi.exec_zapiCall('/zapi/watch',params)
  #resultData = _zattooDB_.zapi.exec_zapiCall('/zapi/watch',params)
  debug('Streams :' +str(resultData))
  if resultData is None:
    xbmcgui.Dialog().notification("ERROR", "NO ZAPI RESULT", channelInfo['logo'], 5000, False)
    return

  streams = resultData['stream']['watch_urls']
  if len(streams)==0:
    xbmcgui.Dialog().notification("ERROR", "NO STREAM FOUND, CHECK SETTINGS!", channelInfo['logo'], 5000, False)
    return
  # change stream if settings are set
 
  elif len(streams) > 1 and  __addon__.getSetting('audio_stream') == 'B' and streams[1]['audio_channel'] == 'B': streamNr = 1
  else:  streamNr = 0
  
  #xbmcgui.Window(10000).setProperty('playstream', streams[streamNr]['url'])

  # save currently playing
  streamsList = []
  for stream in resultData['stream']['watch_urls']: streamsList.append(stream['url'])
  streamsList = '|'.join(streamsList)
  _zattooDB_.set_playing(channel_id, showID, streamsList, streamNr)

  #make Info
  program = _zattooDB_.getPrograms({'index':[channel_id]}, True, startTime, endTime)
  
  listitem = xbmcgui.ListItem(path=streams[streamNr]['url'])
    
  if program:
    program = program[0]
    heading = ('[B]' + channelInfo['title'] + '[/B] ').translate(_umlaut_) + '  ' + program['start_date'].strftime('%H:%M') + '-' + program['end_date'].strftime('%H:%M')
    xbmcgui.Dialog().notification(heading, program['title'].translate(_umlaut_), channelInfo['logo'], 5000, False)

    #set info for recall
    listitem.setThumbnailImage(program['image_small'])
    meta = {'title': program['title'], 'season' : 'S', 'episode': streamNr, 'tvshowtitle': channelInfo['title']+ ', ' + program['start_date'].strftime('%A %H:%M') + '-' + program['end_date'].strftime('%H:%M'), 'premiered' :'premiered', 'duration' : '20', 'rating': 'rating', 'director': 'director', 'writer': 'writer', 'plot': program['description_long']}
    listitem.setInfo(type="Video", infoLabels = meta)
    listitem.setArt({ 'poster': program['image_small'], 'logo' : channelInfo['logo'] })

  if stream_type == 'dash':
        listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
        listitem.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        
  if stream_type == 'dash_widevine':
        listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
        listitem.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        listitem.setProperty('inputstream.adaptive.license_key', streams[1]['license_url'] + "||a{SSM}|")
        listitem.setProperty('inputstream.adaptive.license_type', "com.widevine.alpha")
        
  xbmcplugin.setResolvedUrl(__addonhandle__, True, listitem)
  #play liveTV: info is created in OSD
  if (start=='0'):
    debug('PlayLive')
    player=xbmc.Player()
    #player.startTime=startTime
    player.play(streams[streamNr]['url'], listitem)
    while (player.isPlaying()): xbmc.sleep(100)
     
    _zattooDB_=ZattooDB()
    channelList = _zattooDB_.getChannelList(False)
    #print "ChannelList: " + str(channelList)
    currentChannel = _zattooDB_.get_playing()['channel']
    nr=channelList[currentChannel]['nr']
    show_channelNr(nr+1)
    toggleChannel=xbmcgui.Window(10000).getProperty('toggleChannel')
    if toggleChannel !="": showToggleImg()
    
  else:
    debug('PlayRecall')
    player= myPlayer()
    player.startTime=startTime
    player.play(streams[streamNr]['url'], listitem)
    #xbmc.sleep(1000)
    #player.seekTime(300)
    
    while (player.playing):xbmc.sleep(100)
  
  
def skip_channel(skipDir):
  #new ZattooDB instance because this is called from thread-timer on channel-nr input (sql connection doesn't work)
  _zattooDB_=ZattooDB()

  channelList = _zattooDB_.getChannelList(_listMode_ == 'favourites')
  currentChannel = _zattooDB_.get_playing()['channel']
  nr=channelList[currentChannel]['nr']
  nr += skipDir
  debug(nr)
  debug(len(channelList))
  if nr==len(channelList)-1:
    nr=0
  elif nr<0:
    nr=len(channelList)-2
  debug(nr)
  watch_channel(channelList['index'][nr], '0', '0')
  return nr

def  toggle_channel():
  _zattooDB_=ZattooDB()
  toggleChannel=xbmcgui.Window(10000).getProperty('toggleChannel')
  playing=_zattooDB_.get_playing()
  xbmcgui.Window(10000).setProperty('toggleChannel', playing['channel'])
  
  
  if toggleChannel=="": #xbmc.executebuiltin("Action(Back)") #go back to channel selector
    xbmcgui.Window(10000).setProperty('toggleChannel', xbmcgui.Window(10000).getProperty('lastChannel'))
    debug('last Channel '+str(xbmcgui.Window(10000).getProperty('lastChannel')))
    showToggleImg()
  else:
    watch_channel(toggleChannel, '0', '0')
    channelList = _zattooDB_.getChannelList(_listMode_ == 'favourites')
    nr=channelList[toggleChannel]['nr']
    return nr


def change_stream(dir):
  playing = _zattooDB_.get_playing()
  streams = playing['streams'].split('|')
  streamNr = (playing['current_stream'] + dir) % len(streams)

  _zattooDB_.set_currentStream(streamNr)

  channelInfo = _zattooDB_.get_channelInfo(playing['channel'])
  channel_id=_zattooDB_.get_playing()['channel']
  program = _zattooDB_.getPrograms({'index':[channel_id]}, True)[0]

  title = channelInfo['title'] + " (stream" + str(streamNr) + ")"
  listitem = xbmcgui.ListItem(channelInfo['title'], thumbnailImage=channelInfo['logo'])
  listitem.setInfo('video', {'Title': title, 'plot':program['description_long']})

  xbmc.Player().play(streams[streamNr], listitem)
  xbmcgui.Dialog().notification(title.translate(_umlaut_), program['title'].translate(_umlaut_), channelInfo['logo'], 5000, False)

def search_show(__addonuri__, __addonhandle__, search):
  import urllib.request, urllib.parse, urllib.error

  resultData = _zattooDB_.zapi.exec_zapiCall('/zapi/program/search?query=' + search.replace(" ", "_"), None)
  debug('Suche: '+str(resultData))
  _zattooDB_.set_search(search)
  if resultData is None:
    build_directoryContent([{'title': __addon__.getLocalizedString(31203), 'isFolder': False, 'url':''}], __addonhandle__)
    return
 
    
  programs = sorted(resultData['programs'], key=lambda prog: ( prog['start'], prog['cid']))
  
  channels = _zattooDB_.getChannelList(False)

  recall_shows = []
  record_shows = []
  now = time.time()  # datetime.datetime.now()
  for program in programs:
    start = int(time.mktime(time.strptime(program['start'], "%Y-%m-%dT%H:%M:%SZ"))) + _timezone_  # local timestamp
    end = int(time.mktime(time.strptime(program['end'], "%Y-%m-%dT%H:%M:%SZ"))) + _timezone_  # local timestamp
    
    startLocal = time.localtime(start)  # local timetuple
    endLocal = time.localtime(end)
    if program.get('episode_title', '') is not None:episode_title=program.get('episode_title', '')
    else:episode_title=''
    
    res = program.get('selective_recall_until') 
    #debug(str(res))
    if res is None: restart=False
    else:restart=True
  
    record = program.get('recording_eligible')
    showID = program.get('id')
    
    try:
      if not channels[program['cid']]:
        debug ('suche: '+str(program.get['cid']))
    except KeyError: continue
    
    info = _zattooDB_.getShowLongDescription(str(showID))
    debug('showInfo:  '+str(info)+' '+str(showID))
   
    if info['description'] =='':
      info = _zattooDB_.setProgram(str(showID))
    
    if info == 'NONE': continue
    
    startInfo = _zattooDB_.get_showID(str(showID))
    st = startInfo[0]['start_date']
    
    #debug('ShowID: '+str(showID)+'  '+str(info))
    cred=''
    director=[]
    cast=[]
    credjson = program.get('credits','')
    if credjson is not None:
        try:
          cred = json.loads(credjson)
          debug (cred)
          director=cred['director']
          cast=cred['actor']
        except:pass
    if program.get('image_token') is not None:
      thumbnail = 'https://images.zattic.com/cms/' + program.get('image_token') + '/format_480x360.jpg'
    else: 
      thumbnail = channels[program['cid']]['logo']
      
    item = {
        'title': '[COLOR yellow]' + st.strftime('%d.%m. ') + formatTime(st) + '[/COLOR] ' + '[COLOR lime]' + program.get('cid', '') + '[/COLOR]' + ': ' + program.get('title', '') + ' - ' + episode_title,
        'image': channels[program['cid']]['logo'],
        'thumbnail': thumbnail,
        'plot':  info['description'],
        'country': info['country'],
        'year': info['year'],
        'genre': info['genre'],
        'director': director,
        'cast': cast,
        'isFolder': False
      }
    rec = {
        'title': '[COLOR yellow]'  + st.strftime('%d.%m. ') + formatTime(st)  + '[/COLOR] ' + '[COLOR lime]' + program.get('cid', '') + '[/COLOR]' + ': ' + program.get('title', '') + ' - ' + episode_title,
        'image': channels[program['cid']]['logo'],
        'thumbnail': thumbnail,
        'plot':  info['description'],
        'country': info['country'],
        'year': info['year'],
        'genre': info['genre'],
        'director': director,
        'cast': cast,
        'isFolder': False
      }
    startLocal = time.mktime(startLocal) # local timestamp
    endlocal = time.mktime(endLocal)
    if restart:
      if startLocal < now and endlocal > now:
        item['url'] = __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'watch_c', 'id': program['cid'], 'showID':showID})
        item['url2'] = __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'watch_c', 'id': program['cid'], 'showID':showID, 'restart':'true', 'start': str(start), 'end': str(end)})
        recall_shows.append(item)
        if record:
          rec['url'] = __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'record_p', 'program_id': program['id']})
          record_shows.append(rec)
      elif startLocal > now:
        if record:
          rec['url'] = __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'record_p', 'program_id': program['id']})
          record_shows.append(rec)
    elif startLocal < now and endlocal > now:
        if RECALL:
          item['url2'] = __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'watch_c', 'id': program['cid'], 'start': str(start+300), 'end': str(end)})
          item['url'] = __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'watch_c', 'id': program['cid'], 'showID':showID})
          recall_shows.append(item)
        else:
          item['url'] = __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'watch_c', 'id': program['cid'], 'showID':showID})
          recall_shows.append(item)
        if record and RECALL:
          rec['url'] = __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'record_p', 'program_id': program['id']})
          record_shows.append(rec)
    elif startLocal < now:
      if RECALL and record:
        item['url'] = __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'watch_c', 'id': program['cid'], 'start': str(start+300), 'end': str(end)})
        recall_shows.append(item)      
        rec['url'] = __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'record_p', 'program_id': program['id']})
        record_shows.append(rec)
    else:
      if RECORD:
        rec['url'] = __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'record_p', 'program_id': program['id']})
        record_shows.append(rec)
    
  content = []
  if recall_shows != []:
    content.append({'title': '[B][COLOR blue]' + __addon__.getLocalizedString(31201) + '[/B][/COLOR]', 'isFolder': False, 'url':''})
    for item in recall_shows: content.append(item)
  if record_shows !=[]:
    content.append({'title': '[B][COLOR blue]' + __addon__.getLocalizedString(31202) + '[/B][/COLOR]', 'isFolder': False, 'url':''})
    for rec in record_shows: content.append(rec)
  if record_shows == [] and recall_shows ==[]:
    content.append({'title': __addon__.getLocalizedString(31203), 'isFolder': False, 'url':''})
  build_directoryContent(content, __addonhandle__, True, False)


def showPreview(popularList=''):
  xbmc.executebuiltin("Dialog.Close(all, true)")
  from resources.lib.channelspreview import ChannelsPreview
  preview = ChannelsPreview()
  if popularList=='popular': preview.createPreview('popular')
  else: preview.createPreview(_listMode_ == 'favourites')
  preview.show() #doModal()
  while xbmcgui.Window(10000).getProperty('zattoo_runningView')=="preview": xbmc.sleep(10)
  del preview

def showHelp(__addonuri__, __addonhandle__):
  import urllib.request, urllib.parse, urllib.error
  iconPath = __addon__.getAddonInfo('path') + '/icon.png'
  content = [
    {'title': '[COLOR blue]'+local(10043)+'[/COLOR]', 'url':__addonuri__+ '?' + urllib.parse.urlencode({'mode': 'showhelp'}), 'image': iconPath, 'isFolder': True, },
    {'title': local(128), 'image': iconPath, 'isFolder': True, 'url': __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'helpmy', 'img':'main.png'})},
    {'title': localString(30300), 'image': iconPath, 'isFolder': True, 'url': __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'helpmy', 'img':'Live-Keymap.png'})},
    {'title': 'EPG', 'image': iconPath, 'isFolder': True, 'url': __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'helpmy', 'img':'epg-1.png'})},
    {'title': 'EPG - Touchscreen', 'image': iconPath, 'isFolder': True, 'url': __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'helpmy', 'img':'epg-2.png'})},
    {'title': local(10550), 'image': iconPath, 'isFolder': True, 'url': __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'helpmy', 'img':'Teletext.png'})},

  
  ]
  build_directoryContent(content, __addonhandle__, True, False, 'files')
  
def showEpg():
  from resources.lib.epg import EPG
  currentChannel = _zattooDB_.get_playing()['channel']
  channelList = _zattooDB_.getChannelList(_listMode_ == 'favourites')
  #debug(str(channelList))
  try:
    currentNr=channelList[currentChannel]['nr']
  except:
    currentNr=0
  accountData=_zattooDB_.zapi.get_accountData()
  premiumUser=accountData['session']['user']['subscriptions']!=[]
  epg = EPG(currentNr, premiumUser)
  epg.loadChannels(_listMode_ == 'favourites')
  epg.show() #doModal()
  while xbmcgui.Window(10000).getProperty('zattoo_runningView')=="epg": xbmc.sleep(10)
  del epg

def selectStartChannel():
  channels = _zattooDB_.getChannelList(_listMode_ == 'favourites')
  chanList = [localString(310095)]
  for chan in channels['index']: chanList.append(channels[chan]['title'])
  dialog=xbmcgui.Dialog()
  ret = dialog.select(localString(31009), chanList)
  if ret==-1: return
  __addon__.setSetting('start_liveTV', 'true')
  if ret==0: __addon__.setSetting('start_channel', 'lastChannel')
  else: __addon__.setSetting('start_channel', chanList[ret])
 

 
def input_numbers(nr):
 # if (xbmcgui.Window(10000).getProperty('zattooGUI')!="True"):
    
    gui = zattooGUI("zattooGUI.xml", __addon__.getAddonInfo('path'))
    if nr: gui.act_numbers(int(nr))
    gui.doModal()
    del gui

def show_channelNr(nr):
  #if (xbmcgui.Window(10000).getProperty('zattooGUI')!="True"):
    
    gui = zattooGUI("zattooGUI.xml", __addon__.getAddonInfo('path'))
    if nr: gui.showChannelNr(int(nr))
    gui.doModal()
    del gui

def showToggleImg():
    pip = zattooPiP("zattooGUI.xml", __addon__.getAddonInfo('path'))
    pip.showToggleImg()
    pip.doModal()
    del pip

def showCategory():
    import urllib.request, urllib.error
    __addonuri__= sys.argv[0]
    __addonhandle__ = int(sys.argv[1])
    cat = _zattooDB_.set_category()
    #debug('Kategorien: '+str(cat))
    iconPath = __addon__.getAddonInfo('path') + '/icon.png'
    content = []
      
    for record in cat:
      content.append(
      {
        'title':record['category']+' ('+str(record['len'])+')',
        'image': iconPath,
        'isFolder': True,
        'url': __addonuri__+ '?' + urllib.parse.urlencode({'mode': 'build_category', 'cat': record['category']})
      })
    
    build_directoryContent(content, __addonhandle__, False )
    
def makeOsdInfo():
  channel_id=_zattooDB_.get_playing()['channel'] 
  channelInfo = _zattooDB_.get_channelInfo(channel_id)
  program = _zattooDB_.getPrograms({'index':[channel_id]}, True, datetime.datetime.now(), datetime.datetime.now())
  
  try: program=program[0]
  except: 
    xbmcgui.Dialog().ok('Error',' ','No Info')
    return
    
  nextprog = _zattooDB_.getPrograms({'index':[channel_id]}, True, program['end_date']+datetime.timedelta(seconds=60), program['end_date']+datetime.timedelta(seconds=60))
  #debug ('Program: '+str(nextprog))
  
  if RESTART:
    if program['restart']:
      xbmc.executebuiltin( "Skin.SetBool(%s)" %'restart')
    else:
      xbmc.executebuiltin( "Skin.Reset(%s)" %'restart')
      
  cred = ''
  director = ""
  actor = ""   
  credjson = program['credits']
  
  if credjson is not None:
    try:
      cred = json.loads(credjson)
      director = cred['director']
      director = json.dumps(director, ensure_ascii=False)
      director = director.replace('"','').replace('[','').replace(']','')
      actor  = cred['actor']
      actor = json.dumps(actor, ensure_ascii=False)
      actor = actor.replace('"','').replace('[','').replace(']','')          
    except:pass
  director = director.replace('"','').replace('[','').replace(']','')
  actor = actor.replace('"','').replace('[','').replace(']','')   
         
  description = program['description']
  if description is None: description = ''
  else: description = '  -  ' + description
  win=xbmcgui.Window(10000)
  win.setProperty('title', program['title'] + description)
  win.setProperty('channelInfo', channelInfo['title'] + ', ' + program['start_date'].strftime('%A %H:%M') + '-' + program['end_date'].strftime('%H:%M'))
  win.setProperty('showThumb', program['image_small'])
  win.setProperty('channelLogo', channelInfo['logo'])
  win.setProperty('plot', program['description_long'])
  win.setProperty('genre', '[COLOR blue]'+ local(135) + ':  ' + '[/COLOR]'+ program['genre'])
  win.setProperty('year', '[COLOR blue]' + local(345) + ':  ' + '[/COLOR]' + program['year'])
  win.setProperty('country', '[COLOR blue]' + local(574) + ':  ' + '[/COLOR]' + program['country'])
  win.setProperty('director', '[COLOR blue]' + local(20339) + ':  ' + '[/COLOR]' + str(director))
  win.setProperty('actor', '[COLOR blue]' + local(20337) + ':  ' + '[/COLOR]' + str(actor))
  win.setProperty('nextprog', '[COLOR blue]' + localString(30010) +'[/COLOR]'+ '[COLOR aquamarine]' + nextprog[0]['title'] + '[/COLOR]' + '  ' + '[COLOR khaki]' + nextprog[0]['start_date'].strftime('%A %H:%M')+' - ' +nextprog[0]['end_date'].strftime('%H:%M')+'[/COLOR]')
  
  played = datetime.datetime.now()-program['start_date']
  total = program['end_date'] - program['start_date']
  #win.setProperty('progress', str((100/total.total_seconds())*played.total_seconds()))
  win.setProperty('progress', str((float(100)/total.seconds)*played.seconds))


  win.setProperty('favourite', str(channelInfo['favourite']))
  if channelInfo['favourite']==1: xbmc.executebuiltin( "Skin.SetBool(%s)" %'favourite')
  else: xbmc.executebuiltin( "Skin.Reset(%s)" %'favourite')

        
class myPlayer(xbmc.Player):
  
    def __init__(self, skip=0):
      self.skip=skip
      self.startTime=0
      self.playing=True
      
    def onPlayBackStarted(self):
        
        if (self.skip>0):
            self.seekTime(self.skip)
            self.startTime=self.startTime-datetime.timedelta(seconds=self.skip)
            
    def onPlayBackSeek(self, time, seekOffset):
      
      if self.startTime+datetime.timedelta(milliseconds=time) > datetime.datetime.now().replace(microsecond=0):
        channel=_zattooDB_.get_playing()['channel']
        #_zattooDB_.set_playing() #clear setplaying to start channel in watch_channel
        self.playing=False
     
        xbmc.executebuiltin('RunPlugin("plugin://'+__addonId__+'/?mode=watch_c&id='+channel+'&showOSD=1")')
        
    def onPlayBackStopped(self):
        self.playing=False
        
    def onPlayBackEnded(self):
        channel=_zattooDB_.get_playing()['channel']
        #showID=_zattooDB_.get_playing()['showID']
        # debug(showID)
        # program=_zattooDB_.get_showID(showID)
        # debug(program)
        # #program = _zattooDB_.getPrograms({'index':[channel]}, True, datetime.datetime.now(), datetime.datetime.now())
        # nextprog = _zattooDB_.getPrograms({'index':[channel]}, True, program[0]['end_date']+datetime.timedelta(seconds=60), program[0]['end_date']+datetime.timedelta(seconds=60))
        # debug ('Nextprog'+str(nextprog))
        # start = int(time.mktime(nextprog[0]['start_date'].timetuple()))+1500
        # debug(start)
        # end = int(time.mktime(nextprog[0]['end_date'].timetuple()))
        # url = "plugin://"+__addonId__+"/?mode=watch_c&id=" + nextprog[0]['channel'] + "&showID=" + nextprog[0]['showID'] + "&start=" + str(start) + "&end=" + str(end)
        self.playing=False 
        #debug(url)
        #xbmc.executebuiltin('RunPlugin('+url+')')

        xbmc.executebuiltin('RunPlugin("plugin://'+__addonId__+'/?mode=watch_c&id='+channel+'&showOSD=1")')

class zattooPiP(xbmcgui.WindowXMLDialog):

  def __init__(self, xmlFile, scriptPath):
    xbmcgui.Window(10000).setProperty('zattooPiP', 'True') 
    self.PiP =  __addon__.getSetting('pip')
    
    if self.PiP == "0":
      self.toggleImgBG =xbmcgui.ControlImage(1280, 574, 260, 148, __addon__.getAddonInfo('path') + '/resources/teletextBG.png', aspectRatio=1)
      self.toggleImg =xbmcgui.ControlImage(1280, 576, 256, 144, '', aspectRatio=1)
    else:
      self.toggleImgBG =xbmcgui.ControlImage(1280, 500, 390, 222, __addon__.getAddonInfo('path') + '/resources/teletextBG.png', aspectRatio=1)
      self.toggleImg =xbmcgui.ControlImage(1280, 502, 386, 218, '', aspectRatio=1)
    
    self.addControl(self.toggleImgBG)
    self.addControl(self.toggleImg)
    debug('last cannel :'+str(xbmcgui.Window(10000).getProperty('toggleChannel')))
    self.toggleChannelID=xbmcgui.Window(10000).getProperty('toggleChannel')
    #if self.toggleChannelID!="": self.showToggleImg()

  def showToggleImg(self):
    
    #VERSION=xbmc.getInfoLabel( "System.BuildVersion" )
    #debug(VERSION)
    #if '18' in VERSION: xbmc.executebuiltin("Action(FullScreen)") 

    if self.PiP == "0":
      self.toggleImgBG.setPosition(1022, 574)
      self.toggleImg.setPosition(1024, 576)
    else:      
      self.toggleImgBG.setPosition(890, 500)
      self.toggleImg.setPosition(892, 502)
    self.refreshToggleImg()

  def hideToggleImg(self):
    
    self.toggleChannelID=""
    xbmcgui.Window(10000).setProperty('toggleChannel','')
    if hasattr(self, 'refreshToggleImgTimer'): self.refreshToggleImgTimer.cancel()
    #xbmcgui.Dialog().notification('Toggle', 'Toggle End', __addon__.getAddonInfo('path') + '/icon.png', 3000, False)
    #self.close()
    
  def refreshToggleImg(self):
    self.toggleImg.setImage('http://thumb.zattic.com/'+self.toggleChannelID+'/256x144.jpg?r='+str(int(time.time())), False)
    if hasattr(self, 'refreshToggleImgTimer'): self.refreshToggleImgTimer.cancel()
    self.refreshToggleImgTimer=  threading.Timer(10, self.refreshToggleImg)
    self.refreshToggleImgTimer.start()
    
  def close(self):
    if hasattr(self, 'refreshToggleImgTimer'): self.refreshToggleImgTimer.cancel()
    xbmcgui.Window(10000).setProperty('zattooPiP', 'False')
    super(zattooPiP, self).close()
    
  def onAction(self, action):
    TOGGLE_KEY = __addon__.getSetting('key_toggleChan')
    key=str(action.getButtonCode())
    actionID = action.getId()
   
  
    if actionID == ACTION_STOP:
      self.hideToggleImg()
      self.close()
      xbmc.Player().stop() 
      
    elif actionID in [KEY_NAV_BACK, ACTION_SELECT_ITEM, ACTION_PARENT_DIR, ACTION_MOUSE_LEFT_CLICK]:
      self.hideToggleImg()
      self.close()
      
    elif actionID in [ACTION_MOVE_LEFT, ACTION_GESTURE_SWIPE_LEFT]:
      toggle_channel()
      self.close()
      
    elif key == TOGGLE_KEY:
      toggle_channel()
      self.close()


class zattooGUI(xbmcgui.WindowXMLDialog):

  def __init__(self, xmlFile, scriptPath):
    xbmcgui.Window(10000).setProperty('zattooGUI', 'True')
    
    self.playing= _zattooDB_.get_playing()
    self.channelID = self.playing['channel']
    channels = _zattooDB_.getChannelList(False)
    self.showChannelNr(channels[self.channelID]['nr']+1)

    #self.toggleChannelID=xbmcgui.Window(10000).getProperty('toggleChannel')
    #if self.toggleChannelID!="": self.showToggleImg()

  def onAction(self, action):
    #key=str(action.getButtonCode())
    actionID = action.getId()
    
    if (actionID>57 and actionID<68):self.act_numbers(actionID)
    elif (actionID>142 and actionID<150):
      actionID = actionID - 82
      self.act_numbers(actionID)
    elif actionID  == ACTION_STOP:
      self.close()
      xbmc.Player().stop()  
    elif actionID in [ACTION_PARENT_DIR, KEY_NAV_BACK, ACTION_PREVIOUS_MENU]: self.close()
    elif actionID == ACTION_BUILT_IN_FUNCTION:self.close()
    
 
  def act_numbers(self,action):
      #print('channel ipnut'+str(action))
      if hasattr(self, 'channelInputTimer'): self.channelInputTimer.cancel()
      self.channelInput+=str(action-58)
      self.channelInputCtrl.setLabel(self.channelInput)
      self.channelInputCtrl.setVisible(True)
      if len(self.channelInput)>2: self.channelInputTimeout()
      else:
         self.channelInputTimer = threading.Timer(1.5, self.channelInputTimeout)
         self.channelInputTimer.start()


  def showChannelNr(self, channelNr):
    if not hasattr(self, 'channelInputCtrl'):
      self.channelInputCtrl = xbmcgui.ControlLabel(1000, 0, 270, 75,'', font='font35_title', alignment=1)
      self.addControl(self.channelInputCtrl)
    self.channelNr=channelNr
    self.channelInput=''
    self.channelInputCtrl.setLabel(str(channelNr))
    self.channelInputCtrl.setVisible(True)
    if hasattr(self, 'hideNrTimer'): self.hideNrTimer.cancel()
    self.hideNrTimer=threading.Timer(2, self.hideChannelNr)
    self.hideNrTimer.start()

  def hideChannelNr(self):
    self.channelInputCtrl.setLabel(' ')
    self.channelInputCtrl.setVisible(False)
    self.close()

  def channelInputTimeout(self):
    skip=int(self.channelInput)-self.channelNr
    self.showChannelNr(int(self.channelInput))
    skip_channel(skip)
    self.close()
    
  def close(self):
    if hasattr(self, 'hideNrTimer'): self.hideNrTimer.cancel()
    xbmcgui.Window(10000).setProperty('zattooGUI', 'False')
    super(zattooGUI, self).close()
    
class zattooOSD(xbmcgui.WindowXMLDialog):
  def onInit(self):
    self.getControl(350).setPercent(float(xbmcgui.Window(10000).getProperty('progress')))    

  def onAction(self, action):
    #print('ZATTOOOSD BUTTON'+str(action.getButtonCode()))
    #print('ZATTOOOSD ACTIONID'+str(action.getId()))
    action = action.getId()
    #self.close()
    if action in [ACTION_PARENT_DIR, KEY_NAV_BACK, ACTION_PREVIOUS_MENU]:
      if hasattr(self, 'hideNrTimer'): self.hideNrTimer.cancel()
      self.close()
    elif action in [ACTION_STOP, ACTION_BUILT_IN_FUNCTION]:
      if hasattr(self, 'hideNrTimer'): self.hideNrTimer.cancel()
      self.close()
      #print 'Action Stop'
      xbmc.sleep(1000)
      #xbmc.executebuiltin('Action(OSD)') #close hidden gui
      #xbmc.executebuiltin("Action(Back)")
    elif action == ACTION_SKIPPREW:
      xbmc.executebuiltin("Action(Left)")
    elif action == ACTION_SKIPNEXT:
      xbmc.executebuiltin("Action(Right)")

  def onClick(self, controlID):
    channel=_zattooDB_.get_playing()['channel']
    channeltitle=_zattooDB_.get_channeltitle(channel)
    program = _zattooDB_.getPrograms({'index':[channel]}, True, datetime.datetime.now(), datetime.datetime.now())
    program=program[0]
    self.close() #close OSD

    if controlID==209: #recall
      xbmc.executebuiltin("Action(OSD)") #close hidden gui
      start = int(time.mktime(program['start_date'].timetuple()))
      end = int(time.mktime(program['end_date'].timetuple()))
      showID = program['showID']
      if RECALL: watch_channel(channel,start,end, showID)
      else: watch_channel(channel, start, end, showID, True)
    elif controlID==210: #record program
      setup_recording(program['showID'])
    elif controlID==211: #teletext
      from resources.lib.teletext import Teletext
      tele = Teletext()
      tele.doModal()
      del tele
    elif controlID==201: #Back
      self.close()
    elif controlID==202: #Channel Up
      nr=skip_channel(+1)
    elif controlID==203: #Channel Down
      nr=skip_channel(-1)
    elif controlID==205: #stop
      #xbmc.executebuiltin("Action(OSD)")
      xbmc.executebuiltin("Action(Stop)")
      self.close()
    #elif controlID==208: #start channel
    #  if xbmcgui.Dialog().yesno(channeltitle, __addon__.getLocalizedString(31907)):
    #     __addon__.setSetting(id="start_channel", value=channeltitle)
     
    elif controlID==208: #favourite
      isFavourite=xbmcgui.Window(10000).getProperty('favourite')
      channelList=_zattooDB_.getChannelList()['index']
      update=False
                            
      if isFavourite=="0":
          if xbmcgui.Dialog().yesno(channeltitle, __addon__.getLocalizedString(31908)): 
            channelList.append(channel)
            update=True
      elif xbmcgui.Dialog().yesno(channeltitle, __addon__.getLocalizedString(31909)):
          channelList.remove(channel)
          update=True

      if update:
        channelList=",".join(channelList)
        
        result=_zattooDB_.zapi.exec_zapiCall('/zapi/channels/favorites/update', {'cids': channelList, 'ctype': 'tv'})
        _zattooDB_.updateChannels(True)
        _zattooDB_.updateProgram()
         
    elif controlID>300:
      xbmcgui.Window(10000).setProperty('zattoo_runningView',"")
      xbmcgui.Window(10000).setProperty('zattooGUI', 'False')
      xbmc.executebuiltin("Dialog.Close(all,true)") #close hidden GUI
      #xbmc.executebuiltin("Action(OSD)") #close hidden gui
      
      if controlID==303: xbmc.executebuiltin('ActivateWindow(10025,"plugin://'+__addonId__+'/?mode=channellist")')
      elif controlID==302: xbmc.executebuiltin('RunPlugin("plugin://'+__addonId__+'/?mode=previewOSD")')
      elif controlID==301: xbmc.executebuiltin('RunPlugin("plugin://'+__addonId__+'/?mode=epgOSD")')
      
  def onFocus(self, controlID):
    i=10




def main():

  global _listMode_
  if _listMode_ == None: _listMode_='all'
  #print 'LISTMODE  ' + str(_listMode_)
  global __addonuri__
  global __addonhandle__ 
  __addonuri__ = sys.argv[0]
  __addonhandle__ = int(sys.argv[1])
  args = urllib.parse.parse_qs(sys.argv[2][1:])
  action=args.get('mode', ['root'])[0]
  try:
    channel=_zattooDB_.get_playing()['channel']
    channeltitle=_zattooDB_.get_channeltitle(channel)
    program = _zattooDB_.getPrograms({'index':[channel]}, True, datetime.datetime.now(), datetime.datetime.now())
  except:pass
  try:
    program=program[0]
  except:pass
  
  xbmcgui.Window(10000).setProperty('ZBElastAction', action)

  _keymap_.saveKeyMap()
  _keymap_.toggleKeyMap()


  if action == 'root': build_root(__addonuri__, __addonhandle__)
  elif action == 'channellist': build_channelsList(__addonuri__, __addonhandle__)
  elif action == 'preview': showPreview()
  elif action == 'previewOSD': showPreview()
  elif action == 'epg': showEpg()
  elif action == 'epgOSD': showEpg()
  elif action == 'recordings': build_recordingsList(__addonuri__, __addonhandle__)
  elif action == 'searchlist': build_searchList()
  elif action == 'selectStartChannel': selectStartChannel()
  elif action == 'editKeyMap': _keymap_.editKeyMap()
  elif action == 'deleteKeyMap': _keymap_.deleteKeyMap()
  #elif action == 'showKeyMap': showkeymap()
  elif action == 'record_l': setup_recording(program['showID'])
  elif action == 'search': 
      
      try:
        search = args.get('id')[0]
      except: search=''
      #debug('AddonHandle-action '+str(__addonhandle__))
      search_show(__addonuri__, __addonhandle__, search)
  elif action == 'show_settings':
    __addon__.openSettings()
    _zattooDB_.zapi.renew_session()
  elif action == 'watch_c':
    cid = args.get('id',['ard'])[0]
    if cid=="current": cid=_zattooDB_.get_playing()['channel'] 
    start = args.get('start', '0')[0]
    end = args.get('end', '0')[0]
    showID = args.get('showID', '1')[0]
    restart = args.get('restart', 'false')[0]
    showOSD = args.get('showOSD', '0')[0]
    watch_channel(cid, start, end, showID, restart=='true', showOSD=='1')
  elif action == 'skip_channel':
    skipDir = args.get('skipDir')[0]
    skip_channel(int(skipDir))
  elif action == 'toggle_channel': toggle_channel()
  elif action == 'switchlist':
    
    if __addon__.getSetting('show_favourites')=='true':
      _listMode_ ='all'
      __addon__.setSetting('show_favourites', 'false')
    else: 
      _listMode_ ='favorites'
      __addon__.setSetting('show_favourites', 'true')
    __addon__.setSetting('channellist', _listMode_)
    xbmc.executebuiltin('ReloadSkin()')
    build_channelsList(__addonuri__, __addonhandle__)
  elif action == 'record_p':
    program_id = args.get('program_id')[0]
    setup_recording(program_id)  
  elif action == 'watch_r':
    recording_id = args.get('id')[0]
    start = args.get('start', '0')[0]
    watch_recording(__addonuri__, __addonhandle__, recording_id, start)
  elif action == 'remove_recording':
    recording_id = args.get('recording_id')[0]
    title = args.get('title')[0]
    delete_recording(recording_id, title)
  elif action == 'remove_series':
    recording_id = args.get('recording_id')[0]
    series = args.get('series')[0]
    delete_series(recording_id, series)
  elif action == 'reloadDB':  
    _zattooDB_.reloadDB(True)   
  elif action == 'changeStream':
    
    if stream_type == 'hls': change_stream(1)
    else:
      streams=xbmc.Player().getAvailableAudioStreams()
      debug('AudioStreams ' + str(streams))
      dialog=xbmcgui.Dialog()
      ret = dialog.select('audio streams', streams)
      if ret==-1: return
      xbmc.Player().setAudioStream(ret)
      
  elif action == 'teletext':
    from resources.lib.teletext import Teletext
    tele = Teletext()
    tele.doModal()
    del tele
  elif action == 'makelibrary':
    xbmc.executebuiltin("ActivateWindow(busydialog)")
    _library_.delete_library()
    _library_.make_library()
    xbmc.executebuiltin("Dialog.Close(busydialog)")
  elif action == 'resetdir':
    delete = xbmcgui.Dialog().yesno(__addonname__, __addon__.getLocalizedString(31911))
    if delete:
      _library_.delete_library()
      __addon__.setSetting(id='library_dir', value="")
      xbmc.executebuiltin('Container.Refresh')
  elif action == 'cleanProg':
    _zattooDB_.cleanProg()
  elif action == 'popular': showPreview('popular')
  elif action == 'showInfo': 

    makeOsdInfo()
    osd = zattooOSD("zattooOSD.xml",__addon__.getAddonInfo('path'))
    osd.doModal()
    del osd
    
  elif action == 'nr':
    nr = args.get('nr')[0]
  
    input_numbers(nr)
    
  elif action =='category':
    showCategory()
    
  elif action == 'build_category':
    cat = args.get('cat')[0]
    build_category(__addonuri__, __addonhandle__, cat)
  elif action == 'helpmy':
    img = args.get('img')[0]
    _helpmy_.showHelp(img)
    
  elif action == 'showhelp': showHelp(__addonuri__, __addonhandle__)
    
  elif action == 'inputsearch':
    __addonuri__= sys.argv[0]
    __addonhandle__ = int(sys.argv[1])
    search = xbmcgui.Dialog().input(__addon__.getLocalizedString(31200), type=xbmcgui.INPUT_ALPHANUM)
   
    if search == '': return
    search_show(__addonuri__, __addonhandle__, search)
    
  elif action == 'deletesearch':
    dialog = xbmcgui.Dialog()
    ret = dialog.yesno(localString(320001), '[COLOR gold]'+localString(32025)+'[/COLOR]','', '','','[COLOR red]'+local(19291)+'[/COLOR]')
    if ret == 1:
      al = args.get('al')[0]
      search = args.get('search')[0]
      _zattooDB_.del_search(al,search)
      xbmc.executebuiltin('Container.Refresh')
    
  elif action == 'editsearch':
    item = args.get('search')[0]
    search = _zattooDB_.edit_search(item)
    xbmc.executebuiltin('Container.Refresh')
    

