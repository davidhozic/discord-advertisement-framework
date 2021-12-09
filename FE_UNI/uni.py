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
        

class FE_UNI_OBVESTILA:
    # Class variables
    stat_post_q = [] # Messages queue
    
    def __init__(this):
        pass
    @classmethod                        
    async def file_processor(this):
        while True:
            for dirname, dirs, filenames in os.walk(CONFIG_READ_FOLDER):
                for filename in filenames:
                    if filename.endswith(".bin"):
                        l_msg_object = None
                        try:
                            with open(os.path.join(dirname,filename), 'rb') as l_file:
                                l_msg_object = pickle.load(l_file)
                        except Exception as ex:
                            debug.TRACE(f"Unable to read file, error:\n{ex}", debug.TRACE_LEVELS.ERROR)

                        if l_msg_object is not None and datetime.datetime.now() >  l_msg_object.send_date:
                            this.stat_post_q.append(l_msg_object)
                            os.remove(os.path.join(dirname, filename))
            await asyncio.sleep(1)

    @classmethod
    def get_msg(this):
        l_ret = None
        if this.stat_post_q.__len__() > 0:
            l_ret = this.stat_post_q.pop(0)
            l_ret.text = l_ret.text.rstrip().lstrip()
            if l_ret.text != "":
                l_ret = (l_ret.text, l_ret.embed)
            else:
                l_ret = l_ret.embed
                        
        return l_ret