# mehrai v1
mehrai is a Docker based honeypot whose purpose is catching Mirai binaries. I tossed this together because cowrie shits the bed whenever it gets Mirai connections. It's meant to work in tandem with [Viper](http://viper-framework.readthedocs.io/en/latest/)'s API. As of now, this honeypot is medium-interaction as there's some weirdness that goes on that may involve your interaction. Regardless, there's so many Mirai bots scanning everywhere(seriously. It even loves ec2 IP space for IoT devices.) that you'll be able to grab a few different bins in the first couple of minutes.

This uses Alpine Linux Docker image, which works extremely well for mimicing an IoT device. The telnetd binary is from elsewhere, as the Alpine image does not supply one. The python script uses py-watchdog and watches / for any file additions or modifications, posts them to Viper and kills any running Mirai procs. Sometimes Mirai deletes itself so quickly that the script can't grab everything in time, so it will try to get bins from /proc/pid/exe as well. telnetd will be restarted 15 seconds after the Mirai procs are killed, because Mirai gets pissy when expunged and comes back just to kill telnetd. To run:

```
sudo docker build -t honeypot/mehrai .
sudo docker run -it --rm -p 23:23 honeypot/mehrai /bin/sh

/ # sh /tmp/run.sh
```

Feel free to set a password, or don't.

# Version 2
Much less janky, more robust(not just targeting mirai's) and utilizes the kernels netlink API to monitor procs in a much smoother fashion. Pretty much done.
