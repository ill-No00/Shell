


class History:
    
    def __init__(self):
        self.history = []
        self.current = 0
        
    def add(self,command):
        self.history.append(command)
        
    def list_history(self,num = None):
        if num:
            commands = self.history[-num:]
            for i,cmd in enumerate(commands):
                print(f"{i + (len(self.history) - num) + 1} {cmd} ")
        else:
            for i,command in enumerate(self.history):
                print(f"{i+1} {command}")
                
    def up_key(self):
        try:
            self.current+=1
            latest_command = self.history[-self.current]
            return latest_command
        except IndexError:
            return ""
    def down_key(self):
        try:
            self.current -=1
            cmd = self.history[-self.current]
            return cmd
        except IndexError:
            return ""
    def initialize_on_startup(self,file_path):
        try:
            if file_path : 
                with open(file_path,'r') as f:
                    data = f.read().split("\n")
                    
                    for cmd in data :
                        if len(cmd) > 0:
                            self.history.append(cmd)
            else:
                return
        except FileNotFoundError:
            return
    
    def write_on_exit(self,file):
        
        try:
            
            if file:
                
                with open(file,'w') as f:
                    f.write("\n".join(self.history) + "\n")
                    
        except FileNotFoundError:
            return
                
    
        
history = History()