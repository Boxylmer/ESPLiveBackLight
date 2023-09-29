@REM pushd "DesktopApp" 
@REM call ..\.venv\Scripts\activate # expects .venv is in git repo root folder
@REM pyinstaller --noconfirm ^
@REM             --noconsole ^
@REM             --onedir ^
@REM             --contents-directory giblets ^
@REM             --add-data="Application/resources;Application/resources" ^
@REM             --icon=Application/resources/think.ico ^
@REM             --name "Boxman Fiddlejig" ^
@REM             compile_target.py
@REM popd 


.venv\Scripts\python -m pyinstaller ^
                        --noconfirm ^
                        --noconsole ^
                        --onedir ^
                        --contents-directory giblets ^
                        --add-data="Application/resources;Application/resources" ^
                        --icon=Application/resources/think.ico ^
                        --name "Boxman Fiddlejig" ^
                        compile_target.py