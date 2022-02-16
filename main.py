import vtk
import sys
from enum import Enum


class InputType(Enum):
    NUMPY = "numpy"
    DICOM = "dicom"


input_type = InputType.NUMPY


def commands_print():
    print("Printing available commands:")
    for command in commands.keys():
        print("  " + command)


def set_input_type():
    global input_type

    print("Available types: ")
    for t in InputType:
        print("  " + str(t.value))
    entered_type = input("Set Input Type: ")

    try:
        read_type = InputType(entered_type)
        input_type = read_type
        print("Done.")
    except ValueError:
        print("Type doesn't exist.")


commands = {
    "exit": sys.exit,
    "commands": commands_print,
    "set input type": set_input_type,
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
