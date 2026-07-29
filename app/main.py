import sys
from pathlib import *
import os
from executable import Executable
from builtin import BuiltIn
from data_structure_alg.trie import Trie
from data_structure_alg.LongestCommonPrefix import longest_common_prefix
import re
import termios
import tty

#cat /tmp/cow/mango nonexistent 1> /tmp/ant/fox.md

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
    

    
def handleUnclosedQuotes(res , quotes):
    # we need to listen to the user input and for the closed quotes
    print("")
    sys.stdout.write(">")
    
    while True:
        input = input()

def is_valid_file_name(file):
    pattern = r"\.[a-zA-Z0-9]+$"
    return (" " not in file) and re.search(pattern, file)
        
def handleRedirectOutput(args,curr,result,append=False):
    file = ""
    curr +=  1
    while curr < len(args):
        
        if args[curr] != " ":
            file+=args[curr]
        elif len(file) > 0:

            break
                    
        curr+=1
                
    if is_valid_file_name(file):
        red = {
            "type" : "output",
            "is_redirect" : True,
            "to" : file,
            "append":append
        }
        result["redirect"]["redirect_output"] = red
                    
    else:
        pass
    
    return curr

def handleRedirectError(args,curr,result,append=False):
    file = ""
    curr +=  1
    while curr < len(args):
        
        if args[curr] != " ":
            file+=args[curr]
        elif len(file) > 0:

            break
                    
        curr+=1
                
    if is_valid_file_name(file):
        red = {
            "type" : "error",
            "is_redirect" : True,
            "to" : file,
            "append":append
        }
        result["redirect"]["redirect_error"] = red
                    
    else:
        pass
    
    return curr

        

        
    
    
def treatArgs(args):

    result = {
        "args" : [],
        "redirect":{
        "redirect_output" : {
            "type": "output",
            "is_redirect" : False,
            "to": ""
        },
        "redirect_error":{
            "type": "output",
            "is_redirect" : False,
            "to": ""
        }
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
            
            case "1":
                
                if curr + 1 < len(args) and args[curr+1] == ">":
                    if curr + 2 < len(args) and args[curr+2] == ">":
                        curr = handleRedirectOutput(args,curr+2,result,append=True)
                    else : curr = handleRedirectOutput(args,curr+1,result)
                else:
                    string_arg+=args[curr]
                    curr+=1
            
            case "2":
                if curr + 1 < len(args) and args[curr+1] == ">":
                    if curr + 2 < len(args) and args[curr+2] == ">":
                        curr = handleRedirectError(args,curr+2,result,append=True)
                    else : curr = handleRedirectError(args,curr+1,result)
                else:
                    string_arg+=args[curr]
                    curr+=1
                    
            
            case ">": #redirection
                
                if curr + 1 < len(args) and args[curr+1] == ">":
                    curr = handleRedirectOutput(args,curr+1,result,append=True)
                else : curr = handleRedirectOutput(args,curr,result)
                        
                        
                
                
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

def complete(lcp):
    
    sys.stdout.write("\r")        # Go to start of line
    sys.stdout.write("\033[K")    # Clear from cursor to end of line
    sys.stdout.write("$ ")
    sys.stdout.write(lcp)
    sys.stdout.flush()
    
    
def read_command(trie):
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    user_command = ""

    try:
        tty.setraw(fd)

        sys.stdout.write("$ ")
        sys.stdout.flush()

        while True:
            c = sys.stdin.read(1)

            if c == "\x03":  # Ctrl+C
                break

            if c == "\r" or c == "\n":
                sys.stdout.write("\r\n")
                sys.stdout.flush()
                break

            elif c == "\t":
                if trie.startsWith(user_command):
                    matches = trie.autoComplete(user_command)
                    if len(matches) == 1:
                        
                        user_command = matches[0] + " "
                        complete(user_command)
                    elif len(matches) > 1:
                        
                        lcp = longest_common_prefix(matches)
                        if len(lcp) > len(user_command):
                            user_command = lcp
                            complete(user_command)
                    else:
                        sys.stdout.write("\x07")
                else:
                    sys.stdout.write("\x07")

                continue

            elif c == "\x7f" or c == "\x08":
                if len(user_command) > 0:
                    user_command = user_command[:-1]
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
                continue

            
            user_command += c
            sys.stdout.write(c)
            sys.stdout.flush()

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return user_command

def main():
    
    
    trie = Trie()
    trie.insert("echo")
    trie.insert("type")
    trie.insert("exit")
    trie.insert("pwd")
    trie.insert("cd")
    trie.insert("ls")
    trie.insert("cat")
    
    
    
    while True:

        user_command = read_command(trie)
        if not user_command.strip():
            continue
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
                    
                    exec = Executable(command,res["args"],is_Exe.get("full_path"),res.get("redirect"))
                    
                    exec.run()
                    
                   
                    
                    
                else:
                    print(f"{user_command}: command not found")
    

        
        
    


if __name__ == "__main__":
    main()
