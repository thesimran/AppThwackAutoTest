import pexpect
import sys
import os

child = pexpect.spawn('aws configure')
child.logfile = sys.stdout
child.expect('AWS Access Key ID')
child.sendline(os.environ['AWS_ACCESS_KEY'])
child.expect('AWS Secret Access Key')
child.sendline(os.environ['AWS_SECRET_ACCESS_KEY'])
child.expect('Default region name')
child.sendline('us-east-1')
child.expect('Default output format')
child.sendline('text') # Is this what we want?
