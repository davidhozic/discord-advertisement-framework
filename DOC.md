# **Discord Advertisement Framework (Bot)**
## **Table of contents**
- [**Discord Advertisement Framework (Bot)**](#discord-advertisement-framework-bot)
  - [**Table of contents**](#table-of-contents)
  - [**Introduction**](#introduction)
  - [**Examples**](#examples)
- [**Creatable objects**](#creatable-objects)
  - [framework.**EMBED**](#frameworkembed)
    - [**Parameters**](#parameters)
    - [**Methods**](#methods)
  - [framework.**EmbedFIELD**](#frameworkembedfield)
    - [**Parameters**](#parameters-1)
  - [framework.**FILE**](#frameworkfile)
    - [**Parameters**](#parameters-2)
  - [framework.**AUDIO**](#frameworkaudio)
    - [**Parameters**](#parameters-3)
  - [framework.**GUILD**](#frameworkguild)
    - [**Parameters**](#parameters-4)
  - [framework.**USER**](#frameworkuser)
    - [**Parameters**](#parameters-5)
    - [**Example**](#example)
  - [framework.**xxxMESSAGE**](#frameworkxxxmessage)
    - [**xxxMESSAGE types**](#xxxmessage-types)
    - [**Common parameters**](#common-parameters)
  - [framework.**TextMESSAGE**](#frameworktextmessage)
    - [**Parameters**](#parameters-6)
    - [**Example**](#example-1)
  - [framework.**DirectMESSAGE**](#frameworkdirectmessage)
    - [**Parameters**](#parameters-7)
    - [**Example**](#example-2)
  - [framework.**VoiceMESSAGE**](#frameworkvoicemessage)
    - [**Parameters**](#parameters-8)
    - [**Example**](#example-3)
- [**Functions**](#functions)
  - [framework.**run(...)**](#frameworkrun)
    - [**Parameters**](#parameters-9)
  - [framework.**get_client()**](#frameworkget_client)
    - [**Description**](#description)
  - [framework.**shutdown()**](#frameworkshutdown)
    - [**Description**](#description-1)
- [**Decorators**](#decorators)
  - [framework.**data_function**](#frameworkdata_function)
- [**Logging**](#logging)
  - [**LOG OF SENT MESSAGES**](#log-of-sent-messages)
  - [**Trace messages**](#trace-messages)
- [**Regarding Pycord/discord.py**](#regarding-pycorddiscordpy)

<br>

## **Introduction**
Welcome to the Discord Advertisement Framework.<br>
If you ever needed a tool that allows you to advertise by **automatically sending messages to discord channels (text, voice and direct messages)**, this is the tool for you.
It supports advertising to **multiple guilds at once**, where it can generate **message logs** for each of those guilds where you can easilly find out what messages were successfully sent and which failed (and why they failed).<br>
It allows you to automatically send messages in **custom time ranges** where those ranges can be either **fixed** or **randomized** after each sent message.<br>
You can send data like **normal text**, **embeds**, **files** (TextMESSAGE, DirectMESSAGE) or **audio file** for streaming to discord voice channels (VoiceMESSAGE) , where the data can even be **dynamic** by providing the framework with an **user defined function**.<br>

**Why is it called a framework?**<br>
The project named framework, because it allows you to create additional application layers on top of it by using an user defined function that returns dynamic content.<br>
For an example see [**Examples/Coffee example**](Examples/Additional%20Application%20Layer%20Example/Coffee).

The below documentation describes everything you need to start advertising, thank you for reading it.<br>
If you would like to start right away, you can skip to the [Getting Started](#getting-started) section or see [Examples](#examples).
<br>

## **Examples**
Because I believe reading documention can be a bit boring, I prepaired some examples in the Examples folder which should show everying you might want to do.<br>
Examples folder: [Examples folder](Examples).
<br>

For help with the object parameters see [**Creatable Objects**](#creatable-objects).
<br>

#  **Creatable objects**
## framework.**EMBED**

| **NOTE**<br>                                                       |
| ------------------------------------------------------------------ |
| This is only available to use if running on a **bot account**.<br> |
<br>

The **EMBED** class is an inherited class from discord.Embed meaning it has the same methods as [discord.Embed](https://docs.pycord.dev/en/master/api.html?highlight=discord%20embed#discord.Embed) but you can create a full embed without actually having to call those methods. 
  
### **Parameters**
- Inherited from discord.Embed:
  - For original parameters see [discord.Embed](https://docs.pycord.dev/en/master/api.html?highlight=discord%20embed#discord.Embed)

- Additional:
    - Author name (author_name) - Name of the author
    - Author icon (author_icon) - URL to author's icon
    - Author image(image)       - URL to an image (placed at the bottom)
    - Thumbnail (thumbnail)     - URL for a thumbnail (placed top right)
    - Fields (fields)           - list of [EmbedFIELD](#frameworkembed_field) objects   

### **Methods**
  - ```py
    EMBED.from_discord_embed(
                                _object: discord.Embed
                            )
    ```
      - **Info:** The method converts a **discord.Embed** object into a **framework.EMBED object**
      - **Parameters** 
        - _object : discord.Embed = object to convert
<br>

## framework.**EmbedFIELD**
| **NOTE**<br>                                                       |
| ------------------------------------------------------------------ |
| This is only available to use if running on a **bot account**.<br> |
<br>

The **EmbedFIELD** is used with combination of [framework.**EMBED**:](#frameworkembed) as one of it's parameters that represents one of the fields inside the embedded message.

### **Parameters**
- Field name (name)         : str  -  Name of the field
- Field content (content)   : str  -  Text that is placed inside the embedded field
- Inline (inline)           : bool -  If True and the previous or next embed field also have inline set to true, it will place this field in the same line as the previous or next field
<br>

## framework.**FILE**
The **FILE** objects represents a file you want to send to discord. 

### **Parameters**
- File name (filename)  - path to the file you want to send to discord
<br>

## framework.**AUDIO**
The **AUDIO** parameter represents an audio stream, you want streamed into a voice channel.

### **Parameters**
- File name (filename)  - path to the audio file you want to stream to discord
<br>

## framework.**GUILD**
The **GUILD** object represents a server to which messages will be sent.

### **Parameters**
- **guild_id** - identificator which can be obtain by enabling [developer mode](https://techswift.org/2020/09/17/how-to-enable-developer-mode-in-discord/) in discord's settings and afterwards right-clicking on the server/guild icon in the server list and clicking **"Copy ID"**,
- **messages_to_send** - List of [**TextMESSAGE**](#frameworktextmessage) and/or [**VoiceMESSAGE**](#frameworkvoicemessage)  objects
- **generate_log** - bool variable, if True it will generate a file log for each message send attempt.
```py
framework.GUILD(

        guild_id=123456789,         ## ID of server (guild)
        messages_to_send=[          ## List xxxMESSAGE objects 
            framework.TextMESSAGE(...),  
            framework.VoiceMESSAGE(...),  
            framework.TextMESSAGE(...),  
            framework.VoiceMESSAGE(...),
            ...
        ],
        generate_log=True           ## Generate file log of sent messages (and failed attempts) for this server 
        )
```
<br>

## framework.**USER**
The **USER** object represents a user to which **direct messages** will be sent.
### **Parameters**
- **user_id** - identificator which can be obtain by enabling [developer mode](https://techswift.org/2020/09/17/how-to-enable-developer-mode-in-discord/) in discord's settings and afterwards right-clicking on the server/guild icon in the server list and clicking **"Copy ID"**,
- **messages_to_send** - List of [**DirectMESSAGE**](#frameworkdirectmessage) objects
- **generate_log** - bool variable, if True it will generate a file log for each message send attempt.
### **Example**
```py
framework.USER(

        user_id=123456789,                  ## ID of the user 
        messages_to_send=[                  ## List DirectMESSAGE objects 
            framework.DirectMESSAGE(...),
            framework.DirectMESSAGE(...),
            ...
        ],
        generate_log=True                   ## Generate file log of sent messages (and failed attempts) for this server 
        )
```
<br>

## framework.**xxxMESSAGE**
### **xxxMESSAGE types**
The framework has 3 types of MESSAGE objects:
- [**Text**MESSAGE](#frameworktextmessage)
- [**Direct**MESSAGE](#frameworkdirectmessage)
- [**Voice**MESSAGE](#frameworkvoicemessage)

, where the **Text**MESSAGE and **Direct**MESSAGE are very simillar with the difference being **Direct**MESSAGE is for direct messages (DMs).

### **Common parameters**
Since all the classes inherit the **Base**MESSAGE class, they share certain parameters:
- **start_period** and **end_period**: `int` - The parameters specify the period on which framework will
try to send messages and also (if you are using the [data_function](#frameworkdatafunction)), the period on which your data function wil be called.
    - **start_period** can be one of the 2:
        - **Integer >= 0**: the period will be randomly choosen between **start_period** and **end_period**, and it is randomized after each send attempt.
        - **None**: The sending period will be equal to the **end_period**

- data: `message type dependant` - The data parameter describes the data that will be sent to Dicord, <br>
this is more detaily defined in the inherited classes.
- start_now: `bool` - This parameter dictates if the message should be sent as soon as the framework is ran or wait the period first.

## framework.**TextMESSAGE**
The **Text**MESSAGE class represents a message that will be sent into **text channels**.
### **Parameters**
Additionaly to the [common parameters](#common-parameters) the **Text**MESSAGE accepts the following parameters:
- **data** - The data parameter is the actual data that will be sent using discord's API. The **data types** of this parameter can be: 
     -  **str** (normal text),
     - [framework.**EMBED**](#frameworkembed),
     - [framework.**FILE**](#frameworkfile),
     - **list/tuple** containing the above listed types (maximum 1 str, 1 embed and up to 10 files)
     - **Function** defined by the user:
        <a id=text_msg_param_function></a>
        - Parameters: The function is allowed to accept anything
        - Return: The function **must** return any of the **above data types** or the **None** object if no data is ready to be sent.<br>
        If **None** is returned by the function, the framework will skip the send attempt and retry after it's **configured period**. For example you could make the framework call your function on more regular intervals and then decide within the function if anything is to be returned and if nothing is to be returned, you would return None.
        - **IMPORANT:** if you decide to use an user defined function as the data parameter, you **MUST** use the [framework.**data_function**](#frameworkdatafunction) decorator on it.
        When you pass the function to the data parameter, pass it in the next format:
           
            | **NOTE 1**:                                                                                                                                                                                                                                                                                                                                                                                                                       |
            | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
            | When you use the framework.data_function decorator on the function, it returns a special class that is used by the framework to get data,<br> so consider making another function with the same definition and a different name or consider making this function to retreive data only.<br> Because the decorator returns a class and assigns it to the function name, you can no longer use this function as a regular function, |
                                    
            | **NOTE 2**:                                                                                                                                                                           |
            | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
            | If you don't use the **framework.data_function** decorator, the function will only get called once(when you pass it to the data) and will not be called by the framework dynamically. |
        - Usage:
            ```py
            @framework.data_function # <- IMPORTANT!!!
            def function_name(parameter_1, parameter_2):
                """
                Info: Function returns a different string each time when called by the framework making the sent data dynamic.
                """
                return f"Parameter: {parameter_1}\nTimestamp: {datetime.datetime.now()}"
            
            framework.TextMESSAGE(...,
                            data=function_name(parameter_1, parameter_2),
                            ...)    
            ```

- **channel_ids** - List of IDs of all the channels you want data to be sent into.
- **mode**   - string variable that defines the way message will be sent to a channel.<br>
  This parameter can be:
  - "send"  - Each period a new message will be sent to a channel,
  - "edit"  - The previous message will be edited or a new sent if it doesn't exist,
  - "clear-send" - Previous message sent to a channel will be deleted and then a new message will be sent.<br><br>

### **Example**
```py
framework.TextMESSAGE(
                start_period=None,              # If None, messages will be send on a fixed period (end period)
                end_period=15,                  # If start_period is None, it dictates the fixed sending period,
                                                # If start period is defined, it dictates the maximum limit of randomized period
                data= ["Some Text",
                       framework.EMBED(...),
                       framework.FILE("file.txt")    ],               # Data yo you want sent to the function (Can be of types : str, embed, file, list of types to the left
                                                # or function that returns any of above types(or returns None if you don't have any data to send yet), 
                                                # where if you pass a function you need to use the framework.data_function decorator on top of it ).
                channel_ids=[123456789],        # List of ids of all the channels you want this message to be sent into
                mode="send",                    # New message will be sent each period (can also be "edit" to edit previous message in channel or "clear-send" to delete old message and then send a new message)
                start_now=True                  # Start sending now (True) or wait until period
                ),  
```
<br>

## framework.**DirectMESSAGE**
The **Direct**MESSAGE represents a message that is sent into direct messages of an user. It used with USER class as the **messages_to_send** parameter.<br>
Apart from being sent into direct messages it is very simillar to the [framework.**TextMESSAGE**](#frameworktextmessage).

### **Parameters**
Additionally to the [common parameters](#common-parameters) the **Direct**MESSAGE accepts the following parameters:
- data - This is exactly the same as the data parameter for the [**Text**MESSAGE parameters](#frameworktextmessage), please refer to it's parameters section.
- mode - This is exactly the same as the data parameter for the [**Text**MESSAGE parameters](#frameworktextmessage), please refer to it's parameters section.

### **Example**
```py
framework.USER(
        user_id=123456789,                                  # ID of server (guild)
        messages_to_send=[                                  # List MESSAGE objects
            framework.DirectMESSAGE(
                                    start_period=None,      # If None, messages will be send on a fixed period (end period)
                                    end_period=15,          # If start_period is None, it dictates the fixed sending period,
                                                            # If start period is defined, it dictates the maximum limit of randomized period
                                    data=["Hello World",    # Data you want to sent to the function (Can be of types : str, embed, file, list of types to the left
                                        l_file1,            # or function that returns any of above types(or returns None if you don't have any data to send yet),
                                        l_file2,            # where if you pass a function you need to use the framework.FUNCTION decorator on top of it ).
                                        l_embed],           
                                    mode="send",            # "send" will send a new message every time, "edit" will edit the previous message, "clear-send" will delete
                                                            # the previous message and then send a new one
                                    start_now=True          # Start sending now (True) or wait until period
                                   ),  
        ],
        generate_log=True                                   ## Generate file log of sent messages (and failed attempts) for this user 
```
<br><br>

## framework.**VoiceMESSAGE**
The **Voice**MESSAGE represents a message that will be **streamed** into an audio channel.
| **NOTE 1**                                                                                                |
| --------------------------------------------------------------------------------------------------------- |
| **VoiceMESSAGE** requires  [**FFMPEG**](https://www.ffmpeg.org/) installed and added to **PATH** to work. |

| **NOTE 2**                                                                                                                                                          |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| The period for VoiceMESSAGE dictates the period of CONNECTING.                                                                                                      |
| If your period is 10 second and your audio file is 5 seconds long, then the between messages will be 5 seconds and time between connecting to VC will be 10 seconds |

### **Parameters**
Additionally to the [common parameters](#common-parameters) the **Voice**MESSAGE accepts the following parameters:
- **channel_ids** - List of IDs of all the channels you want data to be sent into.
- data - this parameter represents the data that is actually send to Discord. It can be:
  - [framework.**AUDIO**](#frameworkaudio) - This class represents an audio file that is going to be streamed.
  - **list** containing one audio file, if more are given, only the last is considered. This is allowed only for analogity with the TextMESSAGE and DirectMESSAGE data parameters.
  - **Function** defined by the user:
    - Return: The function **must** return any of the **above data types** or the **None** object if no data is ready to be sent.<br>
    - Other rules here are the same as in [framework.**TextMESSAGE** function parameter](#text_msg_param_function)

### **Example**
```py
framework.VoiceMESSAGE(
                start_period=None,                          # If None, messages will be send on a fixed period (end period)
                end_period=15,                              # If start_period is None, it dictates the fixed streaming period (period of channel join).,
                data=[framework.AUDIO("rick.mp3")],         # Data you want to send (Can be of types : AUDIO or function that returns any of above types [or returns None if you don't have any data to send yet])
                    
                channel_ids=[12345],
                start_now=True
            )
```

# **Functions**
## framework.**run(...)** 
### **Parameters**
- token             : str       = access token for account
- server_list       : list      = List of [framework.GUILD](#frameworkguild) objects
- is_user           : bool      = Set to True if token is from an user account and not a bot account
- user_callback     : function  = User callback function (gets called after framework is ran)
- server_log_output : str       = Path where the server log files will be created
- debug             : bool      = Print trace message to the console,
                                    usefull for debugging if you feel like something is not working
```py
framework.run(  token="your_token_here",                # MANDATORY
                server_list = [framework.GUILD(...),    # MANDATORY
                                framework.GUILD(...)],
                is_user=False,                          # OPTIONAL
                user_callback=None,                     # OPTIONAL
                server_log_output="History"             # OPTIONAL
                debug=True)                             # OPTIONAL
``` 
<br>

## framework.**get_client()**
### **Description**
The framework.**get_client** returns an object which is used to interact with Discord using their API. <br>
You can call this function to get the internal Client object instead of making a new Client objects.<br>
See more here: **[discord.Client](https://docs.pycord.dev/en/master/api.html?highlight=client#discord.Client)**.
<br>

## framework.**shutdown()**
### **Description**
The framework.**shutdown()** functions accepts no parameters and returns None.<br>
It is used to fully shutdown the framework and then **exit** out of the program.<br>


# **Decorators**
**Inside the framework**, there is only one decorator:

## framework.**data_function**

- This decorator accepts a function as it's parameter and then returns a object that will be called by the framework. To use an <u>user defined function as parameter</u> to the [framework.TextMESSAGE/framework.VoiceMESSAGE/DirectMESSAGE](#frameworkxxxmessage) data parameter, you **MUST** use this decorator beforehand. Please see the **Examples** folder.
- Usage:
    ```py
    import datetime
    import framework as fw

    ####################################################################################################
    @fw.data_function # <---- VERY IMPORTANT! If you don't do this, the function will only be called when you pass it to the data parameter
    def some_function(parameter1, parameter2):
        l_dt = datetime.datetime.now()
        return f"Good day! It is {l_dt.day}.{l_dt.month}.{l_dt.year}  {l_dt.hour}:{l_dt.minute}"

    @fw.data_function
    def some_other_function():
        audio_list  = ["Rickroll.mp3", "Careless_Whisper.mp3", ...]
        return fw.AUDIO( audio_list.pop(random.randrange(0, len(audio_list))) ) 
    ####################################################################################################

    servers = [
        fw.GUILD(
            guild_id=123456,
            messages_to_send=[
                fw.TextMESSAGE(
                            start_period=None,
                            end_period=1 * fw.C_DAY_TO_SECOND,
                            data=some_function(1234, 5678),
                            channel_ids= [21345, 23132, 2313223],
                            mode="send",
                            start_now=True
                            ),
                fw.VoiceMESSAGE(
                            start_period=None,
                            end_period=60,
                            data=some_other_function(),
                            channel_ids= [21345, 23132],
                            start_now=True
                            )
            ],
            generate_log=True
        ),
        fw.USER(
            user_id=123456789,
            messages_to_send=[
                fw.DirectMESSAGE(
                            start_period=None,
                            end_period=15,

                            data=["Hello World",
                                    l_file1,
                                    l_file2,
                                    l_embed],
                            mode="send",
                            start_now=True
                            ),  
                    ],
                    generate_log=True
                )
    ]

    ...
    ```
<br>

#  **Logging**
## **LOG OF SENT MESSAGES**
The framework can keep a log of sent messages for **each guild/server**. To enable file logging of sent messages, set the parameter **Generate file log** to True inside each [GUILD OBJECT](#frameworkguild).<br> 
Inside the log you will find data of what was sent, a channel list it succeeded to send this message and a channel list of the ones it failed (If it failed due to slow mode, the message will be sent as soon as possible, overwriting the default period) <br>
All of these file logs will be Markdown files.<br><br>
![TextMESSAGE log](documentation_dep/msg_log_1.png)
<br><br>
![VoiceMESSAGE log](documentation_dep/msg_log_2.png)
<br> 

## **Trace messages**
In case you feel like the framework is not doing it's job properly, eg. you feel like some messages aren't being send or the framework just stops without advertising, the framework offers **console logging** of **trace** messages. Trace messages can be **informative** (eg. which account is logged in), they can be **warnings** (eg. some channels could not be found),<br>
or they can be **errors**. <br>
Most of the trace messages won't stop the framework but will only removed the failed objects and print it to the console, becase you could, eg. get kicked from a server resulting in some channels<br>
not being found.<br><br>
To **enable** trace messages, set the **debug** option to True inside the **[framework.run](#frameworkrun)** function.
<br>

# **Regarding Pycord/discord.py**
The DAF requires a discord API wrapper to work. <br>
The module used by the DAF is called Pycord (previously discord.py) which works great except it does not allow user accounts to login, so I modified to work with user accounts.
When you install the DAF, the modified Pycord version is installed with it.<br>
**If you wish to use the Pycord/discord module in your program, you can import it like this:**
```py
from framework import discord
```
