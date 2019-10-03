#!/usr/bin/env python3
# NANdroid App Restorer
# Crude hack to extract apps and data from NAndroid backup archives and injecting them into Android device

import sys
import os
import subprocess
import errno
import dialog
import argparse
import io
import re
import shutil

encoding = 'utf-8'
no_cult_env = {"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
#retVal = 0
dlgwidth = 60
dlgheight= 20
err_to_ignore = [ "tar: Malformed extended header: missing equal sign", "tar: Removing leading `/' from member names", "tar: Exiting with failure status due to previous errors" ]

try:
    (cols, lins) = os.get_terminal_size()
    dlgwidth=int(cols*4/5)
    dlgheight=int(lins*4/5)
except: pass

def die(code, msg):
    sys.stderr.write(msg)
    exit(code)
        
def adb_cmd_to_string(adbmode, remotecmd):
    #fd = os.popen("adb", cmd=remotecmd, mode='r')
    sp = subprocess.Popen(["adb", adbmode, remotecmd], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    status = 0
    ret = err = b''
    try:
        ret, err = sp.communicate(timeout=12)
        status = sp.wait()
        #if status != 0:
        #    if (not ignore_error) or 
        #        raise Exception("Failed to read adb shell output - %d: %s"%(status,err))
        #if err:
        #    FIXME: don't care for now
    except subprocess.TimeoutExpired:
        err += b'Command TIMEOUT'
        status = 7
    except Exception as ex:
        err += "Other error" #: %s" % ex.args; 
    return str(ret or b'', encoding), str(err or b'', encoding), status

def adb_read_strings(remotecmd):
    return adb_cmd_to_string("shell", remotecmd)

parser = argparse.ArgumentParser()
# nope, $HOME should be available or user can specify it... wd_default = (os.environ.get("HOME") or "/var/tmp") +"/.cache/nanares";
wd_default = ""
try:
    wd_default = os.environ["HOME"]+"/.cache/nanares";
except:
    die(1, "Error: $HOME not set, use --wd to set work directory")
parser.add_argument('--wd', help="Work directory, default: " + wd_default, default = wd_default)
parser.add_argument('--tmp', help="If specified, take this as folder with extracted data and ignore --wd")
parser.add_argument('src', nargs='?', help="Source directory containing a single TWRP backup set")
args = parser.parse_args()

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
        if 'ok' != dlg.yesno("Contents found in " + tmp_dir + ", use that data? Selecting No means wiping this directory!"):
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
    ok = dlg.yesno("Source not specified, fetch from device?")
    if ok == 'ok':
        ret, err, status = adb_read_strings("echo /storage/*/TWRP/BACKUPS/*/* /storage/emulated/0/TWRP/BACKUPS/*/*")
        budirs = list(filter(lambda arg: not "*" in arg, ret.split(' ')))
        dlg_items = map(lambda dir: re.sub(r'.*/', '', dir, dir), budirs)
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

def cut_quoted_arg_1(s): return s.split("'")[1]

for (x,y,z) in os.walk(tmp_dir + "/data/app"):
    #print("DIRSTUFF:", z)
    for a in z:
        if a != "base.apk": continue
        apkpath=x + "/" + a
        name=''
        pkg=''
        tp = subprocess.Popen(["aapt", "dump", "badging", apkpath], stdout=subprocess.PIPE, universal_newlines=True, encoding=encoding)
        for line in tp.stdout:
            if line.startswith("application-label:"): name=cut_quoted_arg_1(line)
            if line.startswith("package:"): pkg=cut_quoted_arg_1(line)
            if name and pkg: break
        print(f'OK: {pkg} ; {name} ; {apkpath}')
        apps[pkg]=(name, apkpath) #{"name": name, "apkpath": apkpath}

if not apps: die(21, "Failed to find any valid apps in " + tmp_dir)
key_apps_data = "APPS+DATA"
key_apps="APPS"
key_data="DATA"
choices = [ (key_apps_data, "Inject apps and data"), (key_apps, "Install only APKs"), (key_data, "Install only data")]

while(True):
    choice, resmode = dlg.menu("Please select operation mode, app selection will follow", choices = choices)
    #print(choice)
    if choice != 'ok': exit(0)

    ansage = {
        key_apps_data: "Please select applications to restore. The extracted data will be injected too, overriding any data if present.",
        key_apps: "Please select apps to restore. No data will be installed, this can be done later.",
        key_data: "Please select data to restore. App must already be installed on the phone!"
        }

    appchoices = []
    for el in apps: appchoices.append((el, apps[el][0], False)) #"" + appchoices[el][0]
    #list(map(lambda el: (el, el["name"] + " (" + pkg + ")", False), apps))

    print(appchoices)
    ret = dlg.checklist(ansage[resmode], choices = appchoices, width=dlgwidth, height=dlgheight, list_height=dlgheight-2)

    print(ret)
