from send2trash import send2trash
from readchar import readkey, key
from math import ceil as roundup
from termcolor import colored
from filetype import is_image
import subprocess
import cursor
import sys
import os

sys.stderr = open(f'C:/Users/Mihnea/Desktop/Random thoughts/Cool stuff/dir_explorer/errors.txt', "a")

TERM_WIDTH       = os.get_terminal_size()[0] # 120 characters per terminal line
FILES_PER_COLUMN = os.get_terminal_size()[1] - 2
INFO_POS         = FILES_PER_COLUMN / 2 - 4

SPACE_BEFORE    = 4   # ( -> ) / (    )
MAX_NAME_WIDTH  = 36  # (max allocated space for filenames)

MAX_COLUMNS = int(TERM_WIDTH / (SPACE_BEFORE + MAX_NAME_WIDTH))

NEXT_DIR = '\\'
cls = lambda: os.system('cls' if os.name=='nt' else 'clear')

DESKTOP_PATH = "C:\\Users\\Mihnea\\Desktop"


COMMAND_LIST = [key.UP, key.DOWN, key.LEFT, key.RIGHT, key.CTRL_F, '\\', key.ENTER, key.CTRL_O, key.BACKSPACE, 
                key.TAB, '`', '~', key.CTRL_N, key.CTRL_R, key.DELETE, key.CTRL_B, key.CTRL_U, '?', '=', '-', key.ESC]
HELP_PAGE    = """
Console application for easier movement through directories.

Controls:
    - arrow keys -> moving between files in the current directory.
    - character  -> moves cursor to the next directory / file that starts with character, if it exists.
    - ctrl+f     -> search for the next directory / file that contains string, if it exists (not case sensitive).
    - '\\'        -> find next directory / file that contains last searched string.
    - enter      -> for directory: switches to the selected directory;
                 -> for file: opens file in default program (or program selector if none).
    - ctrl+o     -> open selected file in paint if it is an image, otherwise notepad.
    - backspace  -> returns to parent directory of current directory.
    - tab        -> opens current directory in file explorer.
    - '`'        -> opens current directory in powershell.
    - '~'        -> opens current directory in another dir-explorer.
    - ctrl+n     -> creates new directory or file:
                    - for file w/  extension: "{filename}.{extension}";
                    - for file w/o extension: "{filename}.";
                    - for directory:          "{filename}".
    - ctrl+r     -> renames selected directory / file.
    - delete     -> move directory / file to recycle bin.
    - ctrl+b     -> open recycle bin in Windows File Explorer.
    - ctrl+u     -> update list (if directory was changed outside this app or terminal window was resized).
    - '='/'-'    -> increases/decreases number of characters in file and directory names before they are cut off.
    - '?'        -> displays current help page.
    - escape     -> quits application.
""" 


def move_cursor(y, x):
    sys.stdout.write("\033[%d;%dH" % (y, x))


def print_filenames(current_path, files):
    global TERM_WIDTH
    global FILES_PER_COLUMN
    global INFO_POS
    global MAX_COLUMNS

    TERM_WIDTH       = os.get_terminal_size()[0] # 120 characters per terminal line
    FILES_PER_COLUMN = os.get_terminal_size()[1] - 2
    INFO_POS         = FILES_PER_COLUMN / 2 - 4
    MAX_COLUMNS = int(TERM_WIDTH / (SPACE_BEFORE + MAX_NAME_WIDTH))

    cls()
    column = 1
    line   = 1

    for file in files:
        # move_cursor(counter % FILES_PER_COLUMN + 1, int(counter / FILES_PER_COLUMN) * (2 + SPACE_BEFORE + MAX_NAME_WIDTH))
        if MAX_COLUMNS < column:
            break
       
        move_cursor(line, (column - 1) * (SPACE_BEFORE + MAX_NAME_WIDTH) + (column != 1))

        name = file
        if MAX_NAME_WIDTH < len(name):
            if not os.path.isdir(current_path + NEXT_DIR + file):
                # if name.rfind('.') != 0 for hidden files
                extension = name[name.rfind('.'):] if name.rfind('.') != 0 else ""
            else: 
                extension = ''
            name = name[0:max(MAX_NAME_WIDTH - 1 - len(extension), 0)] + '-' + extension 

        # if column != 1:
            # print(' ', end='')

        print("    ", end='')
        # print(f'{column} {line}', end='')
        # print(f'{files.index(file)}', end='')

        if os.path.isdir(current_path + NEXT_DIR + file):
            print(colored(name, 'yellow'))
        else:
            print(name)
        
        line += 1
        if line > FILES_PER_COLUMN:
            line    = 1
            column += 1
    
    move_cursor(FILES_PER_COLUMN + 2, 0)
    print("Type '?' for help page.", end='')


def get_files(current_path):
    if current_path == "C:\\":
        os.system("title Local Disk (C:) - Explore")
            
    else:  
        os.system(f'title {current_path[current_path.rfind(NEXT_DIR) + 1:]} - Explore')

    files  = [dir for dir in os.listdir(current_path) if os.path.isdir(current_path + NEXT_DIR + dir)]       # putting directories first 
    files += [file for file in os.listdir(current_path) if not os.path.isdir(current_path + NEXT_DIR + file) # then files
                                                           and file[file.find('.') + 1:] != "ini"]           # that aren't the .ini Windows file for dirs

    total_columns     = roundup(len(files) / FILES_PER_COLUMN)
    lines_last_column = len(files) % FILES_PER_COLUMN

    if lines_last_column == 0:
        lines_last_column = FILES_PER_COLUMN
                    
    if not files:
        total_columns = 1
        lines_last_column = 1

    return files, total_columns, lines_last_column


def main_loop():
    current_path = os.getcwd()

    if "Desktop" not in current_path:
        current_path = DESKTOP_PATH

    cursor.hide()

    files, total_columns, lines_last_column = get_files(current_path)

    column = 1
    line   = 1

    leftwise_column = 1

    print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])

    # saving it outside the while, for repeated searches
    search_str = '\\'
    
    global MAX_NAME_WIDTH
    global MAX_COLUMNS

    while (True):
        move_cursor(line, (column - leftwise_column) * (SPACE_BEFORE + MAX_NAME_WIDTH) + (column != 1))
        print(" -> ")
        # print(column, end='')
        # print(line)
        # print((column - 1) * FILES_PER_COLUMN + line - 1)
        move_cursor(line, (column - leftwise_column) * (SPACE_BEFORE + MAX_NAME_WIDTH) + (column != 1))

        command = readkey()
        

        # arrowkeys for moving within directory
        if command == key.UP:
            print("   ")

            line -= 1
            if line < 1:
                line = FILES_PER_COLUMN

        if command == key.DOWN:
            print("   ")

            line += 1
            if FILES_PER_COLUMN < line or (column == total_columns and lines_last_column < line):
                line = 1
            
        if command == key.LEFT:
            print("   ")

            column -= 1

            if column < leftwise_column and 1 <= column:
                leftwise_column -= 1
                print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])

            if column < 1:
                column = total_columns
                if MAX_COLUMNS < total_columns:
                    leftwise_column = total_columns - MAX_COLUMNS + 1
                    print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])
            
        if command == key.RIGHT:
            print("   ")

            column += 1

            if total_columns < column:
                column = 1
                if 1 < leftwise_column:
                    leftwise_column = 1
                    print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])

            if MAX_COLUMNS <= (column - leftwise_column):
                leftwise_column += 1
                print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])

        # searching by first character in filename
        if command not in COMMAND_LIST:
            first_letter = command.lower()
            current_position = (column - 1) * FILES_PER_COLUMN + line - 1
            new_position = next((i for i in range(len(files)) if files[i][0].lower() == first_letter and i > current_position), 
                            next((i for i in range(len(files)) if files[i][0].lower() == first_letter), current_position))


            if new_position != current_position:
                print("   ")

                column = int((new_position) / FILES_PER_COLUMN) + 1
                line   = (new_position) % FILES_PER_COLUMN + 1

                if column < leftwise_column:
                    leftwise_column = column
                    print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])

                if MAX_COLUMNS <= (column - leftwise_column):
                    leftwise_column = column
                    print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])

        # searching by string in filename
        if command in [key.CTRL_F, '\\']:
            reprint = False
            if command == key.CTRL_F:
                cls()
                move_cursor(INFO_POS, 0)
                cursor.show()
                search_str = input("String to search by:\n").lower()
                cursor.hide()
                cls()
                reprint = True

            if search_str and not search_str.isspace():
                current_position = (column - 1) * FILES_PER_COLUMN + line - 1
                new_position = next((i for i in range(len(files)) if search_str in files[i].lower() and i > current_position), 
                                next((i for i in range(len(files)) if search_str in files[i].lower()), current_position))

                if new_position != current_position:
                    print("   ")

                    column = int((new_position) / FILES_PER_COLUMN) + 1
                    line   = (new_position) % FILES_PER_COLUMN + 1

                    if column < leftwise_column:
                        leftwise_column = column
                        reprint = True

                    if MAX_COLUMNS <= (column - leftwise_column):
                        leftwise_column = column
                        reprint = True
            
            else:
                reprint = True
                
            if reprint:
                print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])


        # went left to the last column from lower 
        if column == total_columns and lines_last_column < line:
            line = lines_last_column


        # go to selected directory / open file in default app (or "select app" prompt)
        if command == key.ENTER:
            changed_directory = False

            try:
                file = files[(column - 1) * FILES_PER_COLUMN + line - 1]
                if os.path.isdir(current_path + NEXT_DIR + file):
                    current_path += NEXT_DIR + file
                    changed_directory = True
                    
                    files, total_columns, lines_last_column = get_files(current_path)
                    
                    column = 1
                    line   = 1

                    leftwise_column = 1
                    
                    print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])

                else: 
                    subprocess.run(f'explorer {current_path + NEXT_DIR + file}', capture_output=False, shell=True)
                    # os.startfile(current_path + NEXT_DIR + file)

            except Exception as e:
                e = str(e)
                cls()
                move_cursor(INFO_POS, 0)
                input(f'\n{e[e.find("]")+2:e.find(":")]}.\nPress enter to continue.\n')
                if changed_directory:
                    current_path = current_path[0:current_path.rfind(NEXT_DIR)]

                print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])
        
        # open images in paint and other files in notepad
        if command == key.CTRL_O:
            file = files[(column - 1) * FILES_PER_COLUMN + line - 1]
            if os.path.isdir(current_path + NEXT_DIR + file):
                cls()
                move_cursor(INFO_POS, 0)
                input(f'\nThis is a directory.\nPress enter to continue.\n')

                print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])

                continue

            try:
                if is_image(current_path + NEXT_DIR + file):
                    # if image, open in paint
                    # interestingly, only paint needs "" in filepath if there are spaces
                    subprocess.run(f'start mspaint "{current_path + NEXT_DIR + file}"', capture_output=False, shell=True)
                else:
                    # else, open in notepad
                    subprocess.run(f'start notepad {current_path + NEXT_DIR + file}', capture_output=False, shell=True)

            except Exception as e:
                e = str(e)
                cls()
                move_cursor(INFO_POS, 0)
                input(f'\n{e[e.find("]")+2:e.find(":")]}.\nPress enter to continue.\n')

                print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])

        # go to parent directory
        if command == key.BACKSPACE:
            prev_dir = current_path[current_path.rfind(NEXT_DIR) + 1:]
            current_path = current_path[0:current_path.rfind(NEXT_DIR)]
            if current_path == "C:":
                current_path = "C:\\"
                
            files, total_columns, lines_last_column = get_files(current_path)

            if prev_dir in files:
                column = int(files.index(prev_dir) / FILES_PER_COLUMN) + 1
                line   = files.index(prev_dir) % FILES_PER_COLUMN + 1

                leftwise_column = 1 if column <= MAX_COLUMNS else (column - MAX_COLUMNS + 1)
            
            print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])


        # open in file explorer
        if command == key.TAB:
            os.startfile(current_path) # open the C:\Windows directory

        # open in powershell
        if command == '`':
            # cwd = os.getcwd()
            os.chdir(current_path)
            os.startfile("powershell.exe") # open powershell in Windows
            # os.chdir(cwd)

        # open additional Dir-Explorer in current directory
        if command == "~":
            os.chdir(current_path)
            os.startfile("explore")


        # creating directory/file
        if command == key.CTRL_N:
            cls()
            move_cursor(INFO_POS, 0)
            cursor.show()
            filename = input("Type name for new directory/file:\n")
            cursor.hide()
            if filename and not filename.isspace():
                try:
                    # if there is a '.' in filename, it creates a file (if the extension is blank, Windows removes the dot by default)
                    if '.' in filename:
                        open(f'{current_path}{NEXT_DIR}{filename}', "a") # !!! append is very important, because otherwise it can overwrite existing file!!!
                    
                    # no '.' in filename, therefore it creates a directory
                    else:
                        os.mkdir(f'{current_path}{NEXT_DIR}{filename}')

                    files, total_columns, lines_last_column = get_files(current_path)

                    new_position = files.index(filename)
                    column = int((new_position) / FILES_PER_COLUMN) + 1
                    line   = (new_position) % FILES_PER_COLUMN + 1
                    
                    leftwise_column = 1 if column <= MAX_COLUMNS else (column - MAX_COLUMNS + 1)

                except Exception as e:
                    e = str(e)
                    input(f'\n{e[e.find("]")+2:e.find(":")]}.\nPress enter to continue.\n')
            
            print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])

        # rename directory/file
        if command == key.CTRL_R:
            cls()
            file = files[(column - 1) * FILES_PER_COLUMN + line - 1]
            move_cursor(INFO_POS, 0)
            cursor.show()
            filename = input(f'Rename {file} to:\n')
            cursor.hide()

            if filename and not filename.isspace():
                try:
                    os.rename(f'{current_path}{NEXT_DIR}{file}', f'{current_path}{NEXT_DIR}{filename}')
                    files, total_columns, lines_last_column = get_files(current_path)
                    
                    new_position = files.index(filename)
                    column = int((new_position) / FILES_PER_COLUMN) + 1
                    line   = (new_position) % FILES_PER_COLUMN + 1
                    
                    leftwise_column = 1 if column <= MAX_COLUMNS else (column - MAX_COLUMNS + 1)
                
                except Exception as e:
                    e = str(e)
                    input(f'\n{e[e.find("]")+2:e.find(":")]}.\nPress enter to continue.\n')
            
            print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])

        # move directory/file to recycle bin
        if command == key.DELETE:
            try:
                file = files[(column - 1) * FILES_PER_COLUMN + line - 1]
                send2trash(current_path + NEXT_DIR + file)

                files, total_columns, lines_last_column = get_files(current_path)

                current_position  = (column - 1) * FILES_PER_COLUMN + line - 1
                current_position -= 1

                if current_position == -1:
                    current_position = 0
                
                column = int((current_position) / FILES_PER_COLUMN) + 1
                line   = (current_position) % FILES_PER_COLUMN + 1
                if column < leftwise_column:
                    leftwise_column = column


            except Exception as e:
                e = str(e)
                cls()
                move_cursor(INFO_POS, 0)
                input(f'\n{e[e.find("]")+2:e.find(":")]}.\nPress enter to continue.\n')

            print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])

        # open recycle bin in windows file explorer
        if command == key.CTRL_B:
            subprocess.run("explorer shell:RecycleBinFolder")

            
        # update current directory (when it was changed outside the app)
        if command == key.CTRL_U:
            files, total_columns, lines_last_column = get_files(current_path)

            print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])


        # making filenames longer
        if command == "=" and 1 < MAX_COLUMNS:
            # changing the width of filenames to maximum possible if we have one less column
            MAX_NAME_WIDTH = int(TERM_WIDTH / (MAX_COLUMNS - 1)) - SPACE_BEFORE
            # MAX_NAME_WIDTH += 1 # increasing size of filenames
            MAX_COLUMNS = int(TERM_WIDTH / (SPACE_BEFORE + MAX_NAME_WIDTH))
            print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])
            if (column - leftwise_column) >= MAX_COLUMNS:
                column -= 1

        # making filenames shorter
        if command == "-" and 8 < MAX_NAME_WIDTH:
            # changing the width of filenames to leave space for an additional column
            MAX_NAME_WIDTH = int(TERM_WIDTH / (MAX_COLUMNS + 1)) - SPACE_BEFORE
            MAX_COLUMNS = int(TERM_WIDTH / (SPACE_BEFORE + MAX_NAME_WIDTH))
            print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])


        # help page
        if command == '?':
            cls()
            move_cursor(0, 0)
            print(HELP_PAGE)
            input("Press enter to continue.\n")
            print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])


        # quit application
        if command == key.ESC:
            move_cursor(0, 0)
            cls()
            break


def main():
    if (len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]):
        print(HELP_PAGE)

    else:
        main_loop()

if __name__ == '__main__':
    main()
