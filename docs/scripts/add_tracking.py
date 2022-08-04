import os


PATH = "./build/html"
for file in os.listdir(PATH):
    data = ""
    file = os.path.join(PATH, file)
    if not os.path.isfile(file):
        continue
    with open(file, "r+", encoding="utf-8") as reader:
        if not file.endswith(".html"):
            continue
        data = reader.read()
        data = data.replace("<head>", '<head>\n<script defer data-domain="daf.davidhozic.top" src="https://plausible.io/js/plausible.js"></script>')

    with open(file, "w", encoding="utf-8") as writer:
        writer.write(data)


