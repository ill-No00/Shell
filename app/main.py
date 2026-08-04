import os
import re
import subprocess
import sys
import termios
import tty
from pathlib import Path

from builtin import BuiltIn
from data_structure_alg.LongestCommonPrefix import longest_common_prefix
from data_structure_alg.trie import Trie
from executable import Executable
from job import *
from token_type import TokenType
from token_t import Token
from pipe import Pipe
from history import history
from variable import variables


class Shell:
    PATH = os.environ.get("PATH", "")

    def __init__(self):
        self.command_trie = Trie("command")
        self.files_trie = Trie("file")
        self.command_trie.initialize()
        self.files_trie.initialize()
        self.COMP_LINE = ""
        self.CURRENT_IND = 0
        self.next_bg_id = 1

    def isExecutable(self, command: str) -> dict:
        """Locates binary executables in PATH environment variable."""
        for directory in self.PATH.split(os.pathsep):
            full_path = os.path.join(directory, command)
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                return {
                    "is_Exe": True,
                    "command_dir": directory,
                    "full_path": full_path,
                }
        return {"is_Exe": False, "command_dir": "", "full_path": ""}

    def is_valid_file_name(self, file: str) -> bool:
        """Validates shell redirection targets."""
        pattern = r"\.[a-zA-Z0-9]+$"
        return (" " not in file) and bool(re.search(pattern, file))

    def _extract_redirect_target(self, args: str, curr: int) -> tuple[str, int]:
        """Helper to safely consume non-whitespace file path tokens for redirection."""
        file = ""
        curr += 1
        while curr < len(args):
            if args[curr] != " ":
                file += args[curr]
            elif len(file) > 0:
                break
            curr += 1
        return file, curr

    def handleRedirectOutput(self, args: str, curr: int, result: dict, append: bool = False) -> int:
        file, next_curr = self._extract_redirect_target(args, curr)
        if self.is_valid_file_name(file):
            result["redirect"]["redirect_output"] = {
                "type": "output",
                "is_redirect": True,
                "to": file,
                "append": append,
            }
        return next_curr

    def handleRedirectError(self, args: str, curr: int, result: dict, append: bool = False) -> int:
        file, next_curr = self._extract_redirect_target(args, curr)
        if self.is_valid_file_name(file):
            result["redirect"]["redirect_error"] = {
                "type": "error",
                "is_redirect": True,
                "to": file,
                "append": append,
            }
        return next_curr

    def treatArgs(self, args: str) -> dict:
        """Tokenizes line input with support for quotes, escapes, stream redirections , and Pipes"""
        result = {
            "args": [],
            "redirect": {
                "redirect_output": {"type": "output", "is_redirect": False, "to": ""},
                "redirect_error": {"type": "output", "is_redirect": False, "to": ""},
            },
        }
        res = []
        curr = 0
        string_arg = ""

        while curr < len(args):
            char = args[curr]
            match char:
                case "'":
                    curr += 1
                    while curr < len(args) and args[curr] != "'":
                        string_arg += " " if args[curr] == "" else args[curr]
                        curr += 1
                    curr += 1

                case '"':
                    curr += 1
                    while curr < len(args) and args[curr] != '"':
                        if args[curr] == "\\":
                            if curr + 1 < len(args) and args[curr + 1] in {'"', "\\"}:
                                curr += 1
                                string_arg += args[curr]
                        else:
                            string_arg += args[curr]
                        curr += 1
                    curr += 1

                case "\\":
                    if curr + 1 < len(args):
                        curr += 1
                        string_arg += args[curr]
                        curr += 1

                case "1":
                    if curr + 1 < len(args) and args[curr + 1] == ">":
                        is_append = (curr + 2 < len(args)) and (args[curr + 2] == ">")
                        advance = curr + 2 if is_append else curr + 1
                        curr = self.handleRedirectOutput(args, advance, result, append=is_append)
                    else:
                        string_arg += char
                        curr += 1

                case "2":
                    if curr + 1 < len(args) and args[curr + 1] == ">":
                        is_append = (curr + 2 < len(args)) and (args[curr + 2] == ">")
                        advance = curr + 2 if is_append else curr + 1
                        curr = self.handleRedirectError(args, advance, result, append=is_append)
                    else:
                        string_arg += char
                        curr += 1

                case ">":
                    is_append = (curr + 1 < len(args)) and (args[curr + 1] == ">")
                    advance = curr + 1 if is_append else curr
                    curr = self.handleRedirectOutput(args, advance, result, append=is_append)

                case " ":
                    if string_arg:
                        res.append(string_arg)
                        string_arg = ""
                    curr += 1
                
                case "|":
                    if curr - 1 > 0 and curr + 1 < len(args) and args[curr - 1] == " " and args[curr + 1] == " ":
                        # create a pipe
                        ...

                case _:
                    string_arg += char
                    curr += 1

        if string_arg:
            res.append(string_arg)

        result["args"] = res
        return result

    def find_blank_ind(self) -> int:
        """Finds index of the first space character outside quoted strings."""
        curr = 0
        while curr < len(self.COMP_LINE):
            c = self.COMP_LINE[curr]
            if c in {'"', "'"}:
                quote = c
                curr += 1
                while curr < len(self.COMP_LINE) and self.COMP_LINE[curr] != quote:
                    curr += 1
                if curr < len(self.COMP_LINE):
                    curr += 1
            elif c == " ":
                return curr
            else:
                curr += 1
        return -1

    def redraw_line(self, new_line: str):
        """Redraws the prompt buffer atomically on terminal output."""
        self.COMP_LINE = new_line
        self.CURRENT_IND = len(new_line)
        sys.stdout.write("\r\033[K$ " + self.COMP_LINE)
        sys.stdout.flush()

    def run_completer_script(
        self,
        script: str,
        argvs: list[str],
        uncompleted: str,
        COMP_LINE: str,
        tab_count: int,
    ) -> str:
        """Executes external completion helper scripts"""
        env = os.environ.copy()
        env["COMP_LINE"] = COMP_LINE
        env["COMP_POINT"] = str(self.CURRENT_IND)

        try:
            result = subprocess.run([script] + argvs, capture_output=True, text=True, env=env)
        except Exception:
            sys.stdout.write("\x07")
            sys.stdout.flush()
            return COMP_LINE

        if not result.stdout:
            sys.stdout.write("\x07")
            sys.stdout.flush()
            return COMP_LINE

        completions = result.stdout.splitlines()
        prefix_base = (uncompleted + " ") if uncompleted else ""

        # Single Completion Match
        if len(completions) == 1:
            match = completions[0]
            completed_str = prefix_base + match + " "
            self.redraw_line(completed_str)
            return completed_str

        # Multiple Completion Matches
        lcp = longest_common_prefix(completions)
        current_word = argvs[1]

        if len(lcp) > len(current_word):
            # Extend partial completion up to LCP
            suffix = " " if lcp in completions else ""
            completed_str = prefix_base + lcp + suffix
            self.redraw_line(completed_str)
            return completed_str

        # No progress possible from LCP
        if tab_count > 1:
            sys.stdout.write("\r\n")
            sys.stdout.write("  ".join(completions) + "\r\n")
            sys.stdout.write(f"$ {COMP_LINE}")
            sys.stdout.flush()
        else:
            sys.stdout.write("\x07")
            sys.stdout.flush()

        return COMP_LINE

    def programmable_completion(self, tab_count: int) -> str:
        """Processes completion rules registered in BuiltIn.REGISTERED_COMPLETIONS."""
        registered_completions = BuiltIn.REGISTERED_COMPLETIONS
        line = self.COMP_LINE

        parts = line.split()
        base_command = parts[0] if parts else ""

        command_comp = registered_completions.get(base_command)
        if not command_comp or not command_comp.get("path"):
            return line

        # Calculate word args for completion script: [cmd, cword, prev_word]
        last_blank_seen = line.rfind(" ")
        if last_blank_seen == -1:
            uncompleted = ""
            current_word = line
        else:
            uncompleted = line[:last_blank_seen]
            current_word = line[last_blank_seen + 1 :]

        words = line.split()
        prev_word = words[-2] if len(words) >= 2 else ""

        argvs = [base_command, current_word, prev_word]

        return self.run_completer_script(
            command_comp.get("path"),
            argvs,
            uncompleted,
            line,
            tab_count,
        )

    def is_registered_completion(self, command: str) -> bool:
        return command in BuiltIn.REGISTERED_COMPLETIONS

    def read_command(self, command_trie: Trie, files_trie: Trie) -> str:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        tab_count = 0

        self.COMP_LINE = ""
        self.CURRENT_IND = 0

        try:
            tty.setraw(fd)
            sys.stdout.write("$ ")
            sys.stdout.flush()

            while True:
                c = sys.stdin.read(1)

                if c in ("\x03", "\r", "\n"):  # Interrupt / Newline
                    tab_count = 0
                    sys.stdout.write("\r\n")
                    sys.stdout.flush()
                    break

                elif c == "\t":
                    tab_count += 1
                    base_command = self.COMP_LINE.split(" ")[0] if self.COMP_LINE else ""

                    # 1. Check for custom Programmable Completion
                    if self.is_registered_completion(base_command):
                        res = self.programmable_completion(tab_count)
                        self.COMP_LINE = res
                        self.CURRENT_IND = len(res)
                        continue

                    #  Default Completion Pipeline
                    matches = []
                    base_prompt = ""
                    c_part = ""

                    if " " in self.COMP_LINE:
                        base_prompt, c_part = self.COMP_LINE.rsplit(" ", 1)
                        base_prompt += " "

                        if "/" in c_part:
                            directory, _ = c_part.rsplit("/", 1)
                            files_trie.add_full_path_recursive(directory)
                            matches = files_trie.autoComplete(c_part)
                        else:
                            matches = files_trie.autoComplete(c_part)
                    else:
                        base_prompt = ""
                        c_part = self.COMP_LINE
                        cmd_matches = command_trie.autoComplete(c_part) if command_trie.startsWith(c_part) else []
                        file_matches = files_trie.autoComplete(c_part) if files_trie.startsWith(c_part) else []
                        matches = sorted(list(set(cmd_matches + file_matches)))

                    if not matches:
                        sys.stdout.write("\x07")
                        sys.stdout.flush()
                        continue

                    if len(matches) == 1:
                        tab_count = 0
                        suffix = "/" if os.path.isdir(matches[0]) else " "
                        self.redraw_line(base_prompt + matches[0] + suffix)
                    else:
                        lcp = longest_common_prefix(matches)
                        if len(lcp) > len(c_part):
                            self.redraw_line(base_prompt + lcp)
                        else:
                            if tab_count == 1:
                                sys.stdout.write("\x07")
                                sys.stdout.flush()
                            elif tab_count >= 2:
                                formatted_matches = [
                                    m + "/" if os.path.isdir(m) else m for m in sorted(matches)
                                ]
                                sys.stdout.write("\r\n" + "  ".join(formatted_matches) + "\r\n")
                                sys.stdout.write(f"$ {self.COMP_LINE}")
                                sys.stdout.flush()
                                tab_count = 0
                    continue

                elif c in ("\x7f", "\x08"):  # Backspace
                    tab_count = 0
                    if len(self.COMP_LINE) > 0:
                        self.COMP_LINE = self.COMP_LINE[:-1]
                        self.CURRENT_IND = len(self.COMP_LINE)
                        sys.stdout.write("\b \b")
                        sys.stdout.flush()
                    continue
                
                elif c == "\x1b":
                    seq = sys.stdin.read(2)

                    if seq == "[A":
                        self.redraw_line(history.up_key())
                    elif seq == "[B":
                        self.redraw_line(history.down_key())

                    continue

                # printable key press
                tab_count = 0
                self.COMP_LINE += c
                self.CURRENT_IND = len(self.COMP_LINE)
                sys.stdout.write(c)
                sys.stdout.flush()

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        return self.COMP_LINE.strip()
    
    def remove_exited_jobs(self):
        all_jobs = jobs.get_jobs()
        for i,job in enumerate(all_jobs):
            command = job.command
            is_Done = job.process.poll() is not None
            if is_Done:
                status = "Done"
                command = command[:-2]
                jobs.delete_job(job.job_number)
                if i== len(all_jobs) - 1:
                    print(f"[{job.job_number}]+  {status:<24}{command}")
                elif i== len(all_jobs) - 2:
                    print(f"[{job.job_number}]-  {status:<24}{command}")
                else:
                    print(f"[{job.job_number}]  {status:<24}{command}")
                    

    def parser(self):
        tokenized_command = []
        command = self.COMP_LINE

        curr = 0
        current_str = ""
        is_piped = False
        expecting_command = True

        def add_word(word):
            nonlocal expecting_command

            if not word:
                return

            # Keep your PATH classification
            if "/" in word:
                token_type = TokenType.PATH
            elif expecting_command:
                token_type = TokenType.COMMAND
            else:
                token_type = TokenType.ARG

            tokenized_command.append(Token(token_type, word))
            expecting_command = False

        def flush_current():
            nonlocal current_str

            if current_str:
                
                add_word(current_str)
                current_str = ""

        while curr < len(command):
            c = command[curr]

            match c:
                
                case "|":
                    flush_current()

                    tokenized_command.append(
                        Token(TokenType.PIPE, "|")
                    )

                    is_piped = True
                    expecting_command = True

                    curr += 1
                    continue
                
                case "\\":
                    # Outside quotes: \ escapes the very next character literally
                    if curr + 1 < len(command):
                        current_str += command[curr + 1]
                        curr += 2  # Move past both '\' and the escaped character
                    else:
                        current_str += "\\"
                        curr += 1
                    continue
                
                case "'":
                    
                    curr += 1
                    while curr < len(command) and command[curr] != "'":
                        current_str += command[curr]
                        curr += 1

                    # Unterminated single quote
                    if curr >= len(command):
                        raise SyntaxError("unterminated single quote")

                    # Skip closing quote
                    curr += 1
                    continue
                
                case "&":
                    flush_current()
                    tokenized_command.append(
                        Token(TokenType.BACKGROUND, "&") 
                    )
                    curr += 1
                    continue

                case '"':
                    
                    curr += 1
                    while curr < len(command) and command[curr] != '"':
                        if command[curr] == "\\":
                            if curr + 1 < len(command) and command[curr + 1] in {'"', "\\", "$", "`"}:
                                # Move to the escaped character
                                curr += 1
                                current_str += command[curr]
                            else:
                                # Preserve backslash if not followed by a special character
                                current_str += "\\"
                        else:
                            current_str += command[curr]

                        curr += 1

                    if curr >= len(command):
                        raise SyntaxError("unterminated double quote")

                    curr += 1  # Skip closing quote
                    continue

                case "<":
                    flush_current()

                    # <<
                    if curr + 1 < len(command) and command[curr + 1] == "<":
                        tokenized_command.append(
                            Token(TokenType.REDIRECT_IN, "<<")
                        )
                        curr += 2

                    # <
                    else:
                        tokenized_command.append(
                            Token(TokenType.REDIRECT_IN, "<")
                        )
                        curr += 1

                    continue

                case "1" | "2":
                    fd = c

                    if curr + 1 < len(command) and command[curr + 1] == ">":

                        flush_current()

                        # 2>&1
                        if (
                            fd == "2"
                            and curr + 3 < len(command)
                            and command[curr + 2] == "&"
                            and command[curr + 3] == "1"
                        ):
                            tokenized_command.append(
                                Token(TokenType.REDIRECT_ERR_TO_OUT, "2>&1")
                            )

                            curr += 4
                            continue

                        # 1>>
                        # 2>>
                        if (
                            curr + 2 < len(command)
                            and command[curr + 2] == ">"
                        ):
                            if fd == "1":
                                tokenized_command.append(
                                    Token(TokenType.APPEND_OUT, "1>>")
                                )
                            else:
                                tokenized_command.append(
                                    Token(TokenType.APPEND_ERR, "2>>")
                                )

                            curr += 3
                            continue

                        # 1>
                        # 2>
                        if fd == "1":
                            tokenized_command.append(
                                Token(TokenType.REDIRECT_OUT, "1>")
                            )
                        else:
                            tokenized_command.append(
                                Token(TokenType.REDIRECT_ERR, "2>")
                            )

                        curr += 2
                        continue

                    # Normal argument containing 1 or 2
                    current_str += c
                    curr += 1
                    continue

                case ">":
                    flush_current()

                    # >>
                    if curr + 1 < len(command) and command[curr + 1] == ">":
                        tokenized_command.append(
                            Token(TokenType.APPEND_OUT, ">>")
                        )
                        curr += 2

                    # >
                    else:
                        tokenized_command.append(
                            Token(TokenType.REDIRECT_OUT, ">")
                        )
                        curr += 1

                    continue

                case " ":
                    flush_current()
                    curr += 1
                    continue
                
                case _:
                    current_str += c
                    curr += 1

        flush_current()
        return tokenized_command, is_piped

    def parse_redirects(self,redirect_tokens):
        """
        Parses a list of redirect tokens into a structured dictionary for stdout/stderr.
        Ex: [Token(REDIRECT_OUT, '>'), Token(ARG, 'out.txt')]
        """
        result = {
            "redirect_output": {"is_redirect": False, "to": None, "append": False},
            "redirect_error": {"is_redirect": False, "to": None, "append": False},
        }

        i = 0
        while i < len(redirect_tokens):
            token = redirect_tokens[i]
            
            # Check if the next token is the target file
            if i + 1 < len(redirect_tokens):
                target_file = redirect_tokens[i + 1].lexeme
                
                match token.lexeme:
                    case ">" | "1>":
                        result["redirect_output"] = {"is_redirect": True, "to": target_file, "append": False}
                        i += 2
                    case ">>" | "1>>":
                        result["redirect_output"] = {"is_redirect": True, "to": target_file, "append": True}
                        i += 2
                    case "2>":
                        result["redirect_error"] = {"is_redirect": True, "to": target_file, "append": False}
                        i += 2
                    case "2>>":
                        result["redirect_error"] = {"is_redirect": True, "to": target_file, "append": True}
                        i += 2
                    case _:
                        i += 1
            else:
                i += 1

        return result

    def main(self):
        files_trie = self.files_trie
        command_trie = self.command_trie
        history.initialize_on_startup(os.environ.get("HISTFILE"))

        while True:
            self.remove_exited_jobs()
            self.COMP_LINE = self.read_command(command_trie, files_trie)
            
            
            # Handle empty line
            if not self.COMP_LINE or not self.COMP_LINE.strip():
                continue

            #adding the command to the history
            history.add(self.COMP_LINE)
            
            tokenized_command, is_piped = self.parser()
            
            if not tokenized_command:
                continue

            if is_piped:
                # Keep pipe execution as requested
                
                pipe = Pipe(tokenized_command)
                pipe.run()
            else:
                # 1. Find the primary command token
                cmd_token = None
                for token in tokenized_command:
                    if token.type in (TokenType.COMMAND, TokenType.PATH):
                        cmd_token = token
                        break

                if not cmd_token:
                    continue

                command_name = cmd_token.lexeme

                # 2. Extract arguments and redirection tokens in a single pass
                cmd_index = tokenized_command.index(cmd_token)
                remaining_tokens = tokenized_command[cmd_index + 1 :]

                args_list = []
                redirect_tokens = []
                
               
                
                i = 0
                while i < len(remaining_tokens):
                    token = remaining_tokens[i]

                    # If this token is a redirect operator, capture operator + target file
                    if token.type not in (TokenType.ARG, TokenType.PATH, TokenType.COMMAND, TokenType.BACKGROUND):
                        redirect_tokens.append(token)
                        if i + 1 < len(remaining_tokens):
                            redirect_tokens.append(remaining_tokens[i + 1])
                            i += 1  # Skip filename token so it's NOT added to args_list
                    else:
                        if "$" in token.lexeme:
                            
                            dollar_pos = token.lexeme.find("$")
                            pre_dollar = token.lexeme[:dollar_pos]
                            if dollar_pos + 1 < len(token.lexeme) and token.lexeme[dollar_pos+1] == "{":
                                curr = dollar_pos + 2
                                var_name=""
                                while curr < len(token.lexeme) and token.lexeme[curr] != "}":
                                    var_name+=token.lexeme[curr]
                                    curr+=1
                                if var_name in variables.variables:
                                    
                                    args_list.append(pre_dollar+variables.variables[var_name]+token.lexeme[curr+1:])
                                else:
                                    if pre_dollar or token.lexeme[curr+1:]:
                                        args_list.append(pre_dollar+token.lexeme[curr+1:])
                            else:    
                                var_name = token.lexeme[dollar_pos+1:]
                                if var_name in variables.variables:
                                    args_list.append(token.lexeme[:dollar_pos] + variables.variables[var_name])
                                else:
                                    if token.lexeme[:dollar_pos]:
                                        args_list.append(token.lexeme[:dollar_pos])
                        else:        
                            args_list.append(token.lexeme)

                    i += 1

                parsed_args = {
                    "args": args_list
                }
                
                extra = self.parse_redirects(redirect_tokens)

                # 3. Command Dispatching
                match command_name:
                    case "exit":
                        history.write_on_exit(os.environ.get("HISTFILE"))
                        history.history = []
                        break

                    case "echo":
                        BuiltIn("echo", parsed_args["args"], extra).run()

                    case "type":
                        BuiltIn("type", parsed_args["args"], extra).run()

                    case "pwd":
                        BuiltIn("pwd", extra=extra).run()

                    case "cd":
                        BuiltIn("cd", parsed_args["args"]).run()

                    case "complete":
                        BuiltIn("complete", parsed_args["args"], extra=extra).run()
                    
                    case "declare":
                        BuiltIn("declare",parsed_args["args"]).run()
                    
                    case "jobs":
                        BuiltIn("jobs", parsed_args["args"]).run()
                    
                    case "history":
                        BuiltIn("history" , parsed_args["args"]).run()

                    case _:
                        is_Exe = self.isExecutable(command_name)
                        if is_Exe.get("is_Exe"):
                            self.next_bg_id += 1
                            exec_item = Executable(
                                command_name,
                                parsed_args["args"],
                                is_Exe.get("full_path"),
                                extra,
                            )
                            exec_item.run()
                        else:
                            print(f"{command_name}: command not found")


if __name__ == "__main__":
    shell = Shell()
    shell.main()