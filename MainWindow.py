from gi.repository import GLib, GObject, Gtk, Vte
import utils
import os, sys

COL_ENABLE, COL_RULE, COL_DESCRITION = range(3)

class MainWindow:
	def __init__(self):
		self.ui = Gtk.Builder()
		self.ui.add_from_file("data/ui/main.ui")
		self.win = self.ui.get_object("window1")
		self.win.connect("destroy", Gtk.main_quit)

		scroll = self.ui.get_object("TerminalScroll")
		self.terminal = Vte.Terminal()
		self.terminal.set_size(80, 25)
		self.terminal.connect("child-exited", self.build_terminated)
		scroll.add_with_viewport(self.terminal)

		self.build_btn = self.ui.get_object("btn_build")
		self.build_btn.connect("toggled", self.toggle_btn_build)

		treeview = self.ui.get_object("treeview_rules")
		treeview.connect("row-activated", self.activate_rule_row)
		renderer = self.ui.get_object("renderer_enable")
		renderer.connect("toggled", self.toggle_enable_rule)

		chooser = self.ui.get_object("chooser_source_top")
		chooser.connect("file-set", self.choose_source_top)
		chooser.connect("file-set", self.choose_source_top)

		self.pid = None
		self.win.show_all()

	def choose_source_top(self, chooser):
		directory = chooser.get_filename()
		self.set_source_top(directory)

	def set_choose_directory(self, directory):
		chooser = self.ui.get_object("chooser_source_top")
		chooser.set_filename(directory)

	def set_ui_enable(self, enable):
		for name in ("btn_build", "combobox_product", "combobox_variant"):
			w = self.ui.get_object(name)
			w.set_sensitive(enable)

	def set_source_top(self, directory):
		print 'set ', directory
		if not utils.check_source_top(directory):
			self.set_ui_enable(False)
			return False

		products = utils.get_product_list(directory)
		if not products:
			self.set_ui_enable(False)
			return False
		combo = self.ui.get_object("combobox_product")
		for product in products:
			combo.append_text(product)
		combo.set_active(0)
		combo = self.ui.get_object("combobox_variant")
		combo.set_active(0)

		self.sourceTop = directory
		self.set_ui_enable(True)
		return True

	def toggle_btn_build(self, button):
		if button.get_active():
			self.run_build()
		else:
			self.stop_build()
		return True

	def toggle_column_enable(self, path):
		model = self.ui.get_object("liststore_rules")
		iter = model.get_iter(path)
		active = model.get(iter, COL_ENABLE)[0]
		model.set(iter, COL_ENABLE, not active)

	def activate_rule_row(self, treeview, path, column):
		self.toggle_column_enable(path)

	def toggle_enable_rule(self, cell, path):
		self.toggle_column_enable(path)

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
		script = "lunch %s-%s"%(product, variant)
		script += ";" + "export OUT_DIR=" + "-".join(("out", product, variant))
		if self.ui.get_object("btn_ccache").get_active():
			script += ";" + "export USE_CCACHE=1"
		make_opts = []

		if self.ui.get_object("btn_parallel_build").get_active():
			cpus = os.sysconf("SC_NPROCESSORS_ONLN")
			make_opts.append("-j%d"%(cpus + 1))
		if self.ui.get_object("btn_clean").get_active():
			make_opts.append("clean")
		if self.ui.get_object("btn_verbose").get_active():
			make_opts.append("showcommands")

		model = self.ui.get_object("liststore_rules")
		def model_iter(model, path, iter, user_data):
			active, rule = model.get(iter, COL_ENABLE, COL_RULE)
			if active:
				make_opts.append(rule)

		model.foreach(model_iter, None)

		script += ";" + "make bootimage " + " ".join(make_opts)
		print 'run:', script
		success, pid = self.terminal.fork_command_full(
			Vte.PtyFlags.NO_WTMP |
				Vte.PtyFlags.NO_UTMP |
				Vte.PtyFlags.NO_LASTLOG,
			self.sourceTop,
			utils.build_cmd_args(script),
			(),
			GLib.SpawnFlags.SEARCH_PATH, None, None)
		self.pid = pid

	def build_terminated(self, terminal):
		print terminal.get_child_exit_status()
		#pid, status = os.waitpid(self.pid, os.WNOHANG)
		#print pid, status
		self.pid = None
		self.build_btn.set_active(False)
