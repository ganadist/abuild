from gi.repository import GLib, GObject, Gtk, Vte
import utils

class MainWindow:
	def __init__(self):
		self.ui = Gtk.Builder()
		self.ui.add_from_file("data/ui/main.ui")
		self.win = self.ui.get_object("window1")
		self.win.connect("destroy", Gtk.main_quit)
		self.win.show_all()
		self.setSourceTop("/home/ganadist/android/src")

	def setSourceTop(self, directory):
		products = utils.getProductsList(directory)
		combo = self.ui.get_object("combobox_product")
		if products:
			for product in products:
				combo.append_text(product)
			combo.set_active(0)
		combo = self.ui.get_object("combobox_variant")
		combo.set_active(0)

