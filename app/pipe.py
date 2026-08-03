import os
import subprocess
from .builtin import BuiltIn
from .token_type import TokenType



class Pipe:
    
    def __init__(self,tokenized_command):
        self.command = tokenized_command
        self.first_c = []
        self.second_c = []
        self.initialize()
        
    def initialize(self):
        pipe_seen = False
        command = self.command
        for token in command:
            if token.lexeme == "|":
                pipe_seen = True
                continue
            if pipe_seen :
                self.second_c.append(token)
            else:
                self.first_c.append(token)
                
    def parse_args(self,tokens):
        res = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
        
            
            if token.type in (TokenType.ARG, TokenType.PATH, TokenType.COMMAND):
                res.append(token.lexeme)
        
            i += 1
        
        return res
                
    def run(self):
        
        
        #create and get file descriptors of the pipe
        read_fd , write_fd = os.pipe()
        c1_pid = None
        c2_pid = None
        
        command1 = self.first_c[0]
        command2 = self.second_c[0]
        
        if command1.lexeme in BuiltIn.BUILT_IN_COMMANDS:
            args = self.parse_args(self.first_c[1:])
            blt_c1 = BuiltIn(command1.lexeme,args)
            retrun = blt_c1.run(out=False)
            
            os.write(write_fd , retrun.encode())
            
        else:
            c1_pid = os.fork()
            
            if c1_pid == 0: #child that will run the first command
                
                os.close(read_fd) # the first child will write in the pipe we dont need it to read from it
                
                os.dup2(write_fd,1)
                
                os.close(write_fd)
                
                
                args = [arg.lexeme for arg in self.first_c[1:]]
                
            
                
                os.execlp(command1.lexeme , command1.lexeme ,*args )
                
        if command2.lexeme in BuiltIn.BUILT_IN_COMMANDS:
            args = self.parse_args(self.second_c[1:])
            blt_c2 = BuiltIn(command2.lexeme,args)
            blt_c2.run()
        else:
            c2_pid = os.fork()
            
            if c2_pid == 0: #child that will run the second command
                
                os.close(write_fd) # the second child only need to read from the pipe
                
                os.dup2(read_fd,0)
                
                os.close(read_fd)
                
                args = [arg.lexeme for arg in self.second_c[1:]]
                
                
                
                os.execlp(command2.lexeme , command2.lexeme ,*args)
            
        os.close(read_fd)
        os.close(write_fd)
        
        if c1_pid:
            os.waitpid(c1_pid,0)
        if c2_pid:
            os.waitpid(c2_pid,0)
        
        
        
        
        
        
    