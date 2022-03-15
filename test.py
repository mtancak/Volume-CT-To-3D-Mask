import numpy as np
from vtk import *
import SimpleITK as sitk
from vtk.util import numpy_support


def cut_image_at_threshold(image, threshold):
    print(image)
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

https://discourse.vtk.org/t/convert-vtk-array-to-numpy-array/3152/4
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

if __name__ == "__main__":
    # https://developpaper.com/example-of-python-reading-dicom-image-simpleitk-and-dicom-package-implementation/
    img_path = 'C:/Users/Milan/Downloads/54879843/DICOM/Doe^Pierre [54879843]/20060101 000000 [ - CRANE POLYGONE]/Data/Dicom/Shoulder/'

    reader = sitk.ImageSeriesReader()
    img_names = reader.GetGDCMSeriesFileNames(img_path)
    reader.SetFileNames(img_names)
    image = reader.Execute()
    image_array = sitk.GetArrayFromImage(image)  # z, y, x

    a = numpyToVTK(image_array)

    display_image_data(a, 270)