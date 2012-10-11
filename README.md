jpt
===

Jeff's Patching Tools

These python script allow easy manipulation of Linux patches, which makes
back-porting them much easier.

The config file is installed in /etc/patch.cfg if installed as root.

The setup.cfg file tells python to install the tool in your home directory, but
if you do that as root, they will go in /root/..., so remove the patch.cfg file. :)
