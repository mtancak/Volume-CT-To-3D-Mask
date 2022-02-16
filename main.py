import vtk
import sys


def commands_print():
    print("Printing available commands:")
    for command in commands.keys():
        print("  " + command)


commands = {
    "exit": sys.exit,
    "commands": commands_print,
}

if __name__ == "__main__":
    print("author: github.com/mtancak")
    print("Utility for converting volumes into segmentation masks")
    print("Type 'commands' for a list of commands")

    while True:
        action = input("Action: ")
        if action in commands:
            commands[action]()
        else:
            print("Command not recognised. (" + action + ")")
            commands_print()
