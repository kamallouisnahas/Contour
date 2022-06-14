# Contour
A semi-automated segmentation and quantitation tool for cyro-soft-X-ray tomography in Python 3.7

############Installation############

Ensure you have Python 3.7 or later installed on your computer before you run Contour.

Python library dependencies:

Pillow, 
numpy,
tkinter,
scipy,
copy


(try: python3 -m pip install -U Pillow)
(or try: python -m pip install Pillow)


#####################################


###Trying out example data###

1. Easy example

Read the information buttons ‘i’ when you encounter them in the program.

Create a new workspace in Contour and import ‘easy_example.tif’.

The voxel dimensions are 20 nm x 20 nm x 10 nm (width, height, depth)

Try to segment the lipid droplets (black spheres) or the mitochondria (grey compartments). Use a minimum width of 5-10 pixels. You should be able to segment them reasonably well if you select an appropriate threshold range.

If parts of the lipid droplets or mitochondria are missing from the segmented volume, use local segmentation to fill in those parts. Use the erase options to remove false segments.

Differentiate the segmented elements and play around with the color scheme and final touches.

2. Difficult example

Do the easy example first.

Create a new workspace in Contour and import ‘difficult_example.tif’.

The original voxel dimensions are 10 nm x 10 nm x 10 nm (width, height, depth)

This image is too large. The maximum dimensions are 512 x 512. It will be scaled down by a factor of 2. 

This is image is too “busy” to segment only the mitochondria in the Imported Image window. Click Skip instead.

A blank segmented volume will appear. You can segment the mitochondria individually by local segmentation.

Differentiate the segmented elements and inspect the volume measurements. These will take into account the original voxel dimensions before the scaling. Click Review elements to inspect each segmented element, or click on desired elements in the table.

3. Imported segmentation example

You can import a segmented volume generated with a different segmentation tool. You can then differentiate and quantitate the elements.

Do not create a new workspace. Instead, change the filename in the box and click Import segmented view. Import ‘imported_segmentation_example.tif’. This image contains vesicles segmented using Segmentation Editor in Fiji.

The original voxel dimensions are 10 nm x 10 nm x 10 nm (width, height, depth)

This image is too large. The maximum dimensions are 512 x 512. It will be scaled down by a factor of 2. 

The segmented view will open directly. Click Differentiate elements.

Click Calculate width to quantitate the longest width of each element in 3D. The measurements can be found in the ‘quantitation’ folder. This process is slow and may take a few minutes for this example.

###############################

For more information, check out our publication:

Nahas, K. L., Ferreira Fernandes, J., Vyas, N., Crump, C., Graham, S. and Harkiolaki, M. (2022)
Contour: a semi-automated segmentation and quantitation tool for cryo-soft-X-ray tomography. _Biological Imaging_, **2**, E3. doi:10.1017/S2633903X22000046

https://www.cambridge.org/core/journals/biological-imaging/article/contour-a-semiautomated-segmentation-and-quantitation-tool-for-cryosoftxray-tomography/35B858F60A8B28468F4A2248BA0C7247

For queries and reporting bugs, email contourqueries@gmail.com

