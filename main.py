import vtk
from vtk.util import numpy_support
import SimpleITK as sitk

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
output_data_subdir = "data/"
output_mask_subdir = "mask/"
classes = ["C:/Users/Milan/Downloads/54879843/DICOM/Doe^Pierre [54879843]/20060101 000000 [ - CRANE POLYGONE]/Data/Class 0/"]

input_data = {}
classes_data = {}

seg_threshold_start = 250
seg_threshold_limit = 500
seg_threshold_step = 50

sig_seg_threshold = 1000

convert_input_flag = True

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


def set_output_data_subdir():
    global output_data_subdir

    output_data_subdir = input("Enter output subdirectory for the data: ")
    print("Set subdirectory to: '" + output_data_subdir + "'.")


def set_output_mask_subdir():
    global output_mask_subdir

    output_mask_subdir = input("Enter output subdirectory for the masks: ")
    print("Set subdirectory to: '" + output_mask_subdir + "'.")


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


# Takes a vtkMapper, or a list of vtkMapper(s), and displays it/them in a vtkRenderWindow
def display_mapper(mapper, style=None):
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(np.random.rand(3))

    # if a list of mappers is displayed, colour each one with a random colour
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

    print("Displaying.")
    
    rwi.Initialize()
    render_window.Render()
    render_window.Start()
    rwi.Start()


# Takes a vtkPolyData, or a list of vtkPolyData, converts it/them into vtkMapper(s) and passes them to display_mapper()
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
    

# Uses VTK's implementation of the Flying Edges algorithm to cut units larger than [threshold] value 
# from a vtkImageData volume and outputs it as a vtkPolyData mesh
# https://www.researchgate.net/publication/282975362_Flying_Edges_A_High-Performance_Scalable_Isocontouring_Algorithm
def cut_image_at_threshold(image, threshold):
    extractor = vtk.vtkFlyingEdges3D()
    extractor.SetInputData(image)
    extractor.SetValue(0, threshold)
    extractor.Update()
    
    stripper = vtk.vtkStripper()
    stripper.SetInputData(extractor.GetOutput())
    stripper.Update()
    
    return stripper.GetOutput()


# Takes a vtkImageData volume, cuts out a vtkPolyData using a [threshold], then renders it using display_mapper()
def display_image_data(image, threshold=1):
    # Following volume rendering example from vtk
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(cut_image_at_threshold(image, threshold))
    mapper.ScalarVisibilityOff()

    display_mapper(mapper)
    
    
# count how many separate objects ("islands") are present in a vtkPolyData mesh, and return a np array with their sizes
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


# VTK interactor style to highlight and return a selected object from a vtkRenderWindowInteractor
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


# Colours in a vtkPolyData mesh shape in a vtkImageData volume with [i] values
# [reverse] sets whether or not you want to colour in outside or inside the mesh
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


# Converts numpy array to vtkImageData
# https://discourse.vtk.org/t/convert-vtk-array-to-numpy-array/3152/4
def numpyToVTK(data, multi_component=False, type='float'):
    '''
    multi_components: rgb has 3 components
    type：float or char
    '''
    if type == 'float':
        data_type = vtk.VTK_FLOAT
    elif type == 'char':
        data_type = vtk.VTK_UNSIGNED_CHAR
    else:
        raise RuntimeError('unknown type')
    if multi_component == False:
        if len(data.shape) == 2:
            data = data[:, :, np.newaxis]
        flat_data_array = data.transpose(2, 1, 0).flatten()
        vtk_data = numpy_support.numpy_to_vtk(num_array=flat_data_array, deep=True, array_type=data_type)
        shape = data.shape
    else:
        assert len(data.shape) == 3, 'only test for 2D RGB'
        flat_data_array = data.transpose(1, 0, 2)
        flat_data_array = np.reshape(flat_data_array, newshape=[-1, data.shape[2]])
        vtk_data = numpy_support.numpy_to_vtk(num_array=flat_data_array, deep=True, array_type=data_type)
        shape = [data.shape[0], data.shape[1], 1]
    img = vtk.vtkImageData()
    img.GetPointData().SetScalars(vtk_data)
    img.SetDimensions(shape[0], shape[1], shape[2])
    return img


def process():
    global input_type
    global input_dir
    global classes

    get_list_of_inputs = os.listdir(input_dir)
    print("Detected (" + str(len(get_list_of_inputs)) + ") inputs. ")

    class_reader = vtk.vtkSTLReader()

    for input_entry in get_list_of_inputs:
        # read in the input
        if input_type == InputType.DICOM:
            # ITK's DICOM reader is more robust than the VTK implementation
            # https://developpaper.com/example-of-python-reading-dicom-image-simpleitk-and-dicom-package-implementation/
            reader = sitk.ImageSeriesReader()
            img_names = reader.GetGDCMSeriesFileNames(input_dir + input_entry)
            reader.SetFileNames(img_names)
            image = reader.Execute()
            image_array = sitk.GetArrayFromImage(image)  # z, y, x

            input_entry_data = numpyToVTK(image_array)
        
        # display the input to the user
        print("Displaying input (" + input_entry + ") at starting threshold:")
        display_image_data(input_entry_data, seg_threshold_start)
        present_classes = int(input("How many classes are present, excluding background? "))
        
        # procedurally increase segmentation threshold until desired number of valid regions achieved
        segmented = False
        seg_threshold = seg_threshold_start
        while not segmented and not (seg_threshold > seg_threshold_limit):
            print("...Segmentation threshold = " + str(seg_threshold))
            segmented_poly = cut_image_at_threshold(input_entry_data, seg_threshold)
            found_region_sizes = get_sig_part_sizes(segmented_poly)
            
            # threshold for a significant poly = sig_seg_threshold connected points
            found_classes = np.sum(found_region_sizes > sig_seg_threshold)
            
            if found_classes >= present_classes:
                segmented = True
                break
            else:
                seg_threshold += seg_threshold_step
        
        if not segmented:
            print("Segmentation of input (" + input_entry + ") failed, continuing to the next one.")
            continue
        
        objects_found = []
        
        # extract the N largest objects from the input, depending on how many classes the user expects
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
        
        # 0 out the output vtkImageData segmentation
        updated_data = add_to_image(blank_poly, input_entry_data, 0, False)
        
        # allows the user to select what to do for each expected class
        for i in range(present_classes):
            command = input("pick', 'load', or 'skip class (" + str(i) + ")? ")
            
            if (command != "pick") and ("load" not in command):
                print("...Skipping...")
                continue
            if command == "pick":  # allows the user to click the object they want to select for current class
                selector = MouseInteractorHighLightActor()
                display_poly_data(objects_found, selector)
                selected_poly = vtk.vtkPolyData()
                selected_poly = selector.LastPickedActor.GetMapper().GetInput()
            elif "load" in command:  # allows the user to apply the input's class's .STL for current class
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
                    display_poly_data(selected_poly, style=None)
                else:  # skip current class
                    print("...not found, skipping...")
                
            # add to output image
            updated_data = add_to_image(selected_poly, updated_data, i+1, True)
        
        # save segmentation to [output_dir]/[name]_output.nii
        writer = vtk.vtkNIFTIImageWriter()
        writer.SetInputData(updated_data)
        writer.SetFileName(output_dir + input_entry + "_output.nii")
        writer.Write()
        writer.Update()
        
        if convert_input_flag:
            # optionally save converted input volume to [output_dir]/[name]_input.nii for convenience
            writer.SetInputData(input_entry_data)
            writer.SetFileName(output_dir + input_entry + "_input.nii")
            writer.Write()
            writer.Update()
            
    print("Done.")
                
                    
                

commands = {
    "process": process,
    "commands": commands_print,
    "info": lambda: print("Type 'info [command]' for more info on how to use a command."),
    "set input type": set_input_type,
    "set input dir": set_input_dir,
    "set output dir": set_output_dir,
    "set convert input": set_convert_input,
    "list classes": list_classes,
    "create class": create_class,
    "delete class": delete_class,
    "exit": sys.exit,
    "quit": sys.exit
}

info = {
    "process": "Initiate segmentation process.",
    "commands": "List available commands.",
    "info": "http://www.github.com/mtancak/",
    "set input type": "Choose between Numpy and DICOM volumes to be used as input.",
    "set input dir": "Choose directory which will contain the input volumes.",
    "set output dir": "Choose directory where the segmentation output will be saved.",
    "set convert input": "Choose whether you want the input volume to be converted to " + 
                            "and saved as a .nii (NIFTI) file in the output directory, " + 
                            "along with the segmentation (this volume will be saved as [name]_input.nii).",
    "list classes": "Prints class indices and their associated directories.",
    "create class": "Allocate a directory to an index.",
    "delete class": "Delete a created class by index.",
    "exit": "Terminate program.",
    "quit": "Terminate program."
}

if __name__ == "__main__":
    print("pyDIssect - Utility for converting DICOMs and other volumes into segmentation masks.")
    print("author: github.com/mtancak")
    print("Type 'commands' for a list of commands.")
    print("Type 'info [command]' for more info on how to use a command.")
    print("Set the input and output directories, optionally create classes with pre-processed .STLs and then begin the segmentation [process]!")

    while True:
        command = input("Enter Command: ")
        if command in commands:
            commands[command]()
        else:
            cmd_split = command.split(" ")
            if (cmd_split[0] == "info") and (cmd_split[1] in commands) and (len(cmd_split) == 2):
                print("(" + cmd_split[1] + ") - " + info[cmd_split[1]])
            else:
                print("Command not recognised. (" + command + ")")
                commands_print()
