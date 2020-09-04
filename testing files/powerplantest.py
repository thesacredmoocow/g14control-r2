import os
import subprocess
default_power_plan = "Balanced"
dpp_GUID = ""
alt_power_plan = "temp power plan"
app_GUID = ""
#print(subprocess.check_output(["powercfg", "-getactivescheme"]))
all_plans = subprocess.check_output(["powercfg", "/l"])
print(str(all_plans).split('\\n'))
for i in str(all_plans).split('\\n'):
    if i.find(default_power_plan) != -1:
        dpp_GUID = i.split(' ')[3]
    if i.find(alt_power_plan) != -1:
        app_GUID = i.split(' ')[3]
print(dpp_GUID)
print(app_GUID)
#print(subprocess.check_output(["powercfg", "/s", "381b4222-f694-41f0-9685-ff5bb260df2e"]))
#Power Scheme GUID: 381b4222-f694-41f0-9685-ff5bb260df2e  (Balanced)
#Power Scheme GUID: ce457de0-6c6b-4294-9262-02eaa222e48a  (temp power plan)