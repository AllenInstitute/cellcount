Dataset:

 - Cells are fluorescently labeled with red, green or both.
 - 2-channel data is collected. Ideally, only cells marked with the red fluorescent label should appear in the red channel (same for green)
 - Due to bleed-through, we notice a tendency for the cells labeled with Green fluorescent label to appear in the red channel. 
 - The degree of bleed-through varies for each animal
 - 32.0 Mb per image
 - 1.25 Gb for 2x for channels + 2x for label for a 20 image training dataset. Can load all of this in memory for patch generation.

Annotations:
 - Initial ground truth consists of approximate cell centers 
 - Composite image was used for reference, and visible cells were assigned as either red-, green-, or both-labeled
 
Pixel-wise ground truth:

Matlab-based workflow to convert obtain pixel-wise labels from cell center annotations.

1. `pwgt/optim_centers_script.m`: Removes inadvertent duplicate cell center annotations. Optimizes the position of the cell center. 
2. `pwgt/FM_script.m`: Generates intermediate .mat files with output from a fast marching based wave propagation algorithm. .mat files contain maps for  visited/not-visited points `KT`, arrival time `T`, distance `D`, simple/non-simple point class `S`.
3. `pwgt/lbl_from_FM.m`: Uses intermediate .mat files to generate individual label maps.

Models:
 - `notebooks/first_run.ipynb`: Unet tested via overfitting on a small patch. 
 - `notebooks/base_unet_datagen.ipynb`: Tests for data generator

Todo:
 - Use transformations to augment label and image (some transformations are exclusive to the image)