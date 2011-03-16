import sys
import os
from threading import Thread
from time import sleep

import pygtk
pygtk.require('2.0')
import gtk
import gobject

from .SftpManager import SftpManager
from .SftpSystemController import SftpSystemController
from .SftpSystemController import get_config_fields as get_controller_config_fields
from .exception import SftpException
from .helper import open_file_browser

def create_button(text, stock_image_id=None, onclick=None):
	hbox = gtk.HBox()
	
	if (stock_image_id is not None):
		icon = gtk.Image()
		icon.set_from_stock(stock_image_id, gtk.ICON_SIZE_SMALL_TOOLBAR)
			
		hbox.pack_start(icon)
			
	label = gtk.Label()
	label.set_text(text)
	label.set_alignment(0, 0)
				
	hbox.pack_start(label)
		
	btn = gtk.Button()
	btn.add(hbox)
		
	if (onclick is not None):
		btn.connect("clicked", onclick)
		
	return btn


class SftpMan:

	def handler_destroy(self, widget, data=None):
		gtk.main_quit()


	def handler_open_by_id(self, btn, system_id):
		controller = SftpSystemController.create_by_id(self._manager, system_id)
		if controller.is_mounted:
			open_file_browser(controller.mount_point_local)
	
	
	def handler_mount_by_id(self, btn, system_id):
		controller = SftpSystemController.create_by_id(self._manager, system_id)
		controller.mount()
		
		self.refresh_list()
	
	
	def handler_unmount_by_id(self, btn, system_id):
		controller = SftpSystemController.create_by_id(self._manager, system_id)
		controller.unmount()
		
		self.refresh_list()
	
	
	def handler_mount_all(self, btn):
		for system_id in self._manager.get_available_ids():
			controller = SftpSystemController.create_by_id(self._manager, system_id)
			controller.mount()
			
		self.refresh_list()
	
	
	def handler_unmount_all(self, btn):
		for system_id in self._manager.get_mounted_ids():
			controller = SftpSystemController.create_by_id(self._manager, system_id)
			controller.unmount()
		
			self.refresh_list()
	
	
	def handler_create_new(self, btn):
		controller = SftpSystemController(self._manager, "new")
 		
 		RecordRenderer(controller, self).render()


	def handler_edit(self, btn, system_id):
		controller = SftpSystemController.create_by_id(self._manager, system_id)
 		
 		RecordRenderer(controller, self).render()


	def refresh_list(self):
		ids_mounted = self._manager.get_mounted_ids()
		
		for childHbox in self._vbox_list.get_children():
			self._vbox_list.remove(childHbox)
		
		separator = gtk.HBox()
		separator.set_size_request(10, 25)
		self._vbox_list.pack_start(separator, False)
		
		ids_available = self._manager.get_available_ids()
		for system_id in ids_available:
			is_mounted = system_id in ids_mounted
			
			hbox = gtk.HBox()
			
			icon = gtk.Image()
			icon.set_from_stock(gtk.STOCK_YES if is_mounted else gtk.STOCK_NO, gtk.ICON_SIZE_SMALL_TOOLBAR)
			hbox.pack_start(icon)

			# Sftp system id
			label = gtk.Label(system_id)
			label.set_alignment(0, 0)
			label.set_size_request(150, 35)
			hbox.pack_start(label)
			
			
			# Open/Mount button
			if (is_mounted):
				btn_mount_or_open = create_button("Open", gtk.STOCK_OPEN)
				btn_mount_or_open.connect("clicked", self.handler_open_by_id, system_id)
			else:
				btn_mount_or_open = create_button("Mount", gtk.STOCK_CONNECT)
				btn_mount_or_open.connect("clicked", self.handler_mount_by_id, system_id)


			# Unmount button			
			btn_unmount = create_button("Unmount", gtk.STOCK_DISCONNECT)
			if (not is_mounted):
				btn_unmount.set_sensitive(False)
			else:
				btn_unmount.connect("clicked", self.handler_unmount_by_id, system_id)
			
			
			# Edit button
			btn_edit = create_button("Edit", gtk.STOCK_EDIT)
			btn_edit.connect("clicked", self.handler_edit, system_id)
			
			hbox.pack_start(btn_mount_or_open)
			hbox.pack_start(btn_unmount)
			hbox.pack_start(btn_edit)
			
			self._vbox_list.pack_start(hbox, False)
		
		if len(ids_available) == 0:
			label = gtk.Label()
			label.set_text("No sftp systems added yet.")
			label.set_justify(gtk.JUSTIFY_CENTER)
			
			self._vbox_list.pack_start(label)
			
		self._vbox_list.show_all()


	def destroy(self, widget, data=None):
		gtk.main_quit()
   
   
	def _create_tool_box(self):
		""" This contains the main toolbar"""
		hbox = gtk.HBox()

		hbox.pack_start(create_button("New", gtk.STOCK_ADD, onclick=self.handler_create_new))
		hbox.pack_start(create_button("Mount all", gtk.STOCK_CONNECT, onclick=self.handler_mount_all))
		hbox.pack_start(create_button("Unmount all", gtk.STOCK_CONNECT, onclick=self.handler_unmount_all))
		
		return hbox
	
	
	def _create_list_container(self):
		""" This would contain the sftp systems list"""
		self._vbox_list = gtk.VBox()
   		self.refresh_list()
   		
   		return self._vbox_list
   	
   	@property
   	def list_container(self):
   		return self._vbox_list
   	
   	
   	def _create_record_container(self):
   		self._hbox_record = gtk.HBox()
   		
   		return self._hbox_record
   	
   	@property
   	def record_container(self):
   		return self._hbox_record
   	
   	
	def __init__(self):
		self._manager = SftpManager()
		
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_title("SftpMan")
		self.window.resize(550, 350)
		self.window.set_position(gtk.WIN_POS_CENTER)
		self.window.connect("destroy", self.handler_destroy)
		
		icon_file = os.path.join(os.path.dirname(__file__), '..', 'sftpman.png')
		if os.path.exists(icon_file):
			self.window.set_icon_from_file(icon_file)		

		vbox_main = gtk.VBox()
		vbox_main.pack_start(self._create_tool_box(), False)
		vbox_main.pack_start(self._create_list_container())
		vbox_main.pack_start(self._create_record_container())

		self.window.add(vbox_main)
		self.window.show_all()
		
		self._in_list_mode = True
		
		# we need to do this if we want to use threads in our GTK app
		gobject.threads_init()
		
		def list_periodic_refresher():
			while True:
				# trying to update the GTK GUI from a thread causes a segmentation fault
				# this is the proper way to do it
				if self._in_list_mode:
					gobject.idle_add(self.refresh_list)
				sleep(15)

		refresher_thread = Thread(target=list_periodic_refresher)
		refresher_thread.daemon = True
		refresher_thread.start()


	def main(self):
		gtk.main()



class RecordRenderer(object):
	"""Deals with the record form (Adding/Editing sftp systems)."""
	
	def __init__(self, controller, program_obj):
		self._controller = controller
		self._program_obj = program_obj
		self._record_container = program_obj.record_container
		
		self._program_obj.list_container.hide()
		self._program_obj._in_list_mode = False
	
	
	def get_fields(self):
		return get_controller_config_fields(self._controller.is_added)


	def render_textbox(self, field_info):
		textbox = gtk.Entry()
		textbox.set_text(str(self._controller.config_get(field_info["id"], field_info["defaultValue"])))
		textbox.set_size_request(250, 25)

		if "isDisabled" in field_info and field_info["isDisabled"] is True:
			textbox.set_sensitive(False)
		
		return textbox


	def get_value_textbox(self, widget):
		return widget.get_text()
	
	
	def render_filepath(self, field_info):
		textbox = gtk.Entry()
		textbox.set_text(str(self._controller.config_get(field_info["id"], field_info["defaultValue"])))


		def filechooserStart(btn):
			buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK)
			filechooser = gtk.FileChooserDialog("Select your private ssh key file:", None, gtk.FILE_CHOOSER_ACTION_OPEN, buttons)
			filechooser.set_current_folder(os.path.expanduser("~"))
			
			if filechooser.run() == gtk.RESPONSE_OK:
				textbox.set_text(filechooser.get_filename())
			
			filechooser.destroy()
		
		btn_browse = create_button("..", onclick=filechooserStart)
		btn_browse.set_size_request(20, 25)
		
		hbox = gtk.HBox()
		hbox.pack_start(textbox)
		hbox.pack_start(btn_browse, False)
		hbox.set_size_request(250, 25)
		
		return hbox
	
	
	def get_value_filepath(self, widget):
		textbox = widget.get_children()[0]

		return textbox.get_text()
	
	
	def render_options(self, field_info):
		options = self._controller.config_get(field_info["id"], field_info["defaultValue"])
		
		textbox = gtk.Entry()
		textbox.set_text(", ".join(options))
		textbox.set_size_request(250, 25)

		return textbox


	def get_value_options(self, widget):
		return [option.strip() for option in widget.get_text().split(",")]
	
	
	def handler_save(self, btn, fields):
		is_mounted_before_save = self._controller.is_mounted
		
		self._controller.unmount()
		
		for field_info in fields:
			widget = field_info["widget"]
			
			get_value_callback = getattr(self, "get_value_%s" % field_info["type"], None)
			if get_value_callback is None:
				raise SftpException("Cannot get value for field type: %s" % field_info["type"])
			
			self._controller.config_set(field_info["id"], get_value_callback(widget))
	
		self._controller.config_write()

		if is_mounted_before_save:
			self._controller.mount()

		self.close()
	
	
	def handler_cancel(self, btn):
		self.close()
	
	
	def handler_delete(self, btn):
		dialog = gtk.MessageDialog(self._program_obj.window, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, "Are you sure?")
		dialog.set_title("Delete %s?" % self._controller.id)
		dialog.show()

		response = dialog.run()
		dialog.destroy()
		if response == gtk.RESPONSE_YES:
			self._controller.unmount()
			self._controller.config_delete()
			self.close()
	
	
	def close(self):
		# Get rid of all the fields we rendered in the record container,
		# but preserve the container for later use
		for child in self._record_container.get_children():
			self._record_container.remove(child)
		
		
		self._program_obj.refresh_list()
		self._program_obj.list_container.show()
		self._program_obj._in_list_mode = True
	
	
	def render(self):
		for child in self._record_container.get_children():
			self._record_container.remove(child)
			
		vbox = gtk.VBox()
		
		title = gtk.Label()
		title_label = "System editing" if self._controller.is_added else "System adding"
		title.set_markup("<big>%s</big>" % title_label)
		vbox.pack_start(title)
		vbox.pack_start(gtk.VSeparator())
		
		fields = []
		for field_info in self.get_fields():
			hbox = gtk.HBox()
			
			label = gtk.Label()
			label.set_text(field_info["title"])
			label.set_alignment(0, 0)
			label.set_size_request(80, 20)
			
			hbox.pack_start(label)
			
			render_callback = getattr(self, "render_%s" % field_info["type"], None)
			if render_callback is None:
				raise SftpException("Missing renderer for field type %s" % field_info["type"])
			
			widget = render_callback(field_info)
			
			field_info["widget"] = widget
			
			hbox.pack_start(widget)
			
			vbox.add(hbox)
			
			fields.append(field_info)
		
		# Form actions (Save, Delete, etc..)
		hbox = gtk.HBox()
		hbox.set_size_request(width=-1, height=25)
		
				
		btn_save = create_button("Save", gtk.STOCK_SAVE)
		btn_save.connect("clicked", self.handler_save, fields)
		hbox.pack_start(btn_save)
		
		btn_cancel = create_button("Cancel", gtk.STOCK_CANCEL, onclick=self.handler_cancel)
		hbox.pack_start(btn_cancel)

		if self._controller.is_added:
			btn_delete = create_button("Delete", gtk.STOCK_DELETE, onclick=self.handler_delete)
			hbox.pack_start(btn_delete)
		
		vbox.add(hbox)
		
		self._record_container.add(vbox)
		self._record_container.show_all()
		
		if not self._controller.is_added:
			# Give focus to the first field (which is "Id/Name")
			fields[0]["widget"].grab_focus()


def start():
	sftpman = SftpMan()
	sftpman.main()
