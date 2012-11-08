SUSE Patch Tools

These python script allow easy manipulation of Linux patches, which makes
back-porting them much easier.

The configuration file will be installed in /etc/patch.cfg if /etc is writable.
Otherwise it is installed in ~/.local/etc/patch.cfg.

If you have installed this tool via an RPM or other package, you'll need
to copy the sample config file from /etc to ~/.local/etc/patch.cfg and edit
it to fit your site.

Tools written by Jeff Mahoney <jeffm@suse.com>
Setuptools integration by Lee Duncan <lduncan@suse.com>
