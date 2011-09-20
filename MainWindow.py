from gi.repository import GLib, GObject, Gtk, Vte
import utils
import os, sys

SOURCE_TOP = "/home/ganadist/android/src"

class MainWindow:
	def __init__(self):
		self.ui = Gtk.Builder()
		self.ui.add_from_file("data/ui/main.ui")
		self.win = self.ui.get_object("window1")
		self.win.connect("destroy", Gtk.main_quit)

		expander = self.ui.get_object("TerminalExpander")
		self.terminal = Vte.Terminal()
		self.terminal.set_size(80, 25)
		self.terminal.connect("child-exited", self.build_terminated)
		expander.add(self.terminal)

		self.build_btn = self.ui.get_object("btn_build")
		self.build_btn.connect("toggled", self.toggle_btn_build)

		self.setSourceTop(SOURCE_TOP)
		self.pid = None

		self.win.show_all()

	def setSourceTop(self, directory):
		products = utils.getProductsList(directory)
		combo = self.ui.get_object("combobox_product")
		if products:
			for product in products:
				combo.append_text(product)
			combo.set_active(0)
		combo = self.ui.get_object("combobox_variant")
		combo.set_active(0)

	def toggle_btn_build(self, button):
		if button.get_active():
			self.run_build()
		else:
			self.stop_build()
		return True

	def stop_build(self):
		self.build_btn.set_label("Build")
		if self.pid:
			import signal
			os.kill(self.pid, signal.SIGTERM)

	def run_build(self):
		self.build_btn.set_label("Stop")
		self.terminal.reset(True, True)
		product = self.ui.get_object("combobox_product").get_active_text()
		variant = self.ui.get_object("combobox_variant").get_active_text()
		lunch = "lunch %s-%s"%(product, variant)
		script = lunch + ";make bootimage"
		print 'run:', script
		success, pid = self.terminal.fork_command_full(
			Vte.PtyFlags.NO_WTMP |
				Vte.PtyFlags.NO_UTMP |
				Vte.PtyFlags.NO_LASTLOG,
			SOURCE_TOP,
			utils.buildCmdArgs(script),
			(),
			GLib.SpawnFlags.SEARCH_PATH, None, None)
		self.pid = pid

	def build_terminated(self, terminal):
		print terminal.get_child_exit_status()
		#pid, status = os.waitpid(self.pid, os.WNOHANG)
		#print pid, status
		self.pid = None
		self.build_btn.set_active(False)
