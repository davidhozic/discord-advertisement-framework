"""
    ~  The advertiser server  ~
@Info:
This file is the server script for sending scheduled messages.
You don't need to change anything here, all the configuration can be done in
conf.py file.
"""


from contextlib import suppress
from framework import discord
import framework as fw
import asyncio
import conf
import os
import re
import datetime
import json
import base64



m_awaiting_send     = [] # (Ready) Messages buffer waiting to be sent

class UNIMESSAGE:
    def __init__(self, text=None, embed=None, files=None, send_date=None, channel=None):
        self.text = text
        self.embed = embed
        self.files = files

        self.send_date = send_date
        self.channel = channel

class UNIEMBEDEDFIELD:      
    all_fields = []
    def __init__(self, pr_name, pr_text):
        self.name = pr_name
        self.text = pr_text

class UNIFILE:
    class FileSizeException(Exception):
        pass
    
    all_files = []
    def __init__(self, filename, fdata=None):
        self.fname = re.sub(r".*(\/|\\)", "", filename)
        self.fdata = fdata
        if fdata is None:
            stats = os.stat(filename)
            if stats.st_size > 8000000:
                raise UNIFILE.FileSizeException("Velikost datoteke je lahko najvec 8MB!")
            with open(filename, "rb") as l_openedfile:
                self.fdata = l_openedfile.read()

def serialize(obj):
    """
    ~  serialize  ~
    @Param: UNIMESSAGE object
    @Info:
        This function converts a UNIMESSAGE objects into json form, so it can be transfered to
        an eg. FTP server that then decodes it.
        This is only used by the message generator.
    """
    ret = None
    with suppress(Exception):
        ret = {
            "text" : obj.text,
            "channel" : obj.channel,
            "files" : [
                {"fname" : file.fname, "fdata" : base64.b64encode(file.fdata).decode("ascii")} for file in obj.files
            ] if obj.files is not None else None,
            "embed" : {
                    "title" : obj.embed.title if discord.Embed.Empty != obj.embed.title and not isinstance(obj.embed.title, discord.embeds.EmbedProxy) else discord.embeds.EmptyEmbed,
                    "author" : {"name": obj.embed.author.name, "icon_url": obj.embed.author.icon_url},
                    "thumbnail" : obj.embed.thumbnail.url,
                    "image" : obj.embed.image.url,
                    "fields" : [
                        {"inline" : field.inline, "name": field.name, "value": field.value} for field in obj.embed.fields
                    ]
                } if obj.embed is not None else None,
            "send_date" : {
                "seconds" : obj.send_date.timestamp(),
                "tz" :  obj.send_date.tzinfo
            }
        }
    return json.dumps(ret)

def deserialize(data):
    """
    ~  deserialize  ~
    @Param: json data
    @Info:
        This function is used to convert a json file representing a scheduled message
        into a UNIMESSAGE object which is a scheduled message object.
    """
    ret = None
    with suppress(Exception):
        ret = UNIMESSAGE()
        d = json.loads(data)
        ret.text = d["text"]
        ret.channel = d["channel"]
        ret.send_date = datetime.datetime.fromtimestamp(d["send_date"]["seconds"], d["send_date"]["tz"])
        if d["files"] is not None:
            ret.files = []
            for file in d["files"]:
                ret.files.append(UNIFILE(file["fname"], base64.b64decode(file["fdata"])))
        if d["embed"] is not None:
            ret.embed = discord.Embed()
            ret.embed.title = d["embed"]["title"]
            ret.embed.set_author(name=d["embed"]["author"]["name"], icon_url=d["embed"]["author"]["icon_url"])
            ret.embed.set_thumbnail(url=d["embed"]["thumbnail"])
            ret.embed.set_image(url=d["embed"]["image"]) 
            ret.embed._fields = d["embed"]["fields"]
    return ret


async def parser():
    """
    ~  async parser  ~
    @Param: void
    @Info:
        This is the task responsible for parsing files inside the OBV/UPLOAD_FILES_HERE folder
        , which contains json files that represent a scheduled message.
    """
    while True:
        for path, dirname, files in os.walk(conf.UPLOAD_FOLDER):
            for filename in files:
                filepath = os.path.join(path, filename)
                filestats = os.stat(filepath)
                if filename.endswith(".json") and filestats.st_size < 100 * 10**6: # Ends with bin and smaller than 100 MB
                    message_contex = None
                    #os.system("sudo chmod 777 OBV/UPLOAD_FILES_HERE/ -R") # For debugging
                    with suppress(Exception):
                        with open(filepath,"r") as op_file:
                            message_contex = deserialize(op_file.read())

                    # Successfully parsed
                    if message_contex is not None:
                        if message_contex.send_date <= datetime.datetime.now():
                            m_awaiting_send.append ( message_contex )

                    if message_contex is None or message_contex.send_date <= datetime.datetime.now():
                        with suppress(FileNotFoundError):
                            os.remove(filepath)

                else:
                    with suppress(FileNotFoundError):
                        os.remove(filepath)
            
        
        await asyncio.sleep(conf.CHECK_PERIOD)

async def message_deleter():
    """
    ~  async message_deleter  ~
    @Param: void
    @Info:
        This is a task that deletes messages sent by this bot
        if they are older than the configured period in conf.py (DELETE_PERIOD).
        The resolution is 1 hour.
    """
    client = fw.get_client()
    channels = []
    for guild in conf.WHITELISTED_GUILDS:
        guild["CHANNEL-IDs"] = [x for x in [client.get_channel(x) for x in guild["CHANNEL-IDs"] if x not in conf.DO_NOT_DELETE_CH_IDS] if x is not None]
        channels.extend(guild["CHANNEL-IDs"] )
        
    while True:
        for channel in channels:
            try:
                async for message in channel.history(limit=20):
                    if message.author.id == client.user.id and (datetime.datetime.now(tz=message.created_at.tzinfo) -  message.created_at).total_seconds() >= conf.DELETE_PERIOD:
                        for tries in range(3):
                            try:
                                await message.delete()
                                await asyncio.sleep(2)
                                break
                            except discord.HTTPException as ex:
                                if ex.status == 429:
                                    await asyncio.sleep(int(ex.headers["retry-after"]))
                            except Exception:
                                break
            except discord.HTTPException as ex:
                pass

        await asyncio.sleep(1*fw.C_HOUR_TO_SECOND)


@fw.data_function
def get_data(ch_id):
    """
    ~  get_data  ~
    @Param: 
        - channel id:
            This function is called multiple times for each channel defined in the conf.py
            and is used to check which channel the data is to be sent, the function
            checks the buffer if any messages in the buffer are meant for this channel
            and then returns the data if any or the None object signaling noting is to be sent.
    @Info:
        This is the data retriever function used by the framework to get the data
        that is to be sent into a certain channel.
    """
    context = None
    for unimsg in m_awaiting_send:
        if type(unimsg) is UNIMESSAGE and unimsg.channel == ch_id: # The channel id must match the ch_id as this is the channel that requested data
            # Delete any of the temporary files that were possibly created by the previos calls
            for filepath in os.listdir(conf.UPLOAD_TEMP_FILE_FOLDER):
                filepath = os.path.join(conf.UPLOAD_TEMP_FILE_FOLDER, filepath)
                os.remove(filepath)

            context = unimsg
            m_awaiting_send.remove(unimsg)
   
            l_ret = []
            if context.files is not None:
                # Create temporary files as the API wrapper library doesn't support direct raw data to be passed
                for file_context in context.files:
                    tmp_file_path = os.path.join(conf.UPLOAD_TEMP_FILE_FOLDER,file_context.fname)
                    with open(tmp_file_path, "wb") as tmp_file:
                        tmp_file.write(file_context.fdata)
                    l_ret.append( fw.FILE(tmp_file_path) )
            if context.text is not None:
                l_ret.append(context.text)
            if context.embed is not None:
                l_tr_datum = datetime.datetime.now()
                l_fw_embed = fw.EMBED.from_discord_embed(context.embed).set_footer(text="{:02d}.{:02d}.{:04d}\t{:02d}:{:02d}".format(l_tr_datum.day,
                                                                                                                    l_tr_datum.month,
                                                                                                                    l_tr_datum.year,
                                                                                                                    l_tr_datum.hour,
                                                                                                                    l_tr_datum.minute))
                                                                                                                    
                l_ret.append( l_fw_embed ) 
            return l_ret

    return None


async def main():
    """
    ~  main  ~
    @Param: void
    @Info:
        This is the callback function that is called after the framework is run,
        it starts the json file parser where the json files contain the scheduled message
        and the message deleter task deletes messages that were sent with the bot and are older
        than the configured period.
    """
    tasks = [
                asyncio.create_task(parser()),  # File parser 
                asyncio.create_task(message_deleter())  # Discord message deleter
            ]
    asyncio.gather(*tasks)


# Create the server list
servers = [
        fw.GUILD (
            guild_id=guild["SERVER-ID"], 
            messages_to_send= [
                fw.TextMESSAGE(None, 5, get_data(ch_id), [ch_id], "send", True) for ch_id in guild["CHANNEL-IDs"]
            ],
            generate_log=True
        ) for guild in conf.WHITELISTED_GUILDS   
]


if __name__ == "__main__":
    fw.run(
            conf.TOKEN,
            servers,
            user_callback=main,
            server_log_output=conf.UPLOAD_ATTEMPT_FOLDER,
            debug=True)
