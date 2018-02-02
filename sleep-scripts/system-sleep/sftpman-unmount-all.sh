#!/bin/bash

# Sleep hook for systemd.
# Takes care of unmounting everything for all users on system suspend/hibernate.
# To be placed in /usr/lib/systemd/system-sleep/

if [ -n "$1" ]; then
	if ([ "$1" = "pre" ]); then
		for username in $(ps aux | grep '/mnt/sshfs/' | grep -v 'grep' | grep -o -E '^(\w+)\s' | uniq); do
			su -l $username -c 'sftpman umount_all'
		done;
	fi
fi

