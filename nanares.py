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

class UI:
    state = tDlgAction.FIRST
    askString = "Got milk?"
    retVal = 0
        
    def opt_set_error(self, optVal):
        if self.retVal != 0:
            return 
        self.retVal = optVal
        
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
                    print("Cannot create work directory: ", sys.exc_info()[0])
                    exit1(1)
            
            return tDlgAction.MAIN_MENU
        if self.state == tDlgAction.ERROR or self.state == tDlgAction.ERROR_FATAL:
            print(self.askString)
            if self.state == tDlgAction.ERROR_FATAL:
                self.opt_set_error(42)
                return tDlgAction.EXIT
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
