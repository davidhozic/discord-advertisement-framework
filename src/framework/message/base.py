"""
    Contains base definitions for different message classes."""

from    typing import Dict, Set, Tuple, Union
from    ..dtypes import *
from    ..tracing import *
from    ..timing import *
from    ..exceptions import *
from    .. import misc
import  random
import  _discord as discord
import  asyncio


__all__ = (
    "BaseMESSAGE",
)

class BaseMESSAGE:
    """
    This is the base class for all the different classes that
    represent a message you want to be sent into discord.
    
    Parameters
    -----------------
    start_period: Union[int, None]
        If this this is not None, then it dictates the bottom limit for range of the randomized period. Set this to None
                                         for a fixed sending period.
    end_period: int
        If start_period is not None, this dictates the upper limit for range of the randomized period. If start_period is None, then this
                            dictates a fixed sending period in SECONDS, eg. if you pass the value `5`, that means the message will be sent every 5 seconds.
    data: inherited class dependant
        The data that will be sent to Discord. Valid data types are defined inside `__valid_data_types__` set.
    start_now: bool
        Dictates if the message should be send immediately after framework start, or wait the period first.
    """
    __slots__ = (
        "randomized_time",
        "period",
        "start_period",
        "end_period",
        "timer",
        "force_retry",
        "data",
        "update_semaphore",
        "_deleted"
    )

    __logname__: str = "" # Used for registering SQL types and to get the message type for saving the log

    # The "__valid_data_types__" should be implemented in the INHERITED classes.
    # The set contains all the data types that the class is allowed to accept, this variable
    # is then checked for allowed data types in the "initialize" function bellow.
    __valid_data_types__ = {}

    def __init__(self,
                start_period : Union[int, None],
                end_period : int,
                data,
                start_now):
        # If start_period is none -> period will not be randomized
        self.start_period = start_period
        self.end_period   = end_period
        if start_period is None:            
            self.randomized_time = False
            self.period = end_period
        else:
            self.randomized_time = True
            self.period = random.randrange(self.start_period, self.end_period)

        self.timer = TIMER()
        self.force_retry = {"ENABLED" : start_now, "TIME" : 0}
        self.data = data
        misc._write_attr_once(self, "_deleted", False)
        misc._write_attr_once(self, "update_semaphore", asyncio.Semaphore(1))

    @property
    def deleted(self) -> bool:
        """
        Property that indicates if an object has been deleted from the shilling list.

        If this is True, you should dereference this object from any variables.
        """
        return self._deleted

    def _delete(self):
        """
        Sets the deleted flag to True, indicating the user should stop
        using this message.
        """
        self._deleted = True

    def _generate_exception(self, 
                           status: int,
                           code: int,
                           description: str,
                           cls: discord.HTTPException) -> discord.HTTPException:
        """
        Generates a discord.HTTPException inherited class exception object.
        This is used for generating dummy exceptions that are then raised inside the `._send_channel()`
        method to simulate what would be the result of a API call, without actually having to call the API (reduces the number of bad responses).

        Parameters
        -------------
        status: int
            Discord status code of the exception.
        code: int
            Discord error code.
        description: str
            The textual description of the error.
        cls: discord.HTTPException
            Inherited class from discord.HTTPException to make exception from.
        """
        resp = Exception()
        resp.status = status
        resp.status_code = status
        resp.reason = cls.__name__
        resp = cls(resp, {"message" : description, "code" : code})
        return resp

    def _generate_log_context(self):
        """
        This method is used for generating a dictionary (later converted to json) of the
        data that is to be included in the message log. This is to be implemented inside the
        inherited classes.
        """
        raise NotImplementedError
    
    def _get_data(self) -> dict:
        """
        Returns a dictionary of keyword arguments that is then expanded
        into other functions (_send_channel, generate_log)
        This is to be implemented in inherited classes due to different data_types
        """
        raise NotImplementedError

    def is_ready(self) -> bool:
        """ 
        This method returns bool indicating if message is ready to be sent
        """
        return (not self.force_retry["ENABLED"] and self.timer.elapsed() > self.period or
                self.force_retry["ENABLED"] and self.timer.elapsed() > self.force_retry["TIME"])

    def reset_timer(self) -> None:
        """ 
        Resets internal timer (and force period)
        """
        self.timer.reset()
        self.timer.start()
        self.force_retry["ENABLED"] = False
        if self.randomized_time is True:
            self.period = random.randrange(self.start_period, self.end_period)

    async def _send_channel(self) -> dict:
        """
        Sends data to a specific channel, this is separate from send
        for easier implementation of similar inherited classes
        The method returns a dictionary: `{"success": bool, "reason": discord.HTTPException}` where 
        `"reason"` is only present if `"success"` `is False`
        """
        raise NotImplementedError

    async def send(self) -> dict:
        """
        Sends a message to all the channels.
        Returns a dictionary generated by the `._generate_log_context` method
        """
        raise NotImplementedError

    async def _initialize_channels(self):
        """
        This method initializes the implementation specific
        api objects and checks for the correct channel input context.
        """
        raise NotImplementedError

    async def initialize_data(self):
        """
        This method checks for the correct data input to the xxxMESSAGE
        object. The expected datatypes for specific implementation is
        defined thru the static variable __valid_data_types__

        Raises
        ------------
        - `DAFParameterError(code=DAF_INVALID_TYPE)` - Raised when a parameter is of invalid type
        - `DAFNotFoundError(code=DAF_MISSING_PARAMETER)` - Raised when no data parameters were passed.
        """

        # Check for correct data types of the MESSAGE.data parameter
        if not isinstance(self.data, _FunctionBaseCLASS):
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
                    if isinstance(data, _FunctionBaseCLASS):
                        raise DAFParameterError(f"The function can only be used on the data parameter directly, not in a iterable. Function: {data.func_name}", DAF_INVALID_TYPE)
                    else:
                        trace(f"INVALID DATA PARAMETER PASSED!\nArgument is of type : {type(data).__name__}\nSee README.md for allowed data types", TraceLEVELS.WARNING)
                        raise DAFParameterError(f"Invalid data type {type(data).__name__}. Allowed types: {type(self).__valid_data_types__}", DAF_INVALID_TYPE)

            if len(self.data) == 0:
                raise DAFNotFoundError(f"No data parameters were passed", DAF_MISSING_PARAMETER)

    async def update(self, init_options: dict={}, **kwargs):
        """
        Used for changing the initialization parameters the object was initialized with.
        
        .. warning::
            Upon updating, the internal state of objects get's reset, meaning you basically have a brand new created object.     
        
        Parameters
        -------------
        init_options: dict
            Contains the initialization options used in .initialize() method for re-initializing certain objects.
            This is implementation specific and not necessarily available.
        original_params:
            The allowed parameters are the initialization parameters first used on creation of the object AND 
        
        Raises
        ------------
        DAFParameterError(code=DAF_UPDATE_PARAMETER_ERROR)
            Invalid keyword argument was passed
        Other
            Raised from .initialize() method
        
        .. versionadded::
            v2.0
        """

        raise NotImplementedError
        
    async def initialize(self, **options):
        """
        The initialize method initializes the message object.
    
        Parameters
        -------------
        - options - keyword arguments sent to _initialize_channels() from an inherited (from _BaseGUILD) class, contains extra init options.
        
        Raises
        -------------
        - Exceptions raised from ._initialize_channels() and .initialize_data() methods
        """

        await self._initialize_channels(**options)
        await self.initialize_data()

