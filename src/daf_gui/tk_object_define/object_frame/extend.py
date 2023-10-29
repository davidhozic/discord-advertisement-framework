HELP_URLS = {
    # "daf": f"https://daf.davidhozic.com/en/v{'.'.join(daf.VERSION.split('.')[:2])}.x/?rtd_search={{}}",
    # "_discord": f"https://docs.pycord.dev/en/v{discord._version.__version__}/search.html?q={{}}",
    "builtins": "https://docs.python.org/3/search.html?q={}"
}

# Mapping which tells the frame which methods can be executed on live objects
EXECUTABLE_METHODS = {
    # daf.guild.GUILD: [daf.guild.GUILD.add_message, daf.guild.GUILD.remove_message],
    # daf.guild.USER: [daf.guild.USER.add_message, daf.guild.USER.remove_message],
    # daf.guild.AutoGUILD: [daf.guild.AutoGUILD.add_message, daf.guild.AutoGUILD.remove_message],
    # daf.client.ACCOUNT: [daf.client.ACCOUNT.add_server, daf.client.ACCOUNT.remove_server]
}

ADDITIONAL_PARAMETER_VALUES = {
    # daf.GUILD.remove_message: {
    #     # GUILD.messages
    #     "message": lambda old_info: old_info.data["messages"]
    # },
    # daf.USER.remove_message: {
    #     # GUILD.messages
    #     "message": lambda old_info: old_info.data["messages"]
    # },
    # daf.AutoGUILD.remove_message: {
    #     # GUILD.messages
    #     "message": lambda old_info: old_info.data["messages"]
    # },
    # daf.ACCOUNT.remove_server: {
    #     # ACCOUNT.servers
    #     "server": lambda old_info: old_info.data["servers"]
    # }
}

DEPRECATION_NOTICES = {
    # daf.AUDIO: [("daf.dtypes.AUDIO", "2.12", "Replaced with daf.dtypes.FILE")],
    # daf.VoiceMESSAGE: [("daf.dtypes.AUDIO as type for data parameter", "2.12", "Replaced with daf.dtypes.FILE")],
}


