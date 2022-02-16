import vtk
import sys
from enum import Enum


class InputType(Enum):
    NUMPY = "numpy"
    DICOM = "dicom"


input_type = InputType.NUMPY
input_dir = None
output_dir = None
classes = []


def commands_print():
    global commands

    print("Printing available commands: ")
    for command in commands.keys():
        print("  " + command)


def set_input_type():
    global input_type

    print("Available types: ")
    for t in InputType:
        print("  " + str(t.value))
    entered_type = input("Enter Input Type: ")

    try:
        read_type = InputType(entered_type)
        input_type = read_type
        print("Done.")
    except ValueError:
        print("Type doesn't exist.")


def set_input_dir():
    global input_dir

    entered_dir = input("Enter input directory: ")
    input_dir = entered_dir
    print("Set input directory to: '" + input_dir + "'.")


def set_output_dir():
    global output_dir

    entered_dir = input("Enter output directory: ")
    output_dir = entered_dir
    print("Set output directory to: '" + output_dir + "'.")


def create_class():
    global classes

    classes.append(input("Enter segmentation class dir: "))
    print("Created segmentation class with index (" + str(len(classes) - 1) + ") from dir '" + classes[-1] + "'. ")


def list_classes():
    global classes

    print("Printing current class indices and directories: ")
    for i, c in enumerate(classes):
        print("  index " + str(i) + " : dir = " + c)


def delete_class():
    global classes

    entered_class = input("Enter index of class to remove ('cancel' to cancel): ")

    if entered_class == "cancel":
        return

    entered_class = int(entered_class)

    if 0 <= entered_class < len(classes):
        del classes[entered_class]
        print("Updated indexes. ")
        list_classes()
    else:
        print("Class index does not exist. (hint: type 'list classes')")


commands = {
    "exit": sys.exit,
    "commands": commands_print,
    "set input type": set_input_type,
    "set input dir": set_input_dir,
    "set output dir": set_output_dir,
    "create class": create_class,
    "list classes": list_classes,
    "delete class": delete_class
}

if __name__ == "__main__":
    print("author: github.com/mtancak")
    print("Utility for converting volumes into segmentation masks.")
    print("Type 'commands' for a list of commands.")

    while True:
        command = input("Enter Command: ")
        if command in commands:
            commands[command]()
        else:
            print("Command not recognised. (" + command + ") ")
            commands_print()
