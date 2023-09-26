call .\.venv\Scripts\activate
pyinstaller --noconfirm --noconsole --add-data="think.ico;." --icon=think.ico compile_target.py
