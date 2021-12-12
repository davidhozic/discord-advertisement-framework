
# <font size=8>**Shilling Framework Documentation**</font>


## <font size=5> **Framework creatable objects** </font>:

- **GUILD**:
    - The **GUILD** object represents a server to which messages will be sent.
    - <u>Parameters</u>:
        - **Guild ID** - identificator which can be obtain by enabling [developer mode (a.k.a application test mode)](https://discord.com/developers/docs/game-sdk/store) in discord's settings and afterwards right-clicking on the server/guild icon in the server list and clicking **"Copy ID"**,
        - **List of <u>MESSAGE</u> objects** - Python list or tuple contating [MESSAGE](#message) objects.


- **MESSAGE** 
    - The **MESSAGE** object containts parameters which contain data that will be sent to the server/guild but also contains parameters that specify behaviour.
    
    - <u>Parameters</u>:
        - **Start Period** , **End Period** - These 2 parameters specify the period on which the messages will be sent.
            - **Start Period** can be either:
              - None - Messages will be sent on intervals specified by **End period**,
              - Integer larger $\geq$ 0 - Messages will be sent on invertvals **randomly** chosen between **<u>Start period** and **End period</u>**, where the randomly chosen intervals will be randomized after each sent message.
        - **Data** parameter - The data parameter is the actual data that will be sent using discord's API. The **data types** of this parameter can be:
          - String (normal text),
          - [Embed](https://www.quora.com/What-are-embeds-on-Discord) ,
          - List containing: string or embed or (string and embed) - Order in list does not matter,
          - **Function** that accepts no parameters and returns any of the **above** three data types.


## <font size=5> **Functions** </font>:
The framework only gives you one function to call making it easy to use.
That function is **run**. The function only accepts one parameter  called user_callback which is a **function that will be called after the framework has been initialized** which allows you to create parallel tasks to the actual framework.
To access the function, use: **framework.run(user_callback function here)**


## <font size=5> **Getting started** </font>:
To start sending messages you must first create a python file, e.g <u>*main.py*</u> and import <u>**framework**</u>.
