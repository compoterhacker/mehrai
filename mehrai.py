#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time, sys, string, json, random
import urllib, urllib2, hashlib, os
import itertools, mimetools, mimetypes
import utils
import netlinks
import argh
from argh.decorators import arg
from watchdog.observers import Observer  
from watchdog.events import PatternMatchingEventHandler

# Kicks shit dropped by skids on yr honeypots over to yr Viper/Snakepit instance

class FileHandler(PatternMatchingEventHandler):

    def process(self, event):

        if event.is_directory is False and os.path.exists(event.src_path) and os.path.basename(event.src_path).startswith('.') is False and os.path.getsize(event.src_path) != 0:
            rand = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))
            os.system("cp " + event.src_path + " /tmp/" + os.path.basename(event.src_path + '.' + rand))
            sha256 = utils.get_sha256(event.src_path)
            print '[!] Sending ' + event.src_path + '.' + rand + ' to Viper\n[!] sha256: ' + sha256
            utils.upload("/tmp/" + os.path.basename(event.src_path + '.' + rand))


    def on_modified(self, event):
        self.process(event)


    def on_created(self, event):
        self.process(event)


@arg('dockerid', help='the untruncated dockerid for the container')
@arg('--recurse', help='recursively monitor the filesystem. WARNING! NOISEY!')
@arg('--monitor', help='monitor mode: not killing the procs, but just monitoring. pcap time.')
def run(dockerid, monitor=False, recurse=False):
    print """\n
                _               _ 
 _ __ ___   ___| |__  _ __ __ _(_)
| '_ ` _ \ / _ \ '_ \| '__/ _` | |
| | | | | |  __/ | | | | | (_| | |
|_| |_| |_|\___|_| |_|_|  \__,_|_|
                                                                 
\n"""

    connector = netlinks.NetlinkConnector()
    observer = Observer()
    # this line may need to be changed, dending on yr docker install
    observer.schedule(FileHandler(), path='/var/lib/docker/devicemapper/mnt/' + dockerid + '/rootfs', recursive=recurse)
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
                        os.system('docker exec ' + dockerid + ' telnetd -b 0.0.0.0:23')

                elif event['event'] == 'FORK':
                    print 'FORK (parent: %d, child: %d):' % (event['parent_pid'],
                        event['child_pid'])
                    print ' - parent exe: %s' % (netlinks.pid_to_exe(event['parent_pid']))
                    print ' - parent cmdline: %s' % (netlinks.pid_to_cmdline(event['parent_pid']))
                    print '   \_ child exe: %s' % (netlinks.pid_to_exe(event['child_pid']))
                    print '   \_ child cmdline: %s' % (netlinks.pid_to_cmdline(event['child_pid']))
                    if 'deleted' in netlinks.pid_to_exe(event['child_pid']) and monitor is False:
                        childpid = str(event['child_pid'])
                        print '   [!] killing %s' % childpid
                        rand = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))
                        os.system('cp /proc/' + childpid + '/exe /tmp/exe.' + rand)
                        utils.upload('/tmp/exe.' + rand)
                        time.sleep(1)
                        os.system('kill -9 ' + childpid)
                        os.system('docker exec ' + dockerid + ' telnetd -b 0.0.0.0:23')

                elif event['event'] == 'EXIT':
                    print 'EXIT (%d):' % (event['process_pid'])
                    print ' - process tgid: %s' % (event['process_tgid'])
                    print ' - process exit code %s' % (event['exit_code'])
                    print ' - process signal %s' % (event['exit_signal'])
                    if event['process_pid'] == telnet:
                        print '    [!] respawning telnetd'
                        os.system('docker exec ' + dockerid + ' telnetd -b 0.0.0.0:23')
                        telnet = utils.getTelnetPid

            print ''

    except KeyboardInterrupt:
        observer.stop()

    observer.join()

if __name__ == "__main__":
    argh.dispatch_commands([run])
