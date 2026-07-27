import sys
from pathlib import *
import os
import subprocess
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
        
    
    
    
def treatArgs(args):

    res = ""
    curr = 0
    
    while curr < len(args):
        
        match args[curr]:
            
            case "'": # get all chars inside singleQuotes
                if curr > 0 and args[curr - 1] == " ":
                    res+= " "
                curr+=1
                while curr < len(args) and args[curr] != "'":
                    if args[curr] == "" or args[curr] == " ":
                        res+= " "
                    else : res+= args[curr]
                    curr+=1
                curr+=1
            
            
                #if curr < len(args):
                    #res = handleUnclosedQuotes(res,quotes="'")
            case " ":
                curr+=1
                continue
            case _:
                if curr > 0 and args[curr - 1] == " ":
                    res+= " "
                res+=args[curr]
                curr+=1
                
    return res           
    
    
    

def main():
    
    BUILT_IN_COMMANDS = {"echo","exit","type","pwd"}
    
    
    while True:
        sys.stdout.write("$ ")
        user_command = input()
        
        start_with = user_command.split(" ")[0]
        
        match start_with:
            case 'exit':
                break
            
            case 'echo':
                res = treatArgs(user_command[5:])
                print(res)
                
            case 'type':
                command = user_command.split(" ")[1]  
                
            
                if command in BUILT_IN_COMMANDS: # check if the command is builtin command
                    print(f'{command} is a shell builtin')
                
                else:
                    command = user_command.split(" ")[1].strip()
                    is_Exe = isExecutable(command)
                    if is_Exe.get("is_Exe"):
                        print(f"{command} is {is_Exe.get('full_path')}")
                    else:
                        print(f"{command}: not found")
            case 'pwd':
                print(Path.cwd())
            
            case 'cd':
                full_command = user_command.split(" ")
                
                command = full_command[0]
                arg = full_command[1]
                
                if arg.startswith("/"):
                    handleAbsolutePath(arg)
                elif arg.startswith('~'):
                    handleHome()
                else:# handle relative path
                    handleRelativePath(arg)
                    
            
            case _:
                full_command = user_command.split(" ")
                is_Exe = isExecutable(full_command[0])
                if is_Exe.get("is_Exe"):
                    # run the program
                    
                    command = full_command[0]
                    args = full_command[1:]
                    
                    result = subprocess.run(
                        [command] + args ,
                        executable= is_Exe.get("full_path"),
                        capture_output = True,
                        text = True
                    )
                    
                    sys.stdout.write(result.stdout)
                    #print(result.stderr)
                    #print(result.returncode)
                    
                else:
                    print(f"{user_command}: command not found")
        
        
    


if __name__ == "__main__":
    main()
