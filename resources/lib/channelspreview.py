# coding=utf-8
#
#    copyright (C) 2017 Steffen Rolapp (github@rolapp.de)
#
#    based on ZattooBoxExtended by Daniel Griner (griner.ch@gmail.com) lisence under GPL
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

import xbmc, xbmcgui, xbmcaddon, time, datetime, threading
from resources.lib.zattooDB import ZattooDB
from resources.lib.guiactions import *

__addon__ = xbmcaddon.Addon()
__addonId__=__addon__.getAddonInfo('id')
localString = __addon__.getLocalizedString

class ChannelsPreview(xbmcgui.WindowXML): #needs to be WindowXML or onInit won't fire
    #print('FAV:'+str(fav))
    #favourites=favourites

    def __new__(cls):
        # GreenAir: change path
        return super(ChannelsPreview, cls).__new__(cls, "zattooGUI.xml", __addon__.getAddonInfo('path'))

    def __init__(self):
        #super(ChannelsPreview, self).__init__()
        self.channels = []
        self.programms = []
        self.controls = []
        self.selected = 0
        self.highlightImage = ''
        self.startChannel = 0
        self.refreshTimerRunning=False
        self.updateNr=0
        xbmcgui.Window(10000).setProperty('zattoo_runningView',"preview")

    def onInit(self):
        self.highLabel=''
        self.rebuildChannels()

    '''
    def onClick(self, controlId):
        print('CLICKED')
        i = 20  # why isn't this called!?
    def onFocus(self):
        print('HASFOCUS')
    '''

    def onAction(self, action):
        actionID = action.getId()
        #print('previewAction'+str(action))
        if actionID in [ACTION_PARENT_DIR, KEY_NAV_BACK, ACTION_PREVIOUS_MENU]:
            self.close()
             #print('SELF CLOSE')
            self.refreshTimerRunning=False
            #xbmc.executebuiltin("PreviousMenu")
        #elif actionID in [ACTION_BUILT_IN_FUNCTION]:
            #self.close()
        elif actionID == ACTION_MOVE_LEFT:
            self.moveHighlight(-1)
        elif actionID == ACTION_MOVE_RIGHT:
            self.moveHighlight(1)
        elif actionID in [ACTION_MOVE_UP, ACTION_MOUSE_WHEEL_UP, ACTION_GESTURE_SWIPE_UP]:
            self.moveHighlight(-5)
        elif actionID in [ACTION_MOVE_DOWN, ACTION_MOUSE_WHEEL_DOWN, ACTION_GESTURE_SWIPE_DOWN]:
            self.moveHighlight(5)
        elif actionID in [ACTION_SELECT_ITEM, ACTION_MOUSE_LEFT_CLICK]:
            self.refreshTimerRunning=False
            url = "plugin://"+__addonId__+"/?mode=watch_c&id=" + self.controls[self.selected%16]['channel']
            xbmc.executebuiltin('XBMC.RunPlugin(%s)' % url)
            #xbmc.executebuiltin("Action(FullScreen)")
        elif actionID == ACTION_MOUSE_MOVE:
            x=int(action.getAmount1()/(self.getWidth()/5))
            y=int(action.getAmount2()/(self.getHeight()/4))
            if (x>2 and y<2):return
            controlNr = self.selected%16
            step=y*3+x-controlNr
            if(y==3):step+=2
            #don't update current or rollover after last channel
            if(step==0 or (self.selected+step>len(self.channels)-2)):return
            self.moveHighlight(step, True)

    def getControlPos(self, nr):
        if (nr<6):
            x = (nr % 3) * 256
            y = int(nr / 3) * 180
        else:
            nr=nr-6
            x = (nr % 5) * 256
            y = int(nr / 5) * 180 + 360
        return {'x':x, 'y':y}

    def createPreview(self, fav):
        imgW = 256
        imgH = 150
        # collect all controls and add them in one call to save time
        allControls = []
        # create preview images first so they are behind highlight image
        images = []

        for nr in range(0, 16):
            pos=self.getControlPos(nr)
            image = xbmcgui.ControlImage(pos['x'],pos['y'] + 1, imgW - 2, imgH, '')
            allControls.append(image)
            images.append(image)

        self.highlightImage = xbmcgui.ControlImage(0, 0, imgW, 178, '')
        allControls.append(self.highlightImage)
        self.highLabel=''

        #add a scroll label for highlighted item
        self.scrollLabel = xbmcgui.ControlFadeLabel(0,0, 240, 30, 'font13', '0xFF000000')
        allControls.append(self.scrollLabel)

        #preloadImage is buffer for image update
        self.preloadImage = xbmcgui.ControlImage(0, -200, 256, 150, '')
        allControls.append(self.preloadImage)

        for nr in range(0, 16):
            pos=self.getControlPos(nr)
            logo = xbmcgui.ControlImage(pos['x'] + 5, pos['y'] + 100, 84, 48, '')
            label = xbmcgui.ControlLabel(pos['x'] + 6, pos['y'] + imgH - 1, 250, 30, 'font13')
            channelNr = xbmcgui.ControlLabel(pos['x'] + 200, pos['y'] + 5, 50, 20, 'font13', alignment=1)

            allControls.append(logo)
            allControls.append(label)
            allControls.append(channelNr)

            self.controls.append({
                'image':images[nr],
                'logo':logo,
                'label':label,
                'channelNr':channelNr,
                'program':'',
                'visible':True
            })

        addonPath=xbmcaddon.Addon().getAddonInfo('path')

        #add info controls
        posX=768
        #bg = xbmcgui.ControlImage(posX-10, -10, 530, 376, 'recentaddedback.png')
        #bg = xbmcgui.ControlImage(posX, 0, 512, 360, 'ContentPanel.png')
        #bg = xbmcgui.ControlImage(posX, 0, 512, 360, 'episodematte.png', colorDiffuse='0xFF333333')
        bg = xbmcgui.ControlImage(posX, 0, 512, 360, addonPath + '/resources/media/previewInfo.png')

        self.infoLogo = xbmcgui.ControlImage(74+posX, 5, 140, 70, (xbmcaddon.Addon().getAddonInfo('path') + '/resources/media/channel-highlight.png'))
        self.infoChannelTitle=xbmcgui.ControlLabel(0+posX, 85, 287, 30, 'TITLE', alignment=2)
        self.infoImg = xbmcgui.ControlImage(284+posX, 3, 225, 146, (xbmcaddon.Addon().getAddonInfo('path') + '/resources/media/channel-highlight.png'))

        self.infoTitle=xbmcgui.ControlFadeLabel(5+posX, 150, 500, 20, 'font16','0xFFFFFFFF',2)
        self.infoDesc=xbmcgui.ControlFadeLabel(5+posX, 180, 500, 20, 'font13','0xFFFFFFFF',2)
        self.infoPlot = xbmcgui.ControlTextBox(8+posX, 205, 500, 128, 'font13')
        self.infoNext = xbmcgui.ControlFadeLabel(8+posX, 333, 500, 128, 'font12','0xFFFFFFFF',2)
        
        allControls.append(bg)
        allControls.append(self.infoLogo)
        allControls.append(self.infoChannelTitle)
        allControls.append(self.infoImg)
        allControls.append(self.infoTitle)
        allControls.append(self.infoDesc)
        allControls.append(self.infoPlot)
        allControls.append(self.infoNext)


        self.addControls(allControls)
        self.highlightImage.setImage(addonPath + '/resources/media/channel-highlight.png')
        self.infoPlot.autoScroll(5000, 1800, 5000)

        self.db = ZattooDB()
        if fav=='popular': self.channels = self.db.getPopularList()
        else: self.channels = self.db.getChannelList(fav)

    def rebuildChannels(self):
        currentChannel = self.db.get_playing()['channel']
        #highlight current channel
        if currentChannel!='0' and (currentChannel in self.channels): self.selected=self.channels[currentChannel]['nr']
        else: self.selected=0
        self.showChannels()
        self.moveHighlight()

        self.refreshTimerRunning=True
        self.refreshImageNr=0
        #self.refreshPreviewImages()
        #threading.Timer(10, self.refreshPreviewImages).start()

    def showChannels(self):
        start=int(self.selected/16)*16
        channels = self.channels
        self.programms = ZattooDB().getPrograms(channels, False, datetime.datetime.now(), datetime.datetime.now())

        #xbmcgui.lock()
        for nr in range(0, 16):
            current = start + nr
            control = self.controls[nr]

            if current > (len(channels) - 2): #-2: skip channel['index']
                control['image'].setVisible(False)
                control['logo'].setVisible(False)
                control['label'].setVisible(False)
                control['channelNr'].setVisible(False)
                control['visible'] = False
            else:
                currenChannel= channels[channels['index'][current]]
                title = ''
                control['program']=''
                for search in self.programms:
                    if search['channel'] == currenChannel['id']:
                        title = search['title']
                        control['program']=search
                        break

                control['logo'].setImage(currenChannel['logo'])
                control['label'].setLabel(title)
                control['channelNr'].setLabel(str(current+1))
                control['channel'] = currenChannel['id']
                if control['visible'] == False:
                    control['image'].setVisible(True)
                    control['logo'].setVisible(True)
                    control['label'].setVisible(True)
                    control['channelNr'].setVisible(True)
                    control['visible'] = True

        #show images
        now = int(time.time())
        for control in self.controls:
            if control['visible']:
                #src = 'http://thumb.zattic.com/' + control['channel'] + '/500x288.jpg?r=' + str(now)
                src = 'http://thumb.zattic.com/' + control['channel'] + '/256x144.jpg?r=' + str(now)
                control['image'].setImage(src, False)
                #xbmc.sleep(50)
                #self.preloadImageSrc=src
       
        #xbmcgui.unlock()
        
    '''
    def refreshPreviewImages(self):
        now = int(time.time())

        control=self.controls[self.refreshImageNr]
        if control['visible']:
            src = 'http://thumb.zattic.com/' + control['channel'] + '/500x288.jpg?r=' + str(now)
            self.controls[self.refreshImageNr-1]['image'].setImage(self.preloadImageSrc, False)
            self.preloadImage.setImage(src, False)
            self.preloadImageSrc=src

        self.refreshImageNr+=1
        if self.refreshImageNr>19:self.refreshImageNr=0

        #if self.refreshTimerRunning:
        #    threading.Timer(2, self.refreshPreviewImages).start()
    '''
                
    def moveHighlight(self, step=0, jump=False):
        controlNr = self.selected%16

        #move around infoBox
        if (step==5 and controlNr<6):step=3
        elif (step==5 and controlNr>13):step=18-controlNr
        elif(step==-5 and controlNr<10 and controlNr>2):
            if(controlNr>8):step=-(controlNr-5)
            else:step=-3

        #reset label
        if self.highLabel: self.controls[controlNr]['label'].setLabel(self.highLabel)

        #rebuild channels?
        controlNr+=step
        self.selected+=step
        if self.selected<0:
            self.selected=len(self.channels)-2 #+self.selected+1
            self.showChannels()
        elif self.selected>len(self.channels)-2:
            self.selected=0 #self.selected-len(self.channels)+1
            self.showChannels()
        elif controlNr>15 or controlNr<0:
            self.showChannels()
        
        if jump:
            self.showInfo(jump)
        else:
            i=10
            #if hasattr(self, 'showInfoTimer'): self.showInfoTimer.cancel()
            #self.showInfoTimer = threading.Timer(0.1, self.showInfo)
            #self.showInfoTimer.start()
            self.showInfo()
        #controlNr = self.selected%16
        #src = 'http://thumb.zattic.com/' + self.controls[controlNr]['channel'] + '/500x288.jpg?r=' + str(int(time.time()))
        #self.controls[controlNr]['image'].setImage(src, False)


    def showInfo(self, jump=True):
        controlNr = self.selected%16
        
        endPos=self.getControlPos(controlNr)
        if (not jump):
            #moving highlight
            pos=self.highlightImage.getPosition()
            stepX=(endPos['x']-pos[0])/5
            stepY=(endPos['y']-pos[1])/5
        
            for nr in range(1, 5):
                self.highlightImage.setPosition(pos[0]+(stepX*nr), pos[1]+(stepY*nr))
                xbmc.sleep(10)
        self.highlightImage.setPosition(endPos['x'], endPos['y'])
 
        #refresh image
        if hasattr(self, 'refreshImageTimer'): self.refreshImageTimer.cancel()
        src = 'http://thumb.zattic.com/' + self.controls[controlNr]['channel'] + '/256x144.jpg?r=' + str(int(time.time()))
        self.refreshImageTimer = threading.Timer(1, lambda: self.controls[controlNr]['image'].setImage(src, False))
        self.refreshImageTimer.start()
                
        

        #program= self.controls[controlNr]['program']
        program=ZattooDB().getPrograms({'index':[self.controls[controlNr]['channel']]}, False, datetime.datetime.now(), datetime.datetime.now())[0]
        nextprog = ZattooDB().getPrograms({'index':[self.controls[controlNr]['channel']]}, False, program['end_date']+datetime.timedelta(seconds=60), program['end_date']+datetime.timedelta(seconds=60))

        self.controls[controlNr]['label'].setLabel('')
        self.highLabel=program['title']
        self.scrollLabel.reset()
        self.scrollLabel.setPosition(endPos['x']+6,endPos['y']+149)
        self.scrollLabel.addLabel(program['title'])

        #update info
        channel=self.channels[self.channels['index'][self.selected]]
        self.infoLogo.setImage(channel['logo'], False)

        self.infoTitle.reset()
        self.infoDesc.reset()
        self.infoNext.reset()
        
        if (not program):
            self.infoChannelTitle.setLabel('[B]'+channel ['title'] +'[/B]\n ')
            self.infoTitle.addLabel('[B] [/B]')
            self.infoImg.setImage('')
            self.infoDesc.addLabel('[B] [/B]')
            self.infoPlot.setText('')
            self.infoNext.addLabel('')
            
        else:
            self.infoChannelTitle.setLabel('[B]'+channel ['title'] +'[/B]\n'+ program['start_date'].strftime('%H:%M') + ' - ' + program['end_date'].strftime('%H:%M'))
            self.infoTitle.addLabel('[B]'+program['title']+'[/B]')
            self.infoImg.setImage(program['image_small'], False)
            self.infoNext.addLabel('[COLOR blue]' + localString(30010) +'[/COLOR]'+ '[COLOR aquamarine]' + nextprog[0]['title'] + '[/COLOR]' + '  ' + '[COLOR khaki]' + nextprog[0]['start_date'].strftime('%H:%M')+' - ' +nextprog[0]['end_date'].strftime('%H:%M')+'[/COLOR]')
    
            desc=program['description']
            if (not desc):desc=" "
            self.infoDesc.addLabel('[B]'+desc+'[/B]')
        
            plot=self.db.getShowInfo(program['showID'],'description')
            if (not plot): plot="No description "
            self.infoPlot.setText(plot)

    def close(self):
           xbmc.executebuiltin('ActivateWindow(10025,"plugin://'+__addonId__+'")')
           xbmcgui.Window(10000).setProperty('zattoo_runningView',"")
           #super(ChannelsPreview, self).close()
           # if not self.isClosing:
               # self.isClosing = True
               # super(ChannelsPreview, self).close()
        
    
