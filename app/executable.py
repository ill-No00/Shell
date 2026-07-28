import subprocess



class Executable:
    
    def __init__(self , name,args,path , extra={}):
        self.name = name
        self.args = args 
        self.extra = extra
        self.path = path
        
    def run(self):
        result = subprocess.run(
            [self.name] + self.args ,
            executable= self.path,
            capture_output = True,
            text = True
        )
        return result
    
    def redirectOut(self):
        pass
    