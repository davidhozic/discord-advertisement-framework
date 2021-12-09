from PySimpleGUI import *
from asyncio import *
import pickle, discord

class MESSAGE:
    def __init__(this, text, embed, send_date):
        this.text = text
        this.embed = embed
        this.send_date = send_date
        
class EMBEDED:      
    def __init__(this, pr_name, pr_text):
        this.name = pr_name
        this.text = pr_text


m_embeds = []
# USER UI DEFINITIONS
class MAIN_MENU:
    # Class variables
    c_layout = \
        [   [Text("Ime datoteke: "), Input(size=(50,None),key="-SAVE-", enable_events=True, disabled=True, visible=False),FileSaveAs("Shrani", file_types=(('BIN', '.bin'),))],
            [Text("Datum posiljanja: [DAN, MESEC, URA, MINUTE]"), Input(key="-DAN-", size=(10,None)), Input(key="-MESEC-", size=(10,None)),Input(key="-URA-", size=(10,None)),Input(key="-MINUTE-", size=(10,None))],
            [Text("------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")],
            [Text("Seznam vseh embeddov:"), Button("Brisi embed", key="-DELETE-EMBED-")],
            [Listbox(m_embeds, size=(400,20), key="-INPUT-DATA-", select_mode=LISTBOX_SELECT_MODE_EXTENDED)],
            [Text("------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")],
            [Text("Mention: "), Input(size=(20,None), key="-MENTION-")],
            [Text("Ime Embedda: "), Input(size=(50,None),key="-EMBED-INPUT-IME-"), Button("Dodaj Embed", key="-ADD-EMBED-")],
            [Text("Vsebina Embeda: ")],
            [Multiline(size=(400,20),key="-EMBED-INPUT-VSEBINA-")]
        ]
    c_scrollable_layout = \
    [
        [Column(c_layout, scrollable=True,size=(1280,720))]
    ]
    c_window = Window("Obvestila-Generator", layout=c_scrollable_layout, finalize=True, size=(1280,720), resizable=True)

    @classmethod
    def update_list(this):
        global m_embeds
        this.c_window.Element("-INPUT-DATA-").update([x.name for x in m_embeds])


async def main_loop():
    global m_embeds
    while True:
        l_key, l_values = MAIN_MENU.c_window.read() # Read event and get dictionary of all data

        if l_key == WIN_CLOSED:
            break

        elif l_key == "-SAVE-": # Save to file
            l_embed = discord.Embed()
            l_mention = l_values["-MENTION-"]
            l_embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/909382417087881276/32be4995f99c9a36279ece66d125960c.png?size=256")
            for element in m_embeds:
                l_embed.add_field(name=element.name, value=element.text, inline=False)

            with open(l_values['-SAVE-'], "wb") as l_file:
                l_msg_object = MESSAGE(l_mention, l_embed, datetime.datetime(datetime.datetime.now().year, int(l_values["-MESEC-"]), int(l_values["-DAN-"]), int(l_values["-URA-"]), int(l_values["-MINUTE-"])))
                l_file.write(pickle.dumps(l_msg_object))
            
        elif l_key == "-ADD-EMBED-":                    # Add embed to list
            m_embeds.append(EMBEDED(l_values["-EMBED-INPUT-IME-"], l_values["-EMBED-INPUT-VSEBINA-"]))
            MAIN_MENU.update_list()
            
        elif l_key == "-DELETE-EMBED-":                  # Delete embed from list based on name
            l_selection         = l_values["-INPUT-DATA-"]
            m_embeds = [x for x in m_embeds if x.name not in l_selection]   # Remove selection
            MAIN_MENU.update_list()


        await sleep(0.10)
if __name__ == "__main__":
    run(main_loop())