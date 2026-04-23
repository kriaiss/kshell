<p align="center">
  <h1 align="center">kshell</h1>
  <p align="center">
    <img src="https://img.shields.io/badge/python-3.12+-blue?style=flat-square" alt="Python">
    <img src="https://img.shields.io/badge/platform-macOS-lightgrey?style=flat-square" alt="Platform">
  </p>
</p>

<p align="center">
  <h1 align="center"># kshell</h1>
  <p align="center">minimalist n lightweight overlay shell for macOS. terminal, launchpad, search, and clipbored history.</p>
  
  <h2 align="center">core features</h1>
  <p align="center">- terminal – integrated zsh/bash session with full vt100 support.</p>
  <p align="center">- launchpad – instant app searching and launching.</p>
  <p align="center">- search – quick web search across google, yandex, youtube, and github (u can change this in the code).</p>

  <h2 align="center">tech stack</h2>
  <p align="center">python 3.12+.</p>
  <p align="center">pyqt6 for the swag interface.</p>
  <p align="center">pyobjc for deep macos integration.</p>
  <p align="center">pyte for terminal emulation.</p>

  <h2 align="center">usage</h2>
  <p align="center">cmd + space – toggle shell visibility./p>
  <p align="center">cmd + 1-4 - switch between tabs.</p>
  <p align="center">esc - hide instantly</p>
</p>


<details>
<summary><b>build & install instructions</b></summary>
  
<p align="center">
  <h2 align="center">### setup</h2>
  <p align="center">```bash</p>
  <p align="center">pip install -r requirements.txt</p>
  <p align="center">python3 main.py</p>

  <h2 align="center">### build .app</h2>
  <p align="center">pyinstaller --noconsole --onefile --osx-bundle-identifier "com.kshell.app" --icon=icon.icns main.py</p>

  <h2 align="center">### also u can download builded .app from releases on github</h2>

  <h2 align="center">### since the app is not signed with an apple developer certificate</h2>
  <p align="center">right-click kshell.app -> open</p>
  <p align="center">go to system settings > privacy n security and click open anyway</p>
  <p align="center">4 hotkeys: allow accessibility and input monitoring in system settings -> privacy n security -> accessibility.</p>

  <p align="center">by kriaiss.</p>
</p>











- clipbored – a smart clipboard history manager that doesn't let your data get "bored".
