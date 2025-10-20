#!/usr/bin/env python3

import os
import sys
import socket
import getpass
import shlex
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

command_history = []

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
                    owner = child.get("owner", USER)
                    group = child.get("group", "users")
                    
                    if child.get("encoding") == "base64":
                        try:
                            content = base64.b64decode(content).decode('utf-8')
                        except:
                            pass
                    
                    file_path = os.path.join(path, name).replace("\\", "/")
                    vfs["files"][file_path] = {
                        "type": "file",
                        "content": content,
                        "name": name,
                        "owner": owner,
                        "group": group
                    }
                    
                elif child.tag == "directory":
                    name = child.get("name")
                    owner = child.get("owner", USER)
                    group = child.get("group", "users")
                    
                    dir_path = os.path.join(path, name).replace("\\", "/")
                    vfs["files"][dir_path] = {
                        "type": "directory",
                        "name": name,
                        "owner": owner,
                        "group": group
                    }
                    parse_node(child, dir_path)
        
        parse_node(root)
        vfs["current_dir"] = "/"
        
        print(f"VFS '{vfs['name']}' loaded successfully from {xml_path}")
        return True
        
    except FileNotFoundError:
        print(f"ERROR: VFS file not found: {xml_path}")
        return False
    except ET.ParseError as e:
        print(f"ERROR: Invalid XML format: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Failed to load VFS: {e}")
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

def get_file_content(path: str) -> str:
    normalized = normalize_path(path)
    
    if normalized in vfs["files"] and vfs["files"][normalized]["type"] == "file":
        return vfs["files"][normalized]["content"]
    
    return None

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

def command_wc(args: list) -> bool:
    if not args:
        print("wc: missing file operand")
        return False
    
    file_path = args[0]
    content = get_file_content(file_path)
    
    if content is None:
        print(f"wc: {file_path}: No such file or directory")
        return False
    
    lines = content.count('\n') + (1 if content and not content.endswith('\n') else 0)
    words = len(content.split())
    chars = len(content)
    
    print(f"  {lines}  {words}  {chars} {file_path}")
    return True

def show_command_history(args: list) -> bool:
    if not command_history:
        print("History is empty")
        return True
    
    for idx, cmd in enumerate(command_history, 1):
        print(f"  {idx}  {cmd}")
    
    return True

def command_chown(args: list) -> bool:
    if len(args) < 2:
        print("chown: missing operand")
        print("Usage: chown [OWNER][:GROUP] FILE")
        return False
    
    owner_spec = args[0]
    file_path = args[1]
    
    if ":" in owner_spec:
        owner, group = owner_spec.split(":", 1)
    else:
        owner = owner_spec
        group = None
    
    normalized_path = normalize_path(file_path)
    
    if normalized_path not in vfs["files"]:
        print(f"chown: cannot access '{file_path}': No such file or directory")
        return False
    
    vfs["files"][normalized_path]["owner"] = owner
    if group:
        vfs["files"][normalized_path]["group"] = group
    
    print(f"Changed owner of '{file_path}' to {owner}" + (f":{group}" if group else ""))
    
    return True

def command_vfs_load(args: list) -> bool:
    if not args:
        print("vfs-load: missing file operand")
        print("Usage: vfs-load <path_to_vfs.xml>")
        return False
    
    vfs_path = args[0]
    
    print(f"Loading new VFS from: {vfs_path}")
    success = load_vfs_from_xml(vfs_path)
    
    if success:
        config['vfs_path'] = vfs_path
        print("VFS loaded successfully. Current directory reset to root.")
    
    return success

def prompt_path():
    if vfs["current_dir"] == "/":
        return "~"
    return "~" + vfs["current_dir"]

def build_prompt() -> str:
    return f"{USER}@{HOST}:{prompt_path()}$ "

def execute_command(cmd: str, args: list) -> bool:
    if cmd == "ls":
        path = args[0] if args else vfs["current_dir"]
        items = list_directory(path)
        
        if items is None:
            print(f"ls: cannot access '{path}': No such file or directory")
            return False
        
        if items:
            print("  ".join(items))
        return True
        
    elif cmd == "cd":
        if not args:
            vfs["current_dir"] = "/"
            return True
        
        if change_directory(args[0]):
            return True
        else:
            print(f"cd: {args[0]}: No such file or directory")
            return False
    
    elif cmd == "wc":
        return command_wc(args)
    
    elif cmd == "history":
        return show_command_history(args)
    
    elif cmd == "chown":
        return command_chown(args)
    
    elif cmd == "vfs-load":
        return command_vfs_load(args)
            
    elif cmd == "conf-dump":
        print("Configuration parameters:")
        print(f"vfs_path = {config['vfs_path']}")
        print(f"startup_script = {config['startup_script']}")
        print(f"vfs_name = {vfs['name']}")
        print(f"current_dir = {vfs['current_dir']}")
        print(f"commands_in_history = {len(command_history)}")
        return True
        
    elif cmd == "exit":
        return True
    else:
        print(f"{cmd}: command not found")
        return False

def execute_startup_script(script_path: str):
    print(f"\n{'='*50}")
    print(f"Executing startup script: {script_path}")
    print('='*50 + '\n')
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"ERROR: Startup script not found: {script_path}")
        return
    except Exception as e:
        print(f"ERROR: Failed to read startup script: {e}")
        return
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        
        if not line or line.startswith("#"):
            continue
        
        print(build_prompt() + line)
        
        command_history.append(line)
        
        try:
            parts = shlex.split(line, posix=True)
            if not parts:
                continue
                
            cmd = parts[0]
            args = parts[1:]
            success = execute_command(cmd, args)
            
            if not success:
                print(f"Warning: Command failed at line {line_num}, continuing...")
        except ValueError as e:
            print(f"ERROR at line {line_num}: Parse error: {e}")
        except Exception as e:
            print(f"ERROR at line {line_num}: {e}")
    
    print(f"\n{'='*50}")
    print("Startup script execution completed")
    print('='*50 + '\n')

def parse_arguments():
    parser = argparse.ArgumentParser(description='OS Shell Emulator - Variant 15')
    parser.add_argument('--vfs', dest='vfs_path', 
                        help='Path to VFS XML file')
    parser.add_argument('--startup', dest='startup_script',
                        help='Path to startup script')
    
    args = parser.parse_args()
    
    if args.vfs_path:
        config['vfs_path'] = args.vfs_path
    if args.startup_script:
        config['startup_script'] = args.startup_script

def main():
    parse_arguments()
    
    print(f"Configuration:")
    print(f"VFS Path: {config['vfs_path']}")
    print(f"Startup Script: {config['startup_script']}")
    print("-" * 50 + "\n")
    
    if config['vfs_path']:
        load_vfs_from_xml(config['vfs_path'])
    else:
        print("No VFS specified. Using empty VFS.")
    
    print()
    
    if config['startup_script']:
        execute_startup_script(config['startup_script'])
    
    while True:
        try:
            line = input(build_prompt())
            
            if not line.strip():
                continue
            
            command_history.append(line)
            
            try:
                parts = shlex.split(line, posix=True)
                if not parts:
                    continue
                    
                cmd = parts[0]
                args = parts[1:]
                
                if cmd == "exit":
                    print("Exiting shell emulator...")
                    break
                    
                execute_command(cmd, args)
                
            except ValueError as e:
                print(f"parse error: {e}")
            except Exception as e:
                print(f"error: {e}")
                
        except EOFError:
            print("\nExiting shell emulator...")
            break
        except KeyboardInterrupt:
            print("\nUse 'exit' command to quit")
            continue

if __name__ == "__main__":
    main()