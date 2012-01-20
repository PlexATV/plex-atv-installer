# plex-atv-installer

A small and simple script for installing plex-atv on your Apple TV (Gen 2).

### Dependencies

You'll need a Apple TV (Gen 2) that is jailbroken. We suggest you use seas0npass since it's the easiest way. The script is only tested on Mac OSX, but I would suspect that it works fine on Linux as well. Windows users are on their own.

### Usage

#### Installation

To install plex-atv on your newly jailbroken ATV you just have to run:
	
	./plex-atv-installer.py install
	
This will try to install it on a Apple TV on the local network called apple-tv.local. If you want to install on another Apple TV (for example living-room-apple-tv), then give it the option --atv-host

	./plex-atv-installer.py --atv-host=living-room-apple-tv.local
	
You can also pass --atv-user and --atv-password if you have changed the defaults from root/alpine

The installer also supports different branches of plex-atv. It defaults to install the stable one, but if you want to install the beta:

	./plex-atv-installer.py -b beta install
	
or snapshot

	./plex-atv-installer.py -b snapshot install
	
#### Remove

You can remove plex-atv from your ATV by running

	./plex-atv-installer.py remove
	
#### Other handy commands

You can upgrade your plex-atv by running:

	./plex-atv-installer.py upgrade
	
You can see what version currently is installed by running:

	./plex-atv-installer.py status
	
You can remove the settings file for plex-atv by running:

	./plex-atv-installer.py removesettings
	
### Known issues

If you install snapshot or beta version and want to revert to stable it's currently not that easy. I will be adding a option for that later. For know, be careful when not installing the stable branch