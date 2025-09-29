import os
import sys
import socket
import getpass
import shlex
import tkinter as tk
from tkinter import scrolledtext
import argparse

USER = getpass.getuser()
HOST = socket.gethostname()
HOME = os.path.expanduser("~")

config = {
    "vfs_path": None,
    "startup_script": None
}

def prompt_path():
    return "~"

def build_prompt() -> str:
    return f"{USER}@{HOST}:{prompt_path()}$ "

def write_out(text: str):
    out.config(state=tk.NORMAL)
    out.insert(tk.END, text)
    out.config(state=tk.DISABLED)
    out.see(tk.END)

def execute_command(cmd: str, args: list) -> bool:
    if cmd == "ls":
        write_out(f"ls args: {args}\n")
        return True
    elif cmd == "cd":
        write_out(f"cd args: {args}\n")
        return True
    elif cmd == "conf-dump":
        write_out("Configuration parameters:\n")
        write_out(f"vfs_path = {config['vfs_path']}\n")
        write_out(f"startup_script = {config['startup_script']}\n")
        return True
    elif cmd == "exit":
        root.after(50, root.destroy)
        return True
    else:
        write_out(f"{cmd}: command not found\n")
        return False

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
    execute_command(cmd, args)

def execute_startup_script(script_path: str):
    write_out(f"Executing startup script: {script_path} ---\n")
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        write_out(f"ERROR: Startup script not found: {script_path}\n")
        return
    except Exception as e:
        write_out(f"ERROR: Failed to read startup script: {e}\n")
        return
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        
        if not line:
            continue
        
        write_out(build_prompt() + line + "\n")
        
        try:
            parts = shlex.split(line, posix=True)
            if parts:
                cmd = parts[0]
                args = parts[1:]

                success = execute_command(cmd, args)
                
                if not success:
                    write_out(f"Warning: Command failed at line {line_num}, continuing...\n")
        except ValueError as e:
            write_out(f"ERROR at line {line_num}: Parse error: {e}\n")
            write_out(f"Skipping erroneous line, continuing...\n")
        except Exception as e:
            write_out(f"ERROR at line {line_num}: {e}\n")
            write_out(f"Skipping erroneous line, continuing...\n")
    
    write_out("--- Startup script execution completed ---\n\n")

def on_enter(event=None):
    line = inpe.get()
    inpe.delete(0, tk.END)
    handle_command(line)

def parse_arguments():
    parser = argparse.ArgumentParser(description='OS Shell Emulator')
    parser.add_argument('--vfs', dest='vfs_path', 
                        help='Path to VFS location')
    parser.add_argument('--startup', dest='startup_script',
                        help='Path to startup script')
    
    args = parser.parse_args()
    
    if args.vfs_path:
        config['vfs_path'] = args.vfs_path
    if args.startup_script:
        config['startup_script'] = args.startup_script

def initialize_gui():
    global root, out, inpe, prompt_lbl
    
    root = tk.Tk()
    root.title("Console Emulator (Stage 2: Configuration)")
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

def main():
    parse_arguments()
    
    initialize_gui()
    
    write_out(f"VFS Path: {config['vfs_path']}\n")
    write_out(f"Startup Script: {config['startup_script']}\n")
    write_out("------------------------------\n\n")
    
    if config['startup_script']:
        execute_startup_script(config['startup_script'])
    
    write_out(build_prompt())
    inpe.focus()
    
    root.mainloop()

if __name__ == "__main__":
    main()