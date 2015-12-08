import boto3
import subprocess
import os
import sys
import datetime
import requests
import time
import pexpect

PROJECT_ARN = 'arn:aws:devicefarm:us-west-2:146362399349:project:4d5b565f-e47d-4d97-808b-f2a78a681edc'
APP_FILE_PATH = 'app/build/outputs/apk/app-debug.apk'
TEST_APK_FILE_NAME_BASE = 'app/build/outputs/apk/app-debug-androidTest-unaligned.apk'
DEVICE_POOL_ARN = 'arn:aws:devicefarm:us-west-2:146362399349:devicepool:4d5b565f-e47d-4d97-808b-f2a78a681edc/250109fd-d752-4559-852f-9ef2858d7398'

def upload_file(file_name, url):
	headers = { 'content-type' : 'application/octet-stream'}
	with open(file_name, 'rb') as f:
		response = requests.put(url, data=f, headers=headers)
	if response.status_code != 200:
		print '\ncode = ' + str(response.status_code) + '\nresponse =\n' + response.text
		sys.exit(1)
	print "Success!"

if __name__ == '__main__':

	is_running_in_travis = False
	try:
		is_running_in_travis = os.environ['IS_RUNNING_IN_TRAVIS']
	except KeyError, e:
		pass

	try:
		if is_running_in_travis:
			child = pexpect.spawn('aws configure')
			child.logfile = sys.stdout
			child.expect('AWS Access Key ID')
			child.sendline(os.environ['AWS_ACCESS_KEY'])
			child.expect('AWS Secret Access Key')
			child.sendline(os.environ['AWS_SECRET_ACCESS_KEY'])
			child.expect('Default region name')
			child.sendline('us-west-2')
			child.expect('Default output format')
			child.sendline('text') # Is this what we want?
	except KeyError, e:
		pass

	now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S").replace(' ', '_').replace(':', '_')
	print "Creating APK upload..."
	devicefarm = boto3.client('devicefarm')
	response = devicefarm.create_upload(projectArn=PROJECT_ARN, name='app-debug.apk', type='ANDROID_APP', 
		contentType='application/octet-stream')
	app_arn = response['upload']['arn']
	print "Successs!"

	app_upload_url = response['upload']['url']
	headers = { 'content-type' : 'application/octet-stream'}
	print 'Uploading APK...'
	upload_file(APP_FILE_PATH, app_upload_url)

	print 'Creating test APK upload...'
	response = devicefarm.create_upload(projectArn=PROJECT_ARN, name=TEST_APK_FILE_NAME_BASE, 
		type='INSTRUMENTATION_TEST_PACKAGE', contentType='application/octet-stream')
	test_apk_arn = response['upload']['arn']
	print 'Success!'

	test_app_url = response['upload']['url']
	headers = { 'content-type' : 'application/octet-stream'}
	print 'Uploading test APK...'
	upload_file(TEST_APK_FILE_NAME_BASE, test_app_url)

	print "Scheduling run..."
	run_name = 'test_run_' + now
	time.sleep(5)
	response = devicefarm.schedule_run(
		projectArn=PROJECT_ARN, 
		appArn=app_arn,
		name=run_name,
		devicePoolArn=DEVICE_POOL_ARN, 
		test={
        'type': 'INSTRUMENTATION',
        'testPackageArn': test_apk_arn
    })
	print 'Run scheduled!'
	run_arn = response['run']['arn']
	status = ''
	while status != 'COMPLETED':
		print 'Current test run status: ' + status
		response = devicefarm.get_run(arn=run_arn)
		status = response['run']['status']
		time.sleep(2)
	print 'Test run complete!'
	result = response['run']['result']
	if result == 'PASSED':
		print 'All tests passed!'
		sys.exit(0)
	else:
		print 'Tests failed. Run ARN = ' + run_arn
		sys.exit(1)

