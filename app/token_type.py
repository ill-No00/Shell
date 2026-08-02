from enum import Enum , auto


class TokenType(Enum):
    
    PATH = auto()
    PIPE = auto()
    
    COMMAND = auto()
    
    REDIRECT_OUT = auto()
    REDIRECT_ERR = auto()
    APPEND_OUT = auto()
    APPEND_ERR = auto()
    
    FLAG = auto()
    
    ARG = auto()
    
    BACKSLASH = auto()