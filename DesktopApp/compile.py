import PyInstaller.__main__

PyInstaller.__main__.run([
    '--noconfirm',
    '--noconsole',
    '--onedir',
    '--contents-directory', 'giblets',
    '--add-data', 'DesktopApp/Application/resources;Application/resources',
    '--icon', 'DesktopApp/Application/resources/think.ico',
    '--name', 'Boxman Fiddlejig',
    '--distpath', './DesktopApp/dist',
    '--workpath', './DesktopApp/build',
    './DesktopApp/compile_target.py',
])