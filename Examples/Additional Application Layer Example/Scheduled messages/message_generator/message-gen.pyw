"""
    ~ message-gen  ~
@Info:
This is the GUI you can use to create scheduled messages.
"""

from   PySimpleGUI import *
import discord
import os
import datetime
import base64

#########################################
#                CONFIG                 #
#########################################
## AUTHOR
C_DEFAULT_AUTHOR_NAME = "ŠSFE"
C_DEFAULT_AUTHOR_IMG   = ""

## Thumbnail
C_DEFAULT_THUMBNAIL = "https://media.discordapp.net/attachments/937257424547639336/949024540938371172/logo.png"

## SEND CHANNEL
C_DEFAULT_CHANNEL_ID  = 787107420782198834

            
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
            if stats.st_size > 8.389e+6:
                raise UNIFILE.FileSizeException("File size can be maximum 8 MB")
            with open(filename, "rb") as l_openedfile:
                self.fdata = l_openedfile.read()


# USER UI DEFINITIONS
class MAIN_MENU:
    # Class variables
    theme("Dark2")

    c_embed_layout = \
        [
            # Title
            [Text("Embed title:", size=(12,None)), Input(size=(90,None), key="-EMBED-TITLE-INPUT-")],
            [Text("Title link:", size=(12,None)), Input(size=(90,None), key="-EMBED-TITLE-LINK-INPUT-")],
            # Author
            [Text("Author name: ", size=(12,None)), Input(C_DEFAULT_AUTHOR_NAME, size=(90,None), key="-EMBED-AUTHOR-NAME-INPUT-")],
            [Text("Author icon url: ", size=(12,None)), Input(C_DEFAULT_AUTHOR_IMG, size=(90,None), key="-EMBED-AUTHOR-IMG-INPUT-")],
            [Text(size=(None,3))],
            # Embedded fields
            [Text("Field name: ",size=(10,None))],
            [Input(size=(94,None),key="-EMBED-FIELD-INPUT-IME-")],
            [Text("Field content: ")],
            [Multiline(size=(100,20),key="-EMBED-POLJE-INPUT-VSEBINA-"), Listbox(UNIEMBEDEDFIELD.all_fields, size=(50,20), key="-INPUT-DATA-", enable_events=True),Button("Add field",key="-ADD-EMBED-FIELD-",size=(10,20), button_color="#000000"), Button("Remove field",size=(10,20), key="-DELETE-EMBED-FIELD-", button_color="#000000")],

            # Embedded image
            [Text("Image url: ",size=(10,None)), Input(key="-EMBED-IMAGE-INPUT-",size=(80,None))],
            [Text("Thumbnail url: ",size=(10,None)), Input(C_DEFAULT_THUMBNAIL, key="-EMBED-THUMBNAIL-INPUT-",size=(80,None))]
        ]

    c_file_layout = \
        [
            [Input(visible=False,key="-ADD-SENDING-FILES-", enable_events=True), FilesBrowse("Add files", button_color="#000000")],
            [Button("Remove files", key="-REMOVE-SENDING-FILES-", button_color="#000000")],
            [Listbox([],select_mode=SELECT_MODE_EXTENDED,key="-FILES-SENDING-LIST-", size=(50,25))]
        ]
    c_normal_text_layour = \
        [   
            [Multiline(size=(200,50), key="-TEXT-")]
        ]
    c_main_layout = \
    [
        [Input(size=(50,None),key="-SAVE-", enable_events=True, disabled=True, visible=False),FileSaveAs("Save", file_types=(('JSON', '.json'),), button_color="#000000"), Input(size=(50,None),key="-OPEN-FILE-", visible=False, enable_events=True), FileBrowse("Open",file_types=(("JSON",".json"),), button_color="#000000")],
        [Text("Date: (Format: Day.Month.Year) "), Input(key="-DATUM-", size=(10,None)), Text("Hour: (Format: Hour.Minutes)"), Input(key="-URA-", size=(10,None)), Text("Channel ID"), Input(C_DEFAULT_CHANNEL_ID,key="-KANAL-", size=(20,None))],
        [TabGroup( [[Tab("Normal text", c_normal_text_layour),Tab("Embedded text", c_embed_layout),Tab("Files", c_file_layout)]]   )],
    ]
    c_window = Window("Obvestila-Generator", layout=c_main_layout, finalize=True, resizable=True)

    @classmethod
    def update_embed_list(self):
        self.c_window.Element("-INPUT-DATA-").update([x.name for x in UNIEMBEDEDFIELD.all_fields])
    
    
    @classmethod
    def get_file_list(self):
        return UNIFILE.all_files 

    @classmethod
    def update_file_list(self):
        self.c_window.Element("-FILES-SENDING-LIST-").update([x.fname for x in UNIFILE.all_files])


def serialize(obj):
    ret = {
        "text" : obj.text,
        "channel" : obj.channel,
        "embed" : {
                "title" : obj.embed.title,
                "author" : {"name": obj.embed.author.name, "icon_url": obj.embed.author.icon_url},
                "thumbnail" : obj.embed.thumbnail.url,
                "url" : obj.embed.url,
                "image" : obj.embed.image.url,
                "fields" : [
                    {"inline" : field.inline, "name": field.name, "value": field.value} for field in obj.embed.fields
                ]
            } if obj.embed is not None else None,
        "send_date" : {
            "seconds" : obj.send_date.timestamp()
        },
        "files" : [
            {"fname" : file.fname, "fdata" : base64.b64encode(file.fdata).decode("ascii")} for file in obj.files
        ] if obj.files is not None else None,
    }
    return json.dumps(ret, indent=4)

def deserialize(data):
    ret = UNIMESSAGE()
    d = json.loads(data)
    ret.text = d["text"]
    ret.channel = d["channel"]
    ret.send_date = datetime.datetime.fromtimestamp(d["send_date"]["seconds"])
    if d["files"] is not None:
        ret.files = []
        for file in d["files"]:
            ret.files.append(UNIFILE(file["fname"], base64.b64decode(file["fdata"])))
    if d["embed"] is not None:
        ret.embed = discord.Embed()
        ret.embed.title = d["embed"]["title"]
        ret.embed.url = d["embed"]["url"]
        ret.embed.set_author(name=d["embed"]["author"]["name"], icon_url=d["embed"]["author"]["icon_url"])
        ret.embed.set_thumbnail(url=d["embed"]["thumbnail"])
        ret.embed.set_image(url=d["embed"]["image"]) 
        ret.embed._fields = d["embed"]["fields"]
    return ret
                    
def main_loop():
    # INIT 
    MAIN_MENU.c_window["-EMBED-POLJE-INPUT-VSEBINA-"].Widget.configure(undo=True)
    MAIN_MENU.c_window["-TEXT-"].Widget.configure(undo=True)
    
    while True:
        l_key, l_values = MAIN_MENU.c_window.read() # Read event and get dictionary of all data

        if l_key == WIN_CLOSED:
            break

        elif l_key == "-INPUT-DATA-" and l_key in l_values and l_values[l_key].__len__() > 0:     # Selected one of embed elements
            l_selection = l_values[l_key][0]
            # Load selected element into editor
            for l_embed in UNIEMBEDEDFIELD.all_fields:
                if l_embed.name == l_selection:
                    break
            MAIN_MENU.c_window.Element("-EMBED-FIELD-INPUT-IME-").update(l_embed.name)
            MAIN_MENU.c_window.Element("-EMBED-POLJE-INPUT-VSEBINA-").update(l_embed.text)


        elif l_key == "-OPEN-FILE-" and l_values["-OPEN-FILE-"]:            
            l_file = l_values[l_key]
            l_msg = None
            MAIN_MENU.c_window.Element("-OPEN-FILE-").update("")
            with open(l_file, "r", encoding="utf-8") as l_file:
                l_msg =  deserialize(l_file.read())
            
            # Generate embeds table
            UNIEMBEDEDFIELD.all_fields.clear()
            if l_msg.embed is not None:
                for l_embed_var in l_msg.embed.fields:
                    UNIEMBEDEDFIELD.all_fields.append(UNIEMBEDEDFIELD(l_embed_var.name, l_embed_var.value))
            # Update other embed data 
                MAIN_MENU.c_window.Element("-EMBED-AUTHOR-IMG-INPUT-").update(l_msg.embed.author.icon_url)
                MAIN_MENU.c_window.Element("-EMBED-IMAGE-INPUT-").update(l_msg.embed.image.url)
                MAIN_MENU.c_window.Element("-EMBED-AUTHOR-NAME-INPUT-").update(l_msg.embed.author.name)
                MAIN_MENU.c_window.Element("-EMBED-THUMBNAIL-INPUT-").update(l_msg.embed.thumbnail.url)
                MAIN_MENU.c_window.Element("-EMBED-TITLE-INPUT-").update(l_msg.embed.title)
                MAIN_MENU.c_window.Element("-EMBED-TITLE-LINK-INPUT-").update(l_msg.embed.url)
            else:
                MAIN_MENU.c_window.Element("-EMBED-AUTHOR-IMG-INPUT-").update("")
                MAIN_MENU.c_window.Element("-EMBED-IMAGE-INPUT-").update("")
                MAIN_MENU.c_window.Element("-EMBED-AUTHOR-NAME-INPUT-").update("")
                MAIN_MENU.c_window.Element("-EMBED-THUMBNAIL-INPUT-").update("")
                MAIN_MENU.c_window.Element("-EMBED-TITLE-INPUT-").update("")
                MAIN_MENU.c_window.Element("-EMBED-TITLE-LINK-INPUT-").update("")

            
            # Generate file table
            if l_msg.files:
                UNIFILE.all_files = l_msg.files

            # Update time windows
            MAIN_MENU.c_window.Element("-DATUM-").update(f"{l_msg.send_date.day}.{l_msg.send_date.month}.{l_msg.send_date.year}")
            MAIN_MENU.c_window.Element("-URA-").update(f"{l_msg.send_date.hour}.{l_msg.send_date.minute}")
            # Update channel input
            MAIN_MENU.c_window.Element("-KANAL-").update(l_msg.channel)
            # Update normal texy
            MAIN_MENU.c_window.Element("-TEXT-").update(l_msg.text)
            
            MAIN_MENU.update_embed_list()
            MAIN_MENU.update_file_list()

        elif l_key == "-SAVE-" and l_values["-SAVE-"] != "": # Save to file
            try:
                l_embed = None
                l_files = None
                l_text = l_values["-TEXT-"]
                if l_text == "":
                    l_text = None
                MAIN_MENU.c_window.Element("-SAVE-").update("") # Clear input in case cancell is called in the next save attempts

                try:
                ## Datetime variables
                    l_parsed_day, l_parsed_month, l_parsed_year = l_values["-DATUM-"].lstrip().rstrip().split(".")
                    l_parsed_hour, l_parsed_minutes  = l_values["-URA-"].lstrip().rstrip().split(".")
                    l_scheduled_time = None
                    l_parsed_hour, l_parsed_minutes,  = int(l_parsed_hour), int(l_parsed_minutes)
                    l_parsed_day, l_parsed_month, l_parsed_year = int(l_parsed_day), int(l_parsed_month), int(l_parsed_year)
                    l_scheduled_time = datetime.datetime(l_parsed_year, l_parsed_month, l_parsed_day, l_parsed_hour, l_parsed_minutes)
                except Exception as ex:
                    Print(f"Invalid date/hour entry")
                    continue
                
                # Generate channel ids list
                l_channel = int(l_values["-KANAL-"])
                if UNIEMBEDEDFIELD.all_fields:
                    l_embed = discord.Embed(color=discord.Color.green())
                    # Set title
                    l_embed.title = l_values["-EMBED-TITLE-INPUT-"]
                    # Set title link
                    l_embed.url = l_values["-EMBED-TITLE-LINK-INPUT-"]
                    # Set author
                    l_embed.set_author(name=l_values['-EMBED-AUTHOR-NAME-INPUT-'], icon_url=l_values["-EMBED-AUTHOR-IMG-INPUT-"])
                    # Set embed image
                    l_embed.set_image(url=l_values["-EMBED-IMAGE-INPUT-"])
                    #Set thumbnail
                    l_embed.set_thumbnail(url=l_values["-EMBED-THUMBNAIL-INPUT-"])
                    for element in UNIEMBEDEDFIELD.all_fields:
                        l_embed.add_field(name=element.name, value=element.text, inline=False)

                    
                # Generate files
                if UNIFILE.all_files:
                    l_files = UNIFILE.all_files

                with open(l_values['-SAVE-'], "w", encoding="utf-8") as l_file:
                    l_msg_object = UNIMESSAGE(l_text, l_embed, l_files,l_scheduled_time, l_channel)
                    l_file.write(serialize(l_msg_object))
            except Exception as ex:
                Print(f"Unable to save file")
            
        elif l_key == "-ADD-EMBED-FIELD-":                    # Add embed to list
            # Remove embed with same name if it exists
            for l_embed in UNIEMBEDEDFIELD.all_fields:
                if l_embed.name == l_values["-EMBED-FIELD-INPUT-IME-"]:
                    UNIEMBEDEDFIELD.all_fields.remove(l_embed)
                    break

            UNIEMBEDEDFIELD.all_fields.append(UNIEMBEDEDFIELD(l_values["-EMBED-FIELD-INPUT-IME-"], l_values["-EMBED-POLJE-INPUT-VSEBINA-"]))
            MAIN_MENU.update_embed_list()
            
        elif l_key == "-DELETE-EMBED-FIELD-" and l_values["-INPUT-DATA-"].__len__() > 0:                  # Delete embed from list based on name
            l_selection = l_values["-INPUT-DATA-"]
            for l_embed in UNIEMBEDEDFIELD.all_fields:
                if l_embed.name == l_selection[0]:
                    UNIEMBEDEDFIELD.all_fields.remove(l_embed)
                    break
            MAIN_MENU.update_embed_list()

        #################################################
        # FILES LAYOUT
        #################################################
        elif l_key == "-ADD-SENDING-FILES-" and l_values["-ADD-SENDING-FILES-"]:
            l_file_list  = l_values["-ADD-SENDING-FILES-"].split(";")
            l_prev_files = MAIN_MENU.get_file_list()
            if l_file_list.__len__() + l_prev_files.__len__() <= 10:
                for l_file in l_file_list:
                    if l_file not in UNIFILE.all_files:
                        try:
                            UNIFILE.all_files.append(UNIFILE(l_file))
                        except Exception as ex:
                            Print(f"Napaka pri datoteki: {l_file}\nNapaka: {ex}\n\n")
                MAIN_MENU.update_file_list()
            else:
                Print("Maksimalno stevilo datotek je lahko 10!")

            
            MAIN_MENU.c_window.Element("-ADD-SENDING-FILES-").update("")
            

        elif l_key == "-REMOVE-SENDING-FILES-" and l_values["-FILES-SENDING-LIST-"]:
            UNIFILE.all_files = [x for x in UNIFILE.all_files if x.fname not in l_values["-FILES-SENDING-LIST-"]]
            MAIN_MENU.update_file_list()
            
            
if __name__ == "__main__":
    main_loop()