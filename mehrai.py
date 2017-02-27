#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time, sys, string, json, random
import urllib, urllib2, hashlib, os
import itertools, mimetools, mimetypes, subprocess
import utils
import netlinks
import argh
import pipes
from argh.decorators import arg
from watchdog.observers import Observer  
from watchdog.events import PatternMatchingEventHandler

# Kicks shit dropped by skids on yr honeypots over to yr Viper/Snakepit instance

class FileHandler(PatternMatchingEventHandler):

    def process(self, event):
        #wordchars += '@{}~-./*?=$:+^'
        fileName = os.path.basename(event.src_path)


        if event.is_directory is False and os.path.exists(event.src_path) and os.path.basename(event.src_path).startswith('.') is False and os.path.getsize(event.src_path) != 0:
            rand = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))
            cmd = ["cp", event.src_path, "/tmp/" + fileName + '.' + rand]
            args = utils.args_to_string(cmd)
            p = subprocess.check_output(cmd, shell=False)
            sha256 = utils.get_sha256('/tmp/' + fileName + '.' + rand)
            print '[!] Sending ' + event.src_path + '.' + rand + ' to Viper\n[!] sha256: ' + sha256
            utils.upload('/tmp/' + fileName + '.' + rand)


    def on_modified(self, event):
        self.process(event)


    def on_created(self, event):
        self.process(event)


@arg('dockerid', help='the untruncated dockerid for the container')
@arg('--recurse', help='recursively monitor the filesystem. WARNING! NOISEY!')
@arg('--monitor', help='monitor mode: not killing the procs, but just monitoring. pcap time.')
@arg('--overlayfs', help='changes default storage device from devicemapper to overlay2 (requires special lookup process')

def map_overlayfs(overlayid):
    fsid = open('/var/lib/docker/image/overlay2/layerdb/mounts/'+overlayid+'/mount-id','r').read()
    fspath = '/var/lib/docker/overlay2/'+fsid+'/diff'
    return fspath

def run(dockerid, monitor=False, recurse=False, overlayfs=False):
    print """\n
                _               _ 
 _ __ ___   ___| |__  _ __ __ _(_)
| '_ ` _ \ / _ \ '_ \| '__/ _` | |
| | | | | |  __/ | | | | | (_| | |
|_| |_| |_|\___|_| |_|_|  \__,_|_|
                                                                 
\n"""

    # default devicemapper
    # this line may need to be changed, dending on yr docker install
    fspath='/var/lib/docker/devicemapper/' + dockerid + '/diff'

    if overlayfs:
        fspath=map_overlayfs(dockerid)

    connector = netlinks.NetlinkConnector()
    observer = Observer()
    observer.schedule(FileHandler(), path=fspath, recursive=recurse)
    observer.start()

    telnet = utils.getTelnetPid

    try:
        while True:
            events = connector.recv()
            for event in events:
                print event

                if event['event'] == 'EXEC':
                    print 'EXEC (%d):' % (event['process_pid'])
                    print ' - process exe: %s' % (netlinks.pid_to_exe(event['process_pid']))
                    print ' - process cmdline: %s' % (netlinks.pid_to_cmdline(event['process_pid']))
                    if 'kill' and 'telnetd' in netlinks.pid_to_cmdline(event['process_pid']):
                        print '    [!] respawning telnetd'
                        cmd = ['docker', 'exec', dockerid, 'telnetd', '-b', '0.0.0.0:23']
                        args = utils.args_to_string(cmd)
                        telnet = subprocess.check_output(args, shell=False)

                elif event['event'] == 'FORK':
                    print 'FORK (parent: %d, child: %d):' % (event['parent_pid'], event['child_pid'])
                    print ' - parent exe: %s' % (netlinks.pid_to_exe(event['parent_pid']))
                    print ' - parent cmdline: %s' % (netlinks.pid_to_cmdline(event['parent_pid']))
                    print '   \_ child exe: %s' % (netlinks.pid_to_exe(event['child_pid']))
                    print '   \_ child cmdline: %s' % (netlinks.pid_to_cmdline(event['child_pid']))
                    if 'deleted' in netlinks.pid_to_exe(event['child_pid']) and monitor is False:
                        childpid = str(event['child_pid'])
                        print '   [!] killing %s' % childpid
                        rand = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))
                        path = '/proc/%s/exe' % childpid
                        tmp = '/tmp/exe.%s' % rand
                        cmd = ['cp', path, tmp]
                        #args = utils.args_to_string(cmd)
                        cp = subprocess.check_output(cmd, shell=False)
                        utils.upload('/tmp/exe.' + rand)
                        cmd = ['kill', '-9', childpid]
                        #args = utils.args_to_string(cmd)
                        proc = subprocess.check_output(cmd, shell=False)
                        cmd = ['docker', 'exec', dockerid, 'telnetd', '-b', '0.0.0.0:23']
                        args = utils.args_to_string(cmd)
                        telnet = subprocess.check_output(cmd, shell=False)

                elif event['event'] == 'EXIT':
                    print 'EXIT (%d):' % (event['process_pid'])
                    print ' - process tgid: %s' % (event['process_tgid'])
                    print ' - process exit code %s' % (event['exit_code'])
                    print ' - process signal %s' % (event['exit_signal'])
                    if event['process_pid'] == telnet:
                        print '    [!] respawning telnetd'
                        cmd = ['docker', 'exec', dockerid, 'telnetd', '-b', '0.0.0.0:23']
                        args = utils.args_to_strings(cmd)
                        proc = subprocess.check_output(cmd, shell=False)
                        telnet = utils.getTelnetPid

            print ''

    except KeyboardInterrupt:
        observer.stop()

    observer.join()

if __name__ == "__main__":
    argh.dispatch_commands([run])


