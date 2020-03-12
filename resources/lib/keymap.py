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

import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import sys, urllib.parse, os
import  time, datetime, threading
from resources.lib.zattooDB import ZattooDB
import xml.etree.ElementTree as ET

__addon__ = xbmcaddon.Addon()
__addonId__=__addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__addondir__  = xbmc.translatePath( __addon__.getAddonInfo('profile') ) 
_zattooDB_ = ZattooDB()

localString = __addon__.getLocalizedString


class KeyListener(xbmcgui.WindowXMLDialog):
    TIMEOUT = 5

    def __new__(cls):
        gui_api = tuple(map(int, xbmcaddon.Addon('xbmc.gui').getAddonInfo('version').split('.')))
        file_name = "DialogNotification.xml" if gui_api >= (5, 11, 0) else "DialogKaiToast.xml"
        return super(KeyListener, cls).__new__(cls, file_name, "")

    def __init__(self):
        self.key = None

    def onInit(self):
        try:
            self.getControl(401).addLabel(localString(32001)+' in 3sec')
            #self.getControl(402).addLabel(localString(32002))
        except AttributeError:
            self.getControl(401).setLabel(localString(32001)+' in 3sec')
            #self.getControl(402).setLabel(localString(32002))

    def onAction(self, action):
        code = action.getButtonCode()
        self.key = None if code == 0 else str(code)
        self.close()

    @staticmethod
    def record_key():
        dialog = KeyListener()
        timeout = threading.Timer(KeyListener.TIMEOUT, dialog.close)
        timeout.start()
        dialog.doModal()
        timeout.cancel()
        key = dialog.key
        del dialog
        return key
        
class KeyMap:

  def editKeyMap(self):
      cmds=['OSD', 'prevChan', 'nextChan', 'toggleChan', 'audio', 'record', 'Teletext', 'Preview', 'EPG', 'List', 'recordlist',  'category', 'playerosd']
      cmdsText=[]
      nr=0
      for cmd in cmds:
          cmdsText.append(localString(32010+int(nr)))
          nr+=1
      dialog=xbmcgui.Dialog()
      cmd = dialog.select(localString(32000), cmdsText)
      if cmd==-1:return
  
      newkey = KeyListener.record_key()
      __addon__.setSetting('key_'+cmds[cmd], newkey)
  
  def saveKeyMap(self):
   
      dest = __addondir__ + '/userKeymap.xml'
    
    # start 
      builder = ET.TreeBuilder()
      builder.start("keymap", {})
      builder.start('fullscreenvideo', {})
      builder.start("keyboard", {})
      
    # Channel up
      key = __addon__.getSetting('key_nextChan')
      if key.isdigit():builder.start("key", {"id":key})
      else: builder.start('up', {})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=skip_channel&amp;skipDir=1")')
      if key.isdigit():builder.end('key')
      else: builder.end('up')
      
    # Channel Down  
      key = __addon__.getSetting('key_prevChan')
      if key.isdigit():builder.start("key", {"id":key})
      else: builder.start('down', {})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=skip_channel&amp;skipDir=-1")')
      if key.isdigit():builder.end('key')
      else: builder.end('down')
      
    # Channel pageup
      key = 'pageup'
      builder.start(key, {})     
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=skip_channel&amp;skipDir=1")')
      builder.end(key)
      
    # Channel pageDown  
      key = 'pagedown'
      builder.start(key, {})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=skip_channel&amp;skipDir=-1")')
      builder.end(key)
      
    # toggle channel
      key = __addon__.getSetting('key_toggleChan')
      if key.isdigit():builder.start("key", {"id":key})
      else: builder.start('left', {})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=toggle_channel")')
      if key.isdigit():builder.end('key')
      else: builder.end('left')
    
    # change stream
      key = __addon__.getSetting('key_audio')
      if key.isdigit():builder.start("key", {"id":key})
      else: builder.start('right', {})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=changeStream")')
      if key.isdigit():builder.end('key')
      else: builder.end('right')
    
    # Zattoo OSD
      key = __addon__.getSetting('key_OSD')
      if key.isdigit():builder.start("key", {"id":key})
      else: builder.start('return', {})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=showInfo")')
      if key.isdigit():builder.end('key')
      else: builder.end('return')
    
    # Teletext
      key = __addon__.getSetting('key_Teletext')
      if key.isdigit():builder.start("key", {"id":key})
      else: builder.start('v', {})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=teletext")')
      if key.isdigit():builder.end('key')
      else: builder.end('v')
      
    # EPG
      key = __addon__.getSetting('key_EPG')
      if key.isdigit():builder.start("key", {"id":key})
      else: builder.start('e', {})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=epg")')
      if key.isdigit():builder.end('key')
      else: builder.end('e')
      
    # Preview
      key = __addon__.getSetting('key_Preview')
      if key.isdigit():builder.start("key", {"id":key})
      else: builder.start('c', {})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=preview")')
      if key.isdigit():builder.end('key')
      else: builder.end('c')
    
    # Channellist
      key = __addon__.getSetting('key_List')
      if key.isdigit():builder.start("key", {"id":key})
      else: builder.start('h', {})
      builder.data('ActivateWindow(10025,"plugin://plugin.video.zattoo_hiq/?mode=channellist")')
      if key.isdigit():builder.end('key')
      else: builder.end('h')
      
    # Record
      key = __addon__.getSetting('key_record')
      if key.isdigit():builder.start("key", {"id":key})
      else: builder.start('k', {})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=record_l")')
      if key.isdigit():builder.end('key')
      else: builder.end('k')
      
    # Recordliste
      key = __addon__.getSetting('key_recordlist')
      if key.isdigit():builder.start("key", {"id":key})
      else: builder.start('b', {})
      builder.data('ActivateWindow(10025,"plugin://plugin.video.zattoo_hiq/?mode=recordings")')
      if key.isdigit():builder.end('key')
      else: builder.end('b')
      
    # Categoryliste
      key = __addon__.getSetting('key_category')
      if key.isdigit():builder.start("key", {"id":key})
      else: builder.start('d', {})
      builder.data('ActivateWindow(10025,"plugin://plugin.video.zattoo_hiq/?mode=category")')
      if key.isdigit():builder.end('key')
      else: builder.end('d')
      
    # Player OSD
      key = __addon__.getSetting('key_playerosd')
      if key.isdigit():builder.start("key", {"id":key})
      else: builder.start('return mod="longpress"', {})
      builder.data('OSD')
      if key.isdigit():builder.end('key')
      else: builder.end('return')
      
    # Genreliste
      #key = __addon__.getSetting('key_genre')
      #if key.isdigit():builder.start("key", {"id":key})
      #else: builder.start('b', {})
      #builder.data('ActivateWindow(10025,"plugin://plugin.video.zattoo_hiq/?mode=genra")')
      #builder.end(key)  
    
    # Numeric
      key = 'zero'
      builder.start(key, {})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=nr&amp;nr=58")')
      builder.end(key)
      
      key = 'one'
      builder.start(key, {})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=nr&amp;nr=59")')
      builder.end(key)
      
      key = 'two'
      builder.start(key, {})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=nr&amp;nr=60")')
      builder.end(key)
      
      key = 'three'
      builder.start(key, {})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=nr&amp;nr=61")')
      builder.end(key)
      
      key = 'four'
      builder.start(key, {})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=nr&amp;nr=62")')
      builder.end(key)
      
      key = 'five'
      builder.start(key, {})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=nr&amp;nr=63")')
      builder.end(key)
      
      key = 'six'
      builder.start(key, {})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=nr&amp;nr=64")')
      builder.end(key)
      
      key = 'seven'
      builder.start(key, {})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=nr&amp;nr=65")')
      builder.end(key)
      
      key = 'eight'
      builder.start(key, {})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=nr&amp;nr=66")')
      builder.end(key)
      
      key = 'nine'
      builder.start(key, {})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=nr&amp;nr=67")')
      builder.end(key)
      
    # End keyboard
      builder.end("keyboard")
          
    # Mouse left Click
      builder.start("mouse", {})
      key = 'leftclick'
      builder.start(key, {})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=showInfo")')
      builder.end(key)
      builder.end("mouse")
    # Touch Tap
      builder.start("touch", {})
      
      key = 'tap'
      builder.start(key, {})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=showInfo")')
      builder.end(key)
      
      key = 'swipe'
      builder.start(key, {"direction":"left"})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=toggle_channel")')
      builder.end(key)
      
      key = 'swipe'
      builder.start(key, {"direction":"up"})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=skip_channel&skipDir=1")')
      builder.end(key)
      
      key = 'swipe'
      builder.start(key, {"direction":"down"})
      builder.data('RunPlugin("plugin://plugin.video.zattoo_hiq/?mode=skip_channel&skipDir=-1")')
      builder.end(key)
      
      builder.end("touch")
      builder.end('fullscreenvideo')
      builder.end("keymap")
      element = builder.close()
      self.prettify(element)
      ET.ElementTree(element).write(dest, 'utf-8')
  
  def deleteKeyMap(self):
      path=xbmc.translatePath(__addondir__ + '/userKeymap.xml')
      if os.path.isfile(path):
        try:
          os.remove(path)
        except:pass
         
  def prettify(self, elem, indent="  ", level=0):
    i = "\n" + level*indent
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + indent
        for el in elem:
            self.prettify(el, indent, level+1)
        if not el.tail or not el.tail.strip():
            el.tail = i
    if not elem.tail or not elem.tail.strip():
        elem.tail = i
  
  def toggleKeyMap(self):
    KEYMAP = __addon__.getSetting('keymap')
    if KEYMAP == "1":
      source = __addondir__ + '/userKeymap.xml'
    elif KEYMAP == "2":
      path = __addondir__ + '/myKeymap.xml'
      if os.path.isfile(path): source = path
      else:
        source =__addon__.getAddonInfo('path') + '/resources/keymap/defaultKeymap.xml'
    else:
      source =__addon__.getAddonInfo('path') + '/resources/keymap/defaultKeymap.xml'
    dest = __addondir__ + '/zattooKeymap.xml'
    with open(source, 'r') as file: content = file.read()
    with open(dest, 'w') as file: file.write(content)
