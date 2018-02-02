# Version 1.0

Relicensed under GPL v3.

Renamed unmount commands:
- `sftpman unmount` -> `sfptman umount`
- `sftpman unmount_all` -> `sfptman umount_all`

Changed the extension (`.js` -> `.json`) of configuration files stored in `~/.config/sftpman/mounts`.
You need to migrate your files manually like this:

```bash
for f in $(ls ~/.config/sftpman/mounts/*.js); do n=$(echo $f | sed 's/.js$/.json/'); mv $f $n; done;
```

# Versions < 1.0

No documented changes.