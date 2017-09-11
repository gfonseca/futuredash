#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
import time
import pipes
import os
import re
import json

ICONS_DIR = "/etc/futuredash/icons/"

class Widget(object):
    def __init__(self, params={}):
        self.params = params

    def render(self, dzen):
        pass

class Date(Widget):
    def render(self, dzen):
        today = datetime.datetime.now()
        t = today.strftime("%a, %d/%m/%Y %H:%M")
        dzen.text(t)

class Vol(Widget):
    def get_range(self):
        return [
            (0, ICONS_DIR+"volm.xbm"),
            (25, ICONS_DIR+"vol0.xbm"),
            (55, ICONS_DIR+"vol1.xbm"),
            (85, ICONS_DIR+"vol2.xbm"),
            (100, ICONS_DIR+"vol3.xbm")
        ]

    def render(self, dzen):
        icons = self.get_range()
        vol, mute = self.get_vol()
        vol_icon = icons[0][1]
        if mute != "off":
            for r,i in icons:
                if vol <= r:
                    vol_icon = i
                    break
            vol = " %d%%" %(vol,)
        else:
            vol = "M"

        dzen.icon(vol_icon)
        dzen.text(str(vol))

    def get_vol(self):
        amixer = os.popen("amixer sget Master").read()
        m = re.compile('\[(\d+)\%]\s*\[(\w+)\]').search(amixer)
        return int(m.group(1)), m.group(2)

class Battery(Widget):
    def get_range(self):
        return [
            (20, ICONS_DIR+"battery0.xbm"),
            (55, ICONS_DIR+"battery1.xbm"),
            (75, ICONS_DIR+"battery2.xbm"),
            (100, ICONS_DIR+"battery3.xbm")
        ]

    def render(self, dzen):
        icons = self.get_range()
        bat = self.get_battery()
        bat_icon = icons[0][1]
        for r, i in icons:
            if bat <= r:
                bat_icon = i
                break

        dzen.icon(bat_icon)
        dzen.text(" %d%%" % (bat,))

    def get_battery(self):
        amixer = os.popen("upower -i /org/freedesktop/UPower/devices/battery_BAT0").read()
        m = re.compile('percentage:\s*(\d+)%').search(amixer)
        return int(m.group(1))

class I3Workspaces(Widget):
    def get_workspaces(self):
        ws = os.popen("i3-msg -t get_workspaces").read()
        try:
            json_works = json.loads(ws)
        except Exception as e:
            json_works = []

        return json_works

    def render(self, dzen):
        selected =  "#4f447e"
        unselected = "#251925"
        out = []
        com = "^p(+5)^ca(1, i3-msg workspace {num})^bg({bg})^fg(#b4ff00) {name} ^ca()^bg({unselected})"
        work_spaces = self.get_workspaces()
        for i in sorted(work_spaces, key=lambda k: k["num"]):
            i['bg'] = selected if i["focused"] else unselected
            i['unselected'] = unselected
            out.append(com.format(**i))

        dzen.text(" ".join(out))


    def get_ip(self, iface):
        ifcon = os.popen("ifconfig %s" % iface,).read()
        m = re.compile('inet\s([0-9\.]*)').search(ifcon)
        return m.group(1)

class Network(Widget):
    def get_default(self):
        default = os.popen("route | grep '^default' | grep -o '[^ ]*$'").read()
        return default

    def render(self, dzen):
        defaults = self.get_default().strip("\n")
        ip = self.get_ip(defaults)
        dzen.icon(ICONS_DIR+"cable.xbm")
        dzen.text(" %s: %s" % (defaults, ip))

    def get_ip(self, iface):
        ifcon = os.popen("ifconfig %s" % iface,).read()
        m = re.compile('inet\s([0-9\.]*)').search(ifcon)
        return m.group(1)

class Wifi(Widget):
    def get_range(self):
        return [
            (20, ICONS_DIR+"net0.xbm"),
            (55, ICONS_DIR+"net1.xbm"),
            (75, ICONS_DIR+"net2.xbm"),
            (100, ICONS_DIR+"net3.xbm")
        ]

    def render(self, dzen):
        icons = self.get_range()
        ssid = self.get_ssid()

        if not ssid:
            return

        level = self.get_level(ssid)
        nt_icon = icons[0][1]
        for r, i in icons:
            if level <= r:
                nt_icon = i
                break

        dzen.icon(nt_icon)
        dzen.text(" %s" % (ssid))

    def calc_three(self, n):
        return (100 * n) / -70

    def get_level(self, ssid):
        f = list(file("/proc/net/wireless"))[2].replace("  ", " ").split(" ")
        f = f[4].strip(".")
        return self.calc_three(int(f))

    def get_ssid(self):
        iwget = os.popen("iwgetid").read()
        m = re.compile('\"([^\"]+)\"').search(iwget)

        if not m:
            return None

        return m.group(1)



class Dzen2(object):
    def __init__(self, dzen_params=None):

        self.dzen_params = {
            "bg": "#000000",
            "fg": "#ffffff",
            "alignment": "r",
            "font": "-*-terminus-medium-r-*-*-9-*-*-*-*-*-iso10646-*",
            "height": "12"
        }

        if(dzen_params):
            self.dzen_params = dict(self.dzen_params.items() + dzen_params.items())

        self.pipe = pipes.Template()
        self.pipe.append('dzen2 -p -h {height} -ta {alignment} -fg \'{fg}\' -bg \'{bg}\' -fn {font} -dock'.format(**self.dzen_params), "--")
        self.f = self.pipe.open("pipefiles", "w")

        self.output = ""

    def clear(self):
        self.output = ""
        return self

    def bar(self):
        self.output += " ^i(%sbar.xbm) " % (ICONS_DIR,)
        return self

    def icon(self, path):
        self.output += "^i(%s)" % (path,)
        return self

    def text(self, text):
        self.output += text
        return self

    def bg_color(self, color):
        self.output += "^bg(%s)" % (color,)
        return self

    def fg_color(self, color):
        self.output += "^fg(%s)" % (color,)
        return self

    def position_right(self):
        self.output += "^p(_RIGHT)^p(-220)"
        return self
    def position(self, pos):
        self.output += "^p(%s)" % (pos,)
        return self

    def send(self):
        print self.output
        self.f.write("%s\n" % self.output,)

    def set_widget(self, w):
        w.render(self)
        return self
