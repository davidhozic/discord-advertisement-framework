import Config, discord, re, datetime, framework



C_DATA_FILE = "delavnice_params.txt"

def find_key(key, data):
    l_ret =  re.search(f"{key}\s*:.*", data)
    if l_ret != None:
        l_ret = re.sub(f"{key}\s*:","", l_ret.group(0)).rstrip().lstrip()
    return l_ret

def get_msg():
    with open (C_DATA_FILE, 'r') as l_data_file:
        l_data_file_content = l_data_file.read()
        l_delavnice_date = [int(x) for x in find_key("datum",l_data_file_content).split("-")]
        l_content = find_key("snov", l_data_file_content)
        l_link = find_key("povezava", l_data_file_content)
        l_index   = int(find_key("indeks", l_data_file_content))
        pass
    l_time_left=(datetime.datetime(*l_delavnice_date) - datetime.datetime.now()).total_seconds()
    l_delavnice_date = f"{l_delavnice_date[2]}.{l_delavnice_date[1]}.{l_delavnice_date[0]} ob {l_delavnice_date[3]}:{l_delavnice_date[4]}"
    if l_time_left < 2 * Config.C_DAY_TO_SECOND:
        if l_time_left <= 1*Config.C_MINUTE_TO_SECOND:
            l_time_left = "Manj kot minuta"
        elif l_time_left <= 1*Config.C_HOUR_TO_SECOND:
            l_time_left = "{:.2f}".format(l_time_left/Config.C_MINUTE_TO_SECOND)  + " min"
        elif l_time_left <= 1*Config.C_DAY_TO_SECOND:
            l_time_left = "{:.2f}".format(l_time_left/Config.C_HOUR_TO_SECOND) + "h"
        else:
            l_time_left = "{:.2f}".format(l_time_left/Config.C_DAY_TO_SECOND) + "d" 
        l_embed = framework.discord.Embed()
        l_embed.add_field(name="__Arduino Delavnice__", value=f"Pridruzite se {l_index}. Arduino delavnicam", inline=False)    
        l_embed.add_field(name="Vsebina", value=f"{l_content}", inline=False)
        l_embed.add_field(name ="Datum", value=f"{l_delavnice_date}", inline=False)
        l_embed.add_field(name ="Povezava do Zooma", value=f"{l_link}", inline=False)
        return l_embed, "<@&905084973244117112>"
    return None