
# **Discord Shilling Framework (DSFW) Documentation**
## **Introduction**
The Discord Shilling/Advertising/Self-Promotion Framework allows you to periodically (absolute or in a random time range)  send messages to discord servers and channels (it's an automatic shiller).
It supports sending normal text, discord embeds(you are required to run on an actual bot) , files and can even accept user defined functions that will be called to get the data you want to send. 
The framework also supports formatted logging which tells you what messages succeeded in which channels and failed in which channels(and why they failed).
<br><br>
You can also build an additional layer on top of the framework, because when run, the framework can call a user defined function before starting shilling, allowing you to eg. make an asyncio task that runs parallel to the shilling framework.
<br><br>
The below documentation describes everything you need to start shilling, thank you for reading it. If you don't like to read you can skip to the [Getting Started](#getting_started) section or see [Examples](#code_examples).

## <a id="code_examples"> </a> **Examples** :
***
Because I believe reading documention can be a bit boring, I prepaired some examples in the Examples folder which should show everying you might want to do.<br>
Examples folder: [Examples folder](Examples).
***
<br><br>

# **Regarding Pycord/discord.py**
The DSFW requires a discord API wrapper to work. <br>
The module used by the DSFW is called Pycord (previously discord.py) which works great except it does not allow user accounts to login, so I modified to work with user accounts.
When you install the DSFW, the modified Pycord version is installed with it.<br>
**If you wish to use the Pycord/discord module in your program, you can import it in one of the following ways:**
```py
import pycordmod as discord
```
or
```py
from framework import discord
```
<br><br>

#  **Creatable objects** :
## <a id="framework_embed"> </a>framework.**EMBED** (available to use if running on a **bot account**):
***
The **EMBED** class is an inherited class from discord.Embed meaning it has the same methods as [discord.Embed](https://docs.pycord.dev/en/master/api.html?highlight=discord%20embed#discord.Embed) but you can create a full embed without actually having to call those methods. 
  
### **Parameters:**
- Author name  (author_name)        : str   - Name of the embed author
- Author Image (author_icon)   : str   - URL to author's image
- Image (image)                     : str   - URL to image that will be placed **at the end** of the embed.
- Thumbnail (thumbnail)             : str   - URL to image that will be placed **at top right** of the embed.
- Embedded Fields (fields)          : list  - List of [framework.**EMBED_FIELD**](#framework_embed_field)<br>

### **Methods**
  - ```py
    EMBED.from_discord_embed(
                                object: discord.Embed
                            )
    ```
      - **Info:** The method converts a **discord.Embed** object into a **framework.EMBED object**
      - **Parameters:** 
        - object : discord.Embed = object to convert
<br><br>

## <a id="framework_embed_field"> </a>framework.**EMBED_FIELD** (available to use if running on a **bot account**):
***
The **EMBED_FIELD** is used with combination of [framework.**EMBED**:](#framework_embed) as one of it's parameters that represents one of the fields inside the embedded message.
### **Parameters:**
- Field name (name)         : str  -  Name of the field
- Field content (content)   : str  -  Text that is placed inside the embedded field
- Inline (inline)           : bool -  If True and the previous or next embed field also have inline set to true, it will place this field in the same line as the previous or next field
<br><br>

## <a id="framework_file"> </a>framework.**FILE**:
***
The **FILE** objects represents a file you want to send to discord. 
### **Parameters:**
- File name (filename)  - path to the file you want to send to discord
<br><br>

## <a id="framework_guild"> </a>framework.**GUILD**:
***
The **GUILD** object represents a server to which messages will be sent.
### **Parameters:**
- **Guild ID** - identificator which can be obtain by enabling [developer mode](https://techswift.org/2020/09/17/how-to-enable-developer-mode-in-discord/) in discord's settings and afterwards right-clicking on the server/guild icon in the server list and clicking **"Copy ID"**,
- **List of <u>MESSAGE</u> objects** - Python list or tuple contating **MESSAGE** objects.
- <a id="framework_guild_gen_file_log"></a>**Generate file log** - bool variable, if True it will generate a file log for each message send attempt.
```py
GUILD(

        guild_id=123456789,         ## ID of server (guild)
        messages_to_send=[          ## List MESSAGE objects 
            framework.MESSAGE(...),  
        ],
        generate_log=True           ## Generate file log of sent messages (and failed attempts) for this server 
        )
```
<br>

## <a id="framework_message"></a> framework.**MESSAGE** 
***
The **MESSAGE** object containts parameters which describe behaviour and data that will be sent to the channels.
### **Parameters:**
- <a id="fw_msg_data_period"></a> **Start Period** , **End Period** (start_period, end_period) - These 2 parameters specify the period on which the messages will be sent.
    - **Start Period** can be either:
      - None - Messages will be sent on intervals specified by **End period**,
      - Integer  >= 0 - Messages will be sent on intervals **randomly** chosen between **<u>Start period** and **End period</u>**, where the randomly chosen intervals will be re-randomized after each sent message.<br><br>

- <a id="framework_message_data"></a> **Data** (data) - The data parameter is the actual data that will be sent using discord's API. The **data types** of this parameter can be: 
  - <a id="framework_message_data_types"></a> **str** (normal text),
  - [framework.**EMBED**](#framework_embed),
  - [framework.**FILE**](#framework_file),
  - **list/tuple** containing any of the above arguments (There can up to **1** string, up to **1** embed and up to **10** [framework.FILE](#framework_file) objects, if more than 1 string or embeds are sent, the framework will only consider the last found).
  - **Function** defined by the user:
    - Parameters: The function is allowed to accept anything
    - Return: The function **must** return any of the **above data types** or the **None** object if no data is ready to be sent.<br>
    If **None** is returned by the function, the framework will skip the send attempt and retry after it's [configured period](#fw_msg_data_period). For example you could make the framework call your function on more regular intervals and then decide within the function if anything is to be returned and if nothing is to be returned, you would return None.
    - **IMPORANT:** if you decide to use an user defined function as the data parameter, you **MUST** use the [framework.**FUNCTION**](#framework_decorators_function) decorator on it.
    <br><br>
    When you pass the function to the data parameter, pass it in the next format:
    - ```py

      @framework.FUNCTION # <- IMPORTANT!!!
      def function_name(parameter_1, parameter_2):
          """
          Info: Function returns a different string each time when called by the framework making the sent data dynamic.
          """
          return f"Parameter: {parameter_1}\nTimestamp: {datetime.datetime.now()}"

      framework.MESSAGE(...,
                        data=function_name(parameter_1, parameter_2),
                        ...)
                                                                        
      ```
    - **NOTE 1**: <br>
        When you use the framework.FUNCTION decorator on the function, it returns a special class that is used by the framework to get data.<br>
        Because the decorator returns a class and assigns it to the function name, you can no longer use this function as a regular function,<br>
        so consider making another function with the same definition and a different name or consider making this function to retreive data only.<br>
    - **NOTE 2**: <br>
        If you don't use the [framework.FUNCTION](framework_decorators_function) decorator, the function will only get called once(when you pass it to the data) and will not be called by the framework dynamically.
<br><br>

- **Channel IDs** (channel_ids) - List of IDs of all the channels you want data to be sent into.
- **Clear Previous** (clear_previous) - A bool variable that can be either True of False. If True, then before sending a new message to the channels, the framework will delete all previous messages sent to discord that originated from this message object.
- **Start Now** (start_now) - A bool variable that can be either True or False. If True, then the framework will send the message as soon as it is run and then wait it's period before trying again. If False, then the message will not be sent immediatly after framework is ready, but will instead wait for the period to elapse.<br>
```py
framework.MESSAGE(
                start_period=None,            # If None, messages will be send on a fixed period (end period)
                end_period=15,                # If start_period is None, it dictates the fixed sending period,
                                                # If start period is defined, it dictates the maximum limit of randomized period
                data="Some Text",             # Data yo you want sent to the function (Can be of types : str, embed, file, list of types to the left
                                                # or function that returns any of above types(or returns None if you don't have any data to send yet), 
                                                # where if you pass a function you need to use the framework.FUNCTION decorator on top of it ).
                channel_ids=[123456789],      # List of ids of all the channels you want this message to be sent into
                clear_previous=True,          # Clear all discord messages that originated from this MESSAGE object
                start_now=True                # Start sending now (True) or wait until period
                ),  
```
<br>

#  **Decorators** :
Python decorators are callable objects that you can use to give your function or class extra functionallity. Essentialy they are meant to accept a function or a class as their parameter and then process whatever they are meant to do with the function or class.
More on Python decorators [here](https://realpython.com/primer-on-python-decorators/).<br>
**Inside the framework**, there is only one decorator:

## <a id="framework_decorators_function"></a> framework.**FUNCTION**:
***
- This decorator accepts a function as it's parameter and then returns a object that will be called by the framework. To use an <u>user defined function as parameter</u> to the [framework.MESSAGE data parameter](#framework_message_data), you **MUST** use this decorator beforehand. Please see the **Examples** folder.
- Usage:<br>
<img src="DOC_src\function_decorator_1.png" alt="drawing" width="600"/>
***
<br>

#  **Functions** :
The framework only gives you one function to call making it easy to use:
## <a id="framework_framework_run"></a>framework.**run**:
***
### **Parameters:**
- token             : str       = access token for account
- server_list       : list      = List of framework.GUILD objects
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
                server_log_output="Logging"             # OPTIONAL
                debug=True)                             # OPTIONAL
```
***
<br>

#  **Logging** :

### <a id="logging_sent_msgs"></a>**LOG OF SENT MESSAGES**
The framework can keep a log of sent messages for **each guild/server**. To enable file logging of sent messages, set the parameter [**Generate file log**](#framework_guild_gen_file_log) to True inside each [GUILD OBJECT](#framework_guild).<br> 
Inside the log you will find data of what was sent (text, embed, files), a channel list it succeeded to send this message and a channel list of the ones it failed (If it failed due to slow mode, the message will be sent as soon as possible, overwriting the default period) <br>
All of these file logs will be Markdown files.<br>
<image alt="Server Log" src="DOC_src\framework_server_log_1.png" width=1920>
(Left is raw Markdown code, to the right is rendered Markdown)

<br>

# <a id="getting_started"></a> **Getting started**:
## <u> Installation</u>
To install the framework use the following command:
```fix
py -3 -m pip install Discord-Shilling-Framework
```
or
```fix
python3 -m pip install Discord-Shilling-Framework
```
<br>

## <u> Sending messages </u>
To start sending messages you must first create a python file, e.g <u>*main.py*</u> and import <u>**framework**</u>.<br>
```py
import framework
```
I recommend you take a look at <u>**Examples folder**</u>.


Then define the server list and in that server list, define **GUILD** objects:
```py
guilds = [
    # GUILD 1
    framework.GUILD(
        123456789,       # ID of server (guild)
        [                # List MESSAGE objects 
            framework.MESSAGE(start_period=None, end_period=0, data="", channel_ids=[123456789, 123456789], clear_previous=False, start_now=True),
            framework.MESSAGE(start_period=None, end_period=0, data="", channel_ids=[123456789, 123456789], clear_previous=False, start_now=True),
        ],
        generate_log=True            # Create file log of sent messages for this server
    ),

    # GUILD 2
    framework.GUILD(
        123456789,       # ID of server (guild)
        [                # List MESSAGE objects 
            framework.MESSAGE(start_period=None, end_period=0, data="", channel_ids=[123456789, 123456789], clear_previous=False, start_now=True),
            framework.MESSAGE(start_period=None, end_period=0, data="", channel_ids=[123456789, 123456789], clear_previous=False, start_now=True),
        ],
        generate_log=True            # Create file log of sent messages for this server
    ),

    # GUILD n
    framework.GUILD(
        123456789,       # ID of server (guild)
        [                # List MESSAGE objects 
            framework.MESSAGE(start_period=None, end_period=0, data="", channel_ids=[123456789, 123456789], clear_previous=False, start_now=True),
            framework.MESSAGE(start_period=None, end_period=0, data="", channel_ids=[123456789, 123456789], clear_previous=False, start_now=True),
        ],
        generate_log=True            # Create file log of sent messages for this server
    )
]
```

Now start the framework by calling the [**framework.run()**](#framework_framework_run) function.

```python

def callback():
    print("Framework is now running")

framework.run(  token="account token here",     # MANDATORY (This is the string that contains the account token, I suggest you define it in a secret.py)
                server_list=guilds,             # MANDATORY -- List of GUILD objects
                is_user=False,                  # OPTIONAL -- Must be true if token is from an user account
                user_callback=None,             # OPTIONAL -- Function that is called after framework is run
                server_log_output="Logging",    # OPTIONAL -- The path to the server log file outputs
                debug=True)                     # OPTIONAL -- For easiser debugging if you think your messages aren't being sent (will print TRACE to the console)

```
That's it, your framework is now running and messages will be periodicaly sent.
