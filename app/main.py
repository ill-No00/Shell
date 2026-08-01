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


class Shell:
    PATH = os.environ.get("PATH", "")

    def __init__(self):
        self.command_trie = Trie("command")
        self.files_trie = Trie("file")
        self.command_trie.initialize()
        self.files_trie.initialize()
        self.COMP_LINE = ""
        self.CURRENT_IND = 0

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
        """Tokenizes line input with support for quotes, escapes, and stream redirections."""
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

                # printable key press
                tab_count = 0
                self.COMP_LINE += c
                self.CURRENT_IND = len(self.COMP_LINE)
                sys.stdout.write(c)
                sys.stdout.flush()

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        return self.COMP_LINE.strip()

    def main(self):
        files_trie = self.files_trie
        command_trie = self.command_trie

        while True:
            self.COMP_LINE = self.read_command(command_trie, files_trie)
            if not self.COMP_LINE:
                continue

            start_with = self.COMP_LINE.split(" ")[0]

            match start_with:
                case "exit":
                    break

                case "echo":
                    arg_res = self.treatArgs(self.COMP_LINE[5:])
                    BuiltIn("echo", arg_res.get("args"), arg_res.get("redirect")).run()

                case "type":
                    arg_res = self.treatArgs(self.COMP_LINE[5:])
                    BuiltIn("type", arg_res.get("args"), arg_res.get("redirect")).run()

                case "pwd":
                    args = self.treatArgs(self.COMP_LINE[4:])
                    BuiltIn("pwd", extra=args.get("redirect")).run()

                case "cd":
                    res = self.treatArgs(self.COMP_LINE[3:])
                    BuiltIn("cd", res.get("args")).run()

                case "complete":
                    res = self.treatArgs(self.COMP_LINE[9:])
                    BuiltIn("complete", res.get("args"), extra=res.get("redirect")).run()

                case _:
                    first_blank = self.find_blank_ind()
                    if first_blank != -1:
                        cmd_part = self.COMP_LINE[:first_blank]
                        args_part = self.COMP_LINE[first_blank + 1 :]
                    else:
                        cmd_part = self.COMP_LINE
                        args_part = ""

                    parsed_cmd = self.treatArgs(cmd_part)["args"]
                    command = parsed_cmd[0] if parsed_cmd else cmd_part

                    is_Exe = self.isExecutable(command)
                    if is_Exe.get("is_Exe"):
                        res = self.treatArgs(args_part)
                        exec_item = Executable(
                            command,
                            res["args"],
                            is_Exe.get("full_path"),
                            res.get("redirect"),
                        )
                        exec_item.run()
                    else:
                        print(f"{self.COMP_LINE}: command not found")


if __name__ == "__main__":
    shell = Shell()
    shell.main()