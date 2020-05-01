#
#    copyright (C) 2017 Steffen Rolapp (github@rolapp.de)   
#
#    based on ZattooBoxExtended by Daniel Griner (griner.ch@gmail.com) license under GPL
#    based on TVGuide by    Tommy Winther http://tommy.winther.nu
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

import datetime, time, os, locale
import threading

import xbmc, xbmcgui, xbmcaddon, xbmcplugin

import sys
reload(sys)
sys.setdefaultencoding('utf8')

from resources.lib.zattooDB import ZattooDB
_zattooDB_ = ZattooDB()

from resources.lib.library import library
_library_=library()
# from notification import Notification
from resources.lib.strings import *

__addon__ = xbmcaddon.Addon()
__addonId__=__addon__.getAddonInfo('id')
__settings__ = xbmcaddon.Addon(__addonId__)
__addonname__ = __addon__.getAddonInfo('name')
__language__ = __settings__.getLocalizedString
localString = __addon__.getLocalizedString
local = xbmc.getLocalizedString

# get Timezone Offset
from tzlocal import get_localzone

try:
  tz = get_localzone()
  offset=tz.utcoffset(datetime.datetime.now()).total_seconds()
  _timezone_=int(offset)
except:pass

_datename_ = {u'Monday': u'Montag', u'Tuesday': u'Dienstag', u'Wednesday':u'Mittwoch'}

DEBUG = True
ACTION_LEFT = 1
ACTION_RIGHT = 2
ACTION_UP = 3
ACTION_DOWN = 4
ACTION_PAGE_UP = 5
ACTION_PAGE_DOWN = 6
ACTION_HOME = 159
ACTION_END = 160

ACTION_0 = 58
ACTION_1 = 59
ACTION_2 = 60
ACTION_3 = 61
ACTION_4 = 62
ACTION_5 = 63
ACTION_6 = 64
ACTION_7 = 65
ACTION_8 = 66
ACTION_9 = 67

ACTION_JUMP_SMS2 = 142
ACTION_JUMP_SMS3 = 143
ACTION_JUMP_SMS4 = 144
ACTION_JUMP_SMS5 = 145
ACTION_JUMP_SMS6 = 146
ACTION_JUMP_SMS7 = 147
ACTION_JUMP_SMS8 = 148
ACTION_JUMP_SMS9 = 149

ACTION_SELECT_ITEM = 7
ACTION_PARENT_DIR = 9
ACTION_PREVIOUS_MENU = 10
ACTION_SHOW_INFO = 11
ACTION_NEXT_ITEM = 14
ACTION_PREV_ITEM = 15

ACTION_MOUSE_WHEEL_UP = 104
ACTION_MOUSE_WHEEL_DOWN = 105
ACTION_MOUSE_MOVE = 107

ACTION_GESTURE_SWIPE_LEFT = 511
ACTION_GESTURE_SWIPE_RIGHT = 521
ACTION_GESTURE_SWIPE_UP = 531
ACTION_GESTURE_SWIPE_DOWN = 541

KEY_NAV_BACK = 92
KEY_CONTEXT_MENU = 117
KEY_HOME = 159

CHANNELS_PER_PAGE = 8

HALF_HOUR = datetime.timedelta(minutes=30)



if __addon__.getSetting('country') == 'CH': SWISS = 'true'
else: SWISS = 'false'
#SWISS = 'true'

def debug(s):
    if DEBUG: xbmc.log(str(s), xbmc.LOGDEBUG)


def setup_recording(params):
    # test ob Aufnahme existiert
    playlist = _zattooDB_.zapi.exec_zapiCall('/zapi/playlist', None)
    for record in playlist['recordings']:
        if int(params['program_id']) == int(record['program_id']):
            xbmcgui.Dialog().ok(__addonname__, __addon__.getLocalizedString(31906))
            return
            
    resultData = _zattooDB_.zapi.exec_zapiCall('/zapi/playlist/program', params)
    #debug('Recording: '+str(params)+'  '+str(resultData))
    if resultData is None:
        xbmcgui.Dialog().ok(__addonname__, __addon__.getLocalizedString(31905))
    else:
        if resultData['success'] == True:
            xbmcgui.Dialog().ok(__addonname__, __addon__.getLocalizedString(31903), __addon__.getLocalizedString(31904))
        else:
            xbmcgui.Dialog().ok(__addonname__, __addon__.getLocalizedString(31905))
      
    _library_.make_library()  # NEW added - by Samoth   


    
class Point(object):
    def __init__(self):
        self.x = self.y = 0

    def __repr__(self):
        return 'Point(x=%d, y=%d)' % (self.x, self.y)


class EPGView(object):
    def __init__(self):
        self.top = self.left = self.right = self.bottom = self.width = self.cellHeight = 0


class ControlAndProgram(object):
    def __init__(self, control, program):
        self.control = control
        self.program = program


class EPG(xbmcgui.WindowXML):
    CHANNELS_PER_PAGE = 8

    C_MAIN_DATE = 4000
    C_MAIN_TITLE = 4020
    C_MAIN_TIME = 4021
    C_MAIN_DESCRIPTION = 4022
    C_MAIN_IMAGE = 4023
    C_MAIN_LOGO = 4024
    C_MAIN_TIMEBAR = 4100
    C_MAIN_LOADING = 4200
    C_MAIN_LOADING_PROGRESS = 4201
    C_MAIN_LOADING_TIME_LEFT = 4202
    C_MAIN_LOADING_CANCEL = 4203
    C_MAIN_MOUSE_CONTROLS = 4300
    C_MAIN_MOUSE_HOME = 4301
    C_MAIN_MOUSE_LEFT = 4302
    C_MAIN_MOUSE_UP = 4303
    C_MAIN_MOUSE_DOWN = 4304
    C_MAIN_MOUSE_RIGHT = 4305
    C_MAIN_MOUSE_EXIT = 4306
    C_MAIN_BACKGROUND = 4600
    C_MAIN_EPG = 5000
    C_MAIN_EPG_VIEW_MARKER = 5001
    C_MAIN_OSD = 6000
    C_MAIN_OSD_TITLE = 6001
    C_MAIN_OSD_TIME = 6002
    C_MAIN_OSD_DESCRIPTION = 6003
    C_MAIN_OSD_CHANNEL_LOGO = 6004
    C_MAIN_OSD_CHANNEL_TITLE = 6005

    def __new__(cls, currentNr, premiumUser):
        # GreenAir: change path
       if __addon__.getSetting('livetv') == "true":
           return super(EPG, cls).__new__(cls, 'script-tvguide-main-livetv.xml', ADDON.getAddonInfo('path'))
       else:
           return super(EPG, cls).__new__(cls, 'script-tvguide-main.xml', ADDON.getAddonInfo('path'))
    def __init__(self, currentNr, premiumUser):
        super(EPG, self).__init__()
#        self.notification = None
        self.redrawingEPG = False
        self.isClosing = False
        self.controlAndProgramList = list()
        self.ignoreMissingControlIds = list()
        self.channelIdx = currentNr
        self.focusPoint = Point()
        self.epgView = EPGView()
        self.lastAction={'action':'', 'time':time.time(), 'count':0}
        self.premiumUser = premiumUser

        # find nearest half hour
        self.viewStartDate = datetime.datetime.today()
        self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)
        xbmcgui.Window(10000).setProperty('zattoo_runningView',"epg")

    def getControl(self, controlId):
        try:
            return super(EPG, self).getControl(controlId)
        except:
            if controlId in self.ignoreMissingControlIds:
                return None
            if not self.isClosing:
                xbmcgui.Dialog().ok("Control not found "+str(controlId), strings(SKIN_ERROR_LINE1), strings(SKIN_ERROR_LINE2), strings(SKIN_ERROR_LINE3))
                self.close()
            return None

    def close(self):
        xbmc.executebuiltin('ActivateWindow(10025,"plugin://'+__addonId__+'")')
        xbmcgui.Window(10000).setProperty('zattoo_runningView',"")
        #super(EPG, self).close()
        #if not self.isClosing:
        #   self.isClosing = True
        #   super(EPG, self).close()

    def onInit(self):
        self.db = ZattooDB()
        control = self.getControl(self.C_MAIN_EPG_VIEW_MARKER)
        if control:
            left, top = control.getPosition()
            self.focusPoint.x = left
            self.focusPoint.y = top
            self.epgView.left = left
            self.epgView.top = top
            self.epgView.right = left + control.getWidth()
            self.epgView.bottom = top + control.getHeight()
            self.epgView.width = control.getWidth()
            self.epgView.cellHeight = control.getHeight() / CHANNELS_PER_PAGE

            # draw epg on open
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)

#        self.notification = Notification(self.database, ADDON.getAddonInfo('path')+'/resources/epg')
        self.updateTimebar()
                
        self.getControl(4400).setVisible(False)
        self.getControl(4401).setVisible(True)

        
       

    


    def onAction(self, action):
        actionId=action.getId()
        #print('EPG:'+str(actionId))
        if actionId in [ACTION_PARENT_DIR, KEY_NAV_BACK, ACTION_PREVIOUS_MENU]:
            self.close()
            return

        elif actionId == ACTION_MOUSE_MOVE:
            # GreenAir: don't show mouse-move infowindow
            #self._showControl(self.C_MAIN_MOUSE_CONTROLS)
            return

        controlInFocus = None
        currentFocus = self.focusPoint
        try:
            controlInFocus = self.getFocus()
            if controlInFocus in [elem.control for elem in self.controlAndProgramList]:
                (left, top) = controlInFocus.getPosition()
                currentFocus = Point()
                currentFocus.x = left + (controlInFocus.getWidth() / 2)
                currentFocus.y = top + (controlInFocus.getHeight() / 2)
        except Exception:
            
            control = self._findControlAt(self.focusPoint)
            if control is None and len(self.controlAndProgramList) > 0:
                control = self.controlAndProgramList[0].control
            if control is not None:
                self.setFocus(control)
                return

        if actionId in [ACTION_LEFT, ACTION_4, ACTION_JUMP_SMS4]:
            self._left(currentFocus)
        elif actionId in [ACTION_RIGHT, ACTION_6, ACTION_JUMP_SMS6]:
            self._right(currentFocus)
        elif actionId in [ACTION_UP, ACTION_2, ACTION_JUMP_SMS2]:

            self._up(currentFocus)
        elif actionId in [ACTION_DOWN, ACTION_8, ACTION_JUMP_SMS8]:
            self._down(currentFocus)
        elif actionId in [ACTION_3, ACTION_JUMP_SMS3]:
            self.viewStartDate -= datetime.timedelta(hours=2)
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)
        elif actionId in [ACTION_9, ACTION_JUMP_SMS9]:
            self.viewStartDate += datetime.timedelta(hours=2)
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)
        elif actionId in [ACTION_NEXT_ITEM, ACTION_PAGE_UP]:
            self._nextDay()
        elif actionId in [ACTION_PREV_ITEM, ACTION_PAGE_DOWN]:
            self._previousDay()
        elif actionId == ACTION_1:
            self._moveUp(CHANNELS_PER_PAGE)
        elif actionId in [ACTION_7, ACTION_JUMP_SMS7]:
            self._moveDown(CHANNELS_PER_PAGE)
        elif actionId == ACTION_MOUSE_WHEEL_UP:
            self._moveUp(scrollEvent=True)
        elif actionId == ACTION_MOUSE_WHEEL_DOWN:
            self._moveDown(scrollEvent=True)
        elif actionId in [KEY_HOME, ACTION_5, ACTION_JUMP_SMS5]:
            self.viewStartDate = datetime.datetime.today()
            self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30,
                                                     seconds=self.viewStartDate.second)
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)
        elif actionId == ACTION_0:
            self.getDate()
        
            
    def onClick(self, controlId):
        if controlId in [self.C_MAIN_LOADING_CANCEL, self.C_MAIN_MOUSE_EXIT]:
            self.close()
            return
            
        elif controlId == 4350: #touch start
            self.getControl(4401).setVisible(False)
            self.getControl(4400).setVisible(True)
        
        elif controlId == 4303:
            self._moveUp(CHANNELS_PER_PAGE)
        elif controlId == 4304:
            self._moveDown(CHANNELS_PER_PAGE)
        elif controlId == 4302:
            self.viewStartDate -= datetime.timedelta(hours=2)
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)
            return
        elif controlId == 4305:
            self.viewStartDate += datetime.timedelta(hours=2)
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)
            return
        elif controlId == 4307:
            self._previousDay()
        elif controlId == 4308:
            self._nextDay()
        elif controlId == 4309:
            self.getDate()
        elif controlId == 4001:
            self.viewStartDate = datetime.datetime.today()
            self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30,
                                                     seconds=self.viewStartDate.second)
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)
        
        if self.isClosing: return

        program = self._getProgramFromControl(self.getControl(controlId))
        if program is None: return

        start = int(time.mktime(program['start_date'].timetuple()))
        end = int(time.mktime(program['end_date'].timetuple()))
        now = time.time()
        url=''
        
        accountData=_zattooDB_.zapi.get_accountData()
        RECORD=accountData['session']['recording_eligible']
        RECALL=accountData['session']['recall_eligible']
        try:
          RESTART=accountData['session']['selective_recall_eligible']
        except KeyError:RESTART = False
        try:
          SERIE=accountData['session']['series_recording_eligible']
        except KeyError:SERIE = False
       
        
       
        # if startime is in the future -> setup recording
        if start > now :
        #if not self.premiumUser: xbmcgui.Dialog().ok('Error',' ',strings(ERROR_NO_PREMIUM))
            if RECORD:
                #print 'SERIES:  ' + str(_zattooDB_.getSeries(program['showID']))
                if SERIE:
                    if _zattooDB_.getSeries(program['showID']):#Series record avilable
                        ret = xbmcgui.Dialog().select(program['channel']+': '+program['title']+' '+program['start_date'].strftime('%H:%M')+' - '+program['end_date'].strftime('%H:%M'),[strings(RECORD_SHOW), strings(RECORD_SERIES)])
                        if ret==0: #recording
                            setup_recording({'program_id': program['showID']})
                            return
                        elif ret==1: #recording_series
                            setup_recording({'program_id': program['showID'], 'series': 'true'})
                            return
                        else: return
                
                elif xbmcgui.Dialog().ok(program['title'], strings(RECORD_SHOW) + "?"):
                    setup_recording({'program_id': program['showID']})
                    return
            
            else: 
                xbmcgui.Dialog().ok('Error',' ',strings(ERROR_NO_PREMIUM))
                return
        # else if endtime is in the past -> recall
        elif end < now:
            if RECALL:
                if __addon__.getSetting('epgPlay')=='true':
                    url = "plugin://"+__addonId__+"/?mode=watch_c&id=" + program['channel'] + "&showID=" + program['showID'] + "&start=" + str(start) + "&end=" + str(end)
                else:
                    if SERIE:
                        if _zattooDB_.getSeries(program['showID']):#Series record avilable
                            ret = xbmcgui.Dialog().select(program['channel']+': '+program['title']+' '+program['start_date'].strftime('%H:%M')+' - '+program['end_date'].strftime('%H:%M'),[strings(PLAY_FROM_START), strings(RECORD_SHOW), strings(RECORD_SERIES)])
                            if ret==0:  #recall
                                url = "plugin://"+__addonId__+"/?mode=watch_c&id=" + program['channel'] + "&showID=" + program['showID'] + "&start=" + str(start) + "&end=" + str(end)
                            elif ret==1: #record
                                #url = "plugin://"+__addonId__+"/?mode=record_p&program_id=" + program['showID']
                                setup_recording({'program_id': program['showID']})
                                return
                            elif ret==2: #record series
                                #url = "plugin://"+__addonId__+"/?mode=record_p&program_id=" + program['showID']
                                setup_recording({'program_id': program['showID'], 'series': 'true'})
                                return
                            else: return
                        else: 
                            ret = xbmcgui.Dialog().select(program['channel']+': '+program['title']+' '+program['start_date'].strftime('%H:%M')+' - '+program['end_date'].strftime('%H:%M'),[strings(PLAY_FROM_START), strings(RECORD_SHOW)])
                            if ret==0:  #recall
                                url = "plugin://"+__addonId__+"/?mode=watch_c&id=" + program['channel'] + "&showID=" + program['showID'] + "&start=" + str(start) + "&end=" + str(end)
                            elif ret==1: #record
                                #url = "plugin://"+__addonId__+"/?mode=record_p&program_id=" + program['showID']
                                setup_recording({'program_id': program['showID']})
                                return
                            else: return
            else:
                xbmcgui.Dialog().ok('Error',' ',strings(ERROR_NO_PREMIUM))
                return
        # else currently playing
        else:
            if __addon__.getSetting('epgPlay')=='true' :
                url = "plugin://"+__addonId__+"/?mode=watch_c&id=" + program['channel'] + "&showID=" + program['showID']
            elif RECALL or RESTART:
                if _zattooDB_.getSeries(program['showID']): #Series record avilable
                    ret = xbmcgui.Dialog().select(program['channel']+': '+program['title']+' '+program['start_date'].strftime('%H:%M')+' - '+program['end_date'].strftime('%H:%M'), [strings(WATCH_CHANNEL), strings(PLAY_FROM_START), strings(RECORD_SHOW), strings(RECORD_SERIES)])
                    if ret==0:  #watch live
                        url = "plugin://"+__addonId__+"/?mode=watch_c&id=" + program['channel'] + "&showID=" + program['showID']
                    elif ret==1:  #recall
                        if RESTART:
                                url = "plugin://"+__addonId__+"/?mode=watch_c&id=" + program['channel'] +"&showID=" + program['showID'] + "&restart=true" + "&start=" + str(start) + "&end=" + str(end)
                        else:
                            url = "plugin://"+__addonId__+"/?mode=watch_c&id=" + program['channel'] + "&showID=" + program['showID'] + "&start=" + str(start) + "&end=" + str(end)
                       
                    elif ret==2: #record
                        #url = "plugin://"+__addonId__+"/?mode=record_p&program_id=" + program['showID']
                        setup_recording({'program_id': program['showID']})
                        return
                    elif ret==3: #record series
                        #url = "plugin://"+__addonId__+"/?mode=record_p&program_id=" + program['showID']
                        setup_recording({'program_id': program['showID'], 'series': 'true'})
                        return
                    else: return
                else:
                    ret = xbmcgui.Dialog().select(program['channel']+': '+program['title']+' '+program['start_date'].strftime('%H:%M')+' - '+program['end_date'].strftime('%H:%M'), [strings(WATCH_CHANNEL), strings(PLAY_FROM_START), strings(RECORD_SHOW)])
                    if ret==0:  #watch live
                        url = "plugin://"+__addonId__+"/?mode=watch_c&id=" + program['channel'] + "&showID=" + program['showID']
                    elif ret==1:  #recall
                        if RESTART:
                                url = "plugin://"+__addonId__+"/?mode=watch_c&id=" + program['channel'] +"&showID=" + program['showID'] + "&restart=true" + "&start=" + str(start) + "&end=" + str(end)
                        else:
                            url = "plugin://"+__addonId__+"/?mode=watch_c&id=" + program['channel'] + "&showID=" + program['showID'] + "&start=" + str(start) + "&end=" + str(end)
                    elif ret==2: #record
                        #url = "plugin://"+__addonId__+"/?mode=record_p&program_id=" + program['showID']
                        setup_recording({'program_id': program['showID']})
                        return
                    else: return
            else:
                if RECORD: 
                    ret = xbmcgui.Dialog().select(program['channel']+': '+program['title']+' '+program['start_date'].strftime('%H:%M')+' - '+program['end_date'].strftime('%H:%M'), [strings(WATCH_CHANNEL), strings(RECORD_SHOW)])
                    if ret==0:  #watch live
                        url = "plugin://"+__addonId__+"/?mode=watch_c&id=" + program['channel'] + "&showID=" + program['showID']
                    
                    elif ret==1: #record
                        #url = "plugin://"+__addonId__+"/?mode=record_p&program_id=" + program['showID']
                        setup_recording({'program_id': program['showID']})
                        return
                    else: return
                else:
                    url = "plugin://"+__addonId__+"/?mode=watch_c&id=" + program['channel'] + "&showID=" + program['showID']
        # German Account                
        # else:
            # #debug('German Account')
            # if start > now : 
                # if self.premiumUser:
                    # #print 'SERIES:  ' + str(_zattooDB_.getSeries(program['showID']))
                    # if _zattooDB_.getSeries(program['showID']):#Series record avilable
                        # ret = xbmcgui.Dialog().select(program['channel']+': '+program['title']+' '+program['start_date'].strftime('%H:%M')+' - '+program['end_date'].strftime('%H:%M'),[strings(RECORD_SHOW), strings(RECORD_SERIES)])
                        # if ret==0: #recording
                            # setup_recording({'program_id': program['showID']})
                            # return
                        # elif ret==1: #recording_series
                            # setup_recording({'program_id': program['showID'], 'series': 'true'})
                            # return
                        # else: return

                    # elif xbmcgui.Dialog().ok(program['title'], strings(RECORD_SHOW) + "?"):
                        # setup_recording({'program_id': program['showID']})
                        # return
                # else: return 
                
            # elif end < now :
                 # #if not self.premiumUser:return 
                 # #url = "plugin://"+__addonId__+"/?mode=watch_c&id=" + program['channel'] +"&showID=" + program['showID'] + "&restart=true" + "&start=" + str(start) + "&end=" + str(end)
                # return
            # else:
                # if (__addon__.getSetting('epgPlay')=='true') or (not self.premiumUser):# or (not _zattooDB_.getRestart(program['showID'])):
                    # url = "plugin://"+__addonId__+"/?mode=watch_c&id=" + program['channel'] + "&showID=" + program['showID']
                # else:
                    # if (_zattooDB_.getSeries(program['showID'])) and (_zattooDB_.getRestart(program['showID'])): #Series record avilable
                        # ret = xbmcgui.Dialog().select(program['channel']+': '+program['title']+' '+program['start_date'].strftime('%H:%M')+' - '+program['end_date'].strftime('%H:%M'), [strings(WATCH_CHANNEL), strings(PLAY_FROM_START), strings(RECORD_SHOW), strings(RECORD_SERIES)])
                        # if ret==0:  #watch live
                            # url = "plugin://"+__addonId__+"/?mode=watch_c&id=" + program['channel'] + "&showID=" + program['showID']
                        # elif ret==1:  #recall
                        
                            # url = "plugin://"+__addonId__+"/?mode=watch_c&id=" + program['channel'] +"&showID=" + program['showID'] + "&restart=true" + "&start=" + str(start) + "&end=" + str(end)
                        # elif ret==2: #record
                            # #url = "plugin://"+__addonId__+"/?mode=record_p&program_id=" + program['showID']
                            # setup_recording({'program_id': program['showID']})
                            # return
                        # elif ret==3: #record series
                            # #url = "plugin://"+__addonId__+"/?mode=record_p&program_id=" + program['showID']
                            # setup_recording({'program_id': program['showID'], 'series': 'true'})
                            # return
                        # else: return
                    # elif (_zattooDB_.getSeries(program['showID'])) and (not _zattooDB_.getRestart(program['showID'])): #Series record avilable
                        # ret = xbmcgui.Dialog().select(program['channel']+': '+program['title']+' '+program['start_date'].strftime('%H:%M')+' - '+program['end_date'].strftime('%H:%M'), [strings(WATCH_CHANNEL), strings(RECORD_SHOW), strings(RECORD_SERIES)])
                        # if ret==0:  #watch live
                            # url = "plugin://"+__addonId__+"/?mode=watch_c&id=" + program['channel'] + "&showID=" + program['showID']
                        
                        # elif ret==1: #record
                            # #url = "plugin://"+__addonId__+"/?mode=record_p&program_id=" + program['showID']
                            # setup_recording({'program_id': program['showID']})
                            # return
                        # elif ret==2: #record series
                            # #url = "plugin://"+__addonId__+"/?mode=record_p&program_id=" + program['showID']
                            # setup_recording({'program_id': program['showID'], 'series': 'true'})
                            # return
                        # else: return
                    # elif _zattooDB_.getRestart(program['showID']):
                        # ret = xbmcgui.Dialog().select(program['channel']+': '+program['title']+' '+program['start_date'].strftime('%H:%M')+' - '+program['end_date'].strftime('%H:%M'), [strings(WATCH_CHANNEL), strings(PLAY_FROM_START), strings(RECORD_SHOW)])
                        # if ret==0:  #watch live
                            # url = "plugin://"+__addonId__+"/?mode=watch_c&id=" + program['channel'] + "&showID=" + program['showID']
                        # elif ret==1:  #recall
                        
                            # url = "plugin://"+__addonId__+"/?mode=watch_c&id=" + program['channel'] +"&showID=" + program['showID'] + "&restart=true" + "&start=" + str(start) + "&end=" + str(end)
                        # elif ret==2: #record
                            # #url = "plugin://"+__addonId__+"/?mode=record_p&program_id=" + program['showID']
                            # setup_recording({'program_id': program['showID']})
                            # return
                        # else: return
                    # else: 
                        # ret = xbmcgui.Dialog().select(program['channel']+': '+program['title']+' '+program['start_date'].strftime('%H:%M')+' - '+program['end_date'].strftime('%H:%M'), [strings(WATCH_CHANNEL), strings(RECORD_SHOW)])
                        # if ret==0:  #watch live
                            # url = "plugin://"+__addonId__+"/?mode=watch_c&id=" + program['channel'] + "&showID=" + program['showID']
                        
                        # elif ret==1: #record
                            # #url = "plugin://"+__addonId__+"/?mode=record_p&program_id=" + program['showID']
                            # setup_recording({'program_id': program['showID']})
                            # return
                        # else: return
        xbmc.executebuiltin('XBMC.RunPlugin(%s)' % url)
        

    def setFocusId(self, controlId):
        control = self.getControl(controlId)
        if control: self.setFocus(control)

    def setFocus(self, control):
        debug('setFocus %d' % control.getId())
        if control in [elem.control for elem in self.controlAndProgramList]:
            debug('Focus before %s' % self.focusPoint)
            (left, top) = control.getPosition()
            if left > self.focusPoint.x or left + control.getWidth() < self.focusPoint.x:
                self.focusPoint.x = left
            self.focusPoint.y = top + (control.getHeight() / 2)
            debug('New focus at %s' % self.focusPoint)

        super(EPG, self).setFocus(control)

    def onFocus(self, controlId):
        
        try:
            controlInFocus = self.getControl(controlId)
        except Exception:
            return
        
        program = self._getProgramFromControl(controlInFocus)
        if program is None: return
        # Test auf Restart
        
        if _zattooDB_.getRestart(program['showID']):
            debug("Showinfo test")
            if program['description'] == None:
                self.setControlLabel(self.C_MAIN_TITLE, '[B][COLOR gold]R[/COLOR][/B]  [B]%s[/B]' % program['title'])
            else:
                self.setControlLabel(self.C_MAIN_TITLE, '[B][COLOR gold]R[/COLOR][/B]  [B]%s[/B]  -  [B]%s[/B]' % (program['title'], program['description']))
        else:
            if program['description'] == None:
                self.setControlLabel(self.C_MAIN_TITLE, '[B]%s[/B]' % program['title'])
            else:
                self.setControlLabel(self.C_MAIN_TITLE, '[B]%s[/B]  -  [B]%s[/B]' % (program['title'], program['description']))

        if program['start_date'] or program['end_date']:
            self.setControlLabel(self.C_MAIN_TIME,'[B]%s - %s[/B]' % (self.formatTime(program['start_date']), self.formatTime(program['end_date'])))
        else:
            self.setControlLabel(self.C_MAIN_TIME, '')

        self.setControlText(self.C_MAIN_DESCRIPTION, '')
        #if hasattr(self, 'descriptionTimer'):self.descriptionTimer.cancel() 
        #self.descriptionTimer= threading.Timer(0.2, self._showDescription, [program['showID']])
        #self.descriptionTimer.start()
        self._showDescription(program['showID'])
        #self.setControlImage(self.C_MAIN_LOGO, program['channel_logo'])

        if program['image_small'] is not None:
            self.setControlImage(self.C_MAIN_IMAGE, program['image_small'])
            #self.setControlImage(self.C_MAIN_BACKGROUND, program['image_small'])

#       if ADDON.getSetting('program.background.enabled') == 'true' and program['image_large'] is not None:
#           self.setControlImage(self.C_MAIN_BACKGROUND, program['image_large'])
    
    def _showDescription(self, id):
        description = ZattooDB().getShowInfo(id,'description')
        if description == '': description = strings(NO_DESCRIPTION)
        self.setControlText(self.C_MAIN_DESCRIPTION, description)


    def _pressed(self,action):
        pressed=False
        last=self.lastAction
        timeDiff=time.time()-last['time']

        if last['count']>0: checkDiff=1
        else: checkDiff=0.2

        if last['action']==action and (timeDiff<checkDiff):
            last['count']+=timeDiff
            if last['count']>1:
                pressed=2
                last['count']=0.01
            else: pressed=1
        else:
            last['action']=action
            last['count']=0

        last['time']=time.time()
        return pressed


    def _left(self, currentFocus):
        '''
        pressed=self._pressed('left')
        if pressed==1: return
        elif pressed==2: control=None
        else: control = self._findControlOnLeft(currentFocus)
        '''
        control = self._findControlOnLeft(currentFocus)
        
        if control is not None:
            self.setFocus(control)
        elif control is None:
            self.viewStartDate -= datetime.timedelta(hours=2)
            self.focusPoint.x = self.epgView.right
            self.onRedrawEPG(self.channelIdx, self.viewStartDate, focusFunction=self._findControlOnLeft)

    def _right(self, currentFocus):
        '''
        pressed=self._pressed('right')
        if pressed==1: return
        elif pressed==2: control=None
        else: control = self._findControlOnRight(currentFocus)
        '''
        control = self._findControlOnRight(currentFocus)
        
        if control is not None:
            self.setFocus(control)
        elif control is None:
            self.viewStartDate += datetime.timedelta(hours=2)
            self.focusPoint.x = self.epgView.left
            self.onRedrawEPG(self.channelIdx, self.viewStartDate, focusFunction=self._findControlOnRight)
        

    def _up(self, currentFocus):
        '''
        pressed=self._pressed('up')
        if pressed==1: return
        elif pressed==2:
            self._nextDay()
            return
        '''
        
        currentFocus.x = self.focusPoint.x
        control = self._findControlAbove(currentFocus)
        if control is not None:
            self.setFocus(control)
        elif control is None:
            self.focusPoint.y = self.epgView.top
            self.onRedrawEPG(self.channelIdx - 1, self.viewStartDate,
                             focusFunction=self._findControlBelow)

    def _down(self, currentFocus):
        '''
        pressed=self._pressed('down')
        if pressed==1: return
        elif pressed==2:
            self._previousDay()
            return
        ''' 
        currentFocus.x = self.focusPoint.x
        control = self._findControlBelow(currentFocus)
        if control is not None:
            self.setFocus(control)
        elif control is None:
            self.focusPoint.y = self.epgView.bottom
            self.onRedrawEPG(self.channelIdx + 1, self.viewStartDate,
                             focusFunction=self._findControlAbove)

    def _nextDay(self):
        date = (self.viewStartDate + datetime.timedelta(days=1))
        datehigh = (datetime.datetime.today() + datetime.timedelta(days=14))
        if date > datehigh:
            d = datetime.datetime.strftime(datetime.datetime.date(date), '%d.%m.%Y')
            xbmcgui.Dialog().notification(str(d), localString(31303), time=3000) 
            return
        self.viewStartDate = date
        self.onRedrawEPG(self.channelIdx, self.viewStartDate)

    def _previousDay(self):
        date = (self.viewStartDate - datetime.timedelta(days=1))
        datelow = (datetime.datetime.today() - datetime.timedelta(days=7))
        if date < datelow:
            d = datetime.datetime.strftime(datetime.datetime.date(date), '%d.%m.%Y')
            xbmcgui.Dialog().notification(str(d), localString(31304), time=3000) 
            return
        self.viewStartDate = date
        self.onRedrawEPG(self.channelIdx, self.viewStartDate)

    def _moveUp(self, count=1, scrollEvent=False):
        if scrollEvent:
            self.onRedrawEPG(self.channelIdx - count, self.viewStartDate)
        else:
            self.focusPoint.y = self.epgView.bottom
            self.onRedrawEPG(self.channelIdx - count, self.viewStartDate, focusFunction=self._findControlAbove)

    def _moveDown(self, count=1, scrollEvent=False):
        if scrollEvent:
            self.onRedrawEPG(self.channelIdx + count, self.viewStartDate)
        else:
            self.focusPoint.y = self.epgView.top
            self.onRedrawEPG(self.channelIdx + count, self.viewStartDate, focusFunction=self._findControlBelow)

    def loadChannels(self, favourites):
        self.favourites = favourites

    def onRedrawEPG(self, channelStart, startTime, focusFunction=None):
        
        import time, locale
        #print 'HeuteTIME  ' + str(time.strftime ('%B-%d/%A/%Y'))
        if self.redrawingEPG or self.isClosing:
            #debug('onRedrawEPG - already redrawing')
            return  # ignore redraw request while redrawing
        #debug('onRedrawEPG')

        self.redrawingEPG = True
        self._showControl(self.C_MAIN_EPG)
        self.updateTimebar(scheduleTimer=False)

        # remove existing controls
        self._clearEpg()

        channels = self.db.getChannelList(self.favourites)
        #debug(channelStart)
        if channelStart < 0:
            channelStart = len(channels) - (int((float(len(channels))/8 - len(channels)/8)*8))
        elif channelStart > len(channels) - 8: channelStart = 0
        # if channelStart < 0:
            # channelStart = 0
        # elif channelStart > len(channels) -1: channelStart = len(channels) - 2
        self.channelIdx = channelStart

        
        '''
        #channels that are visible 
        channels={'index':[]}
        for nr in range(0, CHANNELS_PER_PAGE):
            id=allChannels['index'][channelStart+nr]
            channels[id]= allChannels[id]
            channels['index'].append(id)
        '''

        '''
        programs = self.db.getPrograms(channels, False, startTime, startTime + datetime.timedelta(hours=2))
        if programs is None:
            self.onEPGLoadError()
            return
#        channelsWithoutPrograms = list(channels)
        '''
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        ret=self.db.updateProgram(startTime)
        xbmc.executebuiltin("Dialog.Close(busydialog)")
                
        # date and time row
        #Date = str(self.viewStartDate.strftime ('%A %d. %B %Y'))
        self.setControlLabel(self.C_MAIN_DATE, self.formatDate(self.viewStartDate))
        #self.setControlLabel(self.C_MAIN_DATE, Date)
        time=startTime
        for col in range(1, 5):
            self.setControlLabel(4000 + col, self.formatTime(time))
            time += HALF_HOUR

        # set channel logo or text
        for idx in range(0, CHANNELS_PER_PAGE):
            if (channelStart+idx) >= len(channels['index']):
                self.setControlImage(4110 + idx, ' ')
                self.setControlLabel(4010 + idx, ' ')
            else:
                channel = channels[channels['index'][channelStart+idx]]
                #print 'TEST  ' + str(channel['id'])
                self.setControlLabel(4010 + idx, channel['title'])
                if channel['logo'] is not None: self.setControlImage(4110 + idx, channel['logo'])
                else: self.setControlImage(4110 + idx, ' ')
                    
                programs = self.db.getPrograms( {'index':[channel['id']]}, False, startTime, startTime + datetime.timedelta(hours=2))
                for program in programs:
                    # add channel index and logo for control-handling
                    program['channel_index'] = idx
                    program['channel_logo'] = channel['logo']
        
                    startDelta = program['start_date'] - self.viewStartDate
                    stopDelta = program['end_date'] - self.viewStartDate
        
                    cellStart = self._secondsToXposition(startDelta.seconds)
                    if startDelta.days < 0: cellStart = self.epgView.left
                    cellWidth = self._secondsToXposition(stopDelta.seconds) - cellStart
                    if cellStart + cellWidth > self.epgView.right: cellWidth = self.epgView.right - cellStart
        
                    if cellWidth > 1:
                        noFocusTexture = 'tvguide-program-grey.png'
                        focusTexture = 'tvguide-program-grey-focus.png'
        
                        if cellWidth < 25: title = ''  # Text will overflow outside the button if it is too narrow
                        else: title = program['title']
                    
                        control = xbmcgui.ControlButton(
                            cellStart,
                            self.epgView.top + self.epgView.cellHeight * idx,
                            cellWidth - 2,
                            self.epgView.cellHeight - 2,
                            title,
                            noFocusTexture=noFocusTexture,
                            focusTexture=focusTexture
                        )
        
                        self.controlAndProgramList.append(ControlAndProgram(control, program))

#        for channel in channelsWithoutPrograms:
#            idx = channels.index(channel)
#
#            control = xbmcgui.ControlButton(
#                self.epgView.left,
#                self.epgView.top + self.epgView.cellHeight * idx,
#                (self.epgView.right - self.epgView.left) - 2,
#                self.epgView.cellHeight - 2,
#                strings(NO_PROGRAM_AVAILABLE),
#                noFocusTexture='tvguide-program-grey.png',
#                focusTexture='tvguide-program-grey-focus.png'
#            )
#
#            program = src.Program(channel, strings(NO_PROGRAM_AVAILABLE), None, None, None)
#            self.controlAndProgramList.append(ControlAndProgram(control, program))

        # add program controls
        if focusFunction is None:
            focusFunction = self._findControlAt
        focusControl = focusFunction(self.focusPoint)
        controls = [elem.control for elem in self.controlAndProgramList]
        self.addControls(controls)
        if focusControl is not None:
            debug('onRedrawEPG - setFocus %d' % focusControl.getId())
            self.setFocus(focusControl)

        self.ignoreMissingControlIds.extend([elem.control.getId() for elem in self.controlAndProgramList])

        if focusControl is None and len(self.controlAndProgramList) > 0:
            self.setFocus(self.controlAndProgramList[0].control)

        self.redrawingEPG = False

    def _clearEpg(self):
        controls = [elem.control for elem in self.controlAndProgramList]
        try:
            self.removeControls(controls)
        except RuntimeError:
            for elem in self.controlAndProgramList:
                try:
                    self.removeControl(elem.control)
                except RuntimeError:
                    pass  # happens if we try to remove a control that doesn't exist
        del self.controlAndProgramList[:]

    def onEPGLoadError(self):
        self.redrawingEPG = False
        xbmcgui.Dialog().ok(strings(LOAD_ERROR_TITLE), strings(LOAD_ERROR_LINE1), strings(LOAD_ERROR_LINE2))
        self.close()


    def _secondsToXposition(self, seconds):
        return self.epgView.left + (seconds * self.epgView.width / 7200)

    def _findControlOnRight(self, point):
        distanceToNearest = 10000
        nearestControl = None

        for elem in self.controlAndProgramList:
            control = elem.control
            (left, top) = control.getPosition()
            x = left + (control.getWidth() / 2)
            y = top + (control.getHeight() / 2)

            if point.x < x and point.y == y:
                distance = abs(point.x - x)
                if distance < distanceToNearest:
                    distanceToNearest = distance
                    nearestControl = control

        return nearestControl

    def _findControlOnLeft(self, point):
        distanceToNearest = 10000
        nearestControl = None

        for elem in self.controlAndProgramList:
            control = elem.control
            (left, top) = control.getPosition()
            x = left + (control.getWidth() / 2)
            y = top + (control.getHeight() / 2)

            if point.x > x and point.y == y:
                distance = abs(point.x - x)
                if distance < distanceToNearest:
                    distanceToNearest = distance
                    nearestControl = control

        return nearestControl

    def _findControlBelow(self, point):
        nearestControl = None

        for elem in self.controlAndProgramList:
            control = elem.control
            (leftEdge, top) = control.getPosition()
            y = top + (control.getHeight() / 2)

            if point.y < y:
                rightEdge = leftEdge + control.getWidth()
                if leftEdge <= point.x < rightEdge and (nearestControl is None or nearestControl.getPosition()[1] > top):
                    nearestControl = control

        return nearestControl

    def _findControlAbove(self, point):
        nearestControl = None
        for elem in self.controlAndProgramList:
            control = elem.control
            (leftEdge, top) = control.getPosition()
            y = top + (control.getHeight() / 2)

            if point.y > y:
                rightEdge = leftEdge + control.getWidth()
                if leftEdge <= point.x < rightEdge and (nearestControl is None or nearestControl.getPosition()[1] < top):
                    nearestControl = control

        return nearestControl

    def _findControlAt(self, point):
        for elem in self.controlAndProgramList:
            control = elem.control
            (left, top) = control.getPosition()
            bottom = top + control.getHeight()
            right = left + control.getWidth()

            if left <= point.x <= right and top <= point.y <= bottom:
                return control

        return None

    def _getProgramFromControl(self, control):
        for elem in self.controlAndProgramList:
            if elem.control == control:
                return elem.program
        return None

    def _hideControl(self, *controlIds):
        """
        Visibility is inverted in skin
        """
        for controlId in controlIds:
            control = self.getControl(controlId)
            if control:
                control.setVisible(True)

    def _showControl(self, *controlIds):
        """
        Visibility is inverted in skin
        """
        for controlId in controlIds:
            control = self.getControl(controlId)
            if control:
                control.setVisible(False)

    def formatTime(self, timestamp):
        if timestamp:
            format = xbmc.getRegion('time').replace(':%S', '').replace('%H%H', '%H')
            return timestamp.strftime(format)
        else:
            return ''


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

    def setControlImage(self, controlId, image):
        control = self.getControl(controlId)
        if control:
            control.setImage(image.encode('utf-8'), False)

    def setControlLabel(self, controlId, label):
        control = self.getControl(controlId)
        if control and label:
            control.setLabel(label)

    def setControlText(self, controlId, text):
        control = self.getControl(controlId)
        if control:
            control.setText(text)

    def updateTimebar(self, scheduleTimer=True):
        try:
            # move timebar to current time
            timeDelta = datetime.datetime.today() - self.viewStartDate
            control = self.getControl(self.C_MAIN_TIMEBAR)
            if control:
                (x, y) = control.getPosition()
                try:
                    # Sometimes raises:
                    # exceptions.RuntimeError: Unknown exception thrown from the call "setVisible"
                    control.setVisible(timeDelta.days == 0)
                except:
                    pass
                control.setPosition(self._secondsToXposition(timeDelta.seconds), y)

            if scheduleTimer and not xbmc.abortRequested and not self.isClosing:
                threading.Timer(1, self.updateTimebar).start()
        except Exception:
            pass

    def getDate(self):
        
        format = xbmc.getRegion('dateshort')
        dialog = xbmcgui.Dialog()
        today = datetime.date.today()
        date = dialog.numeric(1, localString(31924)).replace(' ','0').replace('/','.')
        if date == today.strftime('%d.%m.%Y'): return
        datelow = (datetime.date.today() - datetime.timedelta(days=7))
        datehigh = (datetime.date.today() + datetime.timedelta(days=14))

        debug('date EPG '+ str(date))
        
        if time.strptime(date, '%d.%m.%Y') < time.strptime(str(datelow), '%Y-%m-%d'):
            xbmcgui.Dialog().notification(str(date), localString(31304), time=3000) 
            return
        if time.strptime(date, '%d.%m.%Y') > time.strptime(str(datehigh), '%Y-%m-%d'):
            xbmcgui.Dialog().notification(str(date), localString(31303), time=3000) 
            return
        date = time.strptime(date, '%d.%m.%Y')
        current = time.strptime(str(self.viewStartDate.strftime ('%Y-%m-%d')), '%Y-%m-%d')
        timedelta = datetime.timedelta(seconds=time.mktime(date) - time.mktime(current))
        if timedelta.seconds == 82800: 
            timedelta += datetime.timedelta(hours=1)
        debug('Timedelta '+str(timedelta))
        if date > current:
            self.viewStartDate += datetime.timedelta(days=int(str(timedelta)[:2]))
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)
        elif date < current:
            delta = str(timedelta).replace('-','')[:2]
            self.viewStartDate -= datetime.timedelta(days=int(delta))
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)
        
