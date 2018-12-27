# In this version, the UNet is trained on 3 classes, and the network returns probabilities of a given pixel belonging to each class. 
# Labels: 0 = background
# Labels: 1 = foreground
# Labels: 2 = boundary
# For Data v2 

import os
import pdb
import pickle as Pickle
import sys
import time
import timeit
from random import shuffle


#import keras.activations.softmax as Softmax
#import matplotlib.pyplot as plt
import numpy as np
import scipy.io as sio
import tensorflow as tf
from keras import backend as K
from keras.callbacks import LearningRateScheduler, ModelCheckpoint, Callback
from keras.layers import (Concatenate, Conv2D, Cropping2D, Dropout, Input,
                          MaxPooling2D, UpSampling2D, Dense, Activation)
from keras.losses import binary_crossentropy, mean_squared_error
from keras.models import Model
from keras.optimizers import Adam
from keras.utils import plot_model, to_categorical


import _pickle as cPickle
import fileIO
import im3dscroll as I
from custom_dataloader import DataGenerator
from dataclass import dataset, combine_patches
import pdb


runmode = 'train-new'#viewresult or train-new

archid = 'Data_v2_Run_v2'
nepochs = 1500
batch_size = 4
patchsize = 128
save_period = 50

viewrunid = 'Data_v2_Run_v2'
base_path, rel_im_path, rel_lbl_path, rel_result_path = fileIO.set_paths()[0:4]
runid = archid + 'epochs_' + str(nepochs) #+ time.strftime("%Y%m%d-%H%M%S")


#Training data
train_fileid = ['268778_157', '268778_77',
                '271317_95', '271317_143',
                '275376_147', '275376_175',
                '275705_109', '275705_131',
                '279578_111', '279578_123',
                '299769_119', '299769_167',
                '299773_57', '299773_68',
                '301199_74', '315576_116',
                '316809_60', '324471_113',
                '330689_118', '371808_52',
                '386384_47', '387573_103_1',
                '389052_108', '389052_119']

train_data = dataset(train_fileid, batch_size=batch_size, patchsize=patchsize,
                        getpatch_algo='random', npatches=10**3, fgfrac=.5,
                        shuffle=True, rotate=True, flip=True)
train_data.load_im_lbl()
train_generator = DataGenerator(train_data)

#Validation data 
val_fileid = ['371808_60', '387573_103',
              '324471_53', '333241_113']
val_data = dataset(val_fileid, batch_size=batch_size, patchsize=patchsize,
                      getpatch_algo='stride', stride=(64, 64), padding=True,
                      shuffle=False, rotate=False, flip=False)
val_data.load_im_lbl()
val_im,val_lbl = val_data.get_patches() #Validation data is not updated while training.

#Define model
conv_properties = {'activation': 'relu', 'padding': 'same', 'kernel_initializer': 'he_normal'}
input_im = Input(shape=(128, 128, 1), name='input_im')

conv1 = Conv2D(8, 3, **conv_properties)(input_im)   # (batch, 128,128,8)
pool1 = MaxPooling2D(pool_size=(2, 2))(conv1)	    # (batch, 64, 64, 8)

conv2 = Conv2D(8, 3, **conv_properties)(pool1)      # (batch, 64, 64, 8)
pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)	    # (batch, 32, 32, 8)

conv3 = Conv2D(4, 3, **conv_properties)(pool2)		# (batch, 32, 32, 4)
pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)	    # (batch, 16, 16, 4)

conv4 = Conv2D(4, 3, **conv_properties)(pool3)		# (batch, 16, 16, 4)
drop4 = Dropout(0.2)(conv4)						    # (batch, 16, 16, 4)
pool4 = MaxPooling2D(pool_size=(2, 2))(drop4)	    # (batch, 8, 8, 4)

conv5 = Conv2D(4, 3, **conv_properties)(pool4)		# (batch, 8, 8, 4)
drop5 = Dropout(0.2)(conv5)						    # (batch, 8, 8, 4)

up6 = UpSampling2D(size=(2, 2))(drop5)			    # (batch, 16, 16, 4)
up6 = Conv2D(4, 2, **conv_properties)(up6)		    # (batch, 16, 16, 4)
cat6 = Concatenate(axis=3)([drop4, up6])  		    # (batch, 16, 16, 4)
conv6 = Conv2D(4, 3, **conv_properties)(cat6)		# (batch, 16, 16, 4)

up7 = UpSampling2D(size=(2, 2))(conv6)			    # (batch, 32, 32, 4)
up7 = Conv2D(4, 2, **conv_properties)(up7)		    # (batch, 32, 32, 4)
cat7 = Concatenate(axis=3)([conv3, up7])		    # (batch, 32, 32, 8)
conv7 = Conv2D(4, 3, **conv_properties)(cat7)		# (batch, 32, 32, 4)

up8 = UpSampling2D(size=(2, 2))(conv7)			    # (batch, 64, 64, 4)
up8 = Conv2D(8, 2, **conv_properties)(up8)		    # (batch, 64, 64, 8)
cat8 = Concatenate(axis=3)([conv2, up8])  		    # (batch, 64, 64, 16)
conv8 = Conv2D(8, 3, **conv_properties)(cat8)		# (batch, 64, 64, 8)

up9 = UpSampling2D(size=(2, 2))(conv8)			    # (batch, 128,128, 8)
up9 = Conv2D(8, 2, **conv_properties)(up9)		    # (batch, 128,128, 8)
cat9 = Concatenate(axis=3)([conv1, up9])  		    # (batch, 128,128, 16)
conv9 = Conv2D(8, 3, **conv_properties)(cat9)		# (batch, 128,128, 8) 


output_im = Conv2D(3,1, activation='softmax', name='output_im')(conv9)
model = Model(inputs=[input_im], outputs=[output_im])

def loss_fcn_wbce(y_true, y_pred):
    lbl = y_true
    pred = y_pred
    weights = tf.stop_gradient(1. - tf.reduce_mean(lbl, axis=[0, 1, 2]))
    ce = - tf.multiply(lbl, tf.log(pred + K.epsilon())) - tf.multiply((1. - lbl), tf.log(1. - pred + K.epsilon()))
    weighted_ce = tf.multiply(weights, ce)
    return K.mean(weighted_ce, axis=None)


model.compile(optimizer=Adam(),
              loss={'output_im': loss_fcn_wbce},
              metrics=['accuracy'])

bestnet_cb = ModelCheckpoint(filepath=(base_path + rel_result_path + runid + '-bestwt.h5'),
                             monitor='loss', verbose=1, save_best_only=True)

hist_cb = ModelCheckpoint(filepath=(base_path + rel_result_path + runid + '/' + '{epoch:04d}' + '.h5'),
                          verbose=1, save_best_only=False, save_weights_only=True,
                          mode='auto', period=save_period)

class cb(Callback):
    def __init__(self, filename):
        self.filename = filename
        f = open(filename, 'w')
        f.close()

    def on_epoch_end(self, epoch, logs):
        with open(self.filename, 'a') as f:
            f.write(
                str(epoch) + '\t' +
                str(logs['loss']) + '\t' +
                '\n')
            #str(logs['val_loss']) + '\t' +


if runmode == 'train-new':
    checkpoint_path = base_path + rel_result_path + '/' + runid
    if not os.path.exists(checkpoint_path):
        os.makedirs(checkpoint_path)
    
    cb_obj = cb(filename=base_path + rel_result_path + runid + '/' +runid+'.log')
    start_time = timeit.default_timer()
    #validation_data=[{'input_im': val_im}, {'output_im': to_categorical(np.array(val_lbl), num_classes=3)}]
    train_history = model.fit_generator(train_generator,
                                        initial_epoch=0, epochs=nepochs,
                                        shuffle=True,
                                        verbose=2, callbacks=[hist_cb, cb_obj])

    elapsed = timeit.default_timer() - start_time

    summary = train_history.params
    summary.update(train_history.history)
    summary['trainingtime'] = elapsed
    
    # Save trained model
    # plot_model(model, to_file=base_path + rel_result_path + runid + '-arch'+'.png')
    with open(base_path + rel_result_path + runid+'-summary'+'.pkl', 'wb') as file_pi:
        cPickle.dump(summary, file_pi)

elif runmode == 'continue':
    checkpoint_path = base_path + rel_result_path + '/' + runid
    if not os.path.exists(checkpoint_path):
        os.makedirs(checkpoint_path)
    print('Loading previously trained model weights')
    model.load_weights(base_path + rel_result_path + 'Labelsv5_epochs_1000/' + '1000' + '.h5')
    train_history = model.fit_generator(train_generator,
                                        validation_data=[],
                                        initial_epoch=1000, epochs=nepochs,
                                        max_queue_size=20, workers=10,
                                        use_multiprocessing=True, shuffle=True,
                                        verbose=2, callbacks=[hist_cb],
                                        )
    summary = train_history.params
    summary.update(train_history.history)

    # Save trained model
    #plot_model(model, to_file=base_path +
    #          rel_result_path + runid + '-arch'+'.png')
    with open(base_path + rel_result_path + runid+'-summary'+'.pkl', 'wb') as file_pi:
        cPickle.dump(summary, file_pi)

elif runmode == 'viewresult':
    model.load_weights(base_path + rel_result_path + 'Labelsv5_epochs_1500' + '/' + '1500' + '.h5')
    with open(base_path + rel_result_path + 'Labelsv5_epochs_1-summary.pkl', 'rb') as file_pi:
        summary = Pickle.load(file_pi)


