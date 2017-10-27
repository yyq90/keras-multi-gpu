from __future__ import print_function

import time

import numpy as np
from keras.callbacks import Callback

class BatchTiming(Callback):
    """
    It measure robust stats for timing of batches and epochs.
    Useful for measuring the training process.

    For each epoch it prints median batch time and total epoch time.
    After training it prints overall median batch time and median epoch time.

    Usage: model.fit(X_train, Y_train, callbacks=[BatchTiming()])

    All times are in seconds.

    More info: https://keras.io/callbacks/
    """
    def on_train_begin(self, logs={}):
        self.all_batch_times = []
        self.all_epoch_times = []

    def on_epoch_begin(self, epoch, logs={}):
        self.epoch_batch_times = []

    def on_batch_begin(self, batch, logs={}):
        self.start_time = time.time()

    def on_batch_end(self, batch, logs={}):
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        self.epoch_batch_times.append(elapsed_time)
        self.all_batch_times.append(elapsed_time)

    def on_epoch_end(self, epoch, logs={}):
        epoch_time = np.sum(self.epoch_batch_times)
        self.all_epoch_times.append(epoch_time)
        median_batch_time = np.median(self.epoch_batch_times)
        print('Epoch timing - batch (median): %0.5f, epoch: %0.5f (sec)' % \
            (median_batch_time, epoch_time))

    def on_train_end(self, logs={}):
        median_batch_time = np.median(self.all_batch_times)
        median_epoch_time = np.median(self.all_epoch_times)
        print('Overall - batch (median): %0.5f, epoch (median): %0.5f (sec)' % \
            (median_batch_time, median_epoch_time))

class SamplesPerSec(Callback):
    def __init__(self, batch_size):
        self.batch_size = batch_size

    def on_train_begin(self, logs={}):
        self.all_samples_per_sec = []

    def on_batch_begin(self, batch, logs={}):
        self.start_time = time.time()
        # self.batch_size = logs['size']

    def on_batch_end(self, batch, logs={}):
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        samples_per_sec = self.batch_size / elapsed_time
        self.all_samples_per_sec.append(samples_per_sec)

    def on_epoch_end(self, epoch, logs={}):
        self.print_results()

    def print_results(self):
        print('Samples/sec: %0.2f' % np.median(self.all_samples_per_sec))

"""
Enables CUDA profiling (for usage in nvprof) just for a few batches.

The reasons are:

- profiling outputs are big (easily 100s MB - GBs) and repeating
- without a proper stop the outputs sometimes fail to save

Since initially the TensorFlow runtime may take time to optimize the graph we
skip a few epochs and then enable profiling for a few batches within the next
epoch.

It requires the `cudaprofile` package.
"""
class CudaProfile(Callback):
    import cudaprofile

    def __init__(self, warmup_epochs=0, batches_to_profile=None):
        self.warmup_epochs = warmup_epochs
        self.batches_to_profile = batches_to_profile
        self.enabled = False

    def set_params(self, params):
        self.params = params

    def on_epoch_begin(self, epoch, logs={}):
        if epoch == self.warmup_epochs:
            cudaprofile.start()
            self.enabled = True

    def on_batch_end(self, batch, logs={}):
        if self.enabled && batch >= batches_to_profile:
            cudaprofile.stop()
