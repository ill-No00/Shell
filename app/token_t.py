

class Token:
    
    def __init__(self, type, lexeme):
        self.type = type
        self.lexeme = lexeme
    
    def __str__(self):
        return f"{self.type} {self.lexeme}"