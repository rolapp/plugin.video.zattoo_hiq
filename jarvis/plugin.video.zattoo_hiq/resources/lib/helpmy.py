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

__addon__ = xbmcaddon.Addon()
__addonId__=__addon__.getAddonInfo('id')

class HelpGui(xbmcgui.WindowXMLDialog):

  def __init__(self, xmlFile, scriptPath):
    xbmcgui.Window(10000).setProperty('HelpGui', 'True') 
    self.HelpImg =xbmcgui.ControlImage(50, 50, 1180, 596,__addon__.getAddonInfo('path') + '/resources/media/background.png'  , aspectRatio=0)
    self.addControl(self.HelpImg)
    #self.show()
    
  def showHelp(self, Img):
    self.HelpImg.setImage(__addon__.getAddonInfo('path') + '/resources/media/' + Img, False)
    

class helpmy:
    
    def showHelp(self, Img):
	gui = HelpGui("help.xml", __addon__.getAddonInfo('path'))
	gui.showHelp(Img)
	gui.doModal()
	del gui
    
