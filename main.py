import datetime, Config, framework, random, copy
from framework import GUILD, MESSAGE


C_DELAVNICE_DATE = "4.12.2021"
## Messages constants
C_MESSAGE = """Arduino Delavnice - {date}:
Pridruzite se arduino delavnicam, ki bodo {date} ob 17.15 uri <@&905084973244117112>
Preostali cas: {time_left}"""

def get_msg():
    l_time_left=(datetime.datetime(2021,12,4,17,15) - datetime.datetime.now()).total_seconds()
    if l_time_left < C_DAY_TO_SECOND*3:
        if l_time_left <= 1*Config.C_MINUTE_TO_SECOND:
            l_time_left = "Manj kot minuta"
        elif l_time_left <= 1*Config.C_HOUR_TO_SECOND:
            l_time_left = "{:.2f}".format(l_time_left/Config.C_MINUTE_TO_SECOND)  + " min"
        elif l_time_left <= 1*Config.C_DAY_TO_SECOND:
            l_time_left = "{:.2f}".format(l_time_left/Config.C_HOUR_TO_SECOND) + "h"
        else:
            l_time_left = "{:.2f}".format(l_time_left/Config.C_DAY_TO_SECOND) + "d"     
        return C_MESSAGE.format(time_left=l_time_left, date=C_DELAVNICE_DATE)
    return None

class CATS:
    template = [
"https://i.natgeofe.com/n/46b07b5e-1264-42e1-ae4b-8a021226e2d0/domestic-cat_thumb_2x3.jpg",
"https://cdn.britannica.com/q:60/91/181391-050-1DA18304/cat-toes-paw-number-paws-tiger-tabby.jpg",
"https://static01.nyt.com/images/2021/09/14/science/07CAT-STRIPES/07CAT-STRIPES-mediumSquareAt3X-v2.jpg",
"https://icatcare.org/app/uploads/2018/07/Thinking-of-getting-a-cat.png",
"https://i.guim.co.uk/img/media/26392d05302e02f7bf4eb143bb84c8097d09144b/446_167_3683_2210/master/3683.jpg?width=1200&height=1200&quality=85&auto=format&fit=crop&s=49ed3252c0b2ffb49cf8b508892e452d",
"https://images-na.ssl-images-amazon.com/images/I/71+mDoHG4mL.png",
"https://images.unsplash.com/photo-1615789591457-74a63395c990?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxzZWFyY2h8MXx8ZG9tZXN0aWMlMjBjYXR8ZW58MHx8MHx8&w=1000&q=80",
"https://static.independent.co.uk/2021/06/16/08/newFile-4.jpg?width=982&height=726&auto=webp&quality=75",
"https://img.webmd.com/dtmcms/live/webmd/consumer_assets/site_images/article_thumbnails/other/cat_relaxing_on_patio_other/1800x1200_cat_relaxing_on_patio_other.jpg",
"https://images.unsplash.com/photo-1604675223954-b1aabd668078?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxleHBsb3JlLWZlZWR8M3x8fGVufDB8fHx8&w=1000&q=80",
"https://hips.hearstapps.com/hmg-prod.s3.amazonaws.com/images/close-up-of-cat-wearing-sunglasses-while-sitting-royalty-free-image-1571755145.jpg?crop=1.00xw:0.754xh;0,0.122xh&resize=1200:*, https://media.npr.org/assets/img/2021/08/11/gettyimages-1279899488_wide-f3860ceb0ef19643c335cb34df3fa1de166e2761-s1100-c50.jpg,https://icatcare.org/app/uploads/2018/06/Layer-1704-1200x630.jpg,https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSM1cDnT1Q5ZrkfLfxiSgFvC2ZsjpngynJGvg&usqp=CAU,https://media.istockphoto.com/photos/gorgeous-ginger-cat-on-isolated-black-background-picture-id1018078858?k=20&m=1018078858&s=612x612&w=0&h=N8HorY5Ipk-RibWqx3zPERGpdB0ZT8mIhCvkDPRql6A="
]
    randomized = []
    @classmethod
    def randomize(this):
        tmp = copy.copy(CATS.template)
        CATS.randomized.clear()
        while len(tmp) > 0:
            CATS.randomized.append(tmp.pop(random.randrange(0, len(tmp))))
    @classmethod
    def get_cat_pic(this):
        if not len(CATS.randomized):
            CATS.randomize()
        return f"Daily cat pic:\n {CATS.randomized.pop(0)}\n Lp Aproksimacka"

############################################################################################
#                               GUILD MESSAGES DEFINITION                                  #
############################################################################################

GUILD.server_list = [
GUILD(
        639031067868921861,                          # ID Serverja
        # Messages
        [   #       min-sec                     max-sec      sporocilo   #IDji kanalov
            MESSAGE(start_period=0, end_period=Config.C_DAY_TO_SECOND , text=get_msg, channels=[904382137204101130], clear_previous=True, start_now=True)
        ]
    )
]
                                     
############################################################################################

if __name__ == "__main__":
    framework.run()