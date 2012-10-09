#!/usr/bin/env python
# -*- coding: utf-8 -*-

# utils.py by:
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


import pango
import gobject
import gtk
import api

GROUPS = ('1A', '1B', '1C', '2A', '2B', '2C', '3A', '3B')


class HomeWorksList(gtk.TreeView):
    '''Lista de arbol con ls tareas domiciliarias'''
    def __init__(self, hwview, notebook, sftp):
        super(HomeWorksList, self).__init__()

        self._model = gtk.ListStore(str, str, str, str)
        self.set_model(self._model)

        # Cells
        date = gtk.CellRendererText()
        title = gtk.CellRendererText()
        evaluation = gtk.CellRendererText()
        student = gtk.CellRendererText()

        # Columns
        col = gtk.TreeViewColumn('Fecha')
        col.pack_start(date)
        col.add_attribute(date, 'text', 0)
        self.append_column(col)

        col = gtk.TreeViewColumn('Titulo')
        col.pack_start(title)
        col.add_attribute(title, 'text', 1)
        self.append_column(col)

        col = gtk.TreeViewColumn('Evaluación')
        col.pack_start(evaluation)
        col.add_attribute(evaluation, 'text', 2)
        self.append_column(col)

        col = gtk.TreeViewColumn('Alumno')
        col.pack_start(student)
        col.add_attribute(student, 'text', 3)
        self.append_column(col)

        # HomeWorks list
        self._hwlist = []
        self._hwview = hwview
        self._hwview.connect('open', self._open_homework)
        self._hwview.connect('save', self._save_homework)
        self._notebook = notebook
        self.group = GROUPS[0]

        self._sftp = sftp
        self.refresh()

        #
        self.connect("row-activated", self._double_click)
        self.show_all()

    def refresh(self):
        self._model.clear()
        self._hwlist = api.get_homeworks(self._sftp, self.group)

        keys = self._hwlist.keys()
        keys.sort()
        for hw in keys:
            date, comments, evaluation, student, mimetype, extension =\
                                                                self._hwlist[hw]
            try:
                evaluation = evaluation.split('|')[0]
            except:
                evaluation = 'No evaluado'
            self._model.append([date, hw, evaluation, student])

    def _double_click(self, widget, treepath, column):
        keys = self._hwlist.keys()
        keys.sort()
        homework = keys[treepath[0]]
        date, comments, evaluation, student, mimetype, extension =\
                                                          self._hwlist[homework]
        self._hwview.set_data(homework,
                              comments,
                              evaluation,
                              student,
                              self.group)
        self._notebook.set_current_page(1)

    def _open_homework(self, widget, homework):
        '''Abre tarea domiciliaria'''
        extension = self._hwlist[homework][-1]
        api.get_homework(self._sftp, self.group, homework, extension,
                         None, True)

    def _save_homework(self, widget, homework):
        '''Guarda la tarea domiciliaria'''
        f = FileChooser()
        api.get_homework(self._sftp, self.group, homework, f.file_path,
                         False)


class HomeWorkView(gtk.VBox):
    
    __gsignals__ = {'open': (gobject.SIGNAL_RUN_FIRST, None, [str]),
                    'save': (gobject.SIGNAL_RUN_FIRST, None, [str]),
                    }

    def __init__(self):
        super(HomeWorkView, self).__init__()

        self.set_border_width(5)

        hbox = gtk.HBox()
        self.pack_start(hbox, True)

        previewbox = gtk.VBox()
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size('document.png', 150, 150)
        preview = gtk.image_new_from_pixbuf(pixbuf)
        previewbox.pack_start(preview, False)
        hbox.pack_start(previewbox, False, padding=5)

        vbox = gtk.VBox()
        hbox.pack_end(vbox, True, padding=20)

        self.title_label = gtk.Label()
        self.title_label.set_use_markup(True)
        vbox.pack_start(self.title_label, False)

        desc_box = gtk.VBox()
        self.desc_label = gtk.Label()
        self.desc_label.set_use_markup(True)
        self.desc_label.set_line_wrap(True)
        desc_box.pack_start(self.desc_label, False, padding=15)
        vbox.pack_start(desc_box, True)

        bbox = gtk.HBox()

        fvbox = gtk.VBox()
        self.evaluation_n = Entry('Nota')
        fvbox.pack_start(self.evaluation_n, False, True, 0)

        frame = gtk.Frame()
        frame.set_label('Juicio')
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.evaluation_t = gtk.TextView()
        self.evaluation_t.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        scroll.add(self.evaluation_t)
        frame.add(scroll)
        self.evaluation_t.set_size_request(250, 100)
        fvbox.pack_start(frame, True, False, 5)

        bbox.pack_start(fvbox, False)

        button_box = gtk.VBox(spacing=5)

        self.student_label = gtk.Label()
        self.student_label.set_use_markup(True)
        button_box.pack_start(self.student_label, False)

        open_btn = gtk.Button('Abrir')
        open_btn.connect('clicked', self._open_clicked_cb)
        save_btn = gtk.Button('Guardar')
        save_btn.connect('clicked', self._save_clicked_cb)
        button_box.pack_end(save_btn, False)
        button_box.pack_end(open_btn, False)

        bbox.pack_end(button_box, False, True, 5)
        self.pack_end(bbox, False)

        self.show_all()

    def set_data(self, title, comments, evaluation, student, group):
        '''Devuelve los datos de una tarea domiciliaria'''
        title_markup = '<span font_desc="18"><b>%s</b></span>' % title
        self.title_label.set_markup(title_markup)
        self.desc_label.set_markup('<i>%s</i>' % comments)
        self.student_label.set_markup('<b>%s</b>' % (student))
        try:
            number, text = evaluation.split('|', 2)
        except:
            number, text = 'No evaluado', 'No evaluado'
        self.evaluation_n.set_text(number)
        self.evaluation_t.get_buffer().set_text(text)

    def get_evaluation(self):
        '''Devuelve la evaluacion'''
        number = self.evaluation_n.get_text()
        textbuffer = self.evaluation_t.get_buffer()
        text = textbuffer.get_text(textbuffer.get_start_iter(),
                                   textbuffer.get_end_iter(), True)
        title = self.title_label.get_text()

        if title:
            return title, '%s|%s' % (number, text)
        else:
            return None, None

    def _open_clicked_cb(self, widget):
        self.emit('open', self.title_label.get_text())

    def _save_clicked_cb(self, widget):
        self.emit('save', self.title_label.get_text())


class Entry(gtk.Entry):
    '''Entrada de texto'''
    def __init__(self, text):
        gtk.Entry.__init__(self, max=0)

        self.set_text(text)
        self.connect("focus-in-event", self._focus_in)
        self.connect("focus-out-event", self._focus_out)
        self.modify_font(pango.FontDescription("italic"))

        self._text = text

        self.show_all()

    def _focus_in(self, widget, event):
        if widget.get_text() == self._text:
            widget.set_text("")
            widget.modify_font(pango.FontDescription(""))

    def _focus_out(self, widget, event):
        if widget.get_text() == "":
            widget.set_text(self._text)
            widget.modify_font(pango.FontDescription("italic"))


class FileChooser(gtk.FileChooserDialog):
    '''Selector de archivos'''
    def __init__(self):
        gtk.FileChooserDialog.__init__(self,
                                       "Guardar archivo",
                                       None,
                                       gtk.FILE_CHOOSER_ACTION_SAVE,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_SAVE, gtk.RESPONSE_OK))

        self.set_default_response(gtk.RESPONSE_OK)

        response = self.run()
        if response == gtk.RESPONSE_OK:
            self.file_path = self.get_filename()
        self.destroy()


class Canvas(gtk.VBox):

    def __init__(self, sftp=None):
        super(Canvas, self).__init__()

        self.sftp = sftp

        notebook = gtk.Notebook()
        notebook.set_show_tabs(False)

        main = gtk.ScrolledWindow()
        main.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)

        self.homework_view = HomeWorkView()
        self._homeworks_list = HomeWorksList(self.homework_view, notebook,
                                             self.sftp)

        main.add(self._homeworks_list)
        notebook.append_page(main, gtk.Label())

        notebook.append_page(self.homework_view, gtk.Label())

        toolbar = gtk.Toolbar()
        self.pack_start(toolbar, False, True, 0)

        refresh = gtk.ToolButton()
        refresh.connect('clicked', lambda w: self._homeworks_list.refresh())
        refresh.set_stock_id(gtk.STOCK_REFRESH)
        toolbar.insert(refresh, -1)

        go_back = gtk.ToolButton()
        go_back.connect('clicked', lambda w: notebook.set_current_page(0))
        go_back.set_stock_id(gtk.STOCK_GO_BACK)
        go_back.set_sensitive(False)
        toolbar.insert(go_back, -1)

        separator = gtk.SeparatorToolItem()
        separator.set_draw(False)
        separator.set_expand(True)
        toolbar.insert(separator, -1)

        toolitem = gtk.ToolItem()
        label = gtk.Label('Seleccione un grupo:  ')
        toolitem.add(label)
        toolbar.insert(toolitem, -1)

        toolitem = gtk.ToolItem()
        combobox = gtk.combo_box_new_text()
        combobox.connect('changed', self._group_changed)
        for g in GROUPS:
            combobox.append_text(g)
        combobox.set_active(0)
        toolitem.add(combobox)
        toolbar.insert(toolitem, -1)

        self._tbitems = (refresh, go_back, combobox, label)

        notebook.connect('switch-page', self._current_page_changed_cb)

        self.pack_end(notebook, True, True, 0)

        self.show_all()
        notebook.set_current_page(0)

    def _current_page_changed_cb(self, widget, o, page):
        self._tbitems[0].set_sensitive(page == 0)
        self._tbitems[1].set_sensitive(page == 1)
        self._tbitems[2].set_sensitive(page == 0)
        self._tbitems[3].set_sensitive(page == 0)

        if page == 0:
            homework, evaluation = self.homework_view.get_evaluation()
            if homework:
                api.evaluate_homework(self.sftp, self._homeworks_list.group,
                                      homework, evaluation)
                self._homeworks_list.refresh()

    def _group_changed(self, widget):
        self._homeworks_list.group = widget.get_active_text()
        self._homeworks_list.refresh()


if __name__ == '__main__':
    window = gtk.Window()
    window.resize(400, 300)
    window.add(Canvas(api.connect_to_server()))
    window.show_all()
    gtk.main()
