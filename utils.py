import sys, os
import subprocess

SHELL="/bin/bash"

def checkAndroidSourceTop(directory):
	main_mk = os.path.sep.join(('', 'build', 'core', 'main.mk'))
	if not os.access(directory + main_mk, os.R_OK):
		return False
	envsetup = os.path.sep.join(('', 'build', 'envsetup.sh'))
	if not os.access(directory + envsetup, os.R_OK):
		return False

	return True

def getShellOutput(directory, script):
	script = "source build/envsetup.sh > /dev/null;"%{"directory" :directory} + script
	cmd = (SHELL, "-c", script)
	return subprocess.Popen(cmd, cwd = directory,
			stdout=subprocess.PIPE,
			close_fds=True).stdout.read()
	
def getProductsList(directory):
	out = getShellOutput(directory, "echo ${LUNCH_MENU_CHOICES[*]}").split()
	products = []
	for item in out:
		p, variant = item.split('-')
		if not p in products: products.append(p)
	return products
	
if __name__ == '__main__':
	print checkAndroidSourceTop(sys.argv[1])
	print "out = ", getProductsList(sys.argv[1])
