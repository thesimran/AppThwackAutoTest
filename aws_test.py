import pexpect
import sys

child = pexpect.spawn('aws configure')
child.logfile = sys.stdout
child.expect('AWS Access Key ID')
child.sendline('')
child.expect('AWS Secret Access Key')
child.sendline('')
child.expect('Default region name')
child.sendline('us-east-1')
child.expect('Default output format')
child.sendline('text') # Is this what we want?
