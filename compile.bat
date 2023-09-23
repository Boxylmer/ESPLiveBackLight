call .\.venv\Scripts\activate
pyinstaller --noconfirm --noconsole --add-data="think.ico;." compile_target.py
