# Copyright (C) 2008 Valmantas Paliksa <walmis at balticum-tv dot lt>
# Copyright (C) 2008 Tadas Dailyda <tadas at dailyda dot com>
#
# Licensed under the GNU General Public License Version 3
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 
from blueman.Functions import *
from blueman.Functions import _
from blueman.plugins.AppletPlugin import AppletPlugin
from blueman.bluez.Device import Device
from subprocess import Popen

import dbus
from blueman.main.SignalTracker import SignalTracker

class PulseAudio(AppletPlugin):
	__author__ = "Walmis"
	__description__ = _("Automatically loads pulseaudio bluetooth module after audio device is connected.\n<b>Note:</b> Requires pulseaudio 0.9.14 or higher")
	__icon__ = "audio-card"
	__autoload__ = False

	def on_load(self, applet):
		self.signals = SignalTracker()
		self.bus = dbus.SystemBus()
		
		self.signals.Handle("dbus", self.bus, self.on_a2pd_prop_change, "PropertyChanged", "org.bluez.AudioSink", path_keyword="device")
		self.signals.Handle("dbus", self.bus, self.on_hsp_prop_change, "PropertyChanged", "org.bluez.Headset", path_keyword="device")
		
	def on_unload(self):
		self.signals.DisconnectAll()
		
	def on_a2pd_prop_change(self, key, value, device):
		if key == "Connected" and value:
			self.setup_pa(device, "a2dp")
		
	def on_hsp_prop_change(self, key, value, device):
		if key == "Connected" and value:
			self.setup_pa(device, "hsp")
		
	def setup_pa(self, device_path, profile):
		device = Device(device_path)
		props = device.GetProperties()
		
		cmd = ["pactl", "load-module", "module-bluetooth-device", "address=%s" % props["Address"], "profile=%s" % profile]
		
		dprint("Loading pulseaudio module\nexec:", " ".join(cmd))
		def child_closed(pid, cond):
			dprint("Spawn result", cond)
			if cond != 0:
				dprint("Failed to load pulseaudio module")
			else:
				dprint("Pulseaudio module loaded successfully")

		p = Popen(cmd)
		gobject.child_watch_add(p.pid, child_closed)