from gi.repository import GLib, GObject, Gtk, Vte
import utils
import os, sys

COL_ENABLE, COL_RULE, COL_DESCRITION = range(3)
COL_PRODUCT, COL_VARIANT, COL_SCRIPT, COL_TIME, COL_SOURCE = range(5)

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

		self.queue_btn = self.ui.get_object("btn_queue_add")
		self.queue_btn.connect("clicked", self.add_queue)

		self.ui.get_object("btn_retry").connect("clicked", self.retry_build)

		treeview = self.ui.get_object("treeview_rules")
		treeview.connect("row-activated", self.activate_rule_row)
		renderer = self.ui.get_object("renderer_enable")
		renderer.connect("toggled", self.toggle_enable_rule)

		chooser = self.ui.get_object("chooser_source_top")
		chooser.connect("file-set", self.choose_source_top)

		model = self.ui.get_object("liststore_queue")

		treeview = self.ui.get_object("treeview_queue")
		treeview.connect("cursor-changed", self.queue_cursor_changed, model)

		self.ui.get_object("btn_queue_remove").connect("clicked",
				self.remove_queue, treeview, model)
		self.ui.get_object("btn_queue_move_up").connect("clicked",
				self.move_up_queue, treeview, model)
		self.ui.get_object("btn_queue_move_down").connect("clicked",
				self.move_down_queue, treeview, model)

		self.pid = None
		self.win.show_all()

		self.set_ui_enable(False)

	def choose_source_top(self, chooser):
		directory = chooser.get_filename()
		self.set_source_top(directory)

	def set_choose_directory(self, directory):
		chooser = self.ui.get_object("chooser_source_top")
		chooser.set_filename(directory)

	def set_ui_enable(self, enable):
		for name in ("btn_build", "btn_queue_add", "combobox_product", "combobox_variant"):
			w = self.ui.get_object(name)
			w.set_sensitive(enable)

	def set_source_top(self, directory):
		if not utils.check_source_top(directory):
			self.set_ui_enable(False)
			return False

		products = utils.get_product_list(directory)
		if not products:
			self.set_ui_enable(False)
			return False
		combo = self.ui.get_object("combobox_product")
		combo.remove_all()
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
			product = self.ui.get_object("combobox_product").get_active_text()
			variant = self.ui.get_object("combobox_variant").get_active_text()
			script = self.build_make_opts()
			directory = self.sourceTop
			self.run_build(directory, product, variant, script)
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
		if self.pid:
			import signal
			os.kill(self.pid, signal.SIGTERM)

	def build_make_opts(self):
		make_opts = []
		if self.ui.get_object("btn_parallel_build").get_active():
			cpus = os.sysconf("SC_NPROCESSORS_ONLN")
			make_opts.append("-j%d"%(cpus + 1))
		if self.ui.get_object("btn_clean").get_active():
			make_opts.append("clean")
		if self.ui.get_object("btn_verbose").get_active():
			make_opts.append("showcommands")
		if self.ui.get_object("btn_odex").get_active():
			make_opts.append("WITH_DEXPREOPT=true")
		if self.ui.get_object("btn_ccache").get_active():
			make_opts.append("USE_CCACHE=1")

		model = self.ui.get_object("liststore_rules")
		def model_iter(model, path, iter, user_data):
			active, rule = model.get(iter, COL_ENABLE, COL_RULE)
			if active:
				make_opts.append(rule)

		model.foreach(model_iter, None)
		return "make " + " ".join(make_opts)


	def add_queue(self, button):
		product = self.ui.get_object("combobox_product").get_active_text()
		variant = self.ui.get_object("combobox_variant").get_active_text()
		script = self.build_make_opts()
		model = self.ui.get_object("liststore_queue")
		directory = self.sourceTop

		treeiter = model.insert(0)

		for col, value in ((COL_PRODUCT, product),
				(COL_VARIANT, variant),
				(COL_SCRIPT, script),
				(COL_TIME, 0),
				(COL_SOURCE, directory)):
			model.set_value(treeiter, col, value)

	def remove_queue(self, button, treeview, model):
		path, col = treeview.get_cursor()
		iter = model.get_iter(path)

		model.remove(iter)

		for name in ("remove", "move_up", "move_down"):
			self.ui.get_object("btn_queue_"+name).set_sensitive(False)

	def move_up_queue(self, button, treeview, model):
		path, col = treeview.get_cursor()
		iter = model.get_iter(path)

		prev = path.copy()
		if prev.prev():
			model.swap(iter, model.get_iter(prev) )
			self.queue_cursor_changed(treeview, model)

	def move_down_queue(self, button, treeview, model):
		path, col = treeview.get_cursor()
		iter = model.get_iter(path)

		next = path.copy()
		next.next()

		model.swap(iter, model.get_iter(next) )
		self.queue_cursor_changed(treeview, model)

	def queue_cursor_changed(self, treeview, model):
		path, col = treeview.get_cursor()
		if not col:
			for name in ("remove", "move_up", "move_down"):
				self.ui.get_object("btn_queue_"+name).set_sensitive(False)
			return

		self.ui.get_object("btn_queue_remove").set_sensitive(True)

		prev = path.copy()
		self.ui.get_object("btn_queue_move_up").set_sensitive(prev.prev())

		iter = model.get_iter(path)
		next = bool(model.iter_next(iter))
		self.ui.get_object("btn_queue_move_down").set_sensitive(next)

	def retry_build(self, button):
		source = self.ui.get_object("label_source").get_text()
		product = self.ui.get_object("label_product").get_text()
		variant = self.ui.get_object("label_variant").get_text()
		script = self.ui.get_object("label_command").get_text()
		self.run_build(source, product, variant, script)

	def run_build(self, directory, product, variant, script):
		self.build_btn.set_label("Stop")
		self.ui.get_object("spinner1").start();
		self.terminal.reset(True, True)

		self.ui.get_object("label_source").set_text(directory)
		self.ui.get_object("label_product").set_text(product)
		self.ui.get_object("label_variant").set_text(variant)
		self.ui.get_object("label_command").set_text(script)

		script = utils.build_lunch(product, variant) + ";" + script

		print 'run:', script
		success, pid = self.terminal.fork_command_full(
			Vte.PtyFlags.NO_WTMP |
				Vte.PtyFlags.NO_UTMP |
				Vte.PtyFlags.NO_LASTLOG,
			directory,
			utils.build_cmd_args(script),
			(),
			GLib.SpawnFlags.SEARCH_PATH, None, None)
		self.pid = pid

		self.ui.get_object("notebook1").set_current_page(3)
		self.ui.get_object("btn_retry").set_sensitive(False);

	def build_terminated(self, terminal):
		status = terminal.get_child_exit_status()
		if True or status == 0:
			model = self.ui.get_object("liststore_queue")
			iter = model.get_iter_first()
			if iter:
				product, variant, script, directory = model.get(iter,
					COL_PRODUCT, COL_VARIANT, COL_SCRIPT, COL_SOURCE)
				self.run_build(directory, product, variant, script)
				model.remove(iter)
				return

			self.ui.get_object("label_source").set_text("")
			self.ui.get_object("label_product").set_text("")
			self.ui.get_object("label_variant").set_text("")
			self.ui.get_object("label_command").set_text("")
		else:
			# handle error
			self.ui.get_object("btn_retry").set_sensitive(True);
			pass
		self.pid = None
		self.build_btn.set_active(False)
		self.ui.get_object("spinner1").stop();
		self.build_btn.set_label("Build")


