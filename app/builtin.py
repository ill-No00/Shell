
import os
import sys
from pathlib import Path



#extra will contain any redirection

class BuiltIn:
    
    PATH = os.environ.get("PATH")
    BUILT_IN_COMMANDS = {"echo","exit","type","pwd"}
    
    def __init__(self , name,args=[],extra={}):
        self.name = name
        self.args = args
        self.extra = extra
        
    def run(self):
        
        match self.name:
            
            case "echo":
                
                if len(self.extra.keys()) > 0 and self.extra.get("is_redirect"):
                    self.redirectOut()
                else :
                    print(" ".join(self.args))
            
            case "type":
                command = self.args[0]
                
                if command in self.BUILT_IN_COMMANDS: # check if the command is builtin command
                    self.redirectOut(f'{command} is a shell builtin')
                                
                else:
                    is_Exe = self.isExecutable(command)
                    if is_Exe.get("is_Exe"):
                        self.redirectOut(f"{command} is {is_Exe.get('full_path')}")
                    else:
                        self.redirectOut(f"{command}: not found")
            case "pwd":
                print(str(Path.cwd()))
                
            case "cd":
                if self.args[0].startswith("/"):
                    self.handleAbsolutePath(self.args[0])
                elif self.args[0].startswith('~'):
                    self.handleHome()
                else:# handle relative path
                    self.handleRelativePath(self.args[0])
    
    def redirectOut(self,text):
        
        match self.name:
            case "echo":
                with open(self.extra.get("to") , "w") as f:
                    f.write(" ".join(self.args))
            case "type":
                with open(self.extra.get("to") , "w") as f:
                    f.write(text)
    
    def isExecutable(self,command):
            
        directories = self.PATH.split(":")
                    
        for directory in directories:
                        
            full_path = os.path.join(directory,command)
                        
            if os.path.isfile(full_path) and os.access(full_path,os.X_OK):
                
                return {
                    "is_Exe" : True,
                    "command_dir" : directory,
                    "full_path" : full_path
                }
                
        return {
            "is_Exe" : False,
            "command_dir" : ""
        }
        
    def handleAbsolutePath(self,arg):
    
        arg_sub_dir = arg.split('/')[1:]
                        
        current = '/'
        all_dir = os.listdir(current)
                        
                        
        found = True
        for dir in arg_sub_dir:
            candidate = os.path.join(current,dir)
            if os.path.isdir(candidate) and (dir in all_dir):
                current=candidate+'/'
                all_dir = os.listdir(current)
            elif dir not in all_dir:
                found = False
                print(f"cd: {arg}: No such file or directory")
                break
                            
        if found:
            os.chdir(arg)
            
    def handleRelativePath(self,arg):
        # find we need to handle ./ and ../ ./dirname = dirname
        
        arg_sub_dir = arg.split("/")
        current = str(Path.cwd()) 
        
        for arg in arg_sub_dir:
            
            match arg:
                case '.':
                    continue
                case '..':
                    curr_arr = current.split("/")
                    curr_arr.pop()
                    current = "/".join(curr_arr)  
                case _:# there is a named dir 
                    sub_dirs = os.listdir(current)
                    if arg in sub_dirs:
                        current+= "/" + arg
        
        os.chdir(current)
                    
    def handleHome():
        HOME = os.environ.get("HOME")
        os.chdir(HOME)