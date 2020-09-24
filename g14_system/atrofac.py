import os


def set_atrofac(config, user_settings, asus_plan, cpu_curve=None, gpu_curve=None, plugged_in=False, game_running=False):
    user_settings.set("cpu_curve", cpu_curve, plugged_in=plugged_in, game_running=game_running)
    user_settings.set("gpu_curve", gpu_curve, plugged_in=plugged_in, game_running=game_running)
    user_settings.set("plan", asus_plan, plugged_in=plugged_in, game_running=game_running)
    user_settings.set("name", "Custom", plugged_in=plugged_in, game_running=game_running)
    atrofac = str(os.path.join(config.get('temp_dir') + "atrofac-cli.exe"))
    if cpu_curve is not None and gpu_curve is not None:
        os.popen(
            atrofac + " fan --cpu " + cpu_curve + " --gpu " + gpu_curve + " --plan " + asus_plan
        )
    elif cpu_curve is not None and gpu_curve is None:
        os.popen(
            atrofac + " fan --cpu " + cpu_curve + " --plan " + asus_plan
        )
    elif cpu_curve is None and gpu_curve is not None:
        os.popen(
            atrofac + " fan --gpu " + gpu_curve + " --plan " + asus_plan
        )
    else:
        os.popen(
            atrofac + " plan " + asus_plan
        )
