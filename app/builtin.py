
import os
import sys
from pathlib import Path
import re
import json
from job import jobs
from history import history
from variable import variables
import re




class BuiltIn:
    
    PATH = os.environ.get("PATH")
    BUILT_IN_COMMANDS = {"echo","exit","type","pwd","complete","jobs" , "history", "declare"}
    REGISTERED_COMPLETIONS = {}
    
    
    def __init__(self , name,args=[],extra={}):
        self.name = name
        self.args = args
        self.extra = extra
        
    def run(self,out = True):
        
        redirect_out = self.extra.get("redirect_output", {})
        redirect_err = self.extra.get("redirect_error" , {})
        is_background = self.args[-1] == "&" if len(self.args) > 0 else False
        
        if is_background:
            self.args.pop()
        
        match self.name:
            
            case "echo":
                
                if redirect_out.get("is_redirect"):
                    self.redirectOut(text=" ".join(self.args),source=redirect_out)
                else :
                    if out:
                        print(" ".join(self.args))
                    else:
                        return " ".join(self.args) + "\n"
                
                if redirect_err.get("is_redirect"):
                    self.redirectOut(source=redirect_err,text="")
            
            case "type":
                command = self.args[0]
                
                if command in self.BUILT_IN_COMMANDS:# check if the command is builtin command
                    if redirect_out.get("is_redirect"):
                        self.redirectOut(redirect_out,f'{command} is a shell builtin')
                    else:
                        if out:
                            print(f'{command} is a shell builtin',flush=True)
                        else:
                            return f'{command} is a shell builtin' + "\n"
                                
                else:
                    is_Exe = self.isExecutable(command)
                    if is_Exe.get("is_Exe"):
                        if redirect_out.get("is_redirect") :
                            self.redirectOut(redirect_out,f"{command} is {is_Exe.get('full_path')}")
                        else:
                            if out:
                                print(f"{command} is {is_Exe.get('full_path')}" , flush=True)
                            else:
                                return f"{command} is {is_Exe.get('full_path')}" + "\n"
                    else:
                        if redirect_err.get("is_redirect"):
                            self.redirectOut(redirect_err,f"{command}: not found")
                        else:
                            if out:
                                print(f"{command}: not found" , flush=True)
                            else:
                                return f"{command}: not found" + "\n"
            case "pwd":
                if out:
                    print(str(Path.cwd()))
                else:
                    return str(Path.cwd()) + "\n"
                
            case "cd":
                if self.args[0].startswith("/"):
                    self.handleAbsolutePath(self.args[0])
                elif self.args[0].startswith('~'):
                    self.handleHome()
                else:# handle relative path
                    self.handleRelativePath(self.args[0])
            case 'complete':
                flags_args ={}
                
                for i,arg in enumerate(self.args):
                    if re.match(r"^--?[a-zA-Z0-9][a-zA-Z0-9-]*$", arg):
                        if i + 1 < len(self.args):
                            if arg in {'-c','-C'}:
                                flags_args[arg] = {
                                    'path' : self.args[i+1],
                                    'command' : self.args[i+2]
                                }
                            else :
                                flags_args[arg] = self.args[i+1]
                            
                for flag , flag_arg in flags_args.items():
                    
                    match flag:
                        case '-p' | '-P':
                            found = False
                               
                            if flag_arg in self.REGISTERED_COMPLETIONS:
                                completion = self.REGISTERED_COMPLETIONS.get(flag_arg)
                                #if flag_arg.get("path") == completion.get("path"):
                                found = True
                                if out:
                                    print(f"complete -C '{completion.get('path')}' {flag_arg}")
                                else:
                                    return f"complete -C '{completion.get('path')}' {flag_arg}" + "\n"
                                    
                            if not found : 
                                if out:
                                    print(f"complete: {flag_arg}: no completion specification")
                                else:
                                    return f"complete: {flag_arg}: no completion specification" + "\n"
                        case '-c' | '-C':
                            self.register_completion(flag_arg["command"],flag_arg["path"])
                        case '-r' | '-R':
                            
                            self.delete_completion(flag_arg)
            
            case "jobs":
                all_jobs = jobs.get_jobs()
                for i,job in enumerate(all_jobs):
                    command = job.command
                    status = "Running"
                    is_Done = job.process.poll() is not None
                    if is_Done:
                        status = "Done"
                        command = command[:-2]
                        jobs.delete_job(job.job_number)
                    if i== len(all_jobs) - 1:
                        if out:
                            print(f"[{job.job_number}]+  {status:<24}{command}")
                        else:
                            return f"[{job.job_number}]+  {status:<24}{command}" + "\n"
                    elif i== len(all_jobs) - 2:
                        if out:
                            
                            print(f"[{job.job_number}]-  {status:<24}{command}")
                        else:
                            return f"[{job.job_number}]-  {status:<24}{command}" + "\n"
                    else:
                        if out:
                            print(f"[{job.job_number}]  {status:<24}{command}")
                        else:
                            return f"[{job.job_number}]  {status:<24}{command}" + "\n"
                    
                    
                return
            case "history":
                if len(self.args) > 0:
                    if self.is_number(self.args[0]):
                        history.list_history(int(self.args[0]))
                    elif self.args[0].startswith('-'):
                        flag = self.args[0]
                        match flag:
                            case "-r":
                                history_file_path = self.args[1]
                                history_file_data = None
                                try:
                                    with open(history_file_path,"r") as f:
                                        history_file_data = f.read()
                                    commands_from_history_file = history_file_data.split("\n")
                                    for cmd in commands_from_history_file:
                                        if len(cmd) > 0:
                                            history.add(cmd)
                        
                                    
                                except FileNotFoundError:
                                    return
                            case "-w":
                                file_path = self.args[1]
                                try:
                                    with open(file_path,'w') as f:
                                        f.write("\n".join(history.history) + "\n")
                                        
                                    return
                                        
                                except FileNotFoundError:
                                    return
                            case "-a":
                                file_path = self.args[1]
                                try:
                                    
                                    with open(file_path,"a") as f:
                                        f.write("\n".join(history.history) + "\n")
                                        history.history = []
                                        
                                except FileNotFoundError:
                                    return
                else:
                    history.list_history()
            
            case "declare":
                if len(self.args) > 0:
                    if self.args[0].startswith('-'):
                        flag = self.args[0]
                        match flag:
                            
                            case "-p": 
                                var_name = self.args[1]
                                if var_name not in variables.variables:
                                    print(f"declare: {var_name}: not found")
                                else:
                                    print(f"declare -- {var_name}=\"{variables.variables[var_name]}\"")
                    else:
                        if "=" in self.args[0]:
                            name,value = self.args[0].split("=")
                            if self.validate_var_name(name):
                                variables.variables[name] = value
                            else:
                                print(f"declare: `{self.args[0]}': not a valid identifier")
                            
    
    def validate_var_name(self,var_name):
        reg_ex = "^[a-zA-Z_][a-zA-Z0-9_]*$"
        return re.match(reg_ex,var_name)    
    
    def is_number(self,num):
        try:
            float(num)
            return True
        except ValueError:
            return False                    
    def register_completion(self,command, path):
    
        self.REGISTERED_COMPLETIONS[command] = {
            "path": path
        }
    
    def delete_completion(self,command):
        del self.REGISTERED_COMPLETIONS[command]
        
        

        
    
    def redirectOut(self,source,text):
        
        match self.name:
            case "echo":
                with open(source.get("to") , "a" if source.get("append") else "w" ) as f:
                    f.write(text + "\n" if len(text) > 0 else "")
            case "type":
                with open(source.get("to") , "a" if source.get("append") else "w") as f:
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
                    
    def handleHome(self):
        HOME = os.environ.get("HOME")
        os.chdir(HOME)