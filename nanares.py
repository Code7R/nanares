#!/usr/bin/env python3
# NANdroid App Restorer
# Crude hack to extract apps and data from NAndroid backup archives and injecting them into Android device

import sys
import os
import subprocess
from subprocess import Popen, DEVNULL, PIPE
import errno
import dialog
from dialog import Dialog
import argparse
import io
import re
import shutil
import ast

#tp = subprocess.Popen(["/tmp/langsam.sh"], stdout=subprocess.PIPE, universal_newlines=True, encoding='utf-8')#
#for line in tp.stdout:
#    print(line)
#exit(1)

encoding = 'utf-8'
no_cult_env = {"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
#retVal = 0
dlgwidth = 60
dlgheight= 20
err_to_ignore = [ "tar: Malformed extended header: missing equal sign", "tar: Removing leading `/' from member names", "tar: Exiting with failure status due to previous errors" ]

def die(code, msg):
    sys.stderr.write(msg)
    exit(code)
        
#def adb_cmd_to_string(adbmode, remotecmd):
#    #fd = os.popen("adb", cmd=remotecmd, mode='r')
#    sp = subprocess.Popen(["adb", adbmode, remotecmd], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#    status = 0
#    ret = err = b''
#    try:
#        ret, err = sp.communicate(timeout=12)
#        status = sp.wait()
#        #if status != 0:
#        #    if (not ignore_error) or 
#        #        raise Exception("Failed to read adb shell output - %d: %s"%(status,err))
#        #if err:
#        #    FIXME: don't care for now
#    except subprocess.TimeoutExpired:
 #       err += b'Command TIMEOUT'
 #       status = 7
#    except Exception as ex:
#        err += "Other error" #: %s" % ex.args; 
#    return str(ret or b'', encoding), str(err or b'', encoding), status
#
#def adb_read_strings(remotecmd):
#    return adb_cmd_to_string("shell", remotecmd)

parser = argparse.ArgumentParser()
# nope, $HOME should be available or user can specify it... wd_default = (os.environ.get("HOME") or "/var/tmp") +"/.cache/nanares";
wd_default = ""
try:
    wd_default = os.environ["HOME"]+"/.cache/nanares";
except:
    die(1, "Error: $HOME not set, use --wd to set work directory")
parser.add_argument('--wd', help="Work directory, default: " + wd_default, default = wd_default)
parser.add_argument('--tmp', help="If specified, take this as folder with extracted data and ignore --wd")
parser.add_argument('--nodlg', action='store_true', help="No dialog interaction, scan only")
parser.add_argument('src', nargs='?', help="Source directory containing a single TWRP backup set")
args = parser.parse_args()

try:
    (cols, lins) = os.get_terminal_size()
    dlgwidth=int(cols*4/5)
    dlgheight=int(lins*4/5)
except: args.nodlg = True

dlg = dialog.Dialog()
tmp_dir = os.path.join(args.wd, "tmp")
if(args.tmp): tmp_dir = args.tmp
dl_dir = os.path.join(args.wd, "dl")
tmp_stuff = []

try: tmp_stuff = os.listdir(tmp_dir)
except: pass

if args.tmp:
    if not tmp_stuff: die(20, "Unpacked data folder specified but no data found in " + args.tmp)
else:
    if tmp_stuff:
        if dialog.Dialog.OK != dlg.yesno("Contents found in " + tmp_dir + ", use that data? Selecting No means wiping this directory!"):
            shutil.rmtree(tmp_dir, onerror=lambda err: die(11, "Failed to remove tmp directory"))
            tmp_stuff = False

for subdir in [tmp_dir, dl_dir]:
    try:
        os.makedirs(subdir)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(args.wd):
            pass
        else:
            print("Cannot create work directory: ", sys.exc_info()[0])
            exit(2)

src_dir=args.src
if not args.src:
    ok = dlg.yesno("Source not specified, fetch TWRP data from device?")
    if ok == dialog.Dialog.OK:
        remotecmd = "echo /storage/*/TWRP/BACKUPS/*/* /storage/emulated/0/TWRP/BACKUPS/*/*"
        #ret, err, status = adb_read_strings()
        p = subprocess.Popen(["adb", "shell", remotecmd], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, encoding=encoding)
        res = p.stdout.readline().split(' ')
        budirs = list(filter(lambda arg: arg.find('*') < 0, res))
        dlg_items = map(lambda dir: (re.sub(r'.*/', '', dir), dir), budirs)
        #print(budirs, dlg_items)
        button, item = dlg.menu("Please select the source from remote TWRP backup folders", width = dlgwidth, choices = dlg_items)
        if button != 'ok': exit (0)
        remote_dir = next(filter(lambda arg: arg.endswith(item), budirs))
        src_dir = os.path.join(dl_dir, item)
        print("Selected: '" + remote_dir + "', download to " + src_dir)
        os.chdir(dl_dir)
        status = os.system("adb pull " + remote_dir)
        if status != 0:
            print("Error downloading NANdroid backup, exiting...")
            exit(4)
    else:
        exit(3);

os.chdir(tmp_dir)

if not tmp_stuff:
    print("Unpacking data from " + src_dir + " to " + tmp_dir)
    tarballs = list(filter(lambda s: re.match(r'data.*win\d*$', s), os.listdir(src_dir)))
    print("Relevant tarballs: ", tarballs)
    for x in tarballs:
        print(x, "...")
        # we could use https://github.com/arifogel/twrpabx but tar is good enough for apps&data
        tp = subprocess.Popen(["tar", "-xf", os.path.join(src_dir, x)], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,stderr=subprocess.PIPE, env = no_cult_env)
        ret, err = tp.communicate()
        status = tp.wait()
        serr = err.decode(encoding)
        if status == 2:
            tar_fil = serr
            for s in err_to_ignore: tar_fil = str.replace(tar_fil, s, "")
            if(len(serr) > 0 and "" == str.strip(tar_fil)):
                print("GNU tar warnings ignored")
                status = 0
        if status != 0:
            die(17, "tar command failed, " + serr)

apps={}

def cut_arg_1(s, delimiter="'"):
    tokens=s.strip().split(delimiter)
    if len(tokens) > 1:
        return tokens[1]
    return []

for (x,y,z) in os.walk(os.path.join(tmp_dir, "data", "app")):
    #print("DIRSTUFF:", z)
    for a in z:
        if a != "base.apk": continue
        apkpath=x + "/" + a
        name=''
        pkg=''
        tp = subprocess.Popen(["aapt", "dump", "badging", apkpath], stdout=subprocess.PIPE, universal_newlines=True, encoding=encoding)
        for line in tp.stdout:
            if line.startswith("application-label:"): name=cut_arg_1(line)
            if line.startswith("package:"): pkg=cut_arg_1(line)
            if name and pkg: break
        print(f'OK: {pkg} ; {name} ; {apkpath}')
        apps[pkg]={"name": name, "apkpath": apkpath, 'sel': False}

if not apps: die(21, "Failed to find any valid apps in " + tmp_dir)
#key_apps_data = "APPS+DATA"
key_apps="APPS"
key_data="DATA"
key_apps_data="APPS+DATA"
key_uninstall="DEINST"
key_sel="SELECT_APPS"
key_sel_all="SELECT_ALL"
key_sel_none="CLEAR_SELECTION"
key_sel_auto="AUTO_SEL"
key_sel_load="LOAD_SELECTION"

choices_main = [
    (key_sel, "Select apps"),
    (key_sel_all, "Check everything"),
    (key_sel_none, "Uncheck everything"),
    (key_sel_auto, "Check all but not installed ones"),
    ("===", "========"),
    (key_apps_data, "Install apps and data"),
    (key_apps, "Install APKs"),
    (key_data, "Install app data"),
    (key_uninstall, "Uninstall selected apps if possible"),
    ("~~~", "~~~~~~~~"),
    (key_sel_load, "Load previous selection from a previous run in the same workdir")
    ]

key_opt_default = "DEFAULT"
key_opt_reinst = "REINSTALL_SAME"

choices_options = [
    (key_opt_default, "Attempt apk installation, then data, on failure: back off", True),
    (key_opt_reinst, "Try apk reinstallation", True)
    ]

sel_ser_file = os.path.join(args.wd, 'selection.py')

def store_selection(sel):
    with open(sel_ser_file, 'w') as f:f.write(repr(sel))

def apply_selection(sel, inverse):
    global apps
    for el in apps:
        apps[el]['sel'] = (el in sel) != inverse
    store_selection(sel)

def auto_select():
    try:
        p = Popen(["adb", "shell", "pm", "list", "packages"], stdout=PIPE, universal_newlines=True)
        inst_app=[]
        for line in p.stdout:
            print(line)
            arg = cut_arg_1(line, ':')
            if not arg: continue
            inst_app.append(arg)
        apply_selection(inst_app, True)
    except subprocess.CalledProcessError as ex:
        print("ADB failure", ex)
        pass
    
def confirm_start(cnt):
    instructions = f"Please check your phone and make sure that the phone is in offline mode (flight/plane mode) and that all active apps are closed (double check the app list!)" \
f"For some phones, turning off the display/lockscreen timeout is also a good idea. When ready, press OK to start installing {cnt} apps (resp. their data)"
    return dialog.Dialog.OK == dlg.yesno(instructions, width=dlgwidth)

#def selected_appsx():
#    for el in apps:
#        if(apps[el]["sel"]): yield el

def flash_selection(mode):
    selected_apps = filter(lambda el: apps[el]["sel"], apps)
    if mode == key_apps: # or mode == key_apps_data:
        for el in selected_apps:
            print(el) 
    return True

def selected_apps():
    return list(filter(lambda key: apps[key]["sel"], apps))

key_sel_unsuc = "Uncheck_Succeeded"
key_sel_unfail= "Uncheck_Failed"
key_log = "View_Log"
log_path = os.path.join(args.wd, "op.log")
key_reboot = "REBOOT"
key_back = "BACK"

def post_dialog(suc_sel):
    msg = "Congratulations, {0} selected operations succeeded".format(len(suc_sel))
    old_sel = selected_apps()
    if len(suc_sel) != len(old_sel):
        msg = "Some of the selected operations succeeded ({0} of {1})".format(len(suc_sel), len(old_sel))
    # XXX: add finer logics for the cases "no selection" or "all succeeded"
    msg += "\n\nPlease reboot the phone ASAP otherwise the apps might destroy the injected data\n"
    choices = [
        (key_sel_unsuc, "Remove the apps with succeeded operations from the selection"),
        (key_sel_unfail, "Remove the apps behind FAILED operations from selection"),
        (key_log, "View the operations log"),
        (key_reboot, "Reboot phone"),
        (key_back, "Main Menu")
        ]
    while True:
        response, item = dlg.menu(msg, choices = choices, height=dlgheight, width=dlgwidth)
        if response == Dialog.CANCEL or item == "BACK": return
        if item == key_sel_unsuc: # drop the good ones, keep the bad
            for key in suc_sel: apps[key]['sel'] = False
            apply_selection(selected_apps(), False)
        elif item == key_sel_unfail: # keep only the good ones, drop failed
            apply_selection(suc_sel, False)
        elif item == key_log:
            dlg.textbox(log_path, height=dlgheight, width=dlgwidth)
            continue
        elif item == key_reboot:
            subprocess.run(["adb", "reboot"])
        return

def install(inst_apps, inst_data):
    sel_apps = selected_apps()
    if not confirm_start(len(sel_apps)): return
    good = []
    log = open(log_path, 'w')
    dlg.gauge_start("Performing operations", width = dlgwidth)
    prog = -1
    for key in sel_apps:
        prog += 1
        dlg.gauge_update(int(prog*100/len(sel_apps)), key, update_text=True)
        #subprocess.run(["sleep", "1"])
        #continue
        if inst_apps:
            log.write(f"NANARES: Installing {key}:\n")
            p = Popen(["adb", "install", "-r", apps[key]["apkpath"]], stdout=PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            sout, serr = p.communicate()
            log.writelines(sout)
            ok = p.wait() == 0
            if ok and not inst_data: good.append(key)
        if inst_data:
            log.write(f"NANARES: Installing data from {key}:\n")
            p = Popen(["adb", "shell" , f"dumpsys package {key}"], stdout=PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            #sout, serr = p.communicate()
            uid = 0
            for line in p.stdout:
                what = line.strip().split("=")
                if len(what) < 2 or what[0] != "userId": continue
                uid = int(what[1])
                log.write(line)
                break
            if p.wait() != 0: continue
            # have the id, now push data and set attributes
            #p1 = Popen(["tar", "-f-", "-c", "-C", tmp_dir,  "/data/data/"+key ], stdout=PIPE, stderr=DEVNULL)
            #p2 = Popen(["adb", "shell", 'su -c "tar -f- -v -x -C /"'], stdin=p1.stdout, stdout=PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            #p1.stdout.close()
            #sout, serr = p2.communicate()            
            #ok = p2.wait() == 0 and p1.wait() == 0
            #log.writelines(sout)
            xret = ""
            try:
                for push_cmd in [
# pm root commands are failing for unknown reason in the adb call but work in the interactive shell
#                    f'adb shell su -c "pm disable {key}"',
                    f'tar -f- -c -C "{tmp_dir}" data/data/{key} | adb shell su -c "tar -f- -x -C /"',
                    f'adb shell su -c "chown -R {uid}:{uid} /data/data/{key}"',
                    f'adb shell su -c "restorecon -Rv /data/data/{key}"',
#                    f'adb shell su -c "pm enable {key}"',
                    f'adb shell sync'
                    ]:
                    log.write(push_cmd)
                    xret = subprocess.check_output(push_cmd, shell=True, stderr=subprocess.STDOUT);
                    log.write(str(xret, encoding))
            except:
                log.write("FAILED: " + str(xret, encoding))
                continue
            # great, came so far without exceptions of detected failures
            good.append(key)
    log.close()
    dlg.gauge_stop()
    post_dialog(good)

if args.nodlg:
    print("No terminal capabilities, aborting interactive mode")
    exit(11)

while True:
    p = Popen(["adb", "shell", 'su -c "ls /data/data"'], stdout=DEVNULL, stderr=DEVNULL)
    if p.wait() == 0: break
    q = dlg.yesno("Could not execute a root mode command.\n\n"
            + "Please check the phone, make sure that ADB is enabled in Development Settings and that Root manager allows su command for sufficiently long time (like an hour)\n\n"
            + "Check again?",
            width = dlgwidth)
    if Dialog.OK != q: exit(9)

while(True):
    count_all = len(apps)
    count_sel = len(list(filter(lambda el: apps[el]['sel'], apps)))
    choice, resmode = dlg.menu(f"Please select packages and/or what to do with them. Currently selected: {count_sel}/{count_all}", choices = choices_main, height=dlgheight, width=dlgwidth, menu_height=dlgheight-5)
    if choice != dialog.Dialog.OK: exit(0)
    if resmode == key_sel_all:
        apply_selection([], True)
        continue
    if resmode == key_sel_none:
        apply_selection([], False)
        continue
    if resmode == key_sel_auto:
        auto_select()
        continue
    if resmode == key_sel:
        appchoices = []
        def pick_sortkey(key): return apps[key]['name'].lower()
        for el in sorted(apps, key=pick_sortkey) : appchoices.append((el, apps[el]['name'], apps[el]['sel'] or False))
        #list(map(lambda el: (el, el["name"] + " (" + pkg + ")", False), apps))
        #print(appchoices)
        ret_btn, ret_items = dlg.checklist("Apps to act on:", choices = appchoices, width=dlgwidth, height=dlgheight, list_height=dlgheight-2)
        if Dialog.OK == ret_btn: apply_selection(ret_items, False)
    if resmode == key_apps:
        install(True, False)
    if resmode == key_data:
        install(False, True)
    if resmode == key_apps_data:
        install(True, True)
    if resmode == key_sel_load:
        with open(sel_ser_file, 'r') as f: sel = ast.literal_eval(f.read())
        apply_selection(sel, False)
