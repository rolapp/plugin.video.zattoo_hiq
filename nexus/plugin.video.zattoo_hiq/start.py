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

import xbmc, xbmcgui, xbmcaddon, xbmcvfs
import os

__addon__ = xbmcaddon.Addon()
__addondir__  = xbmcvfs.translatePath( __addon__.getAddonInfo('profile') )
__addonId__=__addon__.getAddonInfo('id')
localString = __addon__.getLocalizedString
DEBUG = __addon__.getSetting('debug')

def debug(content):
    if DEBUG:log(content, xbmc.LOGDEBUG)

def notice(content):
    log(content, xbmc.LOGINFO)

def log(msg, level=xbmc.LOGINFO):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level)

#reload Account
profilePath = xbmcvfs.translatePath(__addon__.getAddonInfo('profile'))

if os.path.isfile(os.path.join(profilePath, 'account.cache')):
	xbmcgui.Dialog().notification(localString(30104), localString(31024),  __addon__.getAddonInfo('path') + '/resources/icon.png', 500, False)
	#profilePath = xbmcvfs.translatePath(__addon__.getAddonInfo('profile'))
	os.remove(os.path.join(profilePath, 'cookie.cache'))
	os.remove(os.path.join(profilePath, 'session.cache'))
	os.remove(os.path.join(profilePath, 'account.cache'))
	os.remove(os.path.join(profilePath, 'pzuid.cache'))

# from resources.lib.myplayer import myPlayer
# global player
# player = myPlayer()
import resources.lib.service as service

debug('Start Service')
service.start() 

 


