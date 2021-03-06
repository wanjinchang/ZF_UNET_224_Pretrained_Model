# coding: utf-8
'''
    - train "ZF_UNET_224" CNN with random images
'''

__author__ = 'ZFTurbo: https://kaggle.com/zfturbo'

import os
import cv2
import random
import numpy as np
import pandas as pd
from theano.version import version as __theano_version__
from keras.optimizers import Adam, SGD
from keras.callbacks import ModelCheckpoint, EarlyStopping
from keras import __version__
from zf_unet_224_model import *

np.random.seed(2017)


def show_image(im, name='image'):
    cv2.imshow(name, im)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def gen_random_image():
    img = np.zeros((224, 224, 3), dtype=np.uint8)
    mask = np.zeros((224, 224), dtype=np.uint8)

    # Background
    dark_color0 = random.randint(0, 100)
    dark_color1 = random.randint(0, 100)
    dark_color2 = random.randint(0, 100)
    img[:, :, 0] = dark_color0
    img[:, :, 1] = dark_color1
    img[:, :, 2] = dark_color2

    # Object
    light_color0 = random.randint(dark_color0+1, 255)
    light_color1 = random.randint(dark_color1+1, 255)
    light_color2 = random.randint(dark_color2+1, 255)
    center_0 = random.randint(0, 224)
    center_1 = random.randint(0, 224)
    r1 = random.randint(10, 56)
    r2 = random.randint(10, 56)
    cv2.ellipse(img, (center_0, center_1), (r1, r2), 0, 0, 360, (light_color0, light_color1, light_color2), -1)
    cv2.ellipse(mask, (center_0, center_1), (r1, r2), 0, 0, 360, 255, -1)

    # White noise
    density = random.uniform(0, 0.1)
    for i in range(224):
        for j in range(224):
            if random.random() < density:
                img[i, j, 0] = random.randint(0, 255)
                img[i, j, 1] = random.randint(0, 255)
                img[i, j, 2] = random.randint(0, 255)

    return img, mask


def batch_generator(batch_size):
    while True:
        image_list = []
        mask_list = []
        for i in range(batch_size):
            img, mask = gen_random_image()
            image_list.append(img)
            mask_list.append([mask])

        image_list = np.array(image_list, dtype=np.float32)
        image_list = image_list.transpose((0, 3, 1, 2))
        image_list = preprocess_batch(image_list)
        mask_list = np.array(mask_list, dtype=np.float32)
        mask_list /= 255.0
        yield image_list, mask_list


def train_unet():
    out_model_path = 'zf_unet_224.h5'
    epochs = 400
    patience = 20
    batch_size = 16
    optim_type = 'Adam'
    learning_rate = 0.0001
    model = ZF_UNET_224(0.05, True)
    if os.path.isfile(out_model_path):
        model.load_weights(out_model_path)

    if optim_type == 'SGD':
        optim = SGD(lr=learning_rate, decay=1e-6, momentum=0.9, nesterov=True)
    else:
        optim = Adam(lr=learning_rate)
    model.compile(optimizer=optim, loss=dice_coef_loss, metrics=[dice_coef])

    callbacks = [
        EarlyStopping(monitor='val_loss', patience=patience, verbose=0),
        ModelCheckpoint('zf_unet_224_temp.hdf5', monitor='val_loss', save_best_only=True, verbose=0),
    ]

    print('Start training...')
    history = model.fit_generator(
        generator=batch_generator(batch_size),
        nb_epoch=epochs,
        samples_per_epoch=200*batch_size,
        validation_data=batch_generator(batch_size),
        nb_val_samples=200*batch_size,
        verbose=2,
        callbacks=callbacks)

    model.save_weights(out_model_path)
    pd.DataFrame(history.history).to_csv('zf_unet_224_train.csv', index=False)
    print('Training is finished (weights zf_unet_224.h5 and log zf_unet_224_train.csv are generated )...')


if __name__ == '__main__':
    print('Theano version: {}'.format(__theano_version__))
    print('Keras version {}'.format(__version__))
    train_unet()
