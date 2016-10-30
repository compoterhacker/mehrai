#!/bin/sh

sed -e 's/\/ash/\/sh/' /etc/passwd
dbus &
telnetd -b 0.0.0.0:23
