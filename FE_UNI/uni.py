import re, os, datetime, asyncio, pickle, discord
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
        l_files_to_remove = []
        while True:
            l_files_to_remove.clear()
            for dirname, dirs, filenames in os.walk(CONFIG_READ_FOLDER):
                for filename in filenames:
                    with open(os.path.join(dirname,filename), 'rb') as l_file:
                       l_msg_object = pickle.load(l_file)
                       if datetime.datetime.now() >  l_msg_object.send_date:
                           l_files_to_remove.append(filename)
                           this.stat_post_q.append(l_msg_object)
                    # Remove files
                    for filename in l_files_to_remove:
                        try:
                            os.remove(os.path.join(dirname,filename))
                            l_files_to_remove.remove(filename)
                        finally:
                            pass
            await asyncio.sleep(1)

    @classmethod
    def get_msg(this):
        l_ret = None
        if this.stat_post_q.__len__() > 0:
            l_ret = this.stat_post_q.pop(0)
            l_ret = (l_ret.text, l_ret.embed)
                        
        return l_ret