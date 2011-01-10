#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Licensed under the GNU General Public License Version 3

# Infrared Remote Switcher is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.

# Infrared Remote Switcher is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

import pygtk
pygtk.require('2.0')

import gtk
import gnome.ui
import gnomeapplet
import gobject
import gconf

import os.path
import sys
import subprocess

import logging

import ir_switcher_globals as pglobals

license = """Licensed under the GNU General Public License Version 3

Infrared Remote Switcher is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 3
of the License, or (at your option) any later version.

Infrared Remote Switcher is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
02110-1301, USA.
"""

name = "Infrared Remote Switcher"
comment = "GNOME Applet to enable LIRC. It runs irexec and/or irxevent."
copyright = "Copyright © 2011 Roque Pinel"
authors = ["Roque Pinel <repinel@gmail.com>"]
website = "http://code.google.com/p/ir-switcher/"
website_label = "Infrared Remote Switcher applet Website"

class IR_Switcher_Applet(gnomeapplet.Applet):

    pipes = []

    use_irexec = False
    use_irxevent = False

    prefs_key = "/apps/ir-switcher-applet/preferences"

    logging.basicConfig(level=logging.DEBUG)

    def __init__ (self, applet, iid):
        """Initialize the applet"""

        logging.debug("__init__")

        self.__gobject_init__()

        self.applet = applet
        self.client = gconf.client_get_default()

        self.create_menu(applet)

        gnome.init(pglobals.name, pglobals.version)

        self.logo_pixbuf = gtk.gdk.pixbuf_new_from_file(self.get_image_filename(True))

        self.evbox = gtk.EventBox()

        # determine the size to draw the icon
        size = self.applet.get_size() - 2

        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.get_image_filename(), size, size)
        image = gtk.Image()
        image.set_from_pixbuf(pixbuf)

        self.applet.connect("button-press-event", self.on_button_press)
        self.applet.connect('change-size', self.on_change_size, image)
        self.applet.connect("destroy", self.on_destroy)

        self.load_prefs_data()

        self.applet.add(image)
        self.applet.show_all()
        self.applet.set_background_widget(self.applet)

    def create_menu (self, applet):
        """Create the popup menu"""
        xml="""
        <popup name="button3">
            <menuitem name="ItemIRexec"
                      verb="irexec"
                      label="irexec"
                      type="radio"
                      group="run_group"/>
            <menuitem name="ItemIRxevent"
                      verb="irxevent"
                      label="irxevent"
                      type="radio"
                      group="run_group"/>
            <menuitem name="ItemBoth"
                      verb="both"
                      label="both"
                      type="radio"
                      group="run_group"/>
            <separator/>
            <menuitem name="ItemAbout"
                      verb="About"
                      label="_About"
                      pixtype="stock"
                      pixname="gtk-about"/>
        </popup>"""

        verbs = [('About', self.on_click_about)]
        applet.setup_menu(xml, verbs, None)

        popup = self.applet.get_popup_component()
        popup.connect("ui-event", self.on_change_popup)

    def on_change_size(self, applet, new_size, image):
        """Change the applet's image when the panel size changes"""
        logging.debug("on_change_size")

        self.update_image()

    def on_destroy (self, *data):
        """Kill all pipe before destroy applet"""
        logging.debug("on_destroy")

        for pipe in self.pipes:
            self.kill_pipe(pipe)

        del self.pipes[0:len(self.pipes)]

    def on_change_popup (self, obj, label, *data):
        """Update and store properties from the popup"""
        logging.debug("on_change_popup")

        if self.get_popup_prop("irexec") == "1":
            self.use_irexec = True
            self.use_irxevent = False
        elif self.get_popup_prop("irxevent") == "1":
            self.use_irexec = False
            self.use_irxevent = True
        else:
            self.use_irexec = True
            self.use_irxevent = True

        self.store_prefs_data()

        # restart using the new properties
        if len(self.pipes) > 0:
            for pipe in self.pipes:
                self.kill_pipe(pipe)
            del self.pipes[0:len(self.pipes)]

            self.toggle_on_off()

    def on_click_about (self, obj, label, *data):
        """Show information about applet on choosing 'About' in popup menu"""
        logging.debug("on_click_about")

        About = gtk.AboutDialog()
        About.set_icon(self.logo_pixbuf)
        About.set_logo(self.logo_pixbuf)
        About.set_version(pglobals.version)
        About.set_name(name)
        About.set_license(license)
        About.set_authors(authors)
        About.set_comments(comment)
        About.set_website(website)
        About.set_website_label(website_label)
        About.set_copyright(copyright)
        About.run()
        About.destroy()

    def on_button_press (self, widget, event):
        """If it is a left click, switch the Infrared Remote on/off"""
        logging.debug("on_button_press")

        if event.button == 1:
            self.toggle_on_off()

    def toggle_on_off (self):
        """Switch the Infrared Remote on/off"""
        if len(self.pipes) == 0:
            logging.debug("toggle ON")
            if self.use_irexec:
                pipe = subprocess.Popen(['irexec'])
                self.pipes.append(pipe);

            if self.use_irxevent:
                pipe = subprocess.Popen(['irxevent'])
                self.pipes.append(pipe);
        else:
            logging.debug("toggle OFF")
            for pipe in self.pipes:
                self.kill_pipe(pipe)

            del self.pipes[0:len(self.pipes)]

        print self.pipes

        self.update_image()

    def update_image (self):
        """Update the applet's image"""
        logging.debug("update_image")

        size = self.applet.get_size() - 2
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.get_image_filename(), size, size)
        image = gtk.Image()
        image.set_from_pixbuf(pixbuf)

        self.applet.remove(self.applet.get_children()[0])
        self.applet.add(image)
        self.applet.show_all()

    def get_image_filename (self, default = False):
        """Get the image filename based on the current state"""

        if default or len(self.pipes) > 0:
            logging.debug("get_image_filename ON")
            image_filename = "IR_Switcher_on_48.png"
        else:
            logging.debug("get_image_filename OFF")
            image_filename = "IR_Switcher_off_48.png"

        return os.path.join(pglobals.image_dir, image_filename)

    def set_popup_prop (self, check, uncheck):
        """Set the state from the properties in check and uncheck"""
        logging.debug("set_popup_prop")

        popup = self.applet.get_popup_component()

        for verb in check:
            popup.set_prop("/commands/" + verb, "state", "1")
        for verb in uncheck:
            popup.set_prop("/commands/" + verb, "state", "0")

    def get_popup_prop (self, verb):
        """Get the state from a property"""
        logging.debug("get_popup_prop")

        popup = self.applet.get_popup_component()

        return popup.get_prop("/commands/" + verb, "state")

    def load_prefs_data(self):
        """Load the preferences from the GConf Client """
        logging.debug("load_prefs_data")

        self.use_irexec = self.client.get_bool(self.prefs_key + "/use_irexec")
        self.use_irxevent = self.client.get_bool(self.prefs_key + "/use_irxevent")

        if (self.use_irexec and self.use_irxevent) or (not self.use_irexec and not self.use_irxevent):
            self.set_popup_prop(["both"], ["irexec", "irxevent"])
            self.use_irexec = True
            self.use_irxevent = True
        elif self.use_irexec:
            self.set_popup_prop(["irexec"], ["irxevent", "both"])
        elif self.use_irxevent:
            self.set_popup_prop(["irxevent"], ["irexec", "both"])

    def store_prefs_data(self):
        """Store the preferences in the GConf Client"""
        logging.debug("store_prefs_data")

        self.client.set_bool(self.prefs_key + "/use_irexec", self.use_irexec)
        self.client.set_bool(self.prefs_key + "/use_irxevent", self.use_irxevent)

    def kill_pipe (self, pipe):
        """Kill a Pipe process"""
        logging.debug("kill pipe %s" % pipe.pid)

        try:
            pipe.kill()
            pipe.wait()
        except AttributeError:
            # if we use python 2.5
            from signal import SIGKILL
            from os import kill, waitpid
            kill(pipe.pid, SIGKILL)
            waitpid(pipe.pid, 0)

def applet_factory (applet, iid):
    """Start the applet"""
    IR_Switcher_Applet(applet, iid)
    return gtk.TRUE

def main(args):
    """Main function"""
    gobject.type_register(IR_Switcher_Applet)

    # debug mode should open a window instead of the applet itself
    if len(sys.argv) > 1 and sys.argv[1] == '--window':
        mainWindow = gtk.Window()
        mainWindow.set_title('Applet window')
        mainWindow.connect('destroy', gtk.main_quit)
        applet = gnomeapplet.Applet()
        applet_factory(applet, None)
        applet.reparent(mainWindow)
        mainWindow.show_all()
        gtk.main()
        sys.exit()
    else:
        gnomeapplet.bonobo_factory("OAFIID:IR_Switcher_Factory",
                                    IR_Switcher_Applet.__gtype__,
                                    "hello", "0", applet_factory)

if __name__ == '__main__':
    main(sys.argv)

# EOF

