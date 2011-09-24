import sys, os
import subprocess

SHELL="/bin/bash"

def check_source_top(directory):
	main_mk = os.path.sep.join(('', 'build', 'core', 'main.mk'))
	if not os.access(directory + main_mk, os.R_OK):
		return False
	envsetup = os.path.sep.join(('', 'build', 'envsetup.sh'))
	if not os.access(directory + envsetup, os.R_OK):
		return False
	return True

def build_cmd_args(script):
	script = "source build/envsetup.sh > /dev/null;" + script
	return (SHELL, "-c", script)

def get_shell_output(directory, script):
	cmd = build_cmd_args(script)
	return subprocess.Popen(cmd, cwd = directory,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			close_fds=True).stdout.read()
	
def get_product_list(directory):
	out = get_shell_output(directory, "echo ${LUNCH_MENU_CHOICES[*]}").split()
	products = []
	for item in out:
		if not '-' in item: continue
		p, variant = item.split('-')
		if not p in products: products.append(p)
	return products

def build_lunch(product, variant):
	script = "lunch %s-%s"%(product, variant)
	script += ";" + "export OUT_DIR=" + "-".join(("out", product, variant))
	return script
	
if __name__ == '__main__':
	print check_source_top(sys.argv[1])
	print "out = ", get_product_list(sys.argv[1])
