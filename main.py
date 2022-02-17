import vtk
import sys
import os
import numpy as np

from enum import Enum


class InputType(Enum):
    NUMPY = "numpy"
    DICOM = "dicom"


input_type = InputType.DICOM
input_dir = None
output_dir = None
classes = []

input_data = {}
classes_data = {}

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


def display_poly_data(poly):
    # Following mesh rendering example from vtk
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(poly)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    renderer = vtk.vtkRenderer()
    renderer.AddActor(actor)

    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)

    rwi = vtk.vtkRenderWindowInteractor()
    rwi.SetRenderWindow(render_window)

    render_window.Render()
    render_window.Start()
    rwi.Start()


def display_image_data(image):
    # Following volume rendering example from vtk
    extractor = vtk.vtkFlyingEdges3D()
    extractor.SetInputData(image)
    extractor.SetValue(0, 50)

    stripper = vtk.vtkStripper()
    stripper.SetInputConnection(extractor.GetOutputPort())

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(stripper.GetOutputPort())
    mapper.ScalarVisibilityOff()

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetSpecular(0.3)
    actor.GetProperty().SetSpecularPower(20)
    actor.GetProperty().SetOpacity(1.0)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    renderer = vtk.vtkRenderer()
    renderer.AddActor(actor)

    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)

    rwi = vtk.vtkRenderWindowInteractor()
    rwi.SetRenderWindow(render_window)

    render_window.Render()
    render_window.Start()
    rwi.Start()


def process():
    global input_type
    global input_dir
    global classes

    get_list_of_inputs = os.listdir(input_dir)
    print("Detected (" + str(len(get_list_of_inputs)) + ") inputs. ")

    input_reader = None
    if input_type == InputType.DICOM:
        input_reader = vtk.vtkDICOMImageReader()

    class_reader = vtk.vtkSTLReader()

    for input_entry in get_list_of_inputs:
        input_reader.SetDirectoryName(input_dir + input_entry)
        input_reader.Update()
        input_entry_data = input_reader.GetOutput()
        
        display_image_data(input_entry_data)
                
        for i, class_dir in enumerate(classes):
            class_inputs = os.listdir(class_dir)
            print("Detected (" + str(len(get_list_of_inputs)) + ") inputs for class (" + str(i) + "). ")

            if input_entry + ".stl" in class_inputs:
                class_reader.SetFileName(class_dir + input_entry + ".stl")
                class_reader.Update()
                class_entry_data = class_reader.GetOutput()
                
                display_poly_data(class_entry_data)
                
                normals = vtk.vtkPolyDataNormals()
                normals.SetInputData(class_entry_data)
                normals.ComputePointNormalsOn()
                normals.ComputeCellNormalsOff()
                normals.SetConsistencyOn()
                normals.SetAutoOrientNormalsOn()
                normals.SplittingOff()
                normals.Update()
                
                class_entry_normals = normals.GetOutput().GetPointData().GetNormals()
                
                pt = np.array([0, 0, 0])
                for ptid in range(class_entry_data.GetNumberOfPoints()):
                    class_entry_data.GetPoint(ptid, pt)
                    # create output dicom of same shape and size
                    # get nearest point in mesh
                    # dot product with normal
                    # if x > 0, set class id (i), else 0
                # add output to dictionary
        
                
                    
                

commands = {
    "exit": sys.exit,
    "commands": commands_print,
    "set input type": set_input_type,
    "set input dir": set_input_dir,
    "set output dir": set_output_dir,
    "list classes": list_classes,
    "create class": create_class,
    "delete class": delete_class,
    "process": process
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
