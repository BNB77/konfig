import os
import sys
import socket
import getpass
import shlex
import tkinter as tk
from tkinter import scrolledtext
import argparse
import xml.etree.ElementTree as ET
import base64

USER = getpass.getuser()
HOST = socket.gethostname()
HOME = os.path.expanduser("~")

config = {
    "vfs_path": None,
    "startup_script": None
}

vfs = {
    "name": "default_vfs",
    "current_dir": "/",
    "files": {}
}

def load_vfs_from_xml(xml_path: str) -> bool:
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        vfs["name"] = root.get("name", "vfs")
        vfs["files"] = {}
        
        def parse_node(node, path="/"):
            for child in node:
                if child.tag == "file":
                    name = child.get("name")
                    content = child.text or ""
                    
                    if child.get("encoding") == "base64":
                        try:
                            content = base64.b64decode(content).decode('utf-8')
                        except:
                            pass
                    
                    file_path = os.path.join(path, name).replace("\\", "/")
                    vfs["files"][file_path] = {
                        "type": "file",
                        "content": content,
                        "name": name
                    }
                    
                elif child.tag == "directory":
                    name = child.get("name")
                    dir_path = os.path.join(path, name).replace("\\", "/")
                    vfs["files"][dir_path] = {
                        "type": "directory",
                        "name": name
                    }
                    parse_node(child, dir_path)
        
        parse_node(root)
        vfs["current_dir"] = "/"
        
        write_out(f"VFS '{vfs['name']}' loaded successfully from {xml_path}\n")
        return True
        
    except FileNotFoundError:
        write_out(f"ERROR: VFS file not found: {xml_path}\n")
        return False
    except ET.ParseError as e:
        write_out(f"ERROR: Invalid XML format: {e}\n")
        return False
    except Exception as e:
        write_out(f"ERROR: Failed to load VFS: {e}\n")
        return False

def normalize_path(path: str) -> str:
    if path.startswith("/"):
        return path.replace("\\", "/")
    
    if vfs["current_dir"] == "/":
        result = "/" + path
    else:
        result = vfs["current_dir"] + "/" + path
    
    parts = []
    for part in result.split("/"):
        if part == "..":
            if parts:
                parts.pop()
        elif part and part != ".":
            parts.append(part)
    
    return "/" + "/".join(parts) if parts else "/"

def list_directory(path: str) -> list:
    items = []
    path = normalize_path(path)
    
    if path != "/" and path not in vfs["files"]:
        return None
    
    for file_path, file_info in vfs["files"].items():
        if file_path == path:
            continue
            
        parent = os.path.dirname(file_path).replace("\\", "/")
        if parent == path or (path == "/" and "/" not in file_path.lstrip("/")):
            items.append(file_info["name"])
    
    return sorted(items)

def change_directory(path: str) -> bool:
    new_path = normalize_path(path)
    
    if new_path == "/":
        vfs["current_dir"] = "/"
        return True
    
    if new_path in vfs["files"] and vfs["files"][new_path]["type"] == "directory":
        vfs["current_dir"] = new_path
        return True
    
    return False

def prompt_path():
    if vfs["current_dir"] == "/":
        return "~"
    return "~" + vfs["current_dir"]

def build_prompt() -> str:
    return f"{USER}@{HOST}:{prompt_path()}$ "

def write_out(text: str):
    out.config(state=tk.NORMAL)
    out.insert(tk.END, text)
    out.config(state=tk.DISABLED)
    out.see(tk.END)

def execute_command(cmd: str, args: list) -> bool:
    if cmd == "ls":
        path = args[0] if args else vfs["current_dir"]
        items = list_directory(path)
        
        if items is None:
            write_out(f"ls: cannot access '{path}': No such file or directory\n")
            return False
        
        if items:
            write_out("  ".join(items) + "\n")
        return True
        
    elif cmd == "cd":
        if not args:
            vfs["current_dir"] = "/"
            prompt_lbl.config(text=build_prompt())
            return True
        
        if change_directory(args[0]):
            prompt_lbl.config(text=build_prompt())
            return True
        else:
            write_out(f"cd: {args[0]}: No such file or directory\n")
            return False
            
    elif cmd == "conf-dump":
        write_out("Configuration parameters:\n")
        write_out(f"vfs_path = {config['vfs_path']}\n")
        write_out(f"startup_script = {config['startup_script']}\n")
        write_out(f"vfs_name = {vfs['name']}\n")
        write_out(f"current_dir = {vfs['current_dir']}\n")
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
    write_out(f"\n{'='*50}\n")
    write_out(f"Executing startup script: {script_path}\n")
    write_out('='*50 + '\n\n')
    
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
        
        if not line or line.startswith("#"):
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
        except Exception as e:
            write_out(f"ERROR at line {line_num}: {e}\n")
    
    write_out(f"\n{'='*50}\n")
    write_out("Startup script execution completed\n")
    write_out('='*50 + '\n\n')

def on_enter(event=None):
    line = inpe.get()
    inpe.delete(0, tk.END)
    handle_command(line)

def parse_arguments():
    parser = argparse.ArgumentParser(description='OS Shell Emulator')
    parser.add_argument('--vfs', dest='vfs_path', 
                        help='Path to VFS XML file')
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
    root.title("Shell Emulator - Stage 3: VFS")
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
    
    write_out(f"Configuration:\n")
    write_out(f"VFS Path: {config['vfs_path']}\n")
    write_out(f"Startup Script: {config['startup_script']}\n")
    write_out("-" * 50 + "\n\n")
    
    if config['vfs_path']:
        load_vfs_from_xml(config['vfs_path'])
    else:
        write_out("No VFS specified. Using empty VFS.\n")
    
    write_out("\n")
    
    if config['startup_script']:
        execute_startup_script(config['startup_script'])
    
    write_out(build_prompt())
    inpe.focus()
    root.mainloop()

if __name__ == "__main__":
    main()