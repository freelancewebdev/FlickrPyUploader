#!/usr/bin/python
# -*- coding: utf-8 -*-
import ConfigParser
import sys
import os
import logging
from datetime import datetime
import flickrapi
import webbrowser
import time

cfg = None
localpath = ''
configFilename = ''
logfilename = ''
picsfolder = '/Users/joe/Dropbox/python/dropboxpics/camera'
fileCount = 0
fileSize = 0
flickrObj = None
flickr_key = ''
flickr_secret = ''
flickr_access_token = ''
is_public = 0
is_family = 0
is_friend = 0
tries = 0
allowedfiles = ['.jpg', '.jpeg', '.png', '.gif', '.avi', '.mp4', '.3gp']

def main():
	doGreeting()
	doLocalSetup()
	getConfigs()
	checkAuth()
	uploadPhotos()

def doGreeting():
	sys.stderr.write("\x1b[2J\x1b[H")
	greetingStr = ''
	greetingStr += '\nFlickr Folder Uploader'
	greetingStr += '\n'
	greetingStr += '\nA simple Python script to upload a directory of photos to Flickr.'
	greetingStr += '\nFor full details see http://freelancewebdev.github.com/FlickrPyUploader'
	greetingStr += '\n'  
	greetingStr += '\nCopyright (C) ' + str(datetime.now().year) + ' Joe Molloy (info[at]hyper-typer.com)'
	greetingStr += '\nThis program comes with ABSOLUTELY NO WARRANTY.'
	greetingStr += '\nThis is free software, licensed under the GPL V3'
	greetingStr += '\nand you are welcome to redistribute it'
	greetingStr += '\n'
	print greetingStr

def doLocalSetup():
	global path, configFileName, logFileName
	print 'Setting up basic settings'
	path = os.path.dirname(os.path.abspath(__file__))
	configFileName = __file__ + '.cfg'
	logFileName = __file__ + '.log'
	logging.basicConfig(filename=logFileName,level=logging.DEBUG)
	logging.info('Logging set up')
	if not os.path.isdir(picsfolder):
		print 'Photos folder not found. Exiting.'
		logging.critical('Photo folder not found')
		sys.exit(1)
	else:
		print 'Uplaoding photos from %s.' %picsfolder
	print 'Basic setup complete'

def getConfigs():
	global cfg, flickr_key, flickr_secret, flickr_access_token
	print '\nChecking configuration data...'
	logging.info('Checking config data')
	cfg = ConfigParser.ConfigParser()
	try:
		cfg.read(os.path.join(localpath, configFileName))
		logging.info('Config file loaded')
	except:
		logging.debug('Initial attempt to read config file failed')
		try:
			os.chmod(os.path.join(localpath,configFileName),0777)
			cfg.read(os.path.join(localpath,configFileName))
			logging.debug('Config file loaded after changing permissions')
		except Exception as e:
			logging.critical('Reading config file failed. ' + str(e))
			print 'There was a problem reading the config file'
			print 'Please ensure you have renamed'
			print '\'' + configFileName + '_sample\' to \'' + configFileName + '\''
			print 'and added your own values as appropriate'
			sys.exit()
	try:
		flickr_key = cfg.get('flickr','key')
	except:
		print 'No Flickr application key set in config file. Exiting.'
		logging.critical('No flickr application key found in config file')
		sys.exit(1)
	try:
		flickr_secret = cfg.get('flickr','secret')
	except:
		print 'No Flickr application secret set in config file. Exiting.'
		logging.critical('No Flickr application secret found in config file. Exiting.')
		sys.exit(1)
	try: 
		flickr_access_token = cfg.get('flickr','access_token')
	except:
		pass
	try:
		is_public = cfg.get('flickr','is-public')
	except:
		print 'Setting uploads to private'
		logging.debug('No configuration setting for is-public found so setting uploads to private')
		pass
	try:
		is_family = cfg.get('flickr','is-family')
	except:
		print 'Setting uploads to private from family'
		logging.debug('No configuration setting for is-family found so setting uploads to private')
		pass
	try:
		is_friend = cfg.get('flickr','is-friend')
	except:
		print 'Setting uploads to private'
		logging.debug('No configuration setting for is-friend found so setting uploads to private')
		pass
	print 'Configuration values set up'

def checkAuth():
	global flickrObj
	flickrObj = flickrapi.FlickrAPI(flickr_key, flickr_secret)
	try:
		(flickr_access_token, frob) = flickrObj.get_token_part_one(perms='write')
	except:
		print 'We are running purely in the console.'
		print 'You will have to authenticate manually'
		(flickr_access_token, frob) = flickrObj.get_token_part_one(perms='write', auth_callback=manualAuth)
	if not flickr_access_token:
		raw_input("Press ENTER after you authorized this program")
	else:
		cfg.set('flickr','access_token',flickr_access_token)
		try:
			with os.open(configFilename,'w') as cf:
				cfg.write(cf)
		except:
			print 'Failed to write token to config file'
			logging.debug('Failed to write token to config file')
	flickrObj.get_token_part_two((flickr_access_token, frob))
	print 'We are now authenticated.'

def uploadPhotos():
	global fileCount, tries
	tries = 0
	for root, dirs, files in os.walk(picsfolder):
		for f in files:
			if not f.endswith('.ini') and not f == '.DS_Store' and not f == '._.DS_Store' and not f.endswith('.db') and not f.endswith('.zip') and not f.endswith('.3gp'):
				uploadPhoto(f,root)
	print 'Uploaded %d photos' % fileCount

def uploadPhoto(f,root):
	global tries, fileCount
	print 'Uploading ' + f
	ffullpath = os.path.join(root,f)
	title = os.path.splitext(f)[0]
	desc = '%s (uploaded by Python Flickrapi)' % f
	tags = 'flickrapi flickrpyuploadr'
	try:
		response = flickrObj.upload(filename=ffullpath,title=title,description=desc,tags=tags,is_public=is_public,is_family=is_family,is_friend=is_friend,callback=showProgress)
		fileCount += 1
	except Exception as e:
		if tries < 10:
			print 'There was an error uploading. %s' % str(e)
			print 'Retrying in 30 seconds'
			time.sleep(30)
			try:
				response = flickrObj.upload(ffullpath,title,desc,tags,0,0,0,callback=showProgress)
				fileCount += 1
			except:
				print 'Failed again. (%d tries)' % tries
				tries += 1
				uploadPhoto(f,root)
		else:
			logging.debug('Failed to upload ' + os.path.join(root,f))
			print 'Giving up on ' + os.path.join(root,f) + '\n\n'

def showProgress(progress, done):
    if done:
        print "Done uploading\n\n"
    else:
        print "At %s%%" % progress

def manualAuth(frob,perms):
	auth_url = flickrObj.auth_url(perms,frob)
	print '1. Go to %s in your browser.' % auth_url
	print '2. Give this app permission to operate'
	print '3. Return here and press enter'
    
if __name__ == '__main__':
	main()

