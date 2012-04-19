#
# gtkui.py
#
# Copyright (C) 2009 Chase Sterling <chase.sterling@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

import gtk

from deluge.log import LOG as log
from deluge.ui.client import client
from deluge.plugins.pluginbase import GtkPluginBase
import deluge.component as component
from deluge.ui.gtkui.listview import cell_data_time

from common import get_resource

class GtkUI(GtkPluginBase):
    def enable(self):
        self.glade = gtk.glade.XML(get_resource("config.glade"))

        component.get("Preferences").add_page("SeedTime", self.glade.get_widget("prefs_box"))
        component.get("PluginManager").register_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").register_hook("on_show_prefs", self.on_show_prefs)
        # Columns
        torrentview = component.get("TorrentView")
        torrentview.add_func_column(_("Seed Time"), cell_data_time, [int], status_field=["seeding_time"])
        torrentview.add_func_column(_("Stop Seed Time"), cell_data_time, [int], status_field=["seed_stop_time"])
        # Submenu
        log.debug("add items to torrentview-popup menu.")
        torrentmenu = component.get("MenuBar").torrentmenu
        self.seedtime_menu = SeedTimeMenu()
        torrentmenu.append(self.seedtime_menu)
        self.seedtime_menu.show_all()

    def disable(self):
        component.get("Preferences").remove_page("SeedTime")
        component.get("PluginManager").deregister_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").deregister_hook("on_show_prefs", self.on_show_prefs)
        try:
            # Columns
            component.get("TorrentView").remove_column(_("Seed Time"))
            component.get("TorrentView").remove_column(_("Stop Seed Time"))
            # Submenu
            torrentmenu = component.get("MenuBar").torrentmenu
            torrentmenu.remove(self.seedtime_menu)
        except Exception, e:
            log.debug(e)

    def on_apply_prefs(self):
        log.debug("applying prefs for SeedTime")

        try:
            stop_time = float(self.glade.get_widget("txt_default_stop_time").get_text())
        except ValueError:
            self.glade.get_widget("lbl_error").set_text('You must enter a valid number!')
            return False

        self.glade.get_widget("lbl_error").set_text("")
        config = {
            "apply_stop_time": self.glade.get_widget("chk_apply_stop_time").get_active(),
            "remove_torrent": self.glade.get_widget("chk_remove_torrent").get_active(),
            "default_stop_time": stop_time
        }
        client.seedtime.set_config(config)

    def on_show_prefs(self):
        self.glade.get_widget("lbl_error").set_text("")
        client.seedtime.get_config().addCallback(self.cb_get_config)

    def cb_get_config(self, config):
        """callback for on show_prefs"""
        log.debug('cb get config seedtime')
        self.glade.get_widget("chk_apply_stop_time").set_active(config["apply_stop_time"])
        self.glade.get_widget("chk_remove_torrent").set_active(config["remove_torrent"])
        self.glade.get_widget("txt_default_stop_time").set_text('%.02f' % config["default_stop_time"])

class SeedTimeMenu(gtk.MenuItem):
    def __init__(self):
        gtk.MenuItem.__init__(self, "Seed Stop Time")

        self.sub_menu = gtk.Menu()
        self.set_submenu(self.sub_menu)
        self.items = []

        #attach..
        torrentmenu = component.get("MenuBar").torrentmenu
        self.sub_menu.connect("show", self.on_show, None)

    def get_torrent_ids(self):
        return component.get("TorrentView").get_selected_torrents()

    def on_show(self, widget=None, data=None):
        try:
            for child in self.sub_menu.get_children():
                self.sub_menu.remove(child)
            # TODO: Make thise times customizable, and/or add a custom popup
            for time in (None, 1, 2, 3, 7, 14, 30):
                if time is None:
                    item = gtk.MenuItem('Never')
                else:
                    item = gtk.MenuItem(str(time) + ' days')
                item.connect("activate", self.on_select_time, time)
                self.sub_menu.append(item)
            self.show_all()
        except Exception, e:
            log.exception('AHH!')

    def on_select_time(self, widget=None, time=None):
        log.debug("select seed stop time:%s,%s" % (time ,self.get_torrent_ids()) )
        for torrent_id in self.get_torrent_ids():
            client.seedtime.set_torrent(torrent_id, time)

