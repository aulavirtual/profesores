#!/usr/bin/env python
# -*- coding: utf-8 -*-

# window.py by:
#    Agustin Zubiaga <aguz@sugarlabs.org>
#    Cristhofer Travieso <cristhofert97@gmail.com>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import sys
import gtk
import pango

import api
import widgets
import homeworks

from widgets import GROUPS

GROUPS_DIR = os.path.join('/home/servidor', 'Groups')


class Window(gtk.Window):

    def __init__(self):
        gtk.Window.__init__(self)

        self.set_title('Aula Virtual')
        self.set_border_width(10)
        self.resize(800, 600)
        self.connect('destroy', self.exit)

        self._path = None
        self._name = ''
        self._last_name = ''

        self.show_all()

    def exit(self, widget):
        self.sftp.close()
        sys.exit(0)

    def _do_gui(self):
        notebook = gtk.Notebook()
        self.add(notebook)

        # Documents canvas
        main_container = gtk.VBox()
        main_container.set_border_width(10)
        notebook.append_page(main_container, gtk.Label('Documentos'))

        topbox = gtk.HBox()
        main_container.pack_start(topbox, False, False, 0)

        self._title = widgets.Entry('Escriba el titulo aqui')
        topbox.pack_start(self._title, True, True, 0)

        open_btn = gtk.Button(stock=gtk.STOCK_OPEN)
        open_btn.connect('clicked', lambda w: widgets.FileChooser(self))
        topbox.pack_end(open_btn, False, True, 5)

        label = gtk.Label('Descripcion y/o Resumen:')
        main_container.pack_start(label, False, True, 10)

        self._description = gtk.TextView()
        self._description.set_property('wrap-mode', gtk.WRAP_WORD)
        main_container.pack_start(self._description, True, True, 5)

        bottom = gtk.HBox()
        main_container.pack_end(bottom, False, True, 5)

        self._groups_selector = widgets.GroupChooser()
        bottom.pack_start(self._groups_selector, False, True, 0)

        save = gtk.Button(stock=gtk.STOCK_SAVE)
        save.connect('clicked', self.save_cb)
        bottom.pack_end(save, False, True, 0)

        self.sftp = api.connect_to_server()

        main_container.show_all()

        # HomeWorks canvas
        hwcanvas = homeworks.Canvas(self.sftp)
        notebook.append_page(hwcanvas, gtk.Label('Tareas domiciliarias'))

        notebook.show_all()
        notebook.set_current_page(0)

    def _sign_up(self):
        vbox = gtk.VBox()
        vbox.set_border_width(20)

        title = gtk.Label('Registrate en Aula Virtual')
        title.modify_font(pango.FontDescription('bold 18'))
        vbox.pack_start(title, False, padding=40)

        note = gtk.Label('<span foreground="#FF0000"><i>\
                      * Por favor ingresa los datos correctamente.</i></span>')
        note.set_use_markup(True)
        vbox.pack_start(note, False, True, padding=5)

        hbox = gtk.HBox()
        vbox.pack_start(hbox, False, padding=10)

        label = gtk.Label("Nombre: ")
        hbox.pack_start(label, False, padding=10)

        entry = gtk.Entry()
        entry.connect('changed', self._set_text)
        hbox.pack_start(entry, True, padding=0)

        hbox1 = gtk.HBox()
        hbox1.set_border_width(20)

        label = gtk.Label("Apellido:  ")
        hbox1.pack_start(label, False, padding=0)

        entry = gtk.Entry()
        entry.connect('changed', self._set_text, False)
        hbox1.pack_start(entry, True, padding=0)

        vbox.pack_start(hbox1, False, padding=10)

        hbox2 = gtk.HBox()
        vbox.pack_start(hbox2, False, padding=10)

        label_combo = gtk.Label("Elige tu grupo: ")
        hbox2.pack_start(label_combo, False, True, padding=10)

        combo = gtk.ComboBox()
        liststore = gtk.ListStore(str)
        combo.set_model(liststore)
        cell = gtk.CellRendererText()
        combo.pack_start(cell, True)
        combo.add_attribute(cell, 'text', 0)
        hbox2.pack_start(combo, False, True, padding=10)

        for group in GROUPS:
            liststore.append([group])
        combo.set_active(0)

        accept = gtk.Button('Aceptar')
        accept.connect('clicked', self._accept_clicked, combo, entry, vbox)
        box = gtk.HBox()
        box.pack_end(accept, False)
        vbox.pack_start(box, False)

        self._canvas.add(vbox)
        self.show_all()

    def _set_text(self, widget, name=True):
        if name:
            self._name = widget.get_text()
        else:
            self._last_name = widget.get_text()

    def set_file(self, path):
        self._path = path
        self._title.set_text(os.path.split(path)[1])

    def save_cb(self, widget):
        title = self._title.get_text()

        _buffer = self._description.get_buffer()
        start = _buffer.get_start_iter()
        end = _buffer.get_end_iter()
        description = _buffer.get_text(start, end, True)

        group_id = self._groups_selector.get_active()
        group = GROUPS[group_id]

        if group_id == 0:
            dialog = gtk.MessageDialog(type=gtk.MESSAGE_ERROR)
            dialog.set_markup('<b>%s</b>' % 'No se ha elejido el grupo')
            dialog.format_secondary_text('Por favor elija uno')
            dialog.add_buttons(gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
            dialog.run()
            dialog.destroy()

        else:
            api.save_document(self.sftp, self._path, group, title, description)

            # Question:
            dialog = gtk.MessageDialog(type=gtk.MESSAGE_QUESTION)
            dialog.set_markup('<b>%s</b>' % '¡Documento guardado!')
            dialog.format_secondary_text(
                               '¿Desea enviar el mismo documento a más grupos?')
            dialog.add_buttons(gtk.STOCK_YES, gtk.RESPONSE_YES, gtk.STOCK_NO,
                               gtk.RESPONSE_NO)
            response = dialog.run()

            if response == gtk.RESPONSE_NO:
                self.clear()

            dialog.destroy()

    def clear(self):
        self._path = None
        self._title.set_text('')
        self._description.get_buffer().set_text('')
        self._groups_selector.set_active(0)


if __name__ == '__main__':
    window = Window()
    window._do_gui()
    gtk.main()
