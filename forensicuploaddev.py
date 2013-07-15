# YOU NEED TO INSERT YOUR APP KEY AND SECRET BELOW!
# Go to dropbox.com/developers/apps to create an app.

app_key = ''
app_secret = ''
 
# access_type can be 'app_folder' or 'dropbox', depending on
# how you registered your app.
access_type = 'app_folder'

from dropbox import client, rest, session
from getpass import getpass
#from mechanize import Browser, HTTPRedirectHandler, ControlNotFoundError
from pickle import dumps, loads
from shlex import split
from subprocess import CalledProcessError, check_output, STDOUT
from sys import argv, stdin
from keyring import delete_password, errors, get_password, set_password

def get_request_token():
	print 'Getting request token...'	
	sess = session.DropboxSession(app_key, app_secret, access_type)
	request_token = sess.obtain_request_token()
	url = sess.build_authorize_url(request_token)

	browser = Browser()
	browser.set_handle_redirect(HTTPRedirectHandler)
	browser.open(url)
	browser.select_form(nr=1)
	
	try:
		browser["login_email"] = raw_input('Login Email: ')
		browser["login_password"] = getpass()
		browser.submit()
		browser.select_form(nr=1)
		browser.submit(name='allow_access')
	except ControlNotFoundError:
		print 'Dropbox website cannot be parsed correctly...'
		print '...Possibly because of a wrong username or password.'

	return request_token
 
def get_access_token():
	try:
		token_str = get_password('dropbox', app_key)
	except ValueError:
		print 'Password is incorrect'
	if token_str:
		key, secret = loads(token_str)
		return session.OAuthToken(key, secret)
	request_token = get_request_token()
	sess = session.DropboxSession(app_key, app_secret, access_type)
	access_token = sess.obtain_access_token(request_token)
	token_str = dumps((access_token.key, access_token.secret))
	set_password('dropbox', app_key, token_str)
	return access_token
 
def get_client():
	try:
		access_token = get_access_token()
		sess = session.DropboxSession(app_key, app_secret, access_type)
		sess.set_token(access_token.key, access_token.secret)
		dropbox_client = client.DropboxClient(sess)
		return dropbox_client
	except rest.ErrorResponse:
		print 'Token is disabled or invalid'

def help():
	print ""
	print "This script will allow you to upload output directly to"
	print "your Dropbox account.  First, it will link your account with"
	print "this app (without having to go through a web browser)"
	print "and then allow you to run system commands. The output is"
	print "uploaded to the Apps/Forensic Upload/[given filepath]"
	print "directory of your Dropbox account."
	print ""
	print "Usage:"
	print "	forensicupload.py start | pipe"
	print ""
	print "To use the 'pipe' parameter, pipe the output to this"
	print "script along with the filepath to save to in your"
	print "Dropbox account.  e.g."
	print "'ipconfig | forensicupload.py pipe /case123/ipconfig.txt'"
	print ""
	print "After starting the app with the 'start' paramter, you"
	print "can 'link' your Dropbox account, 'unlink' a previously"
	print "linked account, or 'run' a system command."
	print ""
	print "	- link   = Link your Dropbox account to this app"
	print "			to allow uploading."
	print "	- unlink = Remove the session information for your"
	print "			Dropbox account from this app."
	print "	- run	 = Run a system command and upload the output"
	print "			to your Dropbox account.  This command can"
	print "			take optional parameters to direcly execute"
	print "			a command.  e.g. 'run ipconfig all'.  Otherwise,"
	print "			it will ask for the system command to run."

def link():
	print 'Getting account info...'
	dropbox_client = get_client()
	if dropbox_client == None:
		print 'Link has failed.'
	else:
		print 'linked account:', dropbox_client.account_info()['display_name'],'-',dropbox_client.account_info()['email']

def unlink():
	print 'Unlinking account info...'
	try:
		delete_password('dropbox', app_key)
		print '...Done'
	except errors.PasswordDeleteError:
		print 'There is no account info to unlink'

def upload(filepath, content):
	dropbox_client = get_client()
	if dropbox_client == None:
		print 'Link has failed.'
	else:
		if filepath:
			dropbox_client.put_file(filepath,content)
		else:
			print "You must specify a filepath and file."
			print "e.g. /case1001/ping.txt"

def run(system_command):
	try:
		filepath = raw_input('Upload to which filepath? ')
		upload(filepath, check_output(system_command, stderr=STDOUT, shell=True))
	except CalledProcessError:
		'Error while calling ',system_command,'.'

def command_loop():
	continue_loop = 1

	while(continue_loop):
		print ""
		command_list = split(raw_input('Please select an option: '))
		command = command_list[0]
		if command == 'link':
			link()
		elif command == 'unlink':
			unlink()
		elif command == 'run':
			system_command = None
			if len(command_list) > 1:
				system_command = command_list[1:len(command_list)]
			else:
				system_command = split(raw_input('Which system command? '))
			run(system_command)
		elif command == 'help':
			help()
		elif command == 'quit':
			continue_loop = 0
		else:
			print 'You can run "link", "unlink", "run [command [command args]]", "help", or "quit"'
 
def main():
	if len(argv) < 2:
		help()
	elif argv[1] == 'pipe':
		pipe_input = stdin.read()
		if pipe_input:
			upload(argv[2], pipe_input)
		else:
			print 'No input to upload'
	elif argv[1] == 'start':
		command_loop()
	else:
		help()
 
if __name__ == '__main__':
	main()