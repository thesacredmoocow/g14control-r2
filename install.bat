pip install -r requirements.txt
pip uninstall setuptools
pip install setuptools==44.0.0
python setup.py build
xcopy C:\Users\5353i\Desktop\g14control-master\build\exe.win32-3.8\ C:\G14control\ /E /C