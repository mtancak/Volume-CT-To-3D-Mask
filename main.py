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

seg_threshold_start = 250
seg_threshold_limit = 500
seg_threshold_step = 50

convert_input_flag = False

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
        input_type = InputType(entered_type)
        print("Done.")
    except ValueError:
        print("Type doesn't exist.")


def set_input_dir():
    global input_dir

    input_dir = input("Enter input directory: ")
    print("Set input directory to: '" + input_dir + "'.")


def set_output_dir():
    global output_dir

    output_dir = input("Enter output directory: ")
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


def set_seg_threshold_start():
    global seg_threshold_start

    seg_threshold_start = input("Enter starting segmentation threshold: ")
    print("Set starting segmentation threshold to: '" + seg_threshold_start + "'.")


def set_seg_threshold_limit():
    global seg_threshold_limit

    seg_threshold_limit = input("Enter segmentation threshold limit: ")
    print("Set segmentation threshold limit to: '" + seg_threshold_limit + "'.")


def set_convert_input():
    global convert_input_flag
    
    convert_input_flag = bool(input("Convert input dicoms to .nii files while processing? (True/False): "))
    print("Flag set to: '" + str(convert_input_flag) + "'.")


def display_mapper(mapper, style=None):
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(np.random.rand(3))

    if isinstance(mapper, list):
        for m in mapper:
            actor = vtk.vtkActor()
            actor.SetMapper(m)
            actor.GetProperty().SetColor(np.random.rand(3))
            
            renderer.AddActor(actor)
            
    else:
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        renderer.AddActor(actor)

    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)

    rwi = vtk.vtkRenderWindowInteractor()
    rwi.SetRenderWindow(render_window)
    
    if style:
        style.SetDefaultRenderer(renderer)
        rwi.SetInteractorStyle(style)

    rwi.Initialize()
    render_window.Render()
    render_window.Start()
    rwi.Start()
    print("Displaying.")


def display_poly_data(poly, style=None):
    if isinstance(poly, list):
        mappers = []
        for p in poly:
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(p)
            mapper.ScalarVisibilityOff()
            mappers.append(mapper)

        display_mapper(mappers, style)
    else:
        # Following mesh rendering example from vtk
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(poly)
        mapper.ScalarVisibilityOff()
    
        display_mapper(mapper, style)
    
    
def cut_image_at_threshold(image, threshold):
    extractor = vtk.vtkFlyingEdges3D()
    extractor.SetInputData(image)
    extractor.SetValue(0, threshold)
    extractor.Update()
    
    stripper = vtk.vtkStripper()
    stripper.SetInputData(extractor.GetOutput())
    stripper.Update()
    
    return stripper.GetOutput()


def display_image_data(image, threshold=1):
    # Following volume rendering example from vtk
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(cut_image_at_threshold(image, threshold))
    mapper.ScalarVisibilityOff()

    display_mapper(mapper)
    
    
def get_sig_part_sizes(poly):
    connectivity = vtk.vtkPolyDataConnectivityFilter()
    connectivity.SetExtractionModeToAllRegions()
    connectivity.SetInputData(poly)
    connectivity.Update()
    
    region_count = connectivity.GetNumberOfExtractedRegions()
    region_sizes = np.zeros(region_count, dtype=int)
    
    for i in range(region_count):
        region_sizes[i] = int(connectivity.GetRegionSizes().GetTuple1(i))
    
    return region_sizes


# code from https://kitware.github.io/vtk-examples/site/Python/Picking/HighlightPickedActor/
class MouseInteractorHighLightActor(vtk.vtkInteractorStyleTrackballCamera):

    def __init__(self, parent=None):
        self.AddObserver("LeftButtonPressEvent", self.leftButtonPressEvent)

        self.LastPickedActor = None
        self.LastPickedProperty = vtk.vtkProperty()

    def leftButtonPressEvent(self, obj, event):
        clickPos = self.GetInteractor().GetEventPosition()

        picker = vtk.vtkPropPicker()
        picker.Pick(clickPos[0], clickPos[1], 0, self.GetDefaultRenderer())

        # get the new
        self.NewPickedActor = picker.GetActor()

        # If something was selected
        if self.NewPickedActor:
            # If we picked something before, reset its property
            if self.LastPickedActor:
                self.LastPickedActor.GetProperty().DeepCopy(self.LastPickedProperty)

            # Save the property of the picked actor so that we can
            # restore it next time
            self.LastPickedProperty.DeepCopy(self.NewPickedActor.GetProperty())
            # Highlight the picked actor by changing its properties
            self.NewPickedActor.GetProperty().SetColor(vtk.vtkNamedColors().GetColor3d('Red'))
            self.NewPickedActor.GetProperty().SetDiffuse(1.0)
            self.NewPickedActor.GetProperty().SetSpecular(0.0)
            self.NewPickedActor.GetProperty().EdgeVisibilityOn()

            # save the last picked actor
            self.LastPickedActor = self.NewPickedActor

        self.OnLeftButtonDown()
        return


def add_to_image(poly, image, i, reverse=False):
    stencil_converter = vtk.vtkPolyDataToImageStencil()
    stencil_converter.SetOutputOrigin(image.GetOrigin())
    stencil_converter.SetOutputSpacing(image.GetSpacing())
    stencil_converter.SetOutputWholeExtent(image.GetExtent())
    stencil_converter.SetInputData(poly)
    stencil_converter.Update()
    
    stencil_creator = vtk.vtkImageStencil()
    if reverse:
        stencil_creator.ReverseStencilOn()
    else:
        stencil_creator.ReverseStencilOff()
    stencil_creator.SetBackgroundValue(i)
    stencil_creator.SetInputData(image)
    stencil_creator.SetStencilData(stencil_converter.GetOutput())
    stencil_creator.Update()
    
    return stencil_creator.GetOutput()


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
        
        print("Displaying input (" + input_entry + ") at starting threshold:")
        display_image_data(input_entry_data, seg_threshold_start)
        present_classes = int(input("How many classes are present, excluding background? "))
        
        segmented = False
        seg_threshold = seg_threshold_start
        while not segmented and not (seg_threshold > seg_threshold_limit):
            print("...Segmentation threshold = " + str(seg_threshold))
            segmented_poly = cut_image_at_threshold(input_entry_data, seg_threshold)
            found_region_sizes = get_sig_part_sizes(segmented_poly)
            
            # threshold for a significant poly = 100 connected points
            found_classes = np.sum(found_region_sizes > 100)
            
            if found_classes >= present_classes:
                segmented = True
                break
            else:
                seg_threshold += seg_threshold_step
        
        if not segmented:
            print("Segmentation of input (" + input_entry + ") failed, continuing to the next one.")
            continue
        
        objects_found = []
        
        for i in sorted(zip(list(range(len(found_region_sizes))), found_region_sizes), reverse=True, key=lambda x : x[1])[:present_classes]:
            connectivity = vtk.vtkPolyDataConnectivityFilter()
            connectivity.SetExtractionModeToSpecifiedRegions()
            connectivity.AddSpecifiedRegion(i[0])
            connectivity.SetInputData(segmented_poly)
            connectivity.Update()
            
            cleaner = vtk.vtkCleanPolyData()
            cleaner.SetInputData(connectivity.GetOutput())
            cleaner.Update()
            
            conn_poly = vtk.vtkPolyData()
            conn_poly.DeepCopy(cleaner.GetOutput())
            objects_found.append(conn_poly)
        
        print("Displaying segmentation at (" + str(seg_threshold) + "HU), found (" + str(found_classes) + ") objects): ")
        display_poly_data(objects_found)
        
        blank_poly = vtk.vtkPolyData()
        
        updated_data = add_to_image(blank_poly, input_entry_data, 0, False)
        
        for i in range(present_classes):
            command = input("pick', 'load', or 'skip class (" + str(i) + ")? ")
            
            if (command != "pick") and ("load" not in command):
                print("...Skipping...")
                continue
            if command == "pick":
                selector = MouseInteractorHighLightActor()
                display_poly_data(objects_found, selector)
                selected_poly = vtk.vtkPolyData()
                selected_poly = selector.LastPickedActor.GetMapper().GetInput()
            elif "load" in command:
                selected_class = int(input("Enter class to label this object: "))
                class_inputs = os.listdir(classes[selected_class])
                if input_entry + ".stl" in class_inputs:
                    class_reader.SetFileName(classes[selected_class] + input_entry + ".stl")
                    class_reader.Update()
                    
                    cleaner = vtk.vtkCleanPolyData()
                    cleaner.SetInputData(class_reader.GetOutput())
                    cleaner.Update()
                    
                    connectivity = vtk.vtkConnectivityFilter()
                    connectivity.SetExtractionModeToLargestRegion()
                    connectivity.SetInputData(cleaner.GetOutput())
                    connectivity.Update()
                    
                    selected_poly = connectivity.GetOutput()
                else:
                    print("...not found, skipping...")
                
            # add to output image
            updated_data = add_to_image(selected_poly, updated_data, i+1, True)
        
        writer = vtk.vtkNIFTIImageWriter()
        writer.SetInputData(updated_data)
        writer.SetFileName(output_dir + input_entry + "_output.nii")
        writer.Write()
        writer.Update()
        
        if convert_input_flag:
            writer.SetInputData(input_entry_data)
            writer.SetFileName(output_dir + input_entry + "_input.nii")
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
    "set convert input": set_convert_input,
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
