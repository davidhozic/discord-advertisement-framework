import framework, datetime, os, random



already_sent = False
randomized_images = []

IMAGE_PATH = "./app/images/"

@framework.data_function
def get_data():
    global already_sent, randomized_images
    datum=datetime.datetime.now()
    if datum.hour == 10 and not already_sent:        
        already_sent = True
        if not randomized_images:
            found_images = [os.path.join(IMAGE_PATH,x) for x in os.listdir("./app/images")]
            while found_images:
                randomized_images.append(found_images.pop(random.randrange(0,len(found_images))))
        image = randomized_images.pop(0)
        text = \
        """\
    Good morning @everyone\nDate: {:02d}.{:02d}.{:02d} - {:02d}:{:02d}\
    """.format(datum.day,datum.month,datum.year,datum.hour,datum.minute)
        return text, framework.FILE(image) # Return message to be sent

    elif datum.hour == 11 and already_sent:
        already_sent = False
    return None # Return None if nothing is to be send