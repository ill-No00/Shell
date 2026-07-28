import sys
from pathlib import *
import os
import subprocess
from .executable import Executable
from .builtin import BuiltIn
import re

PATH = os.environ.get("PATH")

def isExecutable(command):
          
    directories = PATH.split(":")
                
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
    
def handleAbsolutePath(arg):
    
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
        
def handleRelativePath(arg):
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
    
def handleUnclosedQuotes(res , quotes):
    # we need to listen to the user input and for the closed quotes
    print("")
    sys.stdout.write(">")
    
    while True:
        input = input()
        
def is_valid_file_name(file):
    pattern = r"\.[a-zA-Z0-9]+$"
    return (" " not in file) and re.search(pattern, file)
        
    
    
def treatArgs(args):

    result = {
        "args" : [],
        "redirect" : {
            "is_redirect" : False,
            "to": ""
        }
    }
    res = []
    curr = 0
    string_arg = ""
    while curr < len(args):
        
        
        
        match args[curr]:
            
            case "'": # get all chars inside singleQuotes

                curr+=1
                while curr < len(args) and args[curr] != "'":
                    if args[curr] == "" or args[curr] == " ":
                        string_arg+= " "
                    else : string_arg+= args[curr]
                    curr+=1
                curr+=1
            
                #if curr < len(args):
                    #string_arg = handleUnclosedQuotes(string_arg,quotes="'")
                    
            case '"': # get all chars inside DoubleQuotes

                curr+=1
                while curr < len(args) and args[curr] != '"':
                    if args[curr] == "" or args[curr] == " ":
                        string_arg+= " "
                    elif args[curr] == "\\":
                        if curr + 1 < len(args) and (args[curr + 1] in {'"' , '\\'}):
                            curr+=1
                            string_arg+=args[curr]
                    else : string_arg+= args[curr]
                    curr+=1
                curr+=1
                
            case "\\": # a backslah found we need to traet the next char as literal
                next_literal = ""
                if curr + 1 < len(args):
                    curr+=1
                    next_literal = args[curr]
                    curr+=1
                
                string_arg+=next_literal
            
            case ">": #redirection
                
                file = ""
                curr+=1
                while curr < len(args):
                    if args[curr] != " ":
                        file+=args[curr]
                    
                    curr+=1
                
                if is_valid_file_name(file):
                    red = {
                        "is_redirect" : True,
                        "to" : file
                    }
                    result["redirect"] = red
                    
                else:
                    pass
                        
                        
                
                
            case " ":
                if string_arg:
                    res.append(string_arg)
                    string_arg=""
                curr+=1
                
            case _:
    
                string_arg+=args[curr]
                curr+=1
    
    if len(string_arg) > 0:
        res.append(string_arg)
    result["args"] = res
    return result         
    
def find_blank_ind(user_command):
    curr = 0

    while curr < len(user_command):
        c = user_command[curr]

        if c in {'"', "'"}:
            quote = c
            curr += 1

            while curr < len(user_command) and user_command[curr] != quote:
                curr += 1

            if curr < len(user_command):
                curr += 1

        elif c == " ":
            return curr

        else:
            curr += 1

    return -1
    

def main():
    
    
    
    
    while True:
        sys.stdout.write("$ ")
        user_command = input()
        
        start_with = user_command.split(" ")[0]
        
        match start_with:
            case 'exit':
                break
            
            case 'echo':
                arg_res = treatArgs(user_command[5:])
                echo = BuiltIn('echo',arg_res.get("args"),arg_res.get("redirect"))
                echo.run()
                
                
            case 'type':
                arg_res = treatArgs(user_command[5:])
                
                type = BuiltIn('type',arg_res.get("args"),arg_res.get("redirect"))
                type.run()
            
                
            case 'pwd':
                args = treatArgs(user_command[4:])
                pwd = BuiltIn('pwd',extra=args.get("redirect"))
                pwd.run()
            
            case 'cd':
                res = treatArgs(user_command[3:])
                cd = BuiltIn('cd',res.get("args"))
                cd.run()  
            
            case _:
                command = ""
                first_char = user_command[0]
                if first_char == "'" or first_char =='"':
                    curr = 1
                    while curr < len(user_command) and user_command[curr] != first_char:
                        if user_command[curr] == "\\":
                            if curr + 1 < len(user_command):
                                
                                next = user_command[curr+1]
                                
                                if next in {"\\"}:
                                    command+=next
                                    curr+=2
                                else:
                                    command+='\\'
                                    curr+=1
                            
                        else : 
                            command+=user_command[curr]
                            curr+=1
                    curr+=1
                else : 
                    command = user_command.split(" ")[0]
                
                is_Exe = isExecutable(command)
                if is_Exe.get("is_Exe"):
                    # run the program
                    
                    first_blank = find_blank_ind(user_command)
                    res = treatArgs(user_command[first_blank+1:])
                    
                    exec = Executable(command,res["args"],is_Exe.get("full_path"))
                    result = exec.run()
                    
                    sys.stdout.write(result.stdout)
                    
                    
                else:
                    print(f"{user_command}: command not found")
        
        
    


if __name__ == "__main__":
    main()
