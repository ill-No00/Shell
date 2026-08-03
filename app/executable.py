import subprocess
import sys
from .job import *


class Executable:

    def __init__(self, name, args, path, extra=None):
        self.name = name
        self.args = list(args) if args else []
        self.extra = extra if extra is not None else {}
        self.path = path

    def run(self):

        redirect_out = self.extra.get("redirect_output", {})
        redirect_err = self.extra.get("redirect_error", {})

        # Fix 1: Check string directly instead of token.lexeme
        is_background = self.args[-1] == "&" if len(self.args) > 0 else False
        bg_out = ""
        result = {}
        

        if is_background:
            job_id = len(jobs.jobs) + 1
            self.args.pop()
            
            result = subprocess.Popen(
                [self.name] + self.args,
                executable=self.path,
                #stdout=subprocess.DEVNULL if not redirect_out.get("is_redirect") else open(redirect_out.get("to"), "a" if redirect_out.get("append") else "w"),
                #stderr=subprocess.DEVNULL if not redirect_err.get("is_redirect") else open(redirect_err.get("to"), "a" if redirect_err.get("append") else "w"),
                text=True,
            )
            bg_out = f"[{job_id}] {result.pid}\n"
            whole_command = f"{self.name} {' '.join(self.args)} &"
            single_job = SingleJob(whole_command, job_id, result.pid, 'Running', result)
            jobs.add_job(single_job)
            
        else:
            result = subprocess.run(
                [self.name] + self.args,
                executable=self.path,
                capture_output=True,
                text=True,
            )

        # Handle Standard Output
        if redirect_out.get("is_redirect"):
            try:
                with open(
                    redirect_out.get("to"),
                    "a" if redirect_out.get("append") else "w",
                ) as f:
                    f.write(result.stdout if not is_background else bg_out)
            except OSError as e:
                sys.stdout.write(f"{redirect_out.get('to')}: {e.strerror}\n")
                sys.stdout.flush()
        else:
            out_to_print = result.stdout if not is_background else bg_out
            if out_to_print:
                sys.stdout.write(out_to_print)
                sys.stdout.flush()

        # Handle Standard Error
        if redirect_err.get("is_redirect"):
            try:
                with open(
                    redirect_err.get("to"),
                    "a" if redirect_err.get("append") else "w",
                ) as f:
                    f.write(result.stderr if not is_background else "")
            except OSError as e:
                sys.stdout.write(f"{redirect_err.get('to')}: {e.strerror}\n")
                sys.stdout.flush()
        else:
            if not is_background and result.stderr:
                sys.stdout.write(result.stderr)
                sys.stdout.flush()