## Description
Console application for easier movement through directories (since W11 File Explorer tends to be annoyingly slow).

## Requirements
- The [ConsoleListInterface](https://github.com/MihneaZar/ConsoleListInterface/) library for the console interface;
- The [termcolor](https://pypi.org/project/termcolor/) library for yellow directory names; 
- The [filetype](https://pypi.org/project/filetype/) library for checking if files are images;
- The [Send2Trash](https://pypi.org/project/Send2Trash/) library for sending files to trash / recycle bin;
- The [pyperclip](https://pypi.org/project/pyperclip/) library for copying paths to clipboard.

## Additional Information
The commands 'python3 dir_explorer.py -h' or 'python3 dir_explorer.py --help' explain how to give a path to the Dir-Explorer. <br>
On first use, it will prompt user to give the path to the ConsoleInterfaceList.py file (containing the respective class). <br>
Typing '?' while in the app will print the help page. <br>
Only tested on Windows 11.

-------------------------------------------------------------------------

*Copyright (c) 2026 Mihnea Bogdan Zarojanu*
