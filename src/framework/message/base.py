"""~ base ~
@Info:
    Contains base definitions for different message classes."""

from    typing import Union
from    ..dtypes import *
from    ..tracing import *
from    ..timing import *
from    ..exceptions import *
import  random
import  _discord as discord


__all__ = (
    "BaseMESSAGE",
)


class BaseMESSAGE:
    """~  BaseMESSAGE  ~
        @Info:
        This is the base class for all the different classes that
        represent a message you want to be sent into discord."""

    __slots__ = (
        "initialized",
        "randomized_time",
        "period",
        "random_range",
        "timer",
        "force_retry",
        "data"
    )

    # The "__valid_data_types__" should be implemented in the INHERITED classes.
    # The set contains all the data types that the class is allowed to accept, this variable
    # is then checked for allowed data types in the "initialize" function bellow.
    __valid_data_types__ = {}

    def __init__(self,
                start_period : Union[float,None],
                end_period : float,
                data,
                start_now : bool=True):
        # If start_period is none -> period will not be randomized
        if start_period is None:            
            self.randomized_time = False
            self.period = end_period
        else:
            self.randomized_time = True
            self.random_range = (start_period, end_period)
            self.period = random.randrange(*self.random_range)

        self.timer = TIMER()
        self.force_retry = {"ENABLED" : start_now, "TIME" : 0}
        self.data = data
        self.initialized = False

    def generate_exception(self, 
                           status: int,
                           code: int,
                           description: str,
                           cls: discord.HTTPException):
        """ ~ method ~
        @Name: generate_exception
        @Info: Generates a discord.HTTPException inherited class exception object
        @Param:
            status: int ~ Atatus code of the exception
            code: int ~ Actual error code
            description: str ~ The textual description of the error
            cls: discord.HTTPException ~ Inherited class to make exception from"""
        resp = Exception()
        resp.status = status
        resp.status_code = status
        resp.reason = cls.__name__
        ex = cls(resp, {"message" : description, "code" : code})
        return ex

    def generate_log_context(self):
        """ ~ method ~
        @Name: generate_log_context
        @Info:
            This method is used for generating a dictionary (later converted to json) of the
            data that is to be included in the message log. This is to be implemented inside the
            inherited classes."""
        raise NotImplementedError
    
    def get_data(self) -> dict:
        """ ~ method ~
        @Name:  get_data
        @Info: Returns a dictionary of keyword arguments that is then expanded
               into other functions (send_channel, generate_log)
               This is to be implemented in inherited classes due to different data_types"""
        raise NotImplementedError

    def is_ready(self) -> bool:
        """ ~ method ~
        @Name:   is_ready
        @Param:  void
        @Info:   This method returns bool indicating if message is ready to be sent"""
        return (not self.force_retry["ENABLED"] and self.timer.elapsed() > self.period or
                self.force_retry["ENABLED"] and self.timer.elapsed() > self.force_retry["TIME"])

    def reset_timer(self) -> None:
        """ ~ method ~
        @Name: restart_time
        @Info: Resets internal timer (and force period)"""
        self.timer.reset()
        self.timer.start()
        self.force_retry["ENABLED"] = False
        if self.randomized_time is True:
            self.period = random.randrange(*self.random_range)

    async def send_channel(self) -> dict:
        """                  ~ send_channel ~
            @Info:
            Sends data to a specific channel, this is seperate from send
            for eaiser implementation of simmilar inherited classes
            @Return:
            The method returns a dictionary containing : {"success": bool, "reason": discord.HTTPException}
            """
        raise NotImplementedError

    async def send(self) -> dict:
        """ ~ async method ~
        Name:   send to channels
        Param:  void
        Info:   This function should be implemented in the inherited class
                and should send the message to all the channels."""
        raise NotImplementedError

    async def initialize_channels(self):
        """ ~ async method ~
        @Name: initialize_channels
        @Info: This method initializes the implementation specific
               api objects and checks for the correct channel inpit context."""
        raise NotImplementedError

    async def initialize_data(self):
        """ ~ async method ~
        @Name:  initialize_data
        @Info:  This method checks for the correct data input to the xxxMESSAGE
                object. The expected datatypes for specific implementation is
                defined thru the static variable __valid_data_types__"""
        # Check for correct data types of the MESSAGE.data parameter
        if not isinstance(self.data, FunctionBaseCLASS):
            # This is meant only as a pre-check if the parameters are correct so you wouldn't eg. start
            # sending this message 6 hours later and only then realize the parameters were incorrect.
            # The parameters also get checked/parsed each period right before the send.

            # Convert any arguments passed into a list of arguments
            if isinstance(self.data, (list, tuple, set)):
                self.data = list(self.data)   # Convert into a regular list to allow removal of items
            else:
                self.data = [self.data]       # Place into a list for iteration, to avoid additional code

            # Check all the arguments
            for data in self.data[:]:
                # Check all the data types of all the passed to the data parameter.
                # If class does not match the allowed types, then the object is removed.
                # The for loop iterates thru a shallow copy (sliced list) of data_params to allow removal of items
                # without affecting the iteration (would skip elements without a copy or use of while loop).

                # The inherited classes MUST DEFINE THE "__valid_data_types__" inside the class which should be a set of the allowed data types

                if (
                        type(data) not in type(self).__valid_data_types__
                    ):
                    if isinstance(data, FunctionBaseCLASS):
                        raise DAFInvalidParameterError(f"The function can only be used on the data parameter directly, not in a iterable. Function: {data.func_name}", DAF_INVALID_TYPE)
                    else:
                        trace(f"INVALID DATA PARAMETER PASSED!\nArgument is of type : {type(data).__name__}\nSee README.md for allowed data types", TraceLEVELS.WARNING)
                        raise DAFInvalidParameterError(f"Invalid data type {type(data).__name__}. Allowed types: {type(self).__valid_data_types__}", DAF_INVALID_TYPE)

            if len(self.data) == 0:
                raise DAFMissingParameterError(f"No data parameters were passed", DAF_MISSING_PARAMETER)


    async def initialize(self, **options):
        """ ~ async method ~
        @Name: initialize
        @Info:
            The initialize method initilizes the message object.
        @Params:
            options :: custom keyword arguments, this differes from inher. to inher. class that
                       is inherited from the BaseGUILD class and must be matched in the inherited class from BaseMESSAGE that
                       you want to use in that specific inherited class from BaseGUILD class"""
        if self.initialized:
            return

        await self.initialize_channels(**options)
        await self.initialize_data()
        self.initialized = True
