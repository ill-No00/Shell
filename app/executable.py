import subprocess
import sys



class Executable:
    
    def __init__(self , name,args,path , extra={}):
        self.name = name
        self.args = args 
        self.extra = extra
        self.path = path
        
    def run(self):
        
        #print(f"running the executable : name {self.name} args {self.args} extra {self.extra}")
        
        redirect_out = self.extra.get("redirect_output")
        redirect_err = self.extra.get("redirect_error")
        
        result = subprocess.run(
            [self.name] + self.args ,
            executable= self.path,
            capture_output = True,
            text = True
        )
        
        
        if redirect_out.get("is_redirect"):
            try:
                with open(redirect_out.get("to"), "a" if redirect_out.get("append") else "w") as f:
                    f.write(result.stdout)
            except OSError as e:
                sys.stderr.write(f"{redirect_out.get('to')}: {e.strerror}\n")
        else:
            if result.stdout:
                sys.stdout.write(result.stdout)
                sys.stdout.flush()

        if redirect_err.get("is_redirect"):
            try:
                with open(redirect_err.get("to"), "a" if redirect_err.get("append") else "w") as f:
                    f.write(result.stderr)
            except OSError as e:
                sys.stderr.write(f"{redirect_err.get('to')}: {e.strerror}\n")
        else:
            if result.stderr:
                sys.stderr.write(result.stderr)
                sys.stderr.flush()
                
                
            
    def remove_trailing_newline(self,text):
        return text[:-1] if text.endswith("\n") else text
        
    
    
    
    
    