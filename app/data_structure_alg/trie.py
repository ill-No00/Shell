import os
from pathlib import Path


class Trie:
    def __init__(self, type_name):
        self.type = type_name
        self.trie = {}

    def initialize(self):
        if self.type == "command":
            # 1. Built-in shell commands
            for cmd in ["echo", "type", "exit", "pwd", "cd"]:
                self.insert(cmd)
            
            # 2. Executables in PATH
            path_env = os.environ.get("PATH", "")
            for directory in path_env.split(":"):
                if not os.path.isdir(directory):
                    continue
                try:
                    for name in os.listdir(directory):
                        full_path = os.path.join(directory, name)
                        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                            self.insert(name.strip())
                except PermissionError:
                    continue

        elif self.type == "file":
            # 3. Files AND Directories in Current Working Directory (CWD)
            cwd = Path.cwd()
            try:
                for name in os.listdir(cwd):
                    # Always insert the simple relative name (whether file OR directory!)
                    self.insert(name.strip())
            except PermissionError:
                pass

    def insert(self, word):
        d = self.trie
        for c in word:
            if c not in d:
                d[c] = {}
            d = d[c]
        d['|'] = {}  # ✅ FIXED: Use empty dict instead of string '|'!
        
    def add_full_path_recursive(self, directory):
        try:
            if not os.path.isdir(directory):
                return

            for name in os.listdir(directory):
                # Form path properly (e.g. "tmp/blueberry")
                if directory == "/":
                    full_path = f"/{name}"
                else:
                    full_path = os.path.join(directory, name)

                # Insert into Trie
                self.insert(full_path.strip())

                # Recurse down subdirectories
                if os.path.isdir(full_path):
                    self.add_full_path_recursive(full_path)

        except PermissionError:
            return

    def search(self, word):
        d = self.trie
        for c in word:
            if c not in d:
                return False
            d = d[c]
        return '|' in d

    def startsWith(self, prefix):
        d = self.trie
        for c in prefix:
            if c not in d:
                return False
            d = d[c]
        return True

    def autoComplete(self, prefix):
        d = self.trie
        for c in prefix:
            if c in d:
                d = d[c]
            else:
                return []
        
        result = []
        self._dfs(d, prefix, result)
        return result

    def _dfs(self, d, current_word, result):
        if '|' in d:
            result.append(current_word)
            
        for c in d:
            if c == '|':
                continue
            self._dfs(d[c], current_word + c, result)