#!/usr/bin/env python3
# NANdroid App Restorer
# Crude hack to extract apps and data from NAndroid backup archives and injecting them into Android device

import sys
import os
import errno
import dialog
import argparse

class tDlgAction:
    EXIT = 1  # just exit asap with retVal code
    ASK_GO = 2, # confirm and start data pushing
    FIRST = 3 # calculate the initial conditions
    ERROR = 4
    ERROR_FATAL = 5
    MAIN_MENU = 6
    DEV_FETCH = 7
    TEST = 42

class UI:
    state = tDlgAction.FIRST
    askString = "Got milk?"
    retVal = 0
    dlg = dialog.Dialog()
        
    def opt_set_error(self, optVal, optMsg):
        if self.retVal == 0:
            self.retVal = optVal
        if optMsg:
            self.askString = optMsg
        
    def switch_screen(self):
        if self.state == tDlgAction.EXIT:
            exit(self.retVal)
        if self.state == tDlgAction.FIRST:
            # print(self.args.wd)
            try:
                os.makedirs(self.args.wd)
            except OSError as exc:
                if exc.errno == errno.EEXIST and os.path.isdir(self.args.wd):
                    pass
                else:
                    #print("Cannot create work directory: ", sys.exc_info()[0])
                    opt_set_error(1, "Cannot create work directory: " + sys.exc_info()[0]);
                    exit(1)
            if not self.args.src:
                ok = self.dlg.yesno("Source not specified, fetch from device?")
                if ok == 'ok':
                    return tDlgAction.DEV_FETCH
                else:
                    return tDlgAction.EXIT
            return tDlgAction.MAIN_MENU
        if self.state == tDlgAction.ERROR:
            return tDlgAction.EXIT
        if self.state == tDlgAction.ERROR_FATAL:
            self.dlg.msgbox(self.askString, height=17, width=72)
            self.opt_set_error(42)
            return tDlgAction.EXIT
        if self.state == tDlgAction.TEST:
            self.dlg.msgbox("oh my god", height=17, width=72)
        if self.state == tDlgAction.DEV_FETCH:
            self.askString = "Fetching from device not implemented yet, please pull manually"
            return tDlgAction.ERROR_FATAL
        self.dlg.msgbox("FATAL: unknown dialog %d" % self.state, height=17, width=72)
        return tDlgAction.EXIT
    
    def act(self):
        while(True):
            self.state = self.switch_screen()
            
    def __init__(self):
        parser = argparse.ArgumentParser()
        # nope, $HOME should be available or user can specify it... wd_default = (os.environ.get("HOME") or "/var/tmp") +"/.cache/nanares";
        wd_default = ""
        try:
            wd_default = os.environ["HOME"]+"/.cache/nanares";
        except:
            self.askString = "Error: $HOME not set, use --wd to set work directory"
            self.state = tDlgAction.ERROR_FATAL
        parser.add_argument('--wd', help="Work directory, default: " + wd_default, default = wd_default)
        parser.add_argument('src', nargs='?' )
        self.args = parser.parse_args()
        # print("h2h: %d" % self.state)

UI().act()
