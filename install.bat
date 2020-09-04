pip install -r requirements.txt
pip uninstall setuptools
pip install setuptools==44.0.0
python setup.py build
xcopy build\exe.win32-3.8\ G14control\ /E /C