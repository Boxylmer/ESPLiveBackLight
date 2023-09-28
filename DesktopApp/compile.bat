pushd "DesktopApp" 
call ..\.venv\Scripts\activate # expects .venv is in git repo root folder
pyinstaller --noconfirm ^
            --noconsole ^
            --onedir ^
            --contents-directory giblets ^
            --add-data="Application/resources;Application/resources" ^
            --icon=Application/resources/think.ico ^
            --name "Boxman Fiddlejig" ^
            compile_target.py
popd 