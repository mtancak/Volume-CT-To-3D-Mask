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


def display_mapper(mapper, style=None):
    renderer = vtk.vtkRenderer()

    if isinstance(mapper, list):
        for m in mapper:
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            
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
            mapper.SetInputData(poly)
            mappers.append(mapper)

            display_mapper(mappers)
    else:
        # Following mesh rendering example from vtk
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(poly)
    
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
    
    
def segment_image(image, threshold):
    poly = cut_image_at_threshold(image, threshold)
    
    print("segment_image")
    display_poly_data(poly)
    
    return poly
    
    
def randomise_colours(poly):
    return poly
    
    
def count_sig_parts(poly):
    connectivity = vtk.vtkPolyDataConnectivityFilter()
    connectivity.SetExtractionModeToAllRegions()
    connectivity.SetInputData(poly)
    connectivity.Update()
    
    region_count = connectivity.GetNumberOfExtractedRegions()
    region_sizes = np.zeros(region_count)
    
    for i in range(region_count):
        region_sizes[i] = connectivity.GetRegionSizes().GetTuple1(i)
    
    # threshold for a significant poly = 100 connected points
    return np.sum(region_sizes > 100)


# https://kitware.github.io/vtk-examples/site/Python/Picking/HighlightPickedActor/
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
            found_classes = count_sig_parts(segmented_poly)
            
            if found_classes >= present_classes:
                segmented = True
                break
            else:
                seg_threshold += seg_threshold_step
        
        if not segmented:
            print("Segmentation of input (" + input_entry + ") failed, continuing to the next one.")
            continue
        
        print("Displaying segmentation at (" + str(seg_threshold) + "HU), found (" + str(found_classes) + ") objects): ")
        # display_poly_data(randomise_colours(segmented_poly))
        display_poly_data(randomise_colours(segmented_poly), MouseInteractorHighLightActor())
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        output_entry_data = vtk.vtkImageData()
        output_entry_data.DeepCopy(input_entry_data)

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
                stencil_creator.ReverseStencilOn()
                stencil_creator.SetBackgroundValue(1)
                stencil_creator.SetInputData(output_entry_data)
                stencil_creator.SetStencilData(stencil_converter.GetOutput())
                stencil_creator.Update()

                stencil_creator1 = vtk.vtkImageStencil()
                stencil_creator1.ReverseStencilOff()
                stencil_creator1.SetBackgroundValue(2)
                stencil_creator1.SetInputData(output_entry_data)
                stencil_creator1.SetStencilData(stencil_converter.GetOutput())
                stencil_creator1.Update()
                
                display_image_data(stencil_creator1.GetOutput())
                
                writer = vtk.vtkNIFTIImageWriter()
                writer.SetInputData(stencil_creator1.GetOutput())
                writer.SetFileName(output_dir + input_entry + ".nii")
                writer.Write()
                writer.Update()
                
                blank_poly = vtk.vtkPolyData()
                
                stencil_converter2 = vtk.vtkPolyDataToImageStencil()
                stencil_converter2.SetOutputOrigin(output_entry_data.GetOrigin())
                stencil_converter2.SetOutputSpacing(output_entry_data.GetSpacing())
                stencil_converter2.SetOutputWholeExtent(output_entry_data.GetExtent())
                stencil_converter2.SetInputData(blank_poly)
                stencil_converter2.Update()
                
                stencil_creator2 = vtk.vtkImageStencil()
                stencil_creator2.ReverseStencilOn()
                stencil_creator2.SetBackgroundValue(0)
                stencil_creator2.SetInputData(input_entry_data)
                stencil_creator2.SetStencilData(stencil_converter2.GetOutput())
                stencil_creator2.Update()
                
                writer = vtk.vtkNIFTIImageWriter()
                writer.SetInputData(stencil_creator2.GetOutput())
                writer.SetFileName(output_dir + input_entry + "_output3.nii")
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
