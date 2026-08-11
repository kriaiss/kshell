<div align="center">
    <pre>
    __         .__           .__  .__   
    |    |/ _| /   _____//   |   \_   _____/|    |   |    |    
    |      <   \_____  \/    ~    \    __)_ |    |   |    |    
    |    |  \  /        \    Y    /        \|    |___|    |___ 
    |____|__ \/_______  /\___|_  /_______  /|_______ \_______ \
            \/        \/       \/        \/         \/       \/
    </pre>
</div>
<p align="center">
  Overlay shell for macOS.
</p>
<p align="center">
    <img src="https://img.shields.io/badge/python-3.12+-blue?style=flat-square" alt="Python">
    <img src="https://img.shields.io/badge/platform-macOS-lightgrey?style=flat-square" alt="Platform">
</p>

⠀

## What is kshell?

`kshell` is a core `ktools` plugin that provides an overlay dashboard for macOS. Instead of keeping all features in one script, `kshell` acts as a host environment for `kshelladdon_*` plugins. 

### Core Features
* **Modular Architecture**: Uses a `QStackedWidget` to mount `kshelladdon_` plugins as tabs.
* **Native Overlays**: `Cmd + Space` global hotkey toggle via PyObjC `NSEvent` interceptors.
* **System Integration**: Transparent backgrounds, smooth slide animations, and automatic support for macOS Dark/Light modes.

⠀

## How to Use (For Users)

1. Download the `kshell` `.zip` archive from the Releases page.
2. Open the **ktools Plugin Manager** from your menu bar and click **import plugins** to install it.
3. To use the global hotkeys (`Cmd + Space`), you must grant your terminal (or Python) `Accessibility` and `Input Monitoring` permissions in `System Settings -> Privacy & Security`.
4. Install any `kshelladdon_*` plugins (like `kterminal` or `ksearch`) the same way.
5. Hit `Cmd + Space` to toggle the `kshell` overlay. Switch tabs with `Cmd + 1-9` or `Cmd + Left/Right`. Hit `Esc` to close it.

⠀

## API & Architecture (For Addon Developers)

`kshell` acts as a tabbed overlay container. If you are building an addon (like a terminal, a calculator, or a search bar), you simply build a `QWidget` and inject it into `kshell`'s internal stack. 

### 1. Mounting your Tab (`register_tab`)
In your addon's initialization phase, retrieve the active `kshell` instance and register your widget. Do this dynamically, because `kshell` might load after your plugin.

```python
kshell = self.ktools.plugins.get('kshell')
if kshell and hasattr(kshell, 'register_tab'):
    # register_tab(id_string, display_name, widget_instance)
    kshell.register_tab("my_addon", "my tab", self.widget)
```

### 2. Auto-Focus and Key Forwarding
`kshell` automatically intercepts key presses (like `Cmd+Space` and `Esc`) at the global level. To ensure your addon receives typing focus correctly when the shell opens, assign your primary input widget (like a `QLineEdit` or `QTextEdit`) to an attribute named `input` or `display` on your main widget class.

```python
class MyTab(QWidget):
    def __init__(self):
        super().__init__()
        self.input = QLineEdit() # kshell will automatically focus this when the tab opens
```

### 3. Cleanup Hooks (`reset_search` and `unregister_tab`)
When `kshell` is hidden (e.g., the user hits `Esc`), it loops through all mounted tabs and looks for a `reset_search()` method. You can implement this to clear input fields automatically.

```python
def reset_search(self):
    self.input.clear()
```

When your plugin is unloaded, you **must** unregister your tab to remove the UI elements from `kshell`'s stack:
```python
def unload(self):
    kshell = self.ktools.plugins.get('kshell')
    if kshell and hasattr(kshell, 'unregister_tab'):
        kshell.unregister_tab("my_addon")
```

### 4. Programmatic Toggling
If your addon performs an action (like launching an app or opening a URL) and you want to automatically close the `kshell` overlay right after, you can trigger `ktools.toggle_plugin("kshell")` directly from your widget:

```python
def execute_action(self):
    # Do your thing...
    
    # Hide the shell
    win = self.window()
    if win and hasattr(win, 'ktools'):
        win.ktools.toggle_plugin("kshell")
```

### 5. UI & Theming Rules (The "kshell" Design Language)
To ensure a cohesive user experience across all tabs, `kshell` enforces a strict, minimalist design philosophy. Addons **must** follow these aesthetic guidelines so they don't look like alien Qt widgets:

* **Backgrounds & Borders**: Never hardcode opaque background colors (e.g., `background: white;`). `kshell` uses a native macOS blurred visual effect (`NSVisualEffectView`). If you use a `QTextEdit`, `QListWidget`, or `QLineEdit`, explicitly set `background: transparent;` and strip the ugly default Qt borders using `self.widget.setFrameStyle(0)`.
* **Typography**: Let `ktools` handle the main font. It globally injects `Menlo` across all UI elements to maintain a unified, terminal-like aesthetic. You do not need to set fonts manually unless you're doing something highly custom.
* **Scrollbars**: Do not style them yourself. `ktools` automatically overrides default Qt scrollbars with a custom, native macOS-style floating design (8px width, rounded handles, transparent background). If your addon uses a `QScrollArea` (like `kshelladdon_klaunchpad`), leave the scrollbar alone and it will blend in perfectly. If your UI doesn't need scrolling, hide them with `self.widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)`.
* **Margins & Spacing**: `kshell` provides a wide horizontal layout (780px). Set your main layout margins to zero (`layout.setContentsMargins(0, 0, 0, 0)`) so you don't double up on padding. Add internal padding to your elements via CSS (e.g., `padding: 15px;`) instead.
* **Smooth Animations**: `kshell` relies heavily on kinetic, smooth UI interactions. If you have interactive elements (like lists or selections), use `QPropertyAnimation` with easing curves (like `QEasingCurve.Type.OutCubic`) rather than instant state changes. See `kshelladdon_klaunchpad` for a reference implementation of a smoothly animated selection indicator.

⠀

by kriaiss.
