import sys, os, pty, signal, pyte, fcntl, termios, struct, codecs, webbrowser
from collections import deque
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QTextEdit, QLineEdit, QLabel, QStackedWidget, 
                             QScrollArea, QFrame, QPushButton, QFileIconProvider)
from PyQt6.QtCore import (Qt, QTimer, QSocketNotifier, QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup, QEvent, QSize, QFileInfo, QFileSystemWatcher)
from PyQt6.QtGui import (QTextCursor, QFont, QColor, QTextCharFormat, QIcon, QAction)
from AppKit import (NSEvent, NSKeyDownMask, NSUserDefaults, NSApp, NSWindowCollectionBehaviorCanJoinAllSpaces)
import urllib.parse
import objc

def get_theme(is_dark):
    bg = "rgba(30, 30, 30, 240)" if is_dark else "rgba(245, 245, 245, 240)"
    text = "#ffffff" if is_dark else "#000000"
    nav_text = "rgba(255, 255, 255, 120)" if is_dark else "rgba(0, 0, 0, 120)"
    border = "rgba(255, 255, 255, 30)" if is_dark else "rgba(0, 0, 0, 30)"
    sub_text = "rgba(255, 255, 255, 150)" if is_dark else "rgba(0, 0, 0, 150)"
    scroll_bg = "rgba(255, 255, 255, 10)" if is_dark else "rgba(0, 0, 0, 10)"
    scroll_handle = "rgba(255, 255, 255, 50)" if is_dark else "rgba(0, 0, 0, 50)"
    scroll_hover = "rgba(255, 255, 255, 80)" if is_dark else "rgba(0, 0, 0, 80)"
    menu_bg = "rgb(40, 40, 40)" if is_dark else "rgb(250, 250, 250)"
    menu_item_hover = "rgba(255, 255, 255, 30)" if is_dark else "rgba(0, 0, 0, 20)"
    selection = "#007AFF"
    btn_hover = "rgba(255, 255, 255, 20)" if is_dark else "rgba(0, 0, 0, 10)"
    
    return f"""
    QWidget#MainContainer {{
        background: {bg};
        border-radius: 24px;
        border: 1px solid {border};
    }}
    QLineEdit {{
        background: rgba(128, 128, 128, 40);
        border-radius: 12px;
        padding: 10px 15px;
        color: {text};
        font-family: 'Menlo';
        border: none;
    }}
    QLabel {{ color: {text}; font-family: 'Menlo'; }}
    QPushButton#NavBtn {{
        color: {nav_text};
        background: transparent;
        border: none;
        font-family: 'Menlo';
        font-size: 14px;
        padding: 8px 12px;
        border-bottom: 2px solid transparent;
    }}
    QPushButton#NavBtn:checked {{ 
        color: {text}; 
        border-bottom: 2px solid {text};
    }}
    QLabel#ClipLabel {{
        color: {sub_text};
        font-size: 13px;
    }}
    QPushButton#ClipCopyBtn {{
        color: {sub_text};
        border: none;
        background: transparent;
        font-size: 11px;
    }}
    QPushButton#ClipCopyBtn:hover {{
        color: {text};
    }}
    QLabel#SearchHint {{
        color: {sub_text};
        font-size: 11px;
        margin-bottom: 30px;
    }}
    QScrollBar:vertical {{
        border: none;
        background: transparent;
        width: 8px;
        margin: 0px 2px 0px 2px;
    }}
    QScrollBar::handle:vertical {{
        background: {scroll_handle};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {scroll_hover};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
        background: none;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    QScrollBar:horizontal {{
        height: 0px;
    }}
    QMenu {{
        background-color: {menu_bg};
        border: 1px solid {border};
        border-radius: 10px;
        padding: 5px;
    }}
    QMenu::item {{
        padding: 6px 25px 6px 20px;
        background-color: transparent;
        color: {text};
        border-radius: 5px;
    }}
    QMenu::item:selected {{
        background-color: {menu_item_hover};
    }}
    QMenu::separator {{
        height: 1px;
        background: {border};
        margin: 4px 10px;
    }}
    QPushButton#LaunchBtn {{
        text-align: left;
        padding: 10px 15px;
        color: {text};
        background: transparent;
        border-radius: 10px;
        font-family: 'Menlo';
        font-size: 14px;
        border: none;
    }}
    QPushButton#LaunchBtn:hover {{
        background: {btn_hover};
    }}
    """

class TerminalTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.display = QTextEdit()
        self.display.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.display.setReadOnly(True)
        self.display.setUndoRedoEnabled(False)
        self.display.setFrameStyle(0)
        self.display.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.display.setStyleSheet("background: transparent; padding: 15px;")
        self.display.setFont(QFont("Menlo", 13))
        self.display.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.display.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self.display)
        self.rows, self.cols = 24, 80
        self.screen = pyte.HistoryScreen(self.cols, self.rows, history=1000)
        self.stream = pyte.Stream(self.screen)
        self.decoder = codecs.getincrementaldecoder("utf-8")(errors="ignore")
        self.pid, self.master_fd = pty.fork()
        if self.pid == 0:
            os.environ["TERM"] = "xterm-256color"
            os.environ["LANG"] = "en_US.UTF-8"
            os.execv("/bin/zsh", ["/bin/zsh", "-i"])
        else:
            fl = fcntl.fcntl(self.master_fd, fcntl.F_GETFL)
            fcntl.fcntl(self.master_fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
            size = struct.pack("HHHH", self.rows, self.cols, 0, 0)
            fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, size)
            self.notifier = QSocketNotifier(self.master_fd, QSocketNotifier.Type.Read)
            self.notifier.activated.connect(self.read_from_pty)
        self.display.keyPressEvent = self.handle_keys

    def read_from_pty(self):
        try:
            raw_data = os.read(self.master_fd, 4096)
            if raw_data:
                self.stream.feed(self.decoder.decode(raw_data))
                self.update_display()
        except: pass

    def update_display(self):
        history_lines = []
        for line in self.screen.history.top:
            if not line: history_lines.append("")
            else:
                width = max(line.keys()) + 1 if line.keys() else 0
                chars = [line.get(i).data if line.get(i) else " " for i in range(width)]
                history_lines.append("".join(chars).rstrip())
        current_lines = [line.rstrip() for line in self.screen.display]
        visible_lines = (history_lines + current_lines)[-1000:]
        self.display.blockSignals(True)
        old_cursor = self.display.textCursor()
        has_selection = old_cursor.hasSelection()
        selection_start = old_cursor.selectionStart()
        selection_end = old_cursor.selectionEnd()
        vbar = self.display.verticalScrollBar()
        at_bottom = vbar.value() >= vbar.maximum() - 15
        self.display.setCurrentCharFormat(QTextCharFormat())
        self.display.setPlainText("\n".join(visible_lines))
        cursor_y = len(history_lines) + self.screen.cursor.y
        cursor_x = self.screen.cursor.x
        block = self.display.document().findBlockByNumber(cursor_y)
        if block.isValid():
            cursor = QTextCursor(block)
            line_length = block.length() - 1
            if cursor_x > line_length:
                cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
                cursor.insertText(" " * (cursor_x - line_length))
            cursor.setPosition(block.position() + cursor_x)
            if cursor.atBlockEnd():
                cursor.insertText(" ")
                cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, 1)
            else:
                cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
            fmt = QTextCharFormat()
            is_dark = NSUserDefaults.standardUserDefaults().stringForKey_("AppleInterfaceStyle") == "Dark"
            fmt.setBackground(QColor("#FFFFFF" if is_dark else "#282a36"))
            fmt.setForeground(QColor("#1e1e1e" if is_dark else "#ffffff"))
            cursor.setCharFormat(fmt)
            self.display.setCurrentCharFormat(QTextCharFormat())
        if has_selection:
            new_cursor = self.display.textCursor()
            new_cursor.setPosition(selection_start)
            new_cursor.setPosition(selection_end, QTextCursor.MoveMode.KeepAnchor)
            self.display.setTextCursor(new_cursor)
        elif at_bottom:
            self.display.moveCursor(QTextCursor.MoveOperation.End)
        self.display.blockSignals(False)

    def handle_keys(self, event):
        key, mod = event.key(), event.modifiers()
        if (key == Qt.Key.Key_C or key == Qt.Key.Key_V) and (mod & Qt.KeyboardModifier.ControlModifier or mod & Qt.KeyboardModifier.MetaModifier):
            if key == Qt.Key.Key_C and self.display.textCursor().hasSelection():
                QApplication.clipboard().setText(self.display.textCursor().selectedText())
            elif key == Qt.Key.Key_V:
                os.write(self.master_fd, QApplication.clipboard().text().encode())
            return
        key_map = {
            Qt.Key.Key_Return: b"\r", Qt.Key.Key_Backspace: b"\x7f", Qt.Key.Key_Tab: b"\t",
            Qt.Key.Key_Up: b"\x1b[A", Qt.Key.Key_Down: b"\x1b[B", Qt.Key.Key_Right: b"\x1b[C",
            Qt.Key.Key_Left: b"\x1b[D", Qt.Key.Key_Escape: b"\x1b", Qt.Key.Key_Space: b" "
        }
        if mod & Qt.KeyboardModifier.ControlModifier and 65 <= key <= 90:
            os.write(self.master_fd, bytes([key - 64]))
        elif key in key_map: os.write(self.master_fd, key_map[key])
        elif event.text(): os.write(self.master_fd, event.text().encode())

    def cleanup(self):
        try:
            if hasattr(self, 'notifier'):
                self.notifier.setEnabled(False)
                self.notifier.deleteLater()
            if self.master_fd:
                os.close(self.master_fd)
            if self.pid:
                os.kill(self.pid, signal.SIGTERM)
                os.waitpid(self.pid, 0)
        except: pass

class LaunchpadTab(QWidget):
    def __init__(self):
        super().__init__()
        self.icon_provider = QFileIconProvider()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.input = QLineEdit()
        self.input.setPlaceholderText("launchpad ready to search...")
        self.input.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.input.textChanged.connect(self.filter_apps)
        self.input.installEventFilter(self)
        self.layout.addWidget(self.input)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")
        self.grid_wrap = QWidget()
        self.grid_layout = QVBoxLayout(self.grid_wrap)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.grid_wrap)
        self.layout.addWidget(self.scroll)
        self.watcher = QFileSystemWatcher(self)
        watch_paths = ["/Applications", os.path.expanduser("~/Applications")]
        for p in watch_paths:
            if os.path.exists(p): self.watcher.addPath(p)
        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.load_apps)
        self.watcher.directoryChanged.connect(lambda: self.update_timer.start(1000))
        self.apps = []
        self.load_apps()

    def load_apps(self):
        self.apps = []
        search_paths = ["/Applications", "/System/Applications", os.path.expanduser("~/Applications")]
        for base_path in search_paths:
            if not os.path.exists(base_path): continue
            try:
                for item in os.listdir(base_path):
                    full_path = os.path.join(base_path, item)
                    if item.endswith(".app") and not item.startswith("."):
                        self.apps.append({"name": item.replace(".app", ""), "path": full_path})
                    elif os.path.isdir(full_path) and not item.startswith("."):
                        try:
                            for sub_item in os.listdir(full_path):
                                if sub_item.endswith(".app") and not sub_item.startswith("."):
                                    self.apps.append({"name": sub_item.replace(".app", ""), "path": os.path.join(full_path, sub_item)})
                        except: continue
            except: continue
        seen = set()
        self.apps = [x for x in self.apps if not (x['path'] in seen or seen.add(x['path']))]
        self.apps.sort(key=lambda x: x['name'].lower())
        self.refresh_list(self.apps)

    def refresh_list(self, app_list):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for app in app_list[:100]:
            btn = QPushButton(f"  {app['name']}")
            btn.setIcon(self.icon_provider.icon(QFileInfo(app['path'])))
            btn.setIconSize(QSize(28, 28))
            btn.setObjectName("LaunchBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, p=app['path']: self.launch(p))
            self.grid_layout.addWidget(btn)
        self.grid_layout.addStretch()

    def filter_apps(self, text):
        query = text.lower().strip()
        self.refresh_list([a for a in self.apps if query in a['name'].lower()])

    def eventFilter(self, obj, event):
        if obj == self.input and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and self.grid_layout.count() > 0:
                item = self.grid_layout.itemAt(0)
                if item and item.widget():
                    item.widget().click()
                    return True
        return super().eventFilter(obj, event)

    def launch(self, path):
        import subprocess
        subprocess.Popen(["open", path])
        self.window().toggle()
    
    def cleanup(self):
        self.watcher.removePaths(self.watcher.directories())
        self.update_timer.stop()

class SearchTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.engines = [("google", "https://google.com/search?q="), ("yandex", "https://yandex.ru/search/?text="), ("youtube", "https://youtube.com/results?search_query="), ("github", "https://github.com/search?q=")]
        self.cur_idx = 0
        self.title = QLabel(">google")
        self.title.setStyleSheet("font-size: 48px; font-weight: bold; margin-bottom: 2px;")
        self.hint = QLabel("change it on tab")
        self.hint.setObjectName("SearchHint")
        self.input = QLineEdit()
        self.input.setPlaceholderText("search ready...")
        self.input.setFixedWidth(450)
        layout.addWidget(self.title, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.hint, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.input, 0, Qt.AlignmentFlag.AlignCenter)
        self.input.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Tab:
                self.cur_idx = (self.cur_idx + 1) % len(self.engines)
                self.title.setText(f">{self.engines[self.cur_idx][0]}")
                return True
            if event.key() == Qt.Key.Key_Return and self.input.text():
                webbrowser.open(self.engines[self.cur_idx][1] + urllib.parse.quote(self.input.text()))
                return True
        return False

class ClipboardTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 10)
        self.input = QLineEdit()
        self.input.setPlaceholderText("clipbored ready to search...")
        self.input.textChanged.connect(self.refresh_list)
        layout.addWidget(self.input)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")
        self.container = QWidget()
        self.card_layout = QVBoxLayout(self.container)
        self.card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)
        self.history = deque(maxlen=100)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.sync_clip)
        self.timer.start(800)

    def sync_clip(self):
        text = QApplication.clipboard().text().strip()
        if not text or len(text) > 100000: return
        if not self.history or text != self.history[0]:
            if text in self.history: self.history.remove(text)
            self.history.appendleft(text)
            if not self.input.text().strip(): self.refresh_list()

    def refresh_list(self):
        while self.card_layout.count():
            item = self.card_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        query = self.input.text().strip().lower()
        for original_text in [t for t in self.history if query in t.lower()][:20]:
            item = QFrame()
            l = QHBoxLayout(item)
            l.setContentsMargins(10, 5, 10, 5)
            preview = " ".join(original_text.split())
            txt = QLabel(preview[:65] + "..." if len(preview) > 65 else preview)
            txt.setObjectName("ClipLabel")
            btn = QPushButton("copy")
            btn.setObjectName("ClipCopyBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda ch, x=original_text: self.copy_and_hide(x))
            l.addWidget(txt)
            l.addStretch()
            l.addWidget(btn)
            self.card_layout.addWidget(item)

    def copy_and_hide(self, text):
        self.timer.stop()
        QApplication.clipboard().setText(text)
        if text in self.history: self.history.remove(text)
        self.history.appendleft(text)
        self.timer.start(800)
        self.window().toggle()

class KShell(QMainWindow):
    def __init__(self, ktools):
        super().__init__()
        self.ktools = ktools

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(780, 500)
        screen = QApplication.primaryScreen().availableGeometry()
        self.end_pos = QPoint(screen.center().x() - 390, screen.center().y() - 250)
        self.start_pos = QPoint(self.end_pos.x(), self.end_pos.y() - 40)
        self.move(self.start_pos)
        self.setWindowOpacity(0.0)
        self.root = QWidget()
        self.root.setObjectName("MainContainer")
        self.main_layout = QVBoxLayout(self.root)
        self.main_layout.setContentsMargins(10, 10, 10, 15)
        self.stack = QStackedWidget()
        self.term = TerminalTab(self)
        self.stack.addWidget(self.term)
        self.stack.addWidget(LaunchpadTab())
        self.stack.addWidget(SearchTab())
        self.stack.addWidget(ClipboardTab())
        self.nav_layout = QHBoxLayout()
        self.nav_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nav_btns = []
        for i, name in enumerate(["terminal", "launchpad", "search", "clipbored"]):
            btn = QPushButton(name)
            btn.setObjectName("NavBtn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda ch, idx=i: self.set_tab(idx))
            self.nav_layout.addWidget(btn)
            self.nav_btns.append(btn)
        self.main_layout.addWidget(self.stack)
        self.main_layout.addLayout(self.nav_layout)
        self.setCentralWidget(self.root)
        self.update_system_theme()
        self.set_tab(0)
        self.installEventFilter(self)
        self.anim_group = QParallelAnimationGroup()
        self.pos_anim = QPropertyAnimation(self, b"pos")
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        for a in [self.pos_anim, self.opacity_anim]:
            a.setDuration(150)
            a.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.anim_group.addAnimation(a)
        self.is_hiding = False
        self.anim_group.finished.connect(self._on_anim_finished)
        from Foundation import NSDistributedNotificationCenter, NSNotificationSuspensionBehaviorDeliverImmediately

    def set_tab(self, idx):
        self.stack.setCurrentIndex(idx)
        for i, b in enumerate(self.nav_btns): b.setChecked(i == idx)
        
        curr = self.stack.currentWidget()
        if not hasattr(curr, "_filtered"):
            target = getattr(curr, "input", getattr(curr, "display", None))
            if target:
                target.installEventFilter(self)
                curr._filtered = True
                
        QTimer.singleShot(10, self.focus_current)

    def focus_current(self):
        curr = self.stack.currentWidget()
        if hasattr(curr, "input"): curr.input.setFocus()
        elif hasattr(curr, "display"): curr.display.setFocus()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                if Qt.Key.Key_1 <= event.key() <= Qt.Key.Key_4:
                    self.set_tab(event.key() - Qt.Key.Key_1)
                    return True
            if event.key() == Qt.Key.Key_Escape:
                self.toggle()
                return True
        return super().eventFilter(obj, event)

    def toggle(self):
        if self.anim_group.state() == QParallelAnimationGroup.State.Running: return
        
        if not self.isVisible() or self.windowOpacity() < 0.5:
            closed_other = self.ktools.request_show("kshell")
            delay = 120 if closed_other else 0
            QTimer.singleShot(delay, self._do_show)
        else:
            self.hide_anim()

    def _do_show(self):
        self.is_hiding = False
        self.update_system_theme()
        self.show()
        self.raise_()
        self.setFocus()
        NSApp.activateIgnoringOtherApps_(True)
        
        self.pos_anim.setStartValue(self.start_pos)
        self.pos_anim.setEndValue(self.end_pos)
        self.opacity_anim.setStartValue(0.0)
        self.opacity_anim.setEndValue(1.0)
        self.anim_group.start()
        
        QTimer.singleShot(500, self.reset_switching)

    def reset_switching(self):
        self.ktools.is_switching = False

    def event(self, event):
        if event.type() == QEvent.Type.WindowDeactivate:
            if getattr(self.ktools, 'is_switching', False):
                return super().event(event)
                
            if self.is_hiding:
                return super().event(event)

            if self.windowOpacity() < 0.95:
                return super().event(event)
                
            if self.isVisible():
                self.hide_anim()
        return super().event(event)
    
    def hide_anim(self):
        self.is_hiding = True
        self.pos_anim.setStartValue(self.end_pos)
        self.pos_anim.setEndValue(self.start_pos)
        self.opacity_anim.setStartValue(1.0)
        self.opacity_anim.setEndValue(0.0)
        self.anim_group.start()

    @objc.signature(b"v@:@")
    def update_system_theme(self, notification=None):
        import AppKit
        AppKit.NSUserDefaults.standardUserDefaults().synchronize()
        
        style = AppKit.NSUserDefaults.standardUserDefaults().stringForKey_("AppleInterfaceStyle")
        is_dark = style == "Dark"
        
        self.setStyleSheet(get_theme(is_dark))
        
        self.root.style().unpolish(self.root)
        self.root.style().polish(self.root)
        self.root.update()
        
        QTimer.singleShot(50, self.term.update_display)

    def _on_anim_finished(self):
        if self.is_hiding:
            self.hide()
            self.setWindowOpacity(0.0) 
            self.is_hiding = False
            self.ktools.restore_focus()

class Plugin:
    def __init__(self, ktools):
        self.ktools = ktools
        self.name = "kshell"
        self.shell = KShell(ktools)
        self.hotkey_handler = self._create_hotkey_handler()
        self.global_monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(NSKeyDownMask, self.hotkey_handler)
        self.local_monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(NSKeyDownMask, self.hotkey_handler)
        self.action = QAction("open kshell (⌘space)", ktools.menu)
        self.action.triggered.connect(self.shell.toggle)

    def _create_hotkey_handler(self):
        def handler(event):
            if event.keyCode() == 49 and event.modifierFlags() & (1 << 20):
                QTimer.singleShot(0, self.shell.toggle)
                return None
            return event
        return handler

    def unload(self):
        if hasattr(self, 'global_monitor'):
            NSEvent.removeMonitor_(self.global_monitor)
            self.global_monitor = None
        if hasattr(self, 'local_monitor'):
            NSEvent.removeMonitor_(self.local_monitor)
            self.local_monitor = None

        try:
            self.shell.term.cleanup()
            
            launch_tab = self.shell.stack.widget(1)
            if hasattr(launch_tab, 'cleanup'):
                launch_tab.cleanup()

            clip_tab = self.shell.stack.widget(3)
            if hasattr(clip_tab, 'timer'):
                clip_tab.timer.stop()
        except Exception as e:
            print(f"kshell cleanup error: {e}")

        if self.shell:
            if hasattr(self.shell, 'anim_group'):
                self.shell.anim_group.stop()
            self.shell.close()
            self.shell.deleteLater()
            self.shell = None

        self.hotkey_handler = None
        import gc
        gc.collect()
        print("kshell: unloaded and processes killed")

    def get_actions(self):
        return [self.action]
    
    def update_theme(self):
        if hasattr(self, 'shell'):
            self.shell.update_system_theme()