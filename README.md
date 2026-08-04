# ish — A Unix-like Shell in Python

**ish** is a Unix-like shell built from scratch in Python.

The goal of this project was to understand what happens underneath the commands we normally use in a terminal, rather than simply using an existing shell.

## Features

- Execute external commands
- Built-in commands
- Command parsing
- Pipes (`|`)
- Multiple pipelines
- Input/output redirection
- Environment variables
- Variable expansion
- Command history
- Load history from a file
- ↑ / ↓ history navigation
- Tab completion
- Background processes (`&`)
- Basic job management
- Process creation using `fork()` / `exec()`
- File descriptor manipulation with `dup2()`

## Example

```bash
$ ish

$ echo "hello world"
hello world

$ ls | grep py
main.py
pipe.py

$ echo "hello" > test.txt
$ cat test.txt
hello

$ export NAME=ish
$ echo $NAME
ish

$ sleep 5 &
[1] 12345

$ history
    1  echo "hello world"
    2  ls | grep py
    3  echo "hello" > test.txt
```

## Running the Shell

Clone the repository and run:

```bash
python3 main.py
```

Or, if you have made the file executable:

```bash
./main.py
```

## Why I Built It

This project started as a way to learn more about Unix processes, file descriptors, pipes, and how shells actually work.

Building features such as:

```text
command → fork → exec
             ↓
          pipe()
             ↓
          dup2()
```

helped me understand concepts that are easy to take for granted when using a terminal every day.

## Status

This is currently an **MVP** and the project is still in progress.

I plan to continue improving the shell and adding more features as I learn more about Unix and low-level programming.

## Tech

- Python 3
- Unix/POSIX system calls
- `os.fork()`
- `os.exec*()`
- `os.pipe()`
- `os.dup2()`
- `os.waitpid()`
- Terminal input / escape sequences
