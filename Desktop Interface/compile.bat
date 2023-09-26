call ..\.venv\Scripts\activate # expects .venv is in git repo root folder
pyinstaller --noconfirm --noconsole --onedir --add-data="Application/resources;Application/resources" --icon=Application/resources/think.ico  compile_target.py
