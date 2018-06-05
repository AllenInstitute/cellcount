import fileIO
import skimage.io as skio
import numpy as np
import timeit
import pdb

class dataset(object):
    def __init__(self, file_id, batch_size=4, patchsize=64, npatches=10**2, fgfrac=.5, shuffle=True, rotate=True, flip=True):
        #Paths
        base_path,rel_im_path,rel_lbl_path,rel_result_path = fileIO.set_paths()
        self.im_path = base_path + rel_im_path
        self.lbl_path = base_path + rel_lbl_path
        self.results_path = base_path + rel_result_path
        self.file_id = file_id

        #Parameters for input
        self.batch_size = batch_size
        self.patchsize = patchsize
        self.npatches_perfile = int(npatches/len(file_id))
        self.shuffle = shuffle
        self.fgfrac = fgfrac

        #Data augmentation
        #See examples in /Users/fruity/Envs/Py3ML/lib/python3.6/site-packages/keras/preprocessing/image.py
        self.rotate = rotate
        self.flip = flip

        #Data buffer list: All raw files are kept in memory. Only minibatches are given to GPU.
        self.im_buffer = list()
        self.lbl_buffer = list()
        return

    def load_im_lbl(self):
        #This loads label and image data into a list
        for f in self.file_id:
            self.im_buffer.append(skio.imread(self.im_path + f + '_raw.tif')[:,:,0])
            self.lbl_buffer.append(skio.imread(self.lbl_path + f + '_labels.tif'))
        return

    def get_epochpatches(self):
        #Use data buffer to generate patches

        im_epoch = np.zeros((0, self.patchsize, self.patchsize, 1))
        lbl_epoch = np.zeros((0, self.patchsize, self.patchsize, 1))

        for f in range(len(self.im_buffer)):
            im_this, lbl_this = fileIO.getpatches_randwithfg(
                im=self.im_buffer[f], lbl=self.lbl_buffer[f],
                patchsize=self.patchsize,
                npatches=self.npatches_perfile,
                fgfrac=self.fgfrac)
            im_epoch = np.append(im_epoch, im_this, axis=0)
            lbl_epoch = np.append(lbl_epoch, lbl_this, axis=0)

        if self.rotate:
            #Stack rotated patches and labels
            im_epoch = np.concatenate(
                (im_epoch,
                 np.rot90(im_epoch, 1, (1, 2)),
                 np.rot90(im_epoch, 2, (1, 2)),
                 np.rot90(im_epoch, 3, (1, 2))), axis=0)

            lbl_epoch = np.concatenate(
                (lbl_epoch,
                 np.rot90(lbl_epoch, 1, (1, 2)),
                 np.rot90(lbl_epoch, 2, (1, 2)),
                 np.rot90(lbl_epoch, 3, (1, 2))), axis=0)

        if self.flip and self.rotate:
            im_epoch = np.concatenate(
                (im_epoch, np.flip(im_epoch, axis=1)), axis=0)

            lbl_epoch = np.concatenate(
                (lbl_epoch, np.flip(lbl_epoch, axis=1)), axis=0)

        elif self.flip and self.rotate:
            im_epoch = np.concatenate(
                (im_epoch,
                 np.flip(im_epoch, axis=1),
                 np.flip(im_epoch, axis=2)), axis=0)
            
            lbl_epoch = np.concatenate(
                (lbl_epoch,
                 np.flip(lbl_epoch, axis=1),
                 np.flip(lbl_epoch, axis=2)), axis=0)

        if self.shuffle:
            shuffle_ind = np.random.permutation(np.arange(im_epoch.shape[0]))
            im_epoch = im_epoch[shuffle_ind]
            lbl_epoch = lbl_epoch[shuffle_ind]

        return im_epoch, lbl_epoch



    
