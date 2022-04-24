from typing import List
import pyodbc
import copy
from    tracing import *

"""
    ~    sql    ~
    The sql module contains definitions related to the 
    relational database logging that is available in this shiller.
    It is only used if the sql logging is enabled by passing
    the framework.run function with the SqlCONTROLLER object.
"""
# CONFIGURATION
C_CONNECTION_TIMEOUT = 2


class SqlCONTROLLER:
    """ ~    SqlCONTROLLER    ~
        The class is used for logging data inside a
        MS SQL Server database by wrapping SQL calls into methods.
        
        @Arguments:
            address:  str - address to the MS SQL Server 
            username: str -  login username
            password: str -  loging password
        """
    
    __slots__ = (
        "addr",
        "user",
        "passw",
        "dbname",
        "conn",
        "cursor"
    )

    def __init__(self,
                 address: str,
                 username: str,
                 password: str,
                 database: str):
        self.addr = address
        self.user = username
        self.passw = password
        self.dbname = database
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """~ connect ~
        Method that initializes connection to the SQL Server
        """
        self.conn = pyodbc.connect(f"""
        DRIVER={{ODBC Driver 17 for SQL Server}};
        SERVER={self.addr};
        """, timeout=C_CONNECTION_TIMEOUT, user=self.user, password=self.passw, autocommit=True, database=self.dbname)
        self.cursor = self.conn.cursor()
        trace(f"{type(self).__name__} is connected to database {self.addr} as user {self.user}", TraceLEVELS.NORMAL)
    
    @property
    def tables(self) -> List[str]:
        """~    @property tables    ~
        This getter method retrieves the names of all created tables inside the database"""
        self.cursor.execute("SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';")
        return [x[2] for x in self.cursor.fetchall()]


#############################
# TESTING
############################
controller = SqlCONTROLLER("212.235.190.203", "sa", "Security1", "Fakulteta")
controller.connect()
pass