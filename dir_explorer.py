import sys
import os

HOMEPATH = os.path.dirname(os.path.realpath(__file__))

if ".paths" not in os.listdir(HOMEPATH):
    console_path = input("Please type path to directory of ConsoleListInterface.py (or leave empty to cancel):\n")
    if console_path[0] == '"':
        console_path = console_path[1:]
    if console_path[-1] == '"':
        console_path = console_path[:-1]
    
    while console_path and not console_path.isspace() and not os.path.exists(f'{console_path}/ConsoleListInterface.py'):
        console_path = input("\nConsoleListInterface.py not found, please download and type path to directory:\n") 
    
    if not console_path or console_path.isspace():
        quit()

    open(f'{HOMEPATH}/.paths', 'w').write(console_path)

sys.path.append(open(f'{HOMEPATH}/.paths').read())

from ConsoleListInterface import ConsoleListInterface, waitForEnter # pyright: ignore[reportMissingImports]
from send2trash import send2trash
from termcolor import colored
from filetype import is_image
from readchar import key
import subprocess
import pyperclip
import sys

sys.stderr = open(f'{HOMEPATH}/errors.txt', "a")

NEXT_DIR  = '\\' # preferable for certain functionalities (rather than '/')
HOMEDRIVE = os.environ["HOMEDRIVE"] 


COMMAND_LIST = [key.ENTER, key.CTRL_O, key.BACKSPACE, key.CTRL_T, key.CTRL_P, key.TAB, '`', '~', 
                key.CTRL_N, key.CTRL_R, key.DELETE, key.CTRL_B, key.CTRL_U, key.ESC]
HELP_PAGE    = """
Console application for easier movement through directories.

Controls:
    - arrow keys -> moving between files in the current directory.
    - character  -> move cursor to the next directory / file that starts with character, if it exists.
    - ctrl+f     -> search for the next directory / file that contains string, if it exists (not case sensitive).
    - '\\'        -> find next directory / file that contains last searched string.
    - enter      -> for directory: switch to the selected directory;
                 -> for file: open file in default program (or program selector if none).
    - ctrl+o     -> open images in paint, python files in vs code, others in notepad.
    - backspace  -> return to parent directory of current directory.
    - ctrl+t     -> print the tree of the current directory.
    - ctrl+p     -> print the path of the current directory (and save it to clipboard).
    - tab        -> open current directory in file explorer.
    - '`'        -> open current directory in powershell.
    - '~'        -> open current directory in another dir-explorer.
    - ctrl+n     -> create new directory or file:
                    - for file w/  extension: "{filename}.{extension}";
                    - for file w/o extension: "{filename}.";
                    - for directory:          "{filename}".
    - ctrl+r     -> rename selected directory / file (if removing extension, do "{filename}.").
    - delete     -> move directory / file to recycle bin.
    - ctrl+b     -> open recycle bin in Windows File Explorer.
    - ctrl+u     -> update list (if directory was changed outside this app or terminal window was resized).
    - '='/'-'    -> increase/decrease number of characters in file and directory names before they are cut off.
    - '?'        -> display current help page.
    - escape     -> quit application.
""" 


def get_files(current_path):
    files  = [dir for dir in os.listdir(current_path) if os.path.isdir(current_path + NEXT_DIR + dir)]       # putting directories first 
    files += [file for file in os.listdir(current_path) if not os.path.isdir(current_path + NEXT_DIR + file) # then files
                                                           and file[file.find('.') + 1:] != "ini"]           # that aren't the .ini Windows file for dirs
    
    if current_path == f'{HOMEDRIVE}\\':
        os.system(f'title Local Disk ({HOMEDRIVE}) - Explore')
            
    else:  
        os.system(f'title {current_path[current_path.rfind(NEXT_DIR) + 1:]} - Explore')

    return files


def print_filename(filename, max_name_width, current_path):
    name = filename
    if max_name_width <= len(name):
        if not os.path.isdir(current_path + NEXT_DIR + filename):
            # if name.rfind('.') != 0 for hidden files
            extension = name[name.rfind('.'):] if name.rfind('.') != 0 else ""
        else: 
            extension = ''
        name = name[0:max(max_name_width - 1 - len(extension), 0)] + '-' + extension 

    # return current_path[current_path.rfind('\\') + 1:]# + ' ' + name

    if os.path.isdir(current_path + NEXT_DIR + filename):
        return colored(name, 'yellow')
    else:
        return name


def print_tree(current_path):
    if current_path == f'{HOMEDRIVE}\\':
        os.system(f'title Local Disk ({HOMEDRIVE}) - Tree')
            
    else:  
        os.system(f'title {current_path[current_path.rfind(NEXT_DIR) + 1:]} - Tree')

    tree = subprocess.run(f'tree "{current_path}" /F', capture_output=True, universal_newlines=True, shell=True).stdout

    if tree.count('\n') > 9000:
        raise Exception("Directory tree too large to display")

    
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

    print(current_path[current_path.rfind(NEXT_DIR) + 1:])
    print(tree, end='')

    print("Press enter to continue.")
    waitForEnter()


def explore_loop(current_path="."):
    # removing quotes from path, they just get in the way
    current_path = current_path.replace('\"', '')
    current_path = current_path.replace('\'', '')
    
    # in case given path ends with '/' or '\', the os.chdir fucks up
    if current_path and (current_path[-1] == NEXT_DIR or current_path[-1] == '/'):
        current_path = current_path[:-1]

    # ignoring given current path if it is not directory
    if not current_path or not os.path.isdir(current_path):
        current_path = os.getcwd()

    # resolving relative path
    if current_path[0] == '.':
        os.chdir(current_path)
        current_path = os.getcwd()

    # current_path = "C:\\Users\\Mihnea"

    files = get_files(current_path)

    console = ConsoleListInterface(items=files, specialCommands=COMMAND_LIST, helpPage=HELP_PAGE, printFunc=lambda filename, max_name_width: print_filename(filename, max_name_width, current_path))

    while (True):
        command, curr_pos = console.interact()

        # go to selected directory / open file in default app (or "select app" prompt)
        if command == key.ENTER:
            changed_directory = False

            try:
                file = files[curr_pos]
                if os.path.isdir(current_path + NEXT_DIR + file):
                    current_path += NEXT_DIR + file if current_path != f'{HOMEDRIVE}\\' else file
                    changed_directory = True
                    
                    files = get_files(current_path)
                    os.chdir(current_path) # changing working directory to current one
                    
                    console.updateList(files)
                    console.updatePos(0)

                else: 

                    if '.' not in file[1:]:
                        # file has no extension, ignoring the '.' from hidden files
                        subprocess.run(f'start notepad {current_path + NEXT_DIR + file}', capture_output=False, shell=True)
                    elif file[file.rfind('.'):] == ".py":
                        os.system(f'start cmd /C python3 "{current_path + NEXT_DIR + file}"') # /C runs file and quits once done
                    elif file[file.rfind('.'):] == ".exe":
                        # os.startfile(current_path + NEXT_DIR + file) # doing it this way for .exe's
                        os.system(f'start "New Window" "{current_path + NEXT_DIR + file}"')
                        # subprocess.Popen(f'"{current_path + NEXT_DIR + file}"', stdout=None)
                    else:
                        subprocess.run(f'explorer {current_path + NEXT_DIR + file}', capture_output=False, shell=True)


            except Exception as e:
                if changed_directory:
                    current_path = current_path[0:current_path.rfind(NEXT_DIR)]

                e = str(e)

                if "WinError" in e:
                    e = e[e.find("]")+2:e.find(":")]

                console.separateInteraction(message=f'\n{e}.\n')

            continue
                    

        # open images in paint and other files in notepad
        if command == key.CTRL_O:
            file = files[curr_pos]
            if os.path.isdir(current_path + NEXT_DIR + file):
                
                console.separateInteraction(message=f'\nThis is a directory.\n')

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

                console.separateInteraction(message=f'\n{e}.\n')

            continue

        # go to parent directory
        if command == key.BACKSPACE:
            prev_dir = current_path[current_path.rfind(NEXT_DIR) + 1:]
            current_path = current_path[0:current_path.rfind(NEXT_DIR)]
            if current_path == HOMEDRIVE:
                current_path = f'{HOMEDRIVE}\\'
                
            files = get_files(current_path)
            os.chdir(current_path) # changing working directory to current one

            console.updateList(files)

            if prev_dir in files:
                console.updatePos(files.index(prev_dir))

            continue
            

        # print current directory tree        
        if command == key.CTRL_T:
            try:
                console.separateInteraction(function=lambda: print_tree(current_path), startAtTop=True)

            except Exception as e:
                e = str(e)

                if "WinError" in e:
                    e = e[e.find("]")+2:e.find(":")]

                else:
                    e = "Directory tree too large to display"

                console.separateInteraction(message=f'\n{e}.\n')

            if current_path == '{HOMEDRIVE}\\':
                os.system(f'title Local Disk ({HOMEDRIVE}) - Explore')
                    
            else:  
                os.system(f'title {current_path[current_path.rfind(NEXT_DIR) + 1:]} - Explore')

            continue
        

        # open in file explorer
        if command == key.TAB:
            os.startfile(current_path) # open the C:\Windows directory
            continue

        # open in powershell
        if command == '`':
            os.startfile("powershell.exe") # open powershell in Windows
            continue

        # open additional Dir-Explorer in current directory
        if command == "~":
            os.startfile("explore")
            continue


        # creating directory/file
        if command == key.CTRL_N:
            
            filename = console.separateInteraction(function=lambda: input("Type name for new directory/file:\n"), showCursor=True)

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

                    files = get_files(current_path)
                    console.updateList(files)

                    new_position = files.index(filename)
                    console.updatePos(new_position)
                    

                except Exception as e:
                    e = str(e)

                    if "WinError" in e:
                        e = e[e.find("]")+2:e.find(":")]

                    console.separateInteraction(message=f'\n{e}.\n')

            continue

        # rename directory/file
        if command == key.CTRL_R:
            file = files[curr_pos]
            filename = console.separateInteraction(function=lambda: input(f"Rename '{file}' to:\n"), showCursor=True)

            if filename and not filename.isspace():
                try:
                    if '.' in file[1:] and '.' not in filename[1:]:
                        filename = filename + file[file.rfind('.'):]
                    os.rename(f'{current_path}{NEXT_DIR}{file}', f'{current_path}{NEXT_DIR}{filename}')

                    files = get_files(current_path)
                    console.updateList(files)

                    if filename[-1] == '.':
                        filename = filename[:-1]
                    
                    new_position = files.index(filename)
                    console.updatePos(new_position)
                
                except Exception as e:
                    e = str(e)

                    if "WinError" in e:
                        e = e[e.find("]")+2:e.find(":")]

                    console.separateInteraction(message=f'\n{e}.\n')

            continue

        # move directory/file to recycle bin
        if command == key.DELETE:
            try:
                file = files[curr_pos]
                send2trash(current_path + NEXT_DIR + file)

                files = get_files(current_path)
                console.updateList(files)

                curr_pos -= 1

                if curr_pos == -1:
                    curr_pos = 0

                console.updatePos(curr_pos)

            except Exception as e:
                e = str(e)

                if "WinError" in e:
                    e = e[e.find("]")+2:e.find(":")]

                console.separateInteraction(message=f'\n{e}.\n')

            continue

        # open recycle bin in windows file explorer
        if command == key.CTRL_B:
            subprocess.run("explorer shell:RecycleBinFolder")
            continue

            
        # update current directory (when it was changed outside the app)
        if command == key.CTRL_U:
            files = get_files(current_path)
            console.updateList(files)
            continue

        # quit application
        if command == key.ESC:
            console.exitInterface()
            quit()


        # debugging current path
        if command == key.CTRL_P:
            console.separateInteraction(message=f'Current path copied to clipboard:\n{current_path}\n')
            pyperclip.copy(current_path)
            


def main():
    if (len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]):
        print("\nConsole application for easier movement through directories.")
        print("\nUsage: 'explore [rel_path | abs_path]'\n")
        print("Dir-Explorer will be open in directory given as path.")
        print("Or it will open in current directory if no path is given or if path does not lead to a directory.\n")

    else:
        current_path = " ".join(sys.argv[1:])
        explore_loop(current_path)

if __name__ == '__main__':
    main()
