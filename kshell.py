from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QStackedWidget, QPushButton, QFrame, QScrollArea, QGraphicsOpacityEffect)
from PyQt6.QtCore import (Qt, QTimer, QPoint, QEvent, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup)
from main import OverlayWindow
from PyQt6.QtGui import QAction, QGuiApplication, QCursor
from AppKit import (NSEvent, NSKeyDownMask, NSUserDefaults, NSApp, 
                    NSWindowCollectionBehaviorCanJoinAllSpaces)
import objc
import Quartz

def get_theme(is_dark):
    bg = "transparent"
    text = "#ffffff" if is_dark else "#000000"
    nav_text = "rgba(255, 255, 255, 120)" if is_dark else "rgba(0, 0, 0, 120)"
    border = "rgba(255, 255, 255, 30)" if is_dark else "rgba(0, 0, 0, 30)"
    sub_text = "rgba(255, 255, 255, 150)" if is_dark else "rgba(0, 0, 0, 150)"
    scroll_handle = "rgba(255, 255, 255, 50)" if is_dark else "rgba(0, 0, 0, 50)"
    scroll_hover = "rgba(255, 255, 255, 80)" if is_dark else "rgba(0, 0, 0, 80)"
    menu_bg = "rgb(40, 40, 40)" if is_dark else "rgb(250, 250, 250)"
    menu_item_hover = "rgba(255, 255, 255, 30)" if is_dark else "rgba(0, 0, 0, 20)"
    btn_hover = "rgba(255, 255, 255, 20)" if is_dark else "rgba(0, 0, 0, 10)"
    
    return f"""
    QFrame#MainContainer {{
        background: {bg};
        border-radius: 24px;
        border: 1px solid {border};
    }}
    QStackedWidget {{
        background: transparent;
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
        margin: 0px 2px;
    }}
    QPushButton#NavBtn:checked {{ 
        color: {text}; 
        border-bottom: 2px solid {text};
    }}
    QLabel#ClipLabel {{
        color: {sub_text};
        font-size: 13px;
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

class KShell(OverlayWindow):
    def __init__(self, ktools):
        super().__init__(ktools, width=780, height=500)
        self.tabs = []
        
        screen = QApplication.primaryScreen().availableGeometry()
        self.end_pos = QPoint(screen.center().x() - 390, screen.center().y() - 250)
        self.start_pos = QPoint(self.end_pos.x(), self.end_pos.y() - 40)
        self.move(self.start_pos)
        
        self.root = QFrame()
        self.root.setObjectName("MainContainer")
        self.main_layout = QVBoxLayout(self.root)
        self.main_layout.setContentsMargins(10, 10, 10, 15)
        
        self.stack = QStackedWidget()
        
        self.nav_scroll = QScrollArea()
        self.nav_scroll.setFixedHeight(45)
        self.nav_scroll.setWidgetResizable(True)
        self.nav_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.nav_scroll.setStyleSheet("background: transparent;")
        self.nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.nav_scroll.wheelEvent = self.nav_wheel_event
        
        self.nav_container = QWidget()
        self.nav_layout = QHBoxLayout(self.nav_container)
        self.nav_layout.setContentsMargins(10, 0, 10, 0)
        self.nav_layout.setSpacing(5)
        self.nav_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.nav_scroll.setWidget(self.nav_container)
        
        self.main_layout.addWidget(self.stack)
        self.main_layout.addWidget(self.nav_scroll)
        self.setCentralWidget(self.root)
        
        self.update_system_theme()
        self.installEventFilter(self)

    def nav_wheel_event(self, event):
        delta = event.angleDelta()
        if abs(delta.x()) > abs(delta.y()):
            val = self.nav_scroll.horizontalScrollBar().value() - delta.x()
        else:
            val = self.nav_scroll.horizontalScrollBar().value() - delta.y()
        self.nav_scroll.horizontalScrollBar().setValue(val)

    def register_tab(self, tab_id, display_name, widget):
        self.unregister_tab(tab_id)
        
        btn = QPushButton(display_name)
        btn.setObjectName("NavBtn")
        btn.setCheckable(True)
        btn.clicked.connect(lambda ch, tid=tab_id: self.set_tab_by_id(tid))
        
        self.nav_layout.addWidget(btn)
        self.stack.addWidget(widget)
        
        self.tabs.append({
            'id': tab_id,
            'name': display_name,
            'widget': widget,
            'button': btn
        })
        
        if len(self.tabs) == 1:
            self.set_tab_by_id(tab_id)

    def unregister_tab(self, tab_id):
        for i, tab in enumerate(self.tabs):
            if tab['id'] == tab_id:
                self.nav_layout.removeWidget(tab['button'])
                tab['button'].deleteLater()
                self.stack.removeWidget(tab['widget'])
                self.tabs.pop(i)
                break

    def set_tab_by_id(self, tab_id):
        for i, tab in enumerate(self.tabs):
            if tab['id'] == tab_id:
                self.set_tab(i)
                break

    def set_tab(self, idx):
        if idx < 0 or idx >= len(self.tabs): 
            return
            
        old_idx = self.stack.currentIndex()
        
        for i, tab in enumerate(self.tabs):
            tab['button'].setChecked(i == idx)
            if i == idx:
                self.nav_scroll.ensureWidgetVisible(tab['button'], 50, 0)
                
        curr = self.tabs[idx]['widget']

        if old_idx != idx:
            direction = 1 if old_idx == -1 or idx > old_idx else -1
            
            if old_idx != -1:
                old_widget = self.stack.widget(old_idx)
                new_widget = curr
                
                if hasattr(self, 'slide_group') and self.slide_group.state() == QParallelAnimationGroup.State.Running:
                    self.slide_group.stop()
                    
                for i in range(self.stack.count()):
                    if i != old_idx and i != idx:
                        w = self.stack.widget(i)
                        w.hide()
                        w.move(0, 0)
                
                self.stack.setCurrentIndex(idx)
                
                old_widget.setGeometry(self.stack.rect())
                old_widget.show()
                old_widget.raise_()
                new_widget.raise_()
                
                start_x = direction * (self.stack.width() or 780)
                
                self.slide_group = QParallelAnimationGroup(self)
                
                anim_in = QPropertyAnimation(new_widget, b"pos")
                anim_in.setDuration(250)
                anim_in.setStartValue(QPoint(start_x, 0))
                anim_in.setEndValue(QPoint(0, 0))
                anim_in.setEasingCurve(QEasingCurve.Type.OutQuart)
                
                anim_out = QPropertyAnimation(old_widget, b"pos")
                anim_out.setDuration(250)
                anim_out.setStartValue(QPoint(0, 0))
                anim_out.setEndValue(QPoint(-start_x, 0))
                anim_out.setEasingCurve(QEasingCurve.Type.OutQuart)
                
                self.slide_group.addAnimation(anim_in)
                self.slide_group.addAnimation(anim_out)
                
                def finish_anim(w_old=old_widget):
                    w_old.hide()
                    w_old.move(0, 0)
                    
                self.slide_group.finished.connect(finish_anim)
                self.slide_group.start()
            else:
                self.stack.setCurrentIndex(idx)
        
        if not hasattr(curr, "_filtered"):
            target = getattr(curr, "input", getattr(curr, "display", None))
            if target:
                target.installEventFilter(self)
                
            curr.installEventFilter(self)
            curr._filtered = True
                
        QTimer.singleShot(10, self.focus_current)

    def open_to_tab(self, idx):
        self.set_tab(idx)
        if hasattr(self, 'anim_group') and self.anim_group.state() == QParallelAnimationGroup.State.Running and not self.is_hiding:
            return
            
        if not self.isVisible() or self.windowOpacity() < 0.5:
            closed_other = self.ktools.request_show("kshell")
            delay = 120 if closed_other else 0
            QTimer.singleShot(delay, lambda: self.ktools._execute_show(self, True))
        else:
            self.raise_()
            self.activateWindow()
            
    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(50, self.focus_current)
        QTimer.singleShot(150, self.focus_current)

    def keyPressEvent(self, event):
        curr = self.stack.currentWidget()
        if curr:
            target = getattr(curr, "input", getattr(curr, "display", None))
            if target and not target.hasFocus():
                target.setFocus()
                from PyQt6.QtCore import QCoreApplication
                QCoreApplication.sendEvent(target, event)
                return
        super().keyPressEvent(event)

    def hideEvent(self, event):
        super().hideEvent(event)
        for tab in self.tabs:
            if hasattr(tab['widget'], 'reset_search'):
                tab['widget'].reset_search()

    def focus_current(self):
        curr = self.stack.currentWidget()
        if curr:
            if hasattr(curr, "input"): 
                curr.input.setFocus()
            elif hasattr(curr, "display"): 
                curr.display.setFocus()
            else:
                curr.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                curr.setFocus()

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Type.KeyPress, QEvent.Type.ShortcutOverride):
            cmd_pressed = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
            
            if cmd_pressed and event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right):
                if event.type() == QEvent.Type.KeyPress and self.tabs:
                    direction = -1 if event.key() == Qt.Key.Key_Left else 1
                    idx = (self.stack.currentIndex() + direction) % len(self.tabs)
                    self.set_tab(idx)
                return True

            if event.type() == QEvent.Type.KeyPress:
                if cmd_pressed:
                    if Qt.Key.Key_1 <= event.key() <= Qt.Key.Key_9:
                        idx = event.key() - Qt.Key.Key_1
                        if idx < len(self.tabs):
                            self.set_tab(idx)
                            return True
                    elif event.key() == Qt.Key.Key_0:
                        if 9 < len(self.tabs):
                            self.set_tab(9)
                            return True
                            
                if event.key() == Qt.Key.Key_Escape:
                    self.ktools.toggle_plugin("kshell")
                    return True
                    
        return super().eventFilter(obj, event)

    def hide_anim(self):
        self.reset_tabs()
        super().hide_anim()

    def reset_tabs(self):
        for tab in self.tabs:
            if hasattr(tab['widget'], 'reset_search'):
                tab['widget'].reset_search()

    @objc.signature(b"v@:@")
    def update_system_theme(self, notification=None):
        try:
            import AppKit
            AppKit.NSUserDefaults.standardUserDefaults().synchronize()
            style = AppKit.NSUserDefaults.standardUserDefaults().stringForKey_("AppleInterfaceStyle")
            is_dark = style == "Dark"
            
            self.setStyleSheet(get_theme(is_dark))
            self.root.style().unpolish(self.root)
            self.root.style().polish(self.root)
            self.root.update()
            
            for tab in self.tabs:
                if hasattr(tab['widget'], 'update_display'):
                    QTimer.singleShot(50, tab['widget'].update_display)
        except:
            pass

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
        
        self._setup_hotkeys()
        
        self.action = QAction("open kshell (⌘space)", self.ktools.manager)
        self.action.triggered.connect(self.toggle_kshell)

    def get_actions(self):
        return [self.action]
    
    def update_theme(self):
        if hasattr(self, 'shell') and self.shell:
            self.shell.update_system_theme()

    def unload(self):
        try:
            if hasattr(self, 'dist_center') and self.dist_center:
                self.dist_center.removeObserver_(self)
        except Exception:
            pass
            
        try:
            if hasattr(self, 'global_monitor') and self.global_monitor:
                NSEvent.removeMonitor_(self.global_monitor)
                self.global_monitor = None
            if hasattr(self, 'local_monitor') and self.local_monitor:
                NSEvent.removeMonitor_(self.local_monitor)
                self.local_monitor = None
            if hasattr(self, 'tap') and self.tap:
                Quartz.CGEventTapEnable(self.tap, False)
                if hasattr(self, 'runLoopSource') and self.runLoopSource:
                    Quartz.CFRunLoopRemoveSource(Quartz.CFRunLoopGetMain(), self.runLoopSource, Quartz.kCFRunLoopCommonModes)
                self.tap = None
        except Exception:
            pass

        try:
            self.action.triggered.disconnect()
        except Exception:
            pass

        if self.shell:
            if hasattr(self.shell, 'anim_group'):
                self.shell.anim_group.stop()
            self.shell.close()
            self.shell.deleteLater()
            self.shell = None

        import gc
        gc.collect()

    def _setup_hotkeys(self):
        def event_tap_callback(proxy, type_, event, refcon):
            try:
                # macos silently kills event taps. love it. hotkeys die permanently if u dont catch kCGEventTapDisabledByTimeout and restart the hook
                if type_ == Quartz.kCGEventTapDisabledByTimeout or type_ == Quartz.kCGEventTapDisabledByUserInput:
                    Quartz.CGEventTapEnable(self.tap, True)
                    return event

                if type_ == Quartz.kCGEventKeyDown:
                    ns_event = NSEvent.eventWithCGEvent_(event)
                    cmd_pressed = bool(ns_event.modifierFlags() & (1 << 20))
                    
                    if cmd_pressed:
                        if ns_event.keyCode() == 49:
                            QTimer.singleShot(0, self.toggle_kshell)
                            return None
            except Exception as e:
                print(f"kshell event tap error: {e}")
            return event

        self._tap_callback = event_tap_callback
        self.tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,
            Quartz.kCGHeadInsertEventTap,
            0,
            (1 << Quartz.kCGEventKeyDown),
            self._tap_callback,
            None
        )
        
        if self.tap:
            self.runLoopSource = Quartz.CFMachPortCreateRunLoopSource(None, self.tap, 0)
            Quartz.CFRunLoopAddSource(Quartz.CFRunLoopGetMain(), self.runLoopSource, Quartz.kCFRunLoopCommonModes)
            Quartz.CGEventTapEnable(self.tap, True)
        else:
            print("kshell: Failed to create active event tap, falling back to passive monitor")
            self.global_monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(NSKeyDownMask, self._global_hotkey_handler)
            self.local_monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(NSKeyDownMask, self._local_hotkey_handler)

    def toggle_kshell(self):
        self.ktools.toggle_plugin("kshell")

    def _global_hotkey_handler(self, event):
        cmd_pressed = bool(event.modifierFlags() & (1 << 20))
        
        if cmd_pressed:
            if event.keyCode() == 49:
                QTimer.singleShot(0, self.toggle_kshell)

    def _local_hotkey_handler(self, event):
        cmd_pressed = bool(event.modifierFlags() & (1 << 20))
        
        if cmd_pressed:
            if event.keyCode() == 49:
                QTimer.singleShot(0, self.toggle_kshell)
                return None
        return event
