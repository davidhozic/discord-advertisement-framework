import re, os, datetime, asyncio, pickle, discord, debug
### SSFE OBVESTILA
CONFIG_READ_FOLDER = "Obvestila"


def find_key(key, data):
    l_ret =  re.search(f"{key}\s*=\s*\".*?\"", data, re.DOTALL)
    if l_ret != None:
        l_ret = re.sub(f"{key}\s*=","", l_ret.group(0)).rstrip().lstrip().replace("\"", "")
    return l_ret

class MESSAGE:
    def __init__(this, text, embed, send_date):
        this.text = text
        this.embed = embed
        this.send_date = send_date
        
class EMBEDED:      
    def __init__(this, pr_name, pr_text):
        this.name = pr_name
        this.text = pr_text
        

def get_msg():
    l_msg_object = None
    l_ret = None
    for dirname, dirs, filenames in os.walk(CONFIG_READ_FOLDER):
            for filename in filenames:
                if filename.endswith(".bin"):
                    try:
                        with open(os.path.join(dirname,filename), 'rb') as l_file:
                            l_msg_object = pickle.load(l_file)
                    except Exception as ex:
                        debug.TRACE(f"Unable to read file, error:\n{ex}", debug.TRACE_LEVELS.ERROR)

                    if l_msg_object is not None and datetime.datetime.now() >=  l_msg_object.send_date:
                        os.remove(os.path.join(dirname, filename))
                        l_ret = []
                        if l_msg_object.text != None:
                            l_ret.append(l_msg_object.text)
                        if l_msg_object.embed != None:
                            l_ret.append(l_msg_object.embed)
                        break          
    return l_ret