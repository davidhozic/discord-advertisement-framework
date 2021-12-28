import enum, Config, time


class TRACE_LEVELS(enum.Enum):
    NORMAL = 0
    WARNING = 1
    ERROR =  2

# Debugging functions
def TRACE(message, level : TRACE_LEVELS): 
    if Config.C_DEBUG or Config.C_DEBUG_FILE_OUTPUT:
        l_timestruct = time.localtime()
        l_timestamp = "Date: {:02d}.{:02d}.{:04d} Time:{:02d}:{:02d}"
        l_timestamp = l_timestamp.format(l_timestruct.tm_mday, l_timestruct.tm_mon, l_timestruct.tm_year,l_timestruct.tm_hour,l_timestruct.tm_min)
        l_trace = f"{l_timestamp}\nTrace level: {level.name}\nMessage: {message}\n"
        if Config.C_DEBUG:
            print(l_trace)
        if Config.C_DEBUG_FILE_OUTPUT:
            with open ("SHILLER_TRACE.txt", 'a', encoding='utf-8') as l_file:
                l_file.write(f"{l_trace}\n")
