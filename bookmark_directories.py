#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bookmark Directories Plugin for Terminator
==========================================
Version : 1.1.0

Features:
  ✓ Manual bookmarks with custom alias
  ✓ Recent directories (last 10, session)
  ✓ Frequent directories (parsed from bash/zsh history)
  ✓ Git repo auto-detection
  ✓ pushd / popd navigation stack (in-memory)
  ✓ Optional directory preview panel
  ✓ Smart search: prefix -> substring -> fuzzy
  ✓ Ctrl+B to open (cd mode)
  ✓ Ctrl+Right to open (pushd mode)
  ✓ Ctrl+Left for instant popd
  ✓ Language toggle: English (default) / Espanol

Installation:
  1. cp bookmark_directories.py ~/.config/terminator/plugins/
  2. Terminator -> Preferences -> Plugins -> enable "BookmarkDirectoriesPlugin"
  3. Restart Terminator
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango

import json
import os
import re
from collections import Counter, deque

import terminatorlib.plugin as plugin

AVAILABLE = ['BookmarkDirectoriesPlugin']

CFG_DIR        = os.path.expanduser('~/.config/terminator')
BOOKMARKS_FILE = os.path.join(CFG_DIR, 'bm_bookmarks.json')
CONFIG_FILE    = os.path.join(CFG_DIR, 'bm_config.json')

CAT_STACK     = 'stack'
CAT_BOOKMARKS = 'bookmarks'
CAT_RECENT    = 'recent'
CAT_FREQUENT  = 'frequent'
CAT_GIT       = 'git'

CAT_COLORS = {
    CAT_STACK:     '#c678dd',
    CAT_BOOKMARKS: '#4a9eff',
    CAT_RECENT:    '#888888',
    CAT_FREQUENT:  '#ff8c42',
    CAT_GIT:       '#6cc644',
}

GIT_SEARCH_ROOTS = [
    '~', '~/projects', '~/dev', '~/code',
    '~/workspace', '~/repos', '~/src',
]

# All UI strings in both languages
STRINGS = {
    'title_normal':             {'en': '🔖 Bookmark Directories',            'es': '🔖 Marcadores de Directorios'},
    'title_pushd':              {'en': '-> pushd -- Bookmark Directories',   'es': '-> pushd -- Marcadores de Directorios'},
    'menu_item':                {'en': '🔖 Bookmark Directories...',          'es': '🔖 Marcadores de Directorios...'},
    'search_placeholder':       {'en': 'Search by alias or path...   (Enter -> cd, Ctrl+Right -> pushd)', 'es': 'Buscar por alias o ruta...   (Enter -> cd, Ctrl+Der -> pushd)'},
    'search_placeholder_pushd': {'en': 'Search...   (Enter -> pushd, Esc -> cancel)', 'es': 'Buscar...   (Enter -> pushd, Esc -> cancelar)'},
    'btn_save_here':            {'en': '📌 Save here',                        'es': '📌 Guardar aqui'},
    'btn_save_here_tooltip':    {'en': 'Add current directory to bookmarks', 'es': 'Añadir el directorio actual a marcadores'},
    'btn_preview_tooltip':      {'en': 'Show / hide preview panel',          'es': 'Mostrar / ocultar vista previa'},
    'cat_stack':                {'en': '↕  Stack',                           'es': '↕  Stack'},
    'cat_bookmarks':            {'en': '📌 Bookmarks',                        'es': '📌 Marcadores'},
    'cat_recent':               {'en': '🕐 Recent',                           'es': '🕐 Recientes'},
    'cat_frequent':             {'en': '🔥 Frequent',                         'es': '🔥 Frecuentes'},
    'cat_git':                  {'en': '⎇  Git Repos',                       'es': '⎇  Git Repos'},
    'stack_label':              {'en': '<small><b>↕ Stack:</b></small>',      'es': '<small><b>↕ Stack:</b></small>'},
    'stack_empty':              {'en': '<small><i> (empty) </i></small>',     'es': '<small><i> (vacio) </i></small>'},
    'btn_cd':                   {'en': '▶  cd',                               'es': '▶  cd'},
    'btn_cd_tooltip':           {'en': 'Go to the selected directory',        'es': 'Ir al directorio seleccionado'},
    'btn_pushd':                {'en': '->  pushd',                           'es': '->  pushd'},
    'btn_pushd_tooltip':        {'en': 'Save current position to stack and go to selected directory', 'es': 'Guardar posicion actual en el stack e ir al directorio seleccionado'},
    'btn_popd':                 {'en': '<-  popd',                            'es': '<-  popd'},
    'btn_popd_tooltip':         {'en': 'Return to the previous directory in the stack', 'es': 'Volver al directorio anterior del stack'},
    'btn_delete':               {'en': '🗑  Delete',                          'es': '🗑  Eliminar'},
    'btn_delete_tooltip':       {'en': 'Remove selected bookmark (Bookmarks section only)', 'es': 'Eliminar el marcador seleccionado (solo en seccion Marcadores)'},
    'btn_cancel':               {'en': 'Cancel',                              'es': 'Cancelar'},
    'preview_frame':            {'en': '  Preview  ',                         'es': '  Vista previa  '},
    'preview_not_exists':       {'en': '⚠  Does not exist: ',                 'es': '⚠  No existe: '},
    'preview_no_permission':    {'en': '⛔  No read permission',               'es': '⛔  Sin permiso de lectura'},
    'preview_empty':            {'en': '(empty)',                             'es': '(vacio)'},
    'preview_more':             {'en': '\n... and {} more entries',           'es': '\n... y {} entradas mas'},
    'preview_summary':          {'en': '\n-- {} dirs, {} files',              'es': '\n-- {} dirs, {} archivos'},
    'new_bm_title':             {'en': '📌 New Bookmark',                     'es': '📌 Nuevo Marcador'},
    'new_bm_alias_label':       {'en': 'Alias:',                             'es': 'Alias:'},
    'new_bm_alias_placeholder': {'en': 'e.g. work, logs, my-project...',     'es': 'ej: trabajo, logs, mi-proyecto...'},
    'new_bm_path_label':        {'en': 'Path:',                              'es': 'Ruta:'},
    'new_bm_save':              {'en': '📌 Save',                             'es': '📌 Guardar'},
    'chooser_title':            {'en': 'Select directory',                   'es': 'Seleccionar directorio'},
    'chooser_select':           {'en': 'Select',                             'es': 'Seleccionar'},
}

CAT_LABEL_KEYS = {
    CAT_STACK:     'cat_stack',
    CAT_BOOKMARKS: 'cat_bookmarks',
    CAT_RECENT:    'cat_recent',
    CAT_FREQUENT:  'cat_frequent',
    CAT_GIT:       'cat_git',
}


class BookmarkDirectoriesPlugin(plugin.MenuItem):

    capabilities = ['terminal_menu']

    _dir_stack      = []
    _recent_dirs    = deque(maxlen=10)
    _last_known_dir = None
    _lang           = 'en'

    def __init__(self):
        plugin.MenuItem.__init__(self)
        os.makedirs(CFG_DIR, exist_ok=True)
        self._bookmarks     = self._load_bookmarks()
        self._config        = self._load_config()
        self._frequent_dirs = []
        self._git_repos     = []
        self._refresh_auto_data()

    # -- Translation ----------------------------------------------------------

    def _t(self, key, *args):
        lang = BookmarkDirectoriesPlugin._lang
        text = STRINGS.get(key, {}).get(lang, STRINGS.get(key, {}).get('en', key))
        return text.format(*args) if args else text

    def _cat_label(self, cat):
        return self._t(CAT_LABEL_KEYS[cat])

    # -- Persistence ----------------------------------------------------------

    def _load_bookmarks(self):
        if os.path.exists(BOOKMARKS_FILE):
            try:
                with open(BOOKMARKS_FILE, encoding='utf-8') as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            except Exception:
                pass
        return []

    def _save_bookmarks(self):
        with open(BOOKMARKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self._bookmarks, f, indent=2, ensure_ascii=False)

    def _load_config(self):
        defaults = {'show_preview': True}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, encoding='utf-8') as f:
                    defaults.update(json.load(f))
            except Exception:
                pass
        return defaults

    def _save_config(self):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2)

    # -- Auto data ------------------------------------------------------------

    def _refresh_auto_data(self):
        self._frequent_dirs = self._parse_history_frequent()
        self._git_repos     = self._find_git_repos()

    def _parse_history_frequent(self, top_n=10):
        paths = []
        for hist_file, is_zsh in [
            (os.path.expanduser('~/.bash_history'), False),
            (os.path.expanduser('~/.zsh_history'),  True),
        ]:
            if not os.path.exists(hist_file):
                continue
            try:
                with open(hist_file, errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if is_zsh:
                            m = re.match(r'^:\s*\d+:\d+;(.+)$', line)
                            line = m.group(1) if m else line
                        self._extract_cd(line, paths)
            except Exception:
                pass
        return [p for p, _ in Counter(paths).most_common(top_n)]

    def _extract_cd(self, line, paths):
        if not line.startswith('cd '):
            return
        raw = line[3:].strip().strip('"\'')
        if not raw or raw in ('-', '..', '.'):
            return
        expanded = os.path.expanduser(raw)
        if os.path.isdir(expanded):
            paths.append(expanded)

    def _find_git_repos(self, max_repos=25):
        repos, seen = [], set()
        for root_tpl in GIT_SEARCH_ROOTS:
            root = os.path.expanduser(root_tpl)
            if not os.path.isdir(root):
                continue
            try:
                for entry in os.scandir(root):
                    if not entry.is_dir() or entry.path in seen:
                        continue
                    if os.path.exists(os.path.join(entry.path, '.git')):
                        repos.append(entry.path)
                        seen.add(entry.path)
                    if len(repos) >= max_repos:
                        return sorted(repos)
            except PermissionError:
                pass
        return sorted(repos)

    # -- Current dir / send ---------------------------------------------------

    def _get_current_dir(self, terminal):
        cls = BookmarkDirectoriesPlugin
        if cls._last_known_dir and os.path.isdir(cls._last_known_dir):
            return cls._last_known_dir
        try:
            pid = terminal.vte.get_child_pid()
            if pid:
                return os.readlink('/proc/%d/cwd' % pid)
        except Exception:
            pass
        return os.path.expanduser('~')

    def _send_cmd(self, terminal, cmd):
        terminal.vte.feed_child((cmd + '\n').encode('utf-8'))

    def _send_cd(self, terminal, dest):
        BookmarkDirectoriesPlugin._last_known_dir = dest
        self._send_cmd(terminal, 'cd "%s"' % dest)

    # -- Plugin entry point ---------------------------------------------------

    def callback(self, menuitems, menu, terminal):
        item = Gtk.MenuItem(label=self._t('menu_item'))
        item.connect('activate', self._open_dialog, terminal)
        menuitems.append(item)
        window = terminal.get_toplevel()
        if isinstance(window, Gtk.Window):
            window.connect('key-press-event', self._on_key_press, terminal)

    def _on_key_press(self, _widget, event, terminal):
        ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        if not ctrl:
            return False
        if event.keyval == Gdk.KEY_b:
            self._open_dialog(None, terminal)
            return True
        if event.keyval == Gdk.KEY_Left:
            self._hotkey_popd(terminal)
            return True
        if event.keyval == Gdk.KEY_Right:
            self._hotkey_pushd(terminal)
            return True
        return False

    def _hotkey_popd(self, terminal):
        stack = BookmarkDirectoriesPlugin._dir_stack
        if stack:
            prev = stack.pop()
            self._track_recent(prev)
            self._send_cd(terminal, prev)

    def _hotkey_pushd(self, terminal):
        self._open_dialog(None, terminal, pushd_mode=True)

    # -- Main dialog ----------------------------------------------------------

    def _open_dialog(self, _widget, terminal, pushd_mode=False):
        self._refresh_auto_data()
        current_dir = self._get_current_dir(terminal)

        dlg = Gtk.Dialog(
            title=self._t('title_pushd') if pushd_mode else self._t('title_normal'),
            transient_for=terminal.get_toplevel(),
            flags=Gtk.DialogFlags.DESTROY_WITH_PARENT,
        )
        dlg.set_default_size(660, 540)

        box = dlg.get_content_area()
        box.set_spacing(0)
        box.set_border_width(0)

        top_bar, lw = self._build_top_bar(current_dir, terminal, dlg)
        box.pack_start(top_bar, False, False, 0)

        search_row = Gtk.Box(spacing=6)
        search_row.set_margin_start(12)
        search_row.set_margin_end(12)
        search_row.set_margin_top(6)
        search_row.set_margin_bottom(2)
        search_lbl   = Gtk.Label(label='🔍')
        search_entry = Gtk.Entry()
        search_entry.set_placeholder_text(
            self._t('search_placeholder_pushd') if pushd_mode
            else self._t('search_placeholder'))
        search_entry.set_hexpand(True)
        search_row.pack_start(search_lbl, False, False, 0)
        search_row.pack_start(search_entry, True, True, 0)
        box.pack_start(search_row, False, False, 0)

        paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        paned.set_margin_start(12)
        paned.set_margin_end(12)
        paned.set_margin_top(4)
        paned.set_margin_bottom(4)

        store = Gtk.ListStore(str, str, str, bool, str)
        tree  = Gtk.TreeView(model=store)
        tree.set_headers_visible(False)
        tree.set_search_column(-1)
        tree.set_activate_on_single_click(False)

        col1 = Gtk.TreeViewColumn()
        col1.set_min_width(170)
        col1.set_max_width(200)
        r1 = Gtk.CellRendererText()
        r1.set_property('ellipsize', Pango.EllipsizeMode.END)
        col1.pack_start(r1, True)
        col1.set_cell_data_func(r1, self._render_col_alias)
        tree.append_column(col1)

        col2 = Gtk.TreeViewColumn()
        r2 = Gtk.CellRendererText()
        r2.set_property('ellipsize', Pango.EllipsizeMode.MIDDLE)
        col2.pack_start(r2, True)
        col2.set_cell_data_func(r2, self._render_col_path)
        tree.append_column(col2)

        scroll_list = Gtk.ScrolledWindow()
        scroll_list.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll_list.set_min_content_height(230)
        scroll_list.add(tree)
        paned.pack1(scroll_list, True, False)

        preview_widget = self._build_preview_widget()
        paned.pack2(preview_widget, False, False)
        paned.set_position(260)
        box.pack_start(paned, True, True, 0)

        stack_bar, sw = self._build_stack_bar()
        box.pack_start(stack_bar, False, False, 0)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.set_margin_top(4)
        box.pack_start(sep, False, False, 0)

        btn_row, bw = self._build_btn_row(
            tree, store, terminal, dlg, current_dir, search_entry, pushd_mode)
        box.pack_start(btn_row, False, False, 8)

        # -- Language toggle handler --
        def apply_language():
            dlg.set_title(
                self._t('title_pushd') if pushd_mode else self._t('title_normal'))
            search_entry.set_placeholder_text(
                self._t('search_placeholder_pushd') if pushd_mode
                else self._t('search_placeholder'))
            lw['btn_save'].set_label(self._t('btn_save_here'))
            lw['btn_save'].set_tooltip_text(self._t('btn_save_here_tooltip'))
            lw['btn_preview'].set_tooltip_text(self._t('btn_preview_tooltip'))
            preview_widget.set_label(self._t('preview_frame'))
            sw['lbl_stack'].set_markup(self._t('stack_label'))
            if 'lbl_empty' in sw:
                sw['lbl_empty'].set_markup(self._t('stack_empty'))
            bw['cd'].set_label(self._t('btn_cd'))
            bw['cd'].set_tooltip_text(self._t('btn_cd_tooltip'))
            bw['pushd'].set_label(self._t('btn_pushd'))
            bw['pushd'].set_tooltip_text(self._t('btn_pushd_tooltip'))
            bw['popd'].set_label(self._t('btn_popd'))
            bw['popd'].set_tooltip_text(self._t('btn_popd_tooltip'))
            bw['delete'].set_label(self._t('btn_delete'))
            bw['delete'].set_tooltip_text(self._t('btn_delete_tooltip'))
            bw['cancel'].set_label(self._t('btn_cancel'))
            self._populate_store(store, search_entry.get_text())
            self._select_first(tree, store)

        def on_lang_en(btn):
            if btn.get_active():
                BookmarkDirectoriesPlugin._lang = 'en'
                apply_language()

        def on_lang_es(btn):
            if btn.get_active():
                BookmarkDirectoriesPlugin._lang = 'es'
                apply_language()

        lw['btn_en'].connect('toggled', on_lang_en)
        lw['btn_es'].connect('toggled', on_lang_es)

        # -- Search / tree events --
        def on_search_changed(entry):
            self._populate_store(store, entry.get_text())
            self._select_first(tree, store)

        def on_search_activate(_entry):
            if pushd_mode:
                self._do_pushd(tree, store, terminal, dlg, current_dir)
            else:
                self._do_cd(tree, store, terminal, dlg, search_entry.get_text())

        def on_search_key(entry, event):
            ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
            if ctrl and event.keyval == Gdk.KEY_Right:
                self._do_pushd(tree, store, terminal, dlg, current_dir)
                return True
            return False

        def on_selection_changed(sel):
            self._update_preview(sel, store, preview_widget)

        def on_row_activated(tv, path, _col):
            it = store.get_iter(path)
            if it and not store[it][3]:
                dest = store[it][2]
                if pushd_mode:
                    BookmarkDirectoriesPlugin._dir_stack.append(current_dir)
                    self._track_recent(current_dir)
                self._track_recent(dest)
                self._send_cd(terminal, dest)
                dlg.response(Gtk.ResponseType.OK)

        def on_preview_toggled(btn):
            self._config['show_preview'] = btn.get_active()
            self._save_config()
            preview_widget.set_visible(self._config['show_preview'])

        search_entry.connect('changed',          on_search_changed)
        search_entry.connect('activate',         on_search_activate)
        search_entry.connect('key-press-event',  on_search_key)
        tree.get_selection().connect('changed',  on_selection_changed)
        tree.connect('row-activated',            on_row_activated)
        lw['btn_preview'].connect('toggled',     on_preview_toggled)

        self._populate_store(store, '')
        self._select_first(tree, store)
        dlg.show_all()
        if not self._config.get('show_preview', True):
            preview_widget.hide()
        search_entry.grab_focus()
        dlg.run()
        dlg.destroy()

    # -- Widget builders ------------------------------------------------------

    def _build_top_bar(self, current_dir, terminal, dlg):
        bar = Gtk.Box(spacing=8)
        bar.set_margin_start(12)
        bar.set_margin_end(12)
        bar.set_margin_top(10)
        bar.set_margin_bottom(2)

        home    = os.path.expanduser('~')
        display = current_dir.replace(home, '~', 1)
        lbl = Gtk.Label()
        lbl.set_markup('<b>pwd:</b>  <tt>%s</tt>' % GLib.markup_escape_text(display))
        lbl.set_xalign(0)
        bar.pack_start(lbl, True, True, 0)

        # Language toggle
        lang_box = Gtk.Box(spacing=0)
        lang_box.get_style_context().add_class('linked')
        btn_en = Gtk.RadioButton(label='🇬🇧')
        btn_en.set_mode(False)
        btn_en.set_tooltip_text('English')
        btn_en.set_active(BookmarkDirectoriesPlugin._lang == 'en')
        btn_es = Gtk.RadioButton.new_from_widget(btn_en)
        btn_es.set_label('🇪🇸')
        btn_es.set_mode(False)
        btn_es.set_tooltip_text('Español')
        btn_es.set_active(BookmarkDirectoriesPlugin._lang == 'es')
        lang_box.pack_start(btn_en, False, False, 0)
        lang_box.pack_start(btn_es, False, False, 0)
        bar.pack_end(lang_box, False, False, 0)

        btn_bm = Gtk.Button(label=self._t('btn_save_here'))
        btn_bm.set_tooltip_text(self._t('btn_save_here_tooltip'))
        btn_bm.connect('clicked', lambda _b: self._dialog_new_bookmark(current_dir, dlg))
        bar.pack_end(btn_bm, False, False, 0)

        btn_prev = Gtk.ToggleButton(label='👁')
        btn_prev.set_tooltip_text(self._t('btn_preview_tooltip'))
        btn_prev.set_active(self._config.get('show_preview', True))
        bar.pack_end(btn_prev, False, False, 0)

        return bar, {'btn_en': btn_en, 'btn_es': btn_es,
                     'btn_save': btn_bm, 'btn_preview': btn_prev}

    def _build_preview_widget(self):
        frame = Gtk.Frame(label=self._t('preview_frame'))
        frame.set_margin_top(4)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(110)
        scroll.set_max_content_height(150)
        tv = Gtk.TextView()
        tv.set_editable(False)
        tv.set_monospace(True)
        tv.set_cursor_visible(False)
        scroll.add(tv)
        frame.add(scroll)
        frame._text_view = tv
        return frame

    def _build_stack_bar(self):
        bar = Gtk.Box(spacing=6)
        bar.set_margin_start(12)
        bar.set_margin_end(12)
        bar.set_margin_top(4)
        bar.set_margin_bottom(4)

        lbl_stack = Gtk.Label()
        lbl_stack.set_markup(self._t('stack_label'))
        bar.pack_start(lbl_stack, False, False, 0)

        widgets = {'lbl_stack': lbl_stack}
        stack   = BookmarkDirectoriesPlugin._dir_stack

        if stack:
            home = os.path.expanduser('~')
            for i, path in enumerate(reversed(stack[-5:])):
                disp = path.replace(home, '~', 1)
                chip = Gtk.Label()
                chip.set_markup('<small><tt> %s </tt></small>' %
                                GLib.markup_escape_text(disp))
                bar.pack_start(chip, False, False, 0)
                if i < min(len(stack), 5) - 1:
                    bar.pack_start(Gtk.Label(label='<'), False, False, 0)
        else:
            lbl_empty = Gtk.Label()
            lbl_empty.set_markup(self._t('stack_empty'))
            bar.pack_start(lbl_empty, False, False, 0)
            widgets['lbl_empty'] = lbl_empty

        return bar, widgets

    def _build_btn_row(self, tree, store, terminal, dlg,
                       current_dir, search_entry, pushd_mode):
        box = Gtk.Box(spacing=6)
        box.set_margin_start(12)
        box.set_margin_end(12)

        btn_cd     = Gtk.Button(label=self._t('btn_cd'))
        btn_pushd  = Gtk.Button(label=self._t('btn_pushd'))
        btn_popd   = Gtk.Button(label=self._t('btn_popd'))
        btn_delete = Gtk.Button(label=self._t('btn_delete'))
        btn_cancel = Gtk.Button(label=self._t('btn_cancel'))

        btn_cd.set_tooltip_text(self._t('btn_cd_tooltip'))
        btn_pushd.set_tooltip_text(self._t('btn_pushd_tooltip'))
        btn_popd.set_tooltip_text(self._t('btn_popd_tooltip'))
        btn_delete.set_tooltip_text(self._t('btn_delete_tooltip'))
        btn_cd.get_style_context().add_class('suggested-action')
        btn_popd.set_sensitive(bool(BookmarkDirectoriesPlugin._dir_stack))

        btn_cd.connect('clicked',     lambda _b: self._do_cd(tree, store, terminal, dlg, search_entry.get_text()))
        btn_pushd.connect('clicked',  lambda _b: self._do_pushd(tree, store, terminal, dlg, current_dir))
        btn_popd.connect('clicked',   lambda _b: self._do_popd(terminal, dlg))
        btn_delete.connect('clicked', lambda _b: self._do_delete(tree, store, search_entry))
        btn_cancel.connect('clicked', lambda _b: dlg.response(Gtk.ResponseType.CANCEL))

        box.pack_start(btn_cd,     False, False, 0)
        box.pack_start(btn_pushd,  False, False, 0)
        box.pack_start(btn_popd,   False, False, 0)
        box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 4)
        box.pack_start(btn_delete, False, False, 0)
        box.pack_end(btn_cancel,   False, False, 0)

        return box, {'cd': btn_cd, 'pushd': btn_pushd, 'popd': btn_popd,
                     'delete': btn_delete, 'cancel': btn_cancel}

    # -- List -----------------------------------------------------------------

    def _populate_store(self, store, query):
        store.clear()
        q = query.strip().lower()
        sections = [
            (CAT_STACK,
             [('[%d] %s' % (i, os.path.basename(p) or p), p)
              for i, p in enumerate(reversed(BookmarkDirectoriesPlugin._dir_stack), 1)]),
            (CAT_BOOKMARKS,
             [(bm.get('alias') or os.path.basename(bm['path']) or bm['path'], bm['path'])
              for bm in self._bookmarks]),
            (CAT_RECENT,
             [(os.path.basename(p) or p, p)
              for p in BookmarkDirectoriesPlugin._recent_dirs]),
            (CAT_FREQUENT,
             [(os.path.basename(p) or p, p) for p in self._frequent_dirs]),
            (CAT_GIT,
             [(os.path.basename(p) or p, p) for p in self._git_repos]),
        ]
        for cat, items in sections:
            matched = [(a, p) for a, p in items
                       if not q or self._smart_match(q, a, p)]
            if not matched:
                continue
            store.append([self._cat_label(cat), '', '', True, cat])
            for alias, path in matched:
                store.append(['', alias, path, False, cat])

    def _smart_match(self, query, alias, path):
        q = query.lower()
        a = alias.lower()
        name = os.path.basename(path).lower()
        p = path.lower()
        if a.startswith(q) or name.startswith(q):
            return True
        if q in a or q in p:
            return True
        return self._fuzzy_match(q, a) or self._fuzzy_match(q, name)

    @staticmethod
    def _fuzzy_match(query, text):
        it = iter(text)
        return all(c in it for c in query)

    def _select_first(self, tree, store):
        for i, row in enumerate(store):
            if not row[3]:
                tree.get_selection().select_path(Gtk.TreePath(i))
                tree.scroll_to_cell(Gtk.TreePath(i))
                return

    # -- Cell renderers -------------------------------------------------------

    def _render_col_alias(self, _col, cell, model, it, _data):
        is_sep = model[it][3]
        cat    = model[it][4]
        if is_sep:
            cell.set_property('markup', '<b><small>%s</small></b>' % model[it][0])
            cell.set_property('foreground', CAT_COLORS.get(cat, '#888888'))
            cell.set_property('cell-background', '#181825')
        else:
            alias = GLib.markup_escape_text(model[it][1])
            cell.set_property('markup', '  %s' % alias)
            cell.set_property('foreground', '#cdd6f4')
            cell.set_property('cell-background', None)

    def _render_col_path(self, _col, cell, model, it, _data):
        is_sep = model[it][3]
        if is_sep:
            cell.set_property('text', '')
            cell.set_property('cell-background', '#181825')
        else:
            home = os.path.expanduser('~')
            disp = model[it][2].replace(home, '~', 1)
            cell.set_property('text', disp)
            cell.set_property('foreground', '#6c7086')
            cell.set_property('cell-background', None)

    # -- Preview --------------------------------------------------------------

    def _update_preview(self, selection, store, preview_widget):
        if not self._config.get('show_preview', True):
            return
        _model, it = selection.get_selected()
        if it is None or store[it][3]:
            return
        path = store[it][2]
        buf  = preview_widget._text_view.get_buffer()
        if not os.path.isdir(path):
            buf.set_text(self._t('preview_not_exists') + path)
            return
        try:
            entries = sorted(os.listdir(path))
        except PermissionError:
            buf.set_text(self._t('preview_no_permission'))
            return
        lines = []
        dirs_count = files_count = 0
        for name in entries[:50]:
            full = os.path.join(path, name)
            if os.path.islink(full):
                lines.append('🔗 %s' % name)
            elif os.path.isdir(full):
                lines.append('📁 %s/' % name)
                dirs_count += 1
            elif os.access(full, os.X_OK):
                lines.append('⚙  %s' % name)
                files_count += 1
            else:
                lines.append('   %s' % name)
                files_count += 1
        if len(entries) > 50:
            lines.append(self._t('preview_more', len(entries) - 50))
        summary = self._t('preview_summary', dirs_count, files_count)
        buf.set_text('\n'.join(lines) + summary if lines
                     else self._t('preview_empty'))

    # -- Actions --------------------------------------------------------------

    def _selected_path(self, tree, store):
        _model, it = tree.get_selection().get_selected()
        if it and not store[it][3]:
            return store[it][2]
        return None

    def _selected_cat(self, tree, store):
        _model, it = tree.get_selection().get_selected()
        return store[it][4] if it else None

    def _track_recent(self, path):
        cls = BookmarkDirectoriesPlugin
        if path in cls._recent_dirs:
            cls._recent_dirs.remove(path)
        cls._recent_dirs.appendleft(path)

    def _do_cd(self, tree, store, terminal, dlg, query=''):
        path = self._selected_path(tree, store)
        if not path and query:
            expanded = os.path.expanduser(query.strip())
            if os.path.isdir(expanded):
                path = expanded
        if path:
            self._track_recent(path)
            self._send_cd(terminal, path)
            dlg.response(Gtk.ResponseType.OK)

    def _do_pushd(self, tree, store, terminal, dlg, current_dir):
        path = self._selected_path(tree, store)
        if path:
            BookmarkDirectoriesPlugin._dir_stack.append(current_dir)
            self._track_recent(current_dir)
            self._track_recent(path)
            self._send_cd(terminal, path)
            dlg.response(Gtk.ResponseType.OK)

    def _do_popd(self, terminal, dlg):
        stack = BookmarkDirectoriesPlugin._dir_stack
        if stack:
            prev = stack.pop()
            self._track_recent(prev)
            self._send_cd(terminal, prev)
            dlg.response(Gtk.ResponseType.OK)

    def _do_delete(self, tree, store, search_entry):
        path = self._selected_path(tree, store)
        cat  = self._selected_cat(tree, store)
        if path and cat == CAT_BOOKMARKS:
            self._bookmarks = [b for b in self._bookmarks if b['path'] != path]
            self._save_bookmarks()
            self._populate_store(store, search_entry.get_text())
            self._select_first(tree, store)

    # -- New bookmark dialog --------------------------------------------------

    def _dialog_new_bookmark(self, prefill_path, parent):
        dlg = Gtk.Dialog(
            title=self._t('new_bm_title'),
            transient_for=parent,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
        )
        dlg.set_default_size(400, 150)
        content = dlg.get_content_area()
        grid = Gtk.Grid(column_spacing=8, row_spacing=8)
        grid.set_margin_start(14); grid.set_margin_end(14)
        grid.set_margin_top(14);   grid.set_margin_bottom(14)

        lbl_alias = Gtk.Label(label=self._t('new_bm_alias_label'))
        lbl_alias.set_xalign(1)
        alias_entry = Gtk.Entry()
        alias_entry.set_placeholder_text(self._t('new_bm_alias_placeholder'))
        alias_entry.set_hexpand(True)

        lbl_path = Gtk.Label(label=self._t('new_bm_path_label'))
        lbl_path.set_xalign(1)
        path_entry = Gtk.Entry()
        path_entry.set_text(prefill_path)
        path_entry.set_hexpand(True)

        btn_browse = Gtk.Button(label='...')
        btn_browse.connect('clicked', lambda _b: self._browse_dir(path_entry, dlg))

        grid.attach(lbl_alias,   0, 0, 1, 1)
        grid.attach(alias_entry, 1, 0, 2, 1)
        grid.attach(lbl_path,    0, 1, 1, 1)
        grid.attach(path_entry,  1, 1, 1, 1)
        grid.attach(btn_browse,  2, 1, 1, 1)
        content.pack_start(grid, True, True, 0)

        dlg.add_buttons(
            self._t('btn_cancel'),  Gtk.ResponseType.CANCEL,
            self._t('new_bm_save'), Gtk.ResponseType.OK,
        )
        dlg.set_default_response(Gtk.ResponseType.OK)
        alias_entry.connect('activate', lambda _e: dlg.response(Gtk.ResponseType.OK))
        dlg.show_all()

        if dlg.run() == Gtk.ResponseType.OK:
            alias = alias_entry.get_text().strip()
            path  = path_entry.get_text().strip()
            if path:
                self._bookmarks = [b for b in self._bookmarks if b['path'] != path]
                self._bookmarks.append({'alias': alias, 'path': path})
                self._save_bookmarks()
        dlg.destroy()

    def _browse_dir(self, path_entry, parent):
        chooser = Gtk.FileChooserDialog(
            title=self._t('chooser_title'),
            parent=parent,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        chooser.add_buttons(
            self._t('btn_cancel'),    Gtk.ResponseType.CANCEL,
            self._t('chooser_select'), Gtk.ResponseType.OK,
        )
        current = path_entry.get_text().strip()
        if os.path.isdir(current):
            chooser.set_current_folder(current)
        if chooser.run() == Gtk.ResponseType.OK:
            path_entry.set_text(chooser.get_filename())
        chooser.destroy()
