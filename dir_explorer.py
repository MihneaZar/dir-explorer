from ConsoleListInterface import ConsoleListInterface, MenuInterface, waitForEnter, autocomplete
from send2trash import send2trash
from termcolor import colored
from filetype import is_image
from readchar import key
import subprocess
import pyperclip
import shutil
import cursor
import yaml
import json
import sys
import os

# only import this module for windows (for reading lnk files)
if os.name == 'nt':
    from win32com.client import Dispatch


HOMEPATH = os.path.dirname(os.path.realpath(__file__))
DATAPATH = f"{HOMEPATH}/data"
GOTOFILE = f"{DATAPATH}/goto_autocomplete.json" # autocomplete data for 'go to directory' (ctrl+G) command

sys.stderr = open(f'{DATAPATH}/errors.txt', "a")

NEXT_DIR  = '\\' # preferable for certain functionalities (rather than '/')
HOMEDRIVE = os.environ["HOMEDRIVE"] 

# for running python files / .exe's
RUN_HERE  = "Run in the same tab"
RUN_CLOSE = "Run in another tab and close it once finished"
RUN_STAY  = "Run in another tab and keep it open once finished"
RUN_TYPES = [RUN_HERE, RUN_CLOSE, RUN_STAY]


COMMAND_LIST = [key.ENTER, key.CTRL_S, key.CTRL_O, key.BACKSPACE, key.CTRL_G, key.CTRL_T, key.CTRL_D, key.CTRL_P, key.TAB, '`', '~', 
                key.CTRL_N, key.CTRL_R, key.CTRL_C, key.CTRL_X, key.INSERT, key.CTRL_Z, key.DELETE, key.CTRL_B, key.CTRL_U, '?', key.ESC]

RUNNABLES = ["exe", "py", "ba", "sh"]

DIR   = "dir"
EXE   = "exe"
OTHER = "other"



def get_file_type(filename, current_path):
    # changing links to the target directory/file
    if filename[filename.rfind('.') + 1:] == "lnk" and os.name == 'nt':
        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(current_path + NEXT_DIR + filename)
        filepath = shortcut.TargetPath
    else:
        filepath = current_path + NEXT_DIR + filename

    if os.path.isdir(filepath):
        return DIR
    elif '.' in filepath and filepath[filepath.rfind('.') + 1:] in RUNNABLES:
        return EXE
    else:
        return OTHER

def get_file_color(filename, current_path, use_light_yellow=False):
    file_type = get_file_type(filename, current_path)

    if file_type == DIR:
        return "light_yellow" if use_light_yellow else "yellow"
    elif file_type == EXE:
        return "cyan"
    else:
        return "light_grey"

def get_copy_move_name(path):
    filename  = path[path.rfind(NEXT_DIR) + 1:]
    filepath  = path[:path.rfind(NEXT_DIR)]
    return colored(filename, get_file_color(filename, filepath, use_light_yellow=True))


def set_top_text(console, current_path):
    top_text = colored(f'{HOMEDRIVE}\n', 'light_yellow') if current_path == f'{HOMEDRIVE}\\' else colored(f'{current_path}\n', 'light_yellow')
    top_text += f"{colored('Copy', 'yellow')}: {', '.join(get_copy_move_name(copy) for copy in console.copy)}\n" if console.copy else ""
    top_text += f"{colored('Move', 'yellow')}: {', '.join(get_copy_move_name(move) for move in console.move)}\n" if console.move else ""

    console.setTopText(top_text)


def get_files(console, current_path):
    files  = [dir for dir in os.listdir(current_path) if get_file_type(dir, current_path) == DIR]     # putting directories first 
    files += [exe for exe in os.listdir(current_path) if get_file_type(exe, current_path) == EXE]     # then runnable files
    files += [file for file in os.listdir(current_path) if get_file_type(file, current_path) == OTHER # then all other files
                                                           and file[file.find('.') + 1:] != "ini"]    # that aren't the .ini Windows file for dirs

    set_top_text(console, current_path)

    return files


def update_goto_autocomplete(curr_string, saved_string):
    # using a vector for pass-by-reference
    prev_string = saved_string[0]
    saved_string[0] = curr_string

    new_autocomplete = None

    # input("prev_string: " + prev_string)
    # input("curr_string: " + curr_string)

    # the autocomplete list changes if:
    # - a '\' or a '/' has been typed   (the current string ends in either slash and the previous string is shorter) -> moving further into a different directory
    # - a '\' or a '/' has been deleted (the previous string ends in either slash and the current string is shorter) -> moving back into the previous directory 
    # - the current string is empty -> moving into the current directory of the dir-explorer
    if (curr_string.endswith(NEXT_DIR) or curr_string.endswith('/') and len(prev_string) < len(curr_string)) or \
       (prev_string.endswith(NEXT_DIR) or prev_string.endswith('/') and len(curr_string) < len(prev_string)) or \
       not curr_string:

        # current directory is all the way to the final slash ('\' or '/') or it is '.\' (current dir from dir-explorer) if there are no slashes in string
        last_slash = max(curr_string.rfind(NEXT_DIR), curr_string.rfind('/'))
        curr_dir = curr_string[:last_slash + 1] if last_slash != -1 else ".\\"
        clean_curr_dir = curr_dir.replace('/', NEXT_DIR) # using a 'clean' path (with only '\') since os.listdir and os.path.isdir have problems with '/'

        # user might have typed a directory that does not actually exist
        if os.path.isdir(clean_curr_dir): 

            # only add the saved directories if in current dir from dir-explorer
            if clean_curr_dir == ".\\":
                # re-reading autocomplete in case it's been changed in a different dir-explorer
                # using try in case autocomplete file has not been created yet or it has been corrupted
                try:
                    goto_autocomplete = json.load(open(GOTOFILE, encoding="utf-8")) # reading automplete file
                except:
                    # fixing goto_autocomplete file
                    with open(GOTOFILE, 'w', encoding='utf-8') as file:
                        json.dump({}, file)
                    goto_autocomplete = {}
                new_autocomplete = [saved_dir for saved_dir in goto_autocomplete]

            else:
                new_autocomplete = []
            # input(new_autocomplete)

            new_autocomplete += [(curr_dir if curr_dir != ".\\" else "") + dir for dir in os.listdir(clean_curr_dir) 
                                 if os.path.isdir(clean_curr_dir + dir) and dir not in new_autocomplete] # avoiding adding same directory from saved and current directory

    # input(new_autocomplete)
    return new_autocomplete


def print_filename(filename, max_name_width, current_path):
    name = filename
    if max_name_width <= len(name):
        if not os.path.isdir(current_path + NEXT_DIR + filename):
            # if name.rfind('.') != 0 for hidden files
            extension = name[name.rfind('.'):] if name.rfind('.') != 0 else ""
        else: 
            extension = ''
        name = name[0:max(max_name_width - 1 - len(extension), 0)] + '-' + extension 

    return colored(name, get_file_color(filename, current_path))


def print_tree(current_path):
    if current_path == f'{HOMEDRIVE}\\':
        os.system(f'title Local Disk ({HOMEDRIVE}) - Tree')
            
    else:  
        os.system(f'title {current_path[current_path.rfind(NEXT_DIR) + 1:]} - Tree')

    tree = subprocess.run(f'tree "{current_path}" /F', capture_output=True, universal_newlines=True, shell=True).stdout

    if tree.count('\n') > 9000:
        raise Exception(colored("Directory tree too large to display.", "yellow"))

    
    # ignoring first three lines of output
    # which are not part of the tree
    for _ in range(0, 3):
        tree = tree[tree.find('\n')+1:]

    tree = tree.replace('¦', '│').replace('+', '├').replace('\\', '└').replace('-', '─') # replacing normal ascii with extended characters


    # replacing '├' with '└' when the element is last in list
    # for whatever reason it's not set right from the output 🙄
    pos = tree.find('├')
    while (pos != -1):
        prev_newline = tree.rfind('\n', 0, pos)
        next_newline = tree.find('\n', pos)

        # if the same position as the '├' on the next line is empty (space or newline), or the string ends, it means it should actually be a '└'
        # aka it's the last item in the list
        if next_newline == -1 or tree[next_newline + (pos - prev_newline)] == ' ' or tree[next_newline + (pos - prev_newline)] == '\n':
            tree = tree[:pos] + '└' + tree[pos+1:]

        pos = tree.find('├', pos+1)

    # removing unnecessary "No subfolders exist" message
    if "No subfolders exist" in tree:
        tree = tree.replace("No subfolders exist", "").rstrip(" \n") + "\n\n"

    print(current_path[current_path.rfind(NEXT_DIR) + 1:])
    print(tree, end='')

    print("Press enter to continue.")
    waitForEnter()


def select_run_type(run_type):
    menu_structure = yaml.safe_load(open(f"{DATAPATH}/running_type_menu.yaml"))
    menu = MenuInterface(menu_structure) 
    menu.updatePos(list(menu.getMenuStructure()[next(item for item in menu_structure)].keys()).index(run_type))
    menu.changeOptionNames([], {run_type: run_type + " (selected)"}) # adding ' (selected)' to chosen run type
    while True:
        path = menu.interactWithMenu()

        # ignoring backspace to main menu
        if not path:
            continue

        path = path[0]
        
        # same run_type selected or exited through esc/backspace
        if "(selected)" in path or path in [key.ESC, key.BACKSPACE]:
            return run_type

        if path in RUN_TYPES:
            # changes = MenuInterface.selectOption(selectedOption=run_type, newSelectedOption=path, options=RUN_TYPES, padding=False, selectText=" (selected)")
            # menu.changeOptionNames([], changes)

            menu.changeOptionNames([], {run_type + " (selected)": run_type}) # removing ' (selected)' from chosen run type
            menu.getMenuStructure()["Selected"] = path # saving newly selected run type
            yaml.safe_dump(menu.getMenuStructure(), open(f"{DATAPATH}/running_type_menu.yaml", 'w'), indent=4, sort_keys=False)
            with open(f"{DATAPATH}/running_type_menu.yaml", 'r') as file:
                lines = [line for line in file.readlines()]
            
            # removing 'null' since it's not needed
            with open(f"{DATAPATH}/running_type_menu.yaml", 'w') as file:
                for line in lines:
                    file.write(line.replace('null', ''))

            return path # returning newly selected run type

def run_exec(command, run_type): 
    if run_type == RUN_CLOSE:
        command = f"start cmd /c {command}"

    if run_type == RUN_STAY:
        command = f"start cmd /k {command}"

    os.system(command)

    if run_type == RUN_HERE:
        print(f"[{colored('Dir-Explorer', 'yellow')}] Program finished. Press enter to continue.\n")
        cursor.hide()
        waitForEnter()


def explore_loop(current_path="."):
    # using try in case autocomplete file has not been created yet or it has been corrupted
    try:
        goto_autocomplete = json.load(open(GOTOFILE, encoding="utf-8")) # reading automplete file
    except:
        # fixing goto_autocomplete file
        with open(GOTOFILE, 'w', encoding='utf-8') as file:
            json.dump({}, file)
        goto_autocomplete = {}

    if current_path in goto_autocomplete:
        current_path = goto_autocomplete[current_path]

    # removing quotes from path, they just get in the way
    current_path = current_path.replace('\"', '')
    current_path = current_path.replace('\'', '')
    
    # in case given path ends with '/' or '\', the os.chdir fucks up
    if current_path and (current_path[-1] == NEXT_DIR or current_path[-1] == '/'):
        current_path = current_path[:-1]

    # ignoring given current path if it is not directory
    if not current_path or not os.path.isdir(current_path):
        current_path = os.getcwd()

    else:
        path_was_given = (current_path != ".") 
        
        # resolving relative path
        os.chdir(current_path)
        current_path = os.getcwd()

        # if a path was given and its not in autocomplete, add it
        if path_was_given:
            autocomplete_name = current_path[current_path.rfind(NEXT_DIR) + 1:]
            if autocomplete_name not in goto_autocomplete:
                goto_autocomplete[autocomplete_name] = current_path
                with open(GOTOFILE, 'w', encoding='utf-8') as file:
                    json.dump(goto_autocomplete, file)

    # set working directory to current_path, in case it's been given as command-line argument 
    os.chdir(current_path)

    console = ConsoleListInterface(items=[], specialCommands=COMMAND_LIST, printFunc=lambda filename, max_name_width: 
                                   print_filename(filename, max_name_width, current_path), helpSearchColor="yellow")
    console.setTitle("Dir-Explorer")

    console.copy = []
    console.move = []

    files = get_files(console, current_path)
    console.updateList(files)

    while (True):
        command, curr_pos = console.interact()

        # shield check for all commands related to current position
        # in case directory contents have been changed outside this dir-explorer
        if command in [key.ENTER, key.CTRL_O, key.CTRL_P, key.CTRL_R, key.CTRL_C, key.CTRL_X, key.DELETE]:
            check_files = get_files(console, current_path)
            if check_files != files:
                console.separateInteraction(message=colored("Directory contents have been changed outside this Dir-Explorer.\nDir-Explorer has updated the list automatically.\n", "yellow"))

                files = check_files
                console.updateList(files)
                continue


        # select run type
        if command == key.CTRL_S:
            # re-reading run_type in case it's been changed in a different dir-explorer
            run_type = yaml.safe_load(open(f"{DATAPATH}/running_type_menu.yaml"))["Selected"] # reading last selected run type
            run_type = console.separateInteraction(function=lambda: select_run_type(run_type))

            continue

        # go to selected directory / open file in default app (or "select app" prompt)
        if command == key.ENTER:
            changed_directory = False

            try:
                file = files[curr_pos]
                if get_file_type(file, current_path) == DIR:
                    # checking if it is a simple directory
                    if os.path.isdir(current_path + NEXT_DIR + file):
                        current_path += NEXT_DIR + file if current_path != f'{HOMEDRIVE}\\' else file
                        changed_directory = True
                    # checking if windows just in case
                    elif os.name == 'nt':
                        shell = Dispatch("WScript.Shell")
                        shortcut = shell.CreateShortCut(current_path + NEXT_DIR + file)
                        current_path = shortcut.TargetPath
                    else: 
                        continue
                    
                    files = get_files(console, current_path)
                    os.chdir(current_path) # changing working directory to current one
                    
                    console.updateList(files)
                    console.updatePos(0)

                else: 
                    # re-reading run_type in case it's been changed in a different dir-explorer
                    run_type = yaml.safe_load(open(f"{DATAPATH}/running_type_menu.yaml"))["Selected"] # reading last selected run type
                    if '.' not in file[1:]:
                        # file has no extension, ignoring the '.' from hidden files
                        subprocess.run(f'start notepad {current_path + NEXT_DIR + file}', capture_output=False, shell=True)
                    elif file[file.rfind('.'):] == ".py":
                        console.separateInteraction(function=lambda: run_exec(f'python3 "{current_path + NEXT_DIR + file}"', run_type),showCursor=True, startAtTop=True)
                        console.setTitle("Dir-Explorer")
                        # updating files in case the other program created/deleted files
                        files = get_files(console, current_path)
                        console.updateList(files)
                    elif file[file.rfind('.'):] in [".exe", ".bat", ".sh"]: 
                        console.separateInteraction(function=lambda: run_exec(f'"{current_path + NEXT_DIR + file}"', run_type), showCursor=True, startAtTop=True)
                        console.setTitle("Dir-Explorer")
                        # updating files in case the other program created/deleted files
                        files = get_files(console, current_path)
                        console.updateList(files)

                    else:
                        subprocess.run(f'explorer {current_path + NEXT_DIR + file}', capture_output=False, shell=True)


            except Exception as e:
                if changed_directory:
                    current_path = current_path[0:current_path.rfind(NEXT_DIR)]

                e = str(e)

                if "WinError" in e:
                    e = e[e.find("]")+2:e.find(":")]
                    
                if e[-1] != '.':
                    e += '.'

                console.separateInteraction(message=f'\n{e}\n')

            continue

        # open images in paint and other files in notepad
        if command == key.CTRL_O:
            file = files[curr_pos]
            if os.path.isdir(current_path + NEXT_DIR + file):
                
                console.separateInteraction(message=colored(f'\nThis is a directory.\n', 'yellow'))

                continue

            try:
                if is_image(current_path + NEXT_DIR + file):
                    # if image, open in paint
                    # interestingly, only paint needs "" in filepath if there are spaces
                    subprocess.run(f'start mspaint "{current_path + NEXT_DIR + file}"', capture_output=False, shell=True)
                elif file[file.rfind('.'):] == ".py":
                    # opening python file in vscode
                    subprocess.run(f'explorer {current_path + NEXT_DIR + file}', capture_output=False, shell=True)
                else:
                    # else, open in notepad
                    subprocess.run(f'start notepad {current_path + NEXT_DIR + file}', capture_output=False, shell=True)

            except Exception as e:
                e = str(e)

                if "WinError" in e:
                    e = e[e.find("]")+2:e.find(":")]

                if e[-1] != '.':
                    e += '.'

                console.separateInteraction(message=f'\n{e}\n')

            continue

        # go to parent directory
        if command == key.BACKSPACE:
            prev_dir = current_path[current_path.rfind(NEXT_DIR) + 1:]
            current_path = current_path[0:current_path.rfind(NEXT_DIR)]
            if current_path == HOMEDRIVE:
                current_path = f'{HOMEDRIVE}\\'
                
            files = get_files(console, current_path)
            os.chdir(current_path) # changing working directory to current one

            console.updateList(files)

            if prev_dir in files:
                console.updatePos(files.index(prev_dir))

            continue
        
        # go directly to directory
        if command == key.CTRL_G:
            saved_string = [""] # using a vector for pass-by-reference
            new_path = console.separateInteraction(function=lambda: autocomplete(update_goto_autocomplete("", saved_string), updateAutocomplete=lambda string: update_goto_autocomplete(string, saved_string), prompt=colored("Go to directory: ", "yellow"), exitOnEsc=True), showCursor=True)
            if not new_path or new_path.isspace():
                continue
            
            if new_path in goto_autocomplete:
                new_path = goto_autocomplete[new_path]
            else:
                new_path = new_path.replace('/', NEXT_DIR)
            
            if os.path.isdir(new_path):
                os.chdir(new_path)

                # resolving relative path
                # might as well do this even if the path is actually absolute
                new_path = os.getcwd()

                # adding path to autocomplete if it's new
                autocomplete_name = new_path[new_path.rfind(NEXT_DIR) + 1:]
                if autocomplete_name not in goto_autocomplete:
                    goto_autocomplete[autocomplete_name] = new_path
                    with open(GOTOFILE, 'w', encoding='utf-8') as file:
                        json.dump(goto_autocomplete, file)

                current_path = new_path
                    
                files = get_files(console, current_path)
                        
                console.updateList(files)
                console.updatePos(0)

            else:
                # removing path from autocomplete file if it does not exist anymore
                autocomplete_name = new_path[new_path.rfind(NEXT_DIR) + 1:]
                if autocomplete_name in goto_autocomplete:
                    del goto_autocomplete[autocomplete_name]
                    with open(GOTOFILE, 'w', encoding='utf-8') as file:
                        json.dump(goto_autocomplete, file)
                    console.separateInteraction(message=colored("Directory path has changed or directory has been deleted.\n", "yellow"))
                else:
                    console.separateInteraction(message=colored("Directory not found.\n", "yellow"))


        # print current directory tree        
        if command == key.CTRL_T:
            try:
                console.separateInteraction(function=lambda: print_tree(current_path), startAtTop=True)

            except Exception as e:
                e = str(e)

                if "WinError" in e:
                    e = e[e.find("]")+2:e.find(":")]
                    
                if e[-1] != '.':
                    e += '.'

                else:
                    e = colored("Directory tree too large to display.", "yellow")

                console.separateInteraction(message=f'\n{e}\n')

            if current_path == '{HOMEDRIVE}\\':
                os.system(f'title Local Disk ({HOMEDRIVE}) - Explore')
                    
            else:  
                os.system(f'title {current_path[current_path.rfind(NEXT_DIR) + 1:]} - Explore')

            continue

        # print path to selected file and copy it to clipboard
        if command == key.CTRL_P:
            file = files[curr_pos] 
            console.separateInteraction(message=f'{colored("Path to selected directory/file copied to clipboard:", "yellow")}\n{colored((current_path + NEXT_DIR + file).replace(NEXT_DIR, "/"), "light_yellow")}\n')
            pyperclip.copy((current_path + NEXT_DIR + file).replace(NEXT_DIR, "/"))
            continue

        # print path to current directory and copy it to clipboard
        if command == key.CTRL_D:
            console.separateInteraction(message=f'{colored("Path to current directory copied to clipboard:", "yellow")}\n{colored(current_path.replace(NEXT_DIR, "/"), "light_yellow")}\n')
            pyperclip.copy(current_path.replace(NEXT_DIR, "/"))
            continue 


        # open in file explorer
        if command == key.TAB:
            os.startfile(current_path) 
            continue

        # open in powershell
        if command == '`':
            # only open powershell if windows
            if os.name == 'nt':
                os.startfile("powershell.exe") # open powershell in Windows
            continue

        # open additional Dir-Explorer in current directory
        if command == "~":
            os.system(f'start cmd /c python3 "{HOMEPATH}{NEXT_DIR}dir_explorer.py"')
            continue


        # creating directory/file
        if command == key.CTRL_N:
            filename = console.separateInteraction(function=lambda: input(f'{colored("Type name for new directory/file:", "yellow")}\n'), showCursor=True)

            if filename and not filename.isspace():
                try:
                    # if there is a '.' in filename, it creates a file (if the extension is blank, Windows removes the dot by default)
                    if '.' in filename[1:]: # [1:] for hidden folders
                        open(f'{current_path}{NEXT_DIR}{filename}', "a") # !!! append is very important, because otherwise it can overwrite existing file!!!
                    
                        if filename[-1] == '.':
                            filename = filename[:-1]

                    # no '.' in filename, therefore it creates a directory
                    else:
                        os.mkdir(f'{current_path}{NEXT_DIR}{filename}')

                    files = get_files(console, current_path)
                    console.updateList(files)

                    new_position = files.index(filename)
                    console.updatePos(new_position)
                    

                except Exception as e:
                    e = str(e)

                    if "WinError" in e:
                        e = e[e.find("]")+2:e.find(":")]
                        
                    if e[-1] != '.':
                        e += '.'

                    console.separateInteraction(message=f'\n{e}\n')

            continue

        # rename directory/file
        if command == key.CTRL_R:
            file = files[curr_pos]
            color = get_file_color(file, current_path, use_light_yellow=True)
            
            filename = console.separateInteraction(function=lambda: autocomplete([file], prompt=f"{colored('Rename', 'yellow')} {colored(file, color)} {colored('to:', 'yellow')}\n", exitOnEsc=True), showCursor=True)

            if filename and not filename.isspace():
                try:
                    if '.' in file[1:] and '.' not in filename[1:]:
                        filename = filename + file[file.rfind('.'):]
                    os.rename(f'{current_path}{NEXT_DIR}{file}', f'{current_path}{NEXT_DIR}{filename}')

                    files = get_files(console, current_path)
                    console.updateList(files)

                    if filename[-1] == '.':
                        filename = filename[:-1]
                    
                    new_position = files.index(filename)
                    console.updatePos(new_position)
                
                except Exception as e:
                    e = str(e)

                    if "WinError" in e:
                        e = e[e.find("]")+2:e.find(":")]
                        
                    if e[-1] != '.':
                        e += '.'

                    console.separateInteraction(message=f'\n{e}\n')

            continue

        # set/unset directory/file to be copied
        if command == key.CTRL_C:
            filepath = current_path + NEXT_DIR + files[curr_pos]
            
            if filepath in console.copy:
                console.copy.remove(filepath)

            else:
                if filepath in console.move:
                    console.move.remove(filepath)

                console.copy += [filepath]
                            
            set_top_text(console, current_path)

            continue

        # set/unset directory/file to be moved
        if command == key.CTRL_X:
            filepath = current_path + NEXT_DIR + files[curr_pos]
            
            if filepath in console.move:
                console.move.remove(filepath)

            else:
                if filepath in console.copy:
                    console.copy.remove(filepath)

                console.move += [filepath]

            set_top_text(console, current_path)

            continue

        # copying and moving directories and files
        if command == key.INSERT:
            for copy in console.copy:
                try:
                    if os.path.isdir(copy):
                        shutil.copytree(copy, current_path + NEXT_DIR + copy[copy.rfind(NEXT_DIR) + 1:], dirs_exist_ok=True)
                    else:
                        shutil.copy(copy, current_path)

                except Exception as e:
                    e = str(e)
                
                    if "WinError" in e:
                        e = e[e.find("]")+2:e.find(":")]
                                    
                    if e[-1] != '.':
                        e += '.'
                
                    console.separateInteraction(message=f'{colored("For", "yellow")} {get_copy_move_name(copy)}{colored(":", "yellow")}\n{e}\n')

            for move in console.move:
                try:
                    shutil.move(move, current_path)

                except Exception as e:
                    e = str(e)
                
                    if "WinError" in e:
                        e = e[e.find("]")+2:e.find(":")]
                                    
                    if e[-1] != '.':
                        e += '.'
                
                    console.separateInteraction(message=f'{colored("For", "yellow")} {get_copy_move_name(move)}{colored(":", "yellow")}\n{e}\n')

            changed = console.copy or console.move

            console.copy = []
            console.move = []

            if changed:
                files = get_files(console, current_path)
                console.updateList(files)

            continue

        # clear all directories and files set to be copied and to be moved
        if command == key.CTRL_Z:
            changed = console.copy or console.move

            console.copy = []
            console.move = []

            if changed:
                set_top_text(console, current_path)

            continue

        # move directory/file to recycle bin
        if command == key.DELETE:
            try:
                file = files[curr_pos]
                send2trash(current_path + NEXT_DIR + file)

                files = get_files(console, current_path)
                console.updateList(files)

                curr_pos -= 1

                if curr_pos == -1:
                    curr_pos = 0

                console.updatePos(curr_pos)

            except Exception as e:
                e = str(e)

                if "WinError" in e:
                    e = e[e.find("]")+2:e.find(":")]
                    
                if e[-1] != '.':
                    e += '.'

                if "0x80270027" in e:
                    e = colored("Directory is open in another application.\nClose the other application to be able to send to Recycle Bin.", "yellow")

                console.separateInteraction(message=f'\n{e}\n')

            continue

        # open recycle bin in windows file explorer
        if command == key.CTRL_B:
            # only try to open if windows
            if os.name=='nt':
                subprocess.run("explorer shell:RecycleBinFolder")

            continue

            
        # update current directory (when it was changed outside the app)
        if command == key.CTRL_U:
            files = get_files(console, current_path)
            console.updateList(files)
            continue

        if command == '?':
            console.separateInteraction(function= lambda: MenuInterface.helpMenu(yaml.safe_load(open(f"{DATAPATH}/help_menu.yaml")), 'light_yellow', 'yellow'))

        # quit application
        if command == key.ESC:
            console.exitInterface()
            quit()
            

def main():
    if (len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]):
        print("\nConsole application for easier movement through directories.")
        print("\nUsage: 'python3 dir_explorer [relative_path | absolute_path | saved_directory]'\n")
        print("Dir-Explorer will be open in directory given as path.")
        print("If a directory was previously opened in Dir-Explorer by path, the path given can be simply its name.")
        print("If the path is not given, or it does not lead to a directory, Dir-Explorer will open in the current directory.\n")

    else:
        current_path = " ".join(sys.argv[1:])
        explore_loop(current_path)

if __name__ == '__main__':
    main()