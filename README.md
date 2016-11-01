# Version 2
Much less janky, more robust(not just targeting mirai's, but mirai centric) and utilizes the kernels netlink API to monitor procs in a much smoother fashion. Now, DONE.

This version is almost completely different. The new approach is taking advantage of the linux kernels Netlink API, thanks to help from homie justin barrick, to get the juarez pumpin. It will catch and print events(EXEC, FORK, EXIT are the main ones we're looking at, and PTRACE, COREDUMP, COMM, SID, GID and UID) and parse them. We catch the typical Mirai behavior and more if you want to put it in monitor mode(not kill the procs). If so, I suggest getting some pcaps.

The files are both picked off from docker's rootfs and /proc/pid/exe, except on the host this time, not in the container. A much more sane approach. They're collected in /tmp and still it's assuming you're using the Viper API(set the URL in utils.py). This is all host based, so you don't even need to enter the container if you don't want to.

To use this version:
```
# docker build -t honeypots/mehrai .
# docker run -it --rm -p 23:23 honeypots/mehrai /bin/sh
/ # telnetd -b 0.0.0.0:23 
```
And then from your host:
```
# python mehrai.py run $(docker ps -l --no-trunc) [--recurse, --monitor]
```
Note: Depending on the version of Docker, you may get a Path status error. In which case, you will have to change the path in mehra.py to the correct one for your install :)
```
 - process exe:
 - process cmdline:

{'comm': 'o2ibfd5hja55vfe', 'process_tgid': 22953, 'event': 'COMM', 'process_pid': 22953}

{'parent_tgid': 22802, 'child_tgid': 22954, 'parent_pid': 22802, 'event': 'FORK', 'child_pid': 22954}
FORK (parent: 22802, child: 22954):
 - parent exe: /home/ubuntu/honeypot/mehrai/venv/bin/python2.7
 - parent cmdline: ['python', 'mehrai.py', '25f391a62ffd8b2827f9165c300f81a4ab066243e25af82d26539419596e1fba', '']
   \_ child exe:
   \_ child cmdline:

{'process_tgid': 22954, 'event': 'EXEC', 'process_pid': 22954}
EXEC (22954):
 - process exe:
 - process cmdline:

{'parent_tgid': 22954, 'child_tgid': 22955, 'parent_pid': 22954, 'event': 'FORK', 'child_pid': 22955}
FORK (parent: 22954, child: 22955):
 - parent exe:
 - parent cmdline:
   \_ child exe:
   \_ child cmdline:

{'process_tgid': 22955, 'event': 'EXEC', 'process_pid': 22955}
EXEC (22955):
 - process exe:
 - process cmdline:

{'parent_tgid': 22953, 'child_tgid': 22956, 'parent_pid': 22953, 'event': 'FORK', 'child_pid': 22956}
FORK (parent: 22953, child: 22956):
 - parent exe:
 - parent cmdline:
   \_ child exe: /dvrHelper (deleted)
   \_ child cmdline: ['63453245te55', '', '', '', '', '', '', '', '', '', '', '']
   [!] killing 22956

{'exit_signal': 17L, 'process_tgid': 22953, 'event': 'EXIT', 'process_pid': 22953, 'exit_code': 0L}
EXIT (22953):
 - process tgid: 22953
 - process exit code 0
 - process signal 17

{'parent_tgid': 22877, 'child_tgid': 22957, 'parent_pid': 22877, 'event': 'FORK', 'child_pid': 22957}
FORK (parent: 22877, child: 22957):
 - parent exe:
 - parent cmdline:
   \_ child exe:
   \_ child cmdline:

{'process_tgid': 22957, 'event': 'EXEC', 'process_pid': 22957}
EXEC (22957):
 - process exe:
 - process cmdline:

{'exit_signal': 17L, 'process_tgid': 22957, 'event': 'EXIT', 'process_pid': 22957, 'exit_code': 32512L}
EXIT (22957):
 - process tgid: 22957
 - process exit code 32512
 - process signal 17

{'process_tgid': 22956, 'event': 'SID', 'process_pid': 22956}

{'parent_tgid': 22956, 'child_tgid': 22958, 'parent_pid': 22956, 'event': 'FORK', 'child_pid': 22958}
FORK (parent: 22956, child: 22958):
 - parent exe:
 - parent cmdline: ['']
   \_ child exe: /dvrHelper (deleted)
   \_ child cmdline: ['63453245te55', '', '', '', '', '', '', '', '', '', '', '']
   [!] killing 22958
```
thasit.


# mehrai v1 
mehrai is a Docker based honeypot whose purpose is catching Mirai binaries. I tossed this together because cowrie shits the bed whenever it gets Mirai connections. It's meant to work in tandem with [Viper](http://viper-framework.readthedocs.io/en/latest/)'s API. As of now, this honeypot is medium-interaction as there's some weirdness that goes on that may involve your interaction. Regardless, there's so many Mirai bots scanning everywhere(seriously. It even loves ec2 IP space for IoT devices.) that you'll be able to grab a few different bins in the first couple of minutes.

This uses Alpine Linux Docker image, which works extremely well for mimicing an IoT device. The telnetd binary is from elsewhere, as the Alpine image does not supply one. The python script uses py-watchdog and watches / for any file additions or modifications, posts them to Viper and kills any running Mirai procs. Sometimes Mirai deletes itself so quickly that the script can't grab everything in time, so it will try to get bins from /proc/pid/exe as well. telnetd will be restarted 15 seconds after the Mirai procs are killed, because Mirai gets pissy when expunged and comes back just to kill telnetd. To run:

```
sudo docker build -t honeypot/mehrai .
sudo docker run -it --rm -p 23:23 honeypot/mehrai /bin/sh

/ # sh /tmp/run.sh
```

Feel free to set a password, or don't.


