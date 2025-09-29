import os
import socket
import getpass
import shlex
import tkinter as tk
from tkinter import scrolledtext

USER = getpass.getuser() 
HOST = socket.gethostname()
HOME = os.path.expanduser("~")

def prompt_path():
    return "~"

def build_prompt() -> str:
    return f"{USER}@{HOST}:{prompt_path()}$ "

def write_out(text: str):
    out.config(state=tk.NORMAL)
    out.insert(tk.END, text)
    out.config(state=tk.DISABLED)
    out.see(tk.END)

def handle_command(line: str):
    write_out(build_prompt() + line + "\n")
    
    if not line.strip():
        return
    
    try:
        parts = shlex.split(line, posix=True)
    except ValueError as e:
        write_out(f"parse error: {e}\n")
        return
    
    cmd = parts[0]
    args = parts[1:]
    
    if cmd == "ls":
        write_out(f"ls args: {args}\n")
    elif cmd == "cd":
        write_out(f"cd args: {args}\n")
    elif cmd == "exit":
        root.after(50, root.destroy)
    else:
        write_out(f"{cmd}: command not found\n")

def on_enter(event=None):
    line = inpe.get()
    inpe.delete(0, tk.END)
    handle_command(line)

root = tk.Tk()
root.title("Console Emulator (Stage 1: REPL)")
root.geometry("1000x600")

main = tk.Frame(root)
main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

inp = tk.Frame(main)
inp.pack(fill=tk.X)

prompt_lbl = tk.Label(inp, text=build_prompt(), font=("Courier", 11))
prompt_lbl.pack(side=tk.LEFT)

inpe = tk.Entry(inp, font=("Courier", 11))
inpe.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
inpe.bind("<Return>", on_enter)

enter_btn = tk.Button(inp, text="Enter", command=on_enter)
enter_btn.pack(side=tk.RIGHT)

out = scrolledtext.ScrolledText(main, height=25, width=80, font=("Courier", 11))
out.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
out.config(state=tk.DISABLED)

write_out(build_prompt())
inpe.focus()

root.mainloop()