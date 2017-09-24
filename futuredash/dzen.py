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


class Bar(Widget):
    def __init__(self, size, percent, active="#ECF1F3", inactive="#ADADC7"):
        self.size = size
        self.percent = percent
        self.active_color = active
        self.inactive_color = inactive
        self.active_bars = self.__calc_bar(size, percent)

    def __calc_bar(self, size, percent):
        return (size * percent) / 100

    def make_bar(self):
        bar = " ^fg({active})" 
        bar += "^i({bar_path})" * self.active_bars
        bar += "^fg({inactive})"
        bar += "^i({bar_path})" * (self.size - self.active_bars)
        return bar.format(active=self.active_color, inactive=self.inactive_color, bar_path=ICONS_DIR+"bar.xbm")
   
    def render(self, dzen):
        bar = self.make_bar()
        dzen.text(bar)


class Date(Widget):
    def render(self, dzen):
        today = datetime.datetime.now()
        t = today.strftime("%a, %d/%b %H:%M")
        dzen.icon(ICONS_DIR+"clock.xbm")
        dzen.text(" "+t)



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
        vol_str = ""
        if mute != "off":
            for r,i in icons:
                if vol <= r:
                    vol_icon = i
                    break
            vol_str = " %d%%" %(vol,)
        else:
            vol_str = "M"

        dzen.icon(vol_icon)
	b = Bar(10, int(vol))
        b.render(dzen)

    def get_vol(self):
        amixer = os.popen("amixer sget Master").read()
        vol = re.compile('\[(\d+)\%\]').search(amixer).group(1)
	mute = re.compile('\[(on|off)\]').search(amixer).group(1)
        return int(vol), mute

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
        visible =  ICONS_DIR+"circle.xbm"
        focused =  ICONS_DIR+"circle_dot.xbm"
        none = ICONS_DIR+"dot.xbm"

        out = []
        com = "^p(+5)^ca(1, i3-msg workspace {num}) ^fg(#D8043F) ^i({icon}) ^ca()"
        work_spaces = self.get_workspaces()
        for i in sorted(work_spaces, key=lambda k: k["num"]):
            icon = none

            if i["visible"] and i["focused"]:
                icon = focused

            if not i["focused"] and i["visible"] :
                icon = visible
            i["icon"] = icon

            out.append(com.format(**i))
        dzen.text(" ".join(out))

class Network(Widget):
    def get_default(self):
        default = os.popen("route | grep '^default' | grep -o '[^ ]*$'").read()
        return default

    def render(self, dzen):
        defaults = self.get_default().strip("\n")
        ip = self.get_ip(defaults)
        dzen.icon(ICONS_DIR+"cable.xbm")
        dzen.text(" %s" % (ip,))

    def get_ip(self, iface):
        ifcon = os.popen("ifconfig %s" % iface,).read()
        m = re.compile('inet\s(addr)?:([0-9\.]*)').search(ifcon)
        return m.group(2)

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
            "bg": "#191F27",
            "fg": "#D8043F",
            "icon_color": "#D8043F",
            "alignment": "r",
            "font": "-*-Source\ Code\ Pro-medium-r-*-*-12-*-*-*-*-*-iso10646-*",
            "height": "20"
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
        self.output += "^fg(%s)^i(%s)^fg()" % (self.dzen_params["icon_color"], path,)
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
