# kshell
<img src="https://img.shields.io/badge/python-3.12+-blue?style=flat-square" alt="Python">
<img src="https://img.shields.io/badge/platform-macOS-lightgrey?style=flat-square" alt="Platform">

minimalist n lightweight overlay shell for macOS. terminal, launchpad, search, and clipbored history.

![kshell preview](kshell.gif)
  
### core features
>terminal – integrated zsh/bash session with full vt100 support.
>launchpad – instant app searching and launching.
>search – quick web search across google, yandex, youtube, and github (u can change this in the code).
>clipbored – a smart clipboard history manager that doesnt let ur data get "bored".

### tech stack
>python 3.12+.
>pyqt6 for the swag interface.
>pyobjc for deep macos integration.
>pyte for terminal emulation.

### usage
>cmd + space – toggle shell visibility.
>cmd + 1-4 - switch between tabs.
>esc - hide instantly.

<details>
<summary><b>build & install instructions</b></summary>
  
### setup
>```bash
>pip install -r requirements.txt
>python3 main.py

### build .app
>pyinstaller --noconsole --onefile --osx-bundle-identifier "com.kshell.app" --icon=icon.icns main.py
also u can download builded .app from releases on github

### since the app is not signed with an apple developer certificate
>right-click kshell.app -> open
>go to system settings > privacy n security and click open anyway
>for hotkeys: allow accessibility and input monitoring in system settings -> privacy n security -> accessibility.

by kriaiss.
