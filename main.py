import vtk
from vtk.util import numpy_support

import sys
import os
import numpy as np

from enum import Enum


class InputType(Enum):
    NUMPY = "numpy"
    DICOM = "dicom"


input_type = InputType.DICOM
input_dir = "C:/Users/Milan/Downloads/54879843/DICOM/Doe^Pierre [54879843]/20060101 000000 [ - CRANE POLYGONE]/Data/Dicom/"
output_dir = "./Output/"
classes = ["C:/Users/Milan/Downloads/54879843/DICOM/Doe^Pierre [54879843]/20060101 000000 [ - CRANE POLYGONE]/Data/Class 0/"]

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
    extractor.SetValue(0, 1)

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

    renderer = vtk.vtkRenderer()
    renderer.SetBackground(255, 0, 50)
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
        input_entry_data.SetOrigin(input_reader.GetImagePositionPatient())
        display_image_data(input_entry_data)
        
        output_entry_data = vtk.vtkImageData()
        # We copy the dimensions of the input vtkImageData
        output_entry_data.SetOrigin(input_entry_data.GetOrigin())
        output_entry_data.SetSpacing(input_entry_data.GetSpacing())
        output_entry_data.SetExtent(input_entry_data.GetExtent())
        output_entry_data.AllocateScalars(6, 1)  # 6 means that we are allocating scalars of type "int", 1 per voxel

        output_scalars = np.zeros(int(np.prod(input_entry_data.GetDimensions())))
        for i in range(len(output_scalars)):
            output_scalars[i] = 1
        
        output_scalars = numpy_support.numpy_to_vtk(output_scalars.ravel(), deep=True, array_type=6)
        output_scalars.SetNumberOfComponents(1)
        output_entry_data.GetPointData().SetScalars(output_scalars)
    
        output_entry_data.Modified()

        for i, class_dir in enumerate(classes):
            class_inputs = os.listdir(class_dir)
            print("Detected (" + str(len(get_list_of_inputs)) + ") inputs for class (" + str(i) + "). ")

            if input_entry + ".stl" in class_inputs:
                class_reader.SetFileName(class_dir + input_entry + ".stl")
                class_reader.Update()
                
                cleaner = vtk.vtkCleanPolyData()
                cleaner.SetInputData(class_reader.GetOutput())
                cleaner.Update()
                
                connectivity = vtk.vtkConnectivityFilter()
                connectivity.SetExtractionModeToLargestRegion()
                connectivity.SetInputData(cleaner.GetOutput())
                connectivity.Update()
                
                display_poly_data(connectivity.GetOutput())
                
                stencil_converter = vtk.vtkPolyDataToImageStencil()
                stencil_converter.SetOutputOrigin(output_entry_data.GetOrigin())
                stencil_converter.SetOutputSpacing(output_entry_data.GetSpacing())
                stencil_converter.SetOutputWholeExtent(output_entry_data.GetExtent())
                stencil_converter.SetInputData(connectivity.GetOutput())
                stencil_converter.Update()
                
                stencil_creator = vtk.vtkImageStencil()
                stencil_creator.ReverseStencilOff()
                stencil_creator.SetBackgroundValue(0)
                stencil_creator.SetInputData(output_entry_data)
                stencil_creator.SetStencilData(stencil_converter.GetOutput())
                stencil_creator.Update()
                
                display_image_data(stencil_creator.GetOutput())
                
                writer = vtk.vtkNIFTIImageWriter()
                writer.SetInputData(stencil_creator.GetOutput())
                writer.SetFileName(output_dir + input_entry + ".nii")
                writer.Write()
                writer.Update()
                
                writer = vtk.vtkNIFTIImageWriter()
                writer.SetInputData(input_entry_data)
                writer.SetFileName(output_dir + input_entry + "_output.nii")
                writer.Write()
                writer.Update()
    print("Done.")
                
                    
                

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
