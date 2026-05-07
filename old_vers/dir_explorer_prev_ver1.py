from readchar import readkey, key
from math import ceil as roundup
from termcolor import colored
from functools import reduce
import subprocess
import platform
import cursor
import sys
import os

sys.stderr = open(f'C:/Users/Mihnea/Desktop/Random thoughts/Cool stuff/dir_explorer/errors.txt', "a")

TERM_WIDTH       = 120 # 120 characters per terminal line
FILES_PER_COLUMN = 29

SPACE_BEFORE    = 4   # ( -> ) / (    )
MAX_NAME_WIDTH  = 36  # (max allocated space for filenames)

MAX_COLUMNS = int(TERM_WIDTH / (SPACE_BEFORE + MAX_NAME_WIDTH))

NEXT_DIR = '\\'
cls = lambda: os.system('cls' if os.name=='nt' else 'clear')

start_dirs = {"Desktop": "C:\\Users\\Mihnea\\Desktop", "Mihnea": "C:\\Users\\Mihnea", "C": "C:\\"}


def move_cursor(y, x):
    sys.stdout.write("\033[%d;%dH" % (y, x))


def read_input():
    cls()
    print("Choose starting folder: ")
    print(f'Options: {reduce(lambda d1, d2: d1 + ", " + d2, start_dirs)}, name of folder inside Desktop (hit tab for autocomplete)')
    move_cursor(1, len("Choose starting folder: ") + 1)
    print(end='', flush=True)

    autocomplete_list = [dir for dir in os.listdir(start_dirs["Desktop"]) if os.path.isdir(start_dirs["Desktop"] + NEXT_DIR + dir)]
    autocomplete_list.sort()
    
    term_width = os.get_terminal_size()[0]
    continuous_tab = False
    poss_dirs = []

    previous_path = ""
    directory = ""
    while (True):
        command = readkey()

        if command == key.TAB:
            if not continuous_tab:
                if poss_dirs:
                    move_cursor(6, 0)
                    curr_pos = 1
                    for folder in poss_dirs:
                        next_print     = ' ' * len(folder + "; ") 
                        next_print_len = len(folder + "; ") 
                        if curr_pos + next_print_len <= term_width:
                            print(next_print, end = '')
                            curr_pos += next_print_len
                        else:
                            print()
                            print(next_print, end = '')
                            curr_pos = next_print_len

                else:
                    move_cursor(4, 0)
                    print("Possible folders:\n")

                poss_dirs = [dir for dir in autocomplete_list if dir.lower().startswith(directory.lower())]
                if poss_dirs:
                    move_cursor(6, 0)
                    curr_pos = 1
                    for folder in poss_dirs:
                        next_print     = colored(folder, 'yellow') + "; "
                        next_print_len = len(folder + "; ") 
                        if curr_pos + next_print_len <= term_width:
                            print(next_print, end = '')
                            curr_pos += next_print_len
                        else:
                            print()
                            print(next_print, end = '')
                            curr_pos = next_print_len
                
            else:
                move_cursor(1, len(f'Choose starting folder: {previous_path + directory}') + 1)
                print(' ' * len(last_tab_found))
            
            move_cursor(1, len(f'Choose starting folder: {previous_path + directory}') + 1)
            
            first_found = next((dir for dir in poss_dirs if dir.startswith(directory) and (not continuous_tab or dir > last_tab_found)), 
                next((dir for dir in poss_dirs if dir.startswith(directory)), directory))
            last_tab_found = first_found
            continuous_tab  = True
            print(colored(first_found[len(directory):], 'yellow'), end='', flush=True)

        else:
            if continuous_tab: 
                directory = last_tab_found
            continuous_tab = False
        
        if command.isalpha() or command == ' ':
            print(colored(command, 'yellow'), end='', flush=True)
            directory += command

        if command in [NEXT_DIR, '/']:
            if os.path.isdir(start_dirs["Desktop"] + NEXT_DIR + previous_path + NEXT_DIR + directory):
                print(NEXT_DIR, end='', flush=True)
                previous_path += NEXT_DIR + directory
                directory = ""
                autocomplete_list = [dir for dir in os.listdir(start_dirs["Desktop"] + NEXT_DIR + previous_path) 
                                    if os.path.isdir(start_dirs["Desktop"] + NEXT_DIR + previous_path + NEXT_DIR + dir)]

                autocomplete_list.sort()

        if command == key.BACKSPACE and (previous_path or directory):
            print("\b \b", end='', flush=True)
            if directory == "":
                directory     = previous_path[previous_path.rfind(NEXT_DIR) + 1:]
                previous_path = previous_path[:previous_path.rfind(NEXT_DIR)]
                autocomplete_list = [dir for dir in os.listdir(start_dirs["Desktop"] + NEXT_DIR + previous_path) 
                                     if os.path.isdir(start_dirs["Desktop"] + NEXT_DIR + previous_path + NEXT_DIR + dir)]
                autocomplete_list.sort()

            else:
                directory = directory[:-1]

        if command == key.ENTER:
            break

        if command == key.ESC:
            cls()
            quit()

    if not previous_path and not directory:
        return "Desktop"

    return previous_path + (NEXT_DIR if previous_path != "" else '') + directory


def get_start_path():
    directory = read_input()
    if directory[0] == NEXT_DIR:
        directory = directory[1:]

    if directory in start_dirs:
        return start_dirs[directory]
    
    if os.path.isdir(start_dirs["Desktop"] + NEXT_DIR + directory):
        return start_dirs["Desktop"] + NEXT_DIR + directory
    
    cwd = os.getcwd()
    return cwd if ("dir_explorer" not in cwd and "Desktop" in cwd) else start_dirs["Desktop"]


def print_filenames(current_path, files):
    cls()
    column = 1
    line   = 1

    for file in files:
        # move_cursor(counter % FILES_PER_COLUMN + 1, int(counter / FILES_PER_COLUMN) * (2 + SPACE_BEFORE + MAX_NAME_WIDTH))
        if column > MAX_COLUMNS:
            break
       
        move_cursor(line, (column - 1) * (SPACE_BEFORE + MAX_NAME_WIDTH) + (column != 1))

        name = file
        if len(name) > MAX_NAME_WIDTH:
            if not os.path.isdir(current_path + NEXT_DIR + file):
                # if name.rfind('.') != 0 for hidden files
                extension = name[name.rfind('.'):] if name.rfind('.') != 0 else ""
            else: 
                extension = ''
            name = name[0:MAX_NAME_WIDTH - 1 - len(extension)] + '-' + extension 

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


def main_loop():
    # current_path = str(pathlib.Path().resolve())
    current_path = get_start_path()

    cursor.hide()
    files = [dir for dir in os.listdir(current_path) if dir[dir.find('.') + 1:] != "ini"]
    files = list(filter(lambda file: os.path.isdir(current_path + NEXT_DIR + file), files)) + list(filter(lambda file: not os.path.isdir(current_path + NEXT_DIR + file), files))
    print_filenames(current_path, files)

    column = 1
    line   = 1

    leftwise_column = 1

    total_columns     = roundup(len(files) / FILES_PER_COLUMN)
    columns_last_line = len(files) % FILES_PER_COLUMN
    
    global MAX_NAME_WIDTH
    global MAX_COLUMNS

    while (True):
        move_cursor(line, (column - leftwise_column) * (SPACE_BEFORE + MAX_NAME_WIDTH) + (column != 1))
        print(" -> ")
        # print(str(column) + ' ' + str(line))
        # print((column - 1) * FILES_PER_COLUMN + line - 1)
        move_cursor(line, (column - leftwise_column) * (SPACE_BEFORE + MAX_NAME_WIDTH) + (column != 1))

        command = readkey()

        if command not in [key.UP, key.DOWN, key.LEFT, key.RIGHT, key.ENTER, key.BACKSPACE, key.TAB, key.ESC, '`', '~', '=', '-']:
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

                if (column - leftwise_column) >= MAX_COLUMNS:
                    leftwise_column += 1
                    column = leftwise_column
                    print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])


        if (command == "=" and 1 < MAX_COLUMNS):
            # changing the width of filenames to maximum possible if we have one less column
            MAX_NAME_WIDTH = int(TERM_WIDTH / (MAX_COLUMNS - 1)) - SPACE_BEFORE
            # MAX_NAME_WIDTH += 1 # increasing size of filenames
            MAX_COLUMNS = int(TERM_WIDTH / (SPACE_BEFORE + MAX_NAME_WIDTH))
            print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])
            if (column - leftwise_column) >= MAX_COLUMNS:
                column -= 1


        if (command == "-" and 8 < MAX_NAME_WIDTH):
            # changing the width of filenames to leave space for an additional column
            MAX_NAME_WIDTH = int(TERM_WIDTH / (MAX_COLUMNS + 1)) - SPACE_BEFORE
            MAX_COLUMNS = int(TERM_WIDTH / (SPACE_BEFORE + MAX_NAME_WIDTH))
            print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])


        if (command == key.UP):
            print("   ")

            line -= 1
            if line < 1:
                line = FILES_PER_COLUMN

        if (command == key.DOWN):
            print("   ")

            line += 1
            if FILES_PER_COLUMN < line or (column == total_columns and columns_last_line < line):
                line = 1
            
        if (command == key.LEFT):
            print("   ")

            column -= 1

            if column < leftwise_column and 1 <= column:
                leftwise_column -= 1
                print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])

            if column < 1:
                column = total_columns
                if total_columns > MAX_COLUMNS:
                    leftwise_column = total_columns - MAX_COLUMNS + 1
                    print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])

            
        if (command == key.RIGHT):
            print("   ")

            column += 1

            if total_columns < column:
                column = 1
                if leftwise_column > 1:
                    leftwise_column = 1
                    print_filenames(current_path, files)

            if (column - leftwise_column) >= MAX_COLUMNS:
                leftwise_column += 1
                print_filenames(current_path, files[(leftwise_column - 1) * FILES_PER_COLUMN:])

        if column == total_columns and columns_last_line < line:
            line = columns_last_line   

        if command == key.ENTER:
            changed_directory = False

            try:
                file = files[(column - 1) * FILES_PER_COLUMN + line - 1]
                if os.path.isdir(current_path + NEXT_DIR + file):
                    current_path += NEXT_DIR + file
                    changed_directory = True
                    files = os.listdir(current_path)
                    files = list(filter(lambda file: os.path.isdir(current_path + NEXT_DIR + file), files)) + list(filter(lambda file: not os.path.isdir(current_path + NEXT_DIR + file) and file[file.find('.') + 1:] != "ini", files))
                    print_filenames(current_path, files)
                    column = 1
                    line   = 1

                    total_columns     = roundup(len(files) / FILES_PER_COLUMN)
                    columns_last_line = len(files) % FILES_PER_COLUMN

                    if columns_last_line == 0:
                        columns_last_line = FILES_PER_COLUMN

                else: 
                    if platform.system() == 'Windows':    # Windows
                        subprocess.run(f'explorer {current_path + NEXT_DIR + file}', capture_output=False)
                        # os.startfile(current_path + NEXT_DIR + file)
                    else:                                   # linux variants
                        subprocess.call(('xdg-open', current_path + NEXT_DIR + file))

            except:
                if changed_directory:
                    current_path = current_path[0:current_path.rfind(NEXT_DIR)]

        if command == key.BACKSPACE:
            prev_dir = current_path[current_path.rfind(NEXT_DIR) + 1:]
            current_path = current_path[0:current_path.rfind(NEXT_DIR)]
            if current_path == "C:":
                current_path = "C:\\"
            files = os.listdir(current_path)
            files = list(filter(lambda file: os.path.isdir(current_path + NEXT_DIR + file), files)) + list(filter(lambda file: not os.path.isdir(current_path + NEXT_DIR + file) and file[file.find('.') + 1:] != "ini", files))
            print_filenames(current_path, files)

            if prev_dir not in files:
                column = 1
                line   = 1
            else:
                column = int(files.index(prev_dir) / FILES_PER_COLUMN) + 1
                line   = files.index(prev_dir) % FILES_PER_COLUMN + 1

            total_columns     = roundup(len(files) / FILES_PER_COLUMN)
            columns_last_line = len(files) % FILES_PER_COLUMN

        if command == key.TAB:
            os.startfile(current_path) # open the C:\Windows folder

        if command in ['`', '~']:
            cwd = os.getcwd()
            os.chdir(current_path)
            os.startfile("powershell.exe") # open powershell in Windows
            os.chdir(cwd)

        if (command == key.ESC):
            move_cursor(0, 0)
            cls()
            break


def main():
    main_loop()

if __name__ == '__main__':
    main()
