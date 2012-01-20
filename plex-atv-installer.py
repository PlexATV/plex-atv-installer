#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#   Copyright (c) 2008-2012 Tobias Hieta <tobias@hieta.se>
#

import optparse
VERSION = "1.0"
REPO_VERSION = "1.0"
from pexpect import pxssh
import sys
import re

repo_base_url = 'http://nightlies.plexapp.com/plex-atv-plugin/repo/com.plexapp.repo.%s_'+REPO_VERSION+'_iphoneos-arm.deb'

def get_options():
    usage = """Usage: %prog [options] command
    
%prog is a easy way to install plex-atv on your
Apple TV (Gen 2). If you want to install just
run ./%prog install.
    
Commands:
  install - install plex-atv
  upgrade - attempt to upgrade plex-atv
  remove - remove plex-atv
  status - print status and version of plex-atv
  removesettings - remove settings for plex-atv"""
  
    op = optparse.OptionParser(version='%prog ' + VERSION, usage = usage)
    op.add_option("", "--atv-host", 
        dest='atvhost',
        default='apple-tv.local',
        type='string',
        help="Hostname or IP number for the Apple TV (default: %default)")
    op.add_option("", "--atv-user", 
        dest='atvuser',
        default='root',
        type='string',
        help='Username for accessing the Apple TV (default: %default)')
    op.add_option("", "--atv-password", 
        dest='atvpassword',
        default='alpine',
        type='string',
        help='Password for accessing the Apple TV (default: %default)')
    op.add_option('-b', '--branch',
        dest='branch',
        default='stable',
        type='choice',
        action='store',
        choices=['stable', 'beta', 'snapshot'],
        help='What branch of Plex-ATV to use: stable/beta/snapshot (default: %default)')
    op.add_option('-d', '--debug',
        dest='debug',
        default=False,
        action='store_true',
        help='Turn on debug')
    op.add_option('-r', '--no-restart',
        dest='restart',
        default=True,
        action='store_false',
        help='Don\'t restart the AppleTV process')


    return (op, op.parse_args())

class ATVChannel:
    def __init__(self, host, user, password, debug=False):
        self.host = host
        self.user = user
        self.password = password
        self.plex_version = "0"
        self.plex_installed = False
        if debug:
            self.ssh = pxssh.pxssh(logfile=sys.stdout)
        else:
            self.ssh = pxssh.pxssh()
        
        self.login()
        
    def login(self):
        print "!Logging in (%s:%s@%s)" % (self.user, self.password, self.host)
        self.ssh.login(self.host, self.user, self.password, original_prompt="root#")
        print "!connected"
        self.ssh.sendline('uname -a')
        self.ssh.prompt()
        if not "AppleTV2,1" in self.ssh.before:
            print "!!Not an Apple TV? uname reports:\n " + self.ssh.before + "!!"
            sys.exit(1)
        self.ssh.sendline('dpkg --version')
        self.ssh.prompt()
        if not "Debian `dpkg' package management program" in self.ssh.before:
            print "!!No DPKG installed? Did you jailbreak it correctly?"
            sys.exit(1)
        
        (i, v) = self.get_package_info('com.plex.client-plugin')
        self.plex_installed = i
        self.plex_version = v

    def get_package_info(self, pkgname):
        installed = False
        version = None
        
        self.ssh.sendline('dpkg -p %s' % pkgname)
        self.ssh.prompt()
        if not "Package: " + pkgname in self.ssh.before:
            print "!package %s not installed" % pkgname
            return (installed, version)
        
        for l in self.ssh.before.split('\n'):
            match = re.match('^Version: (.*)$', l)
            if match:
                version = match.group(1).strip()
                break
        
        self.ssh.sendline('dpkg -s ' + pkgname)
        self.ssh.prompt()
        
        for l in self.ssh.before.split('\n'):
            match = re.match('^Status: (.*)$', l)
            if match:
                if not 'not-installed' in match.group(1):
                    installed = True
                break
        
        #print "!package %s is installed %d version %s" % (pkgname, installed, version)
        return (installed, version)
        
    def check_repo(self, branch):
        (i, v) = self.get_package_info('com.plexapp.repo.' + branch)
        if i and v == REPO_VERSION:
            return
            
        print "!install repo"
        url = repo_base_url % branch
        self.ssh.sendline('wget -O /tmp/repo.deb -q ' + url)
        self.ssh.prompt()
        self.ssh.sendline('dpkg -i /tmp/repo.deb')
        self.ssh.prompt()
    
    def install(self, branch, do_repo_check = True):
        if do_repo_check:
            self.check_repo(branch)
        
        print "!updating sources"
        self.ssh.sendline('apt-get update')
        self.ssh.prompt()
        
        print "!looking for updates"
        self.ssh.sendline('apt-get install --yes --force-yes com.plex.client-plugin')
        self.ssh.prompt()
        
        (i, v) = self.get_package_info('com.plex.client-plugin')
        if not i:
            print "!!failed to install: " + self.ssh.before + '!!'
            sys.exit(1)
            
        if not self.plex_installed or not v == self.plex_version:
            self.plex_version = v
            self.plex_installed = i
            print "!new version is %s" % (self.plex_version)
            return True
        else:
            print "!no new version found"
            return False
            
    def restart_apple_tv(self):
        print "!restarting AppleTV process"
        self.ssh.sendline('killall AppleTV')
        self.ssh.prompt()
        
    def remove(self):
        (i, v) = self.get_package_info('com.plex.client-plugin')
        if not i:
            print "!plex-atv is not installed"
            return False
            
        print "!uninstalling version %s of Plex-ATV" % v
        self.ssh.sendline('apt-get remove --yes --force-yes com.plex.client-plugin')
        self.ssh.prompt()
        (i, v) = self.get_package_info('com.plex.client-plugin')
        if i:
            print "!!failed to remove the client"
            sys.exit(1)
        return True

    def removesettings(self):
        self.ssh.sendline('rm -f /var/mobile/Library/Preferences/com.plex.client-plugin.plist')
        self.ssh.prompt()
        return True

if __name__ == '__main__':
    (op, (options, args)) = get_options()
    
    if len(args) < 1:
        op.print_usage()
        sys.exit(1)
    
    # first we need a channel to the ATV
    chan = ATVChannel(options.atvhost, options.atvuser, options.atvpassword, options.debug)

    want_restart = False
    
    if args[0] == 'install':
        want_restart = chan.install(options.branch)
    elif args[0] == 'upgrade':
        want_restart = chan.install(options.branch, False)
    elif args[0] == 'remove':
        want_restart = chan.remove()
    elif args[0] == 'status':
        if chan.plex_installed:
            print "!plex-atv is installed, current version " + chan.plex_version
        else:
            print "!no plex-atv installed"
        sys.exit(0)
    elif args[0] == 'removesettings':
        want_restart = chan.removesettings()
    elif args[0] == 'restart':
        want_restart = True
    else:
        print "Need an action, can be install, remove or status"
        sys.exit(1)
    
    if want_restart and options.restart:
        chan.restart_apple_tv()
        
    print "!done - no errors"