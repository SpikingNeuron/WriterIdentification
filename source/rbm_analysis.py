"""
This file is responsible for utility methods to analyse the training of RBMs.
You can only run this code if you have trained RBMs for respective HIDDEN_NEURONS.
"""
import numpy as np
import os
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

# config
from pandas.io.sas.sas7bdat import _index

HIDDEN_NEURONS = 4000


def plot_training_error(hidden_neurons):
    """
    Plot the training errors for various epochs
    :param hidden_neurons:
    :type hidden_neurons:
    :return:
    :rtype:
    """
    matplotlib.style.use('classic')

    path = '../data/new_representation/rbm_' + str(hidden_neurons) + '/'
    save_path = '../documentation/'
    files = os.listdir(path)
    mean_squared_error = []

    for file in files:
        ff = file.split('_')
        for f in ff:
            if f == 'err':
                err = np.load(path + file)
                epoch = int(ff[1])
                mean_squared_error.append((epoch, float(err)))

    mean_squared_error.sort()
    err_all = np.asarray([v for k, v in mean_squared_error])
    index_all = np.asarray([k for k, v in mean_squared_error])

    df = pd.DataFrame(data=err_all[1:], index=index_all[1:])
    df.columns = ['RBM error']
    ax = df.plot()
    ax.set_xlabel("Epochs")
    ax.set_ylabel("Mean Squared Error")
    ax.set_title("Mean squared error of RBM with " + str(hidden_neurons) + " hidden neurons.")
    plt.tight_layout()
    plt.savefig(save_path+"RBM_mse_"+str(hidden_neurons)+".pdf")

    pass


def build_hidden_activities(hidden_neurons, start_epoch, end_epoch, skip):
    """

    This routine plots hidden activities based on test data.
    This helps us to visualize how the training of RBM progressed as error reduces.

    :param hidden_neurons:
    :type hidden_neurons:
    :param start_epoch:
    :type start_epoch: int
    :param end_epoch:
    :type end_epoch: int
    :param skip: how many epochs to jump
    :type skip: int
    :return:
    :rtype:
    """
    from source.utility.data_handling import load_features_and_labels
    from collections import namedtuple
    import csv

    directory = "../data/new_representation/rbm_" + str(hidden_neurons) + "/_"

    # load features
    g_train, g_train_label, g_test, g_test_label, g_feature_name = load_features_and_labels()
    _train = np.transpose(np.asarray(g_train))
    _test = np.transpose(np.asarray(g_test))

    # hidden activity
    test_hidden_activities = []
    test_hidden_activities_bin = []
    train_hidden_activities = []
    train_hidden_activities_bin = []
    activities_epochs = []
    activities_mse = []

    # get the epochs
    for epoch in range(start_epoch, end_epoch, skip):

        print('Working on epoch ' + str(epoch) + '\n')

        # load model
        w_vh = np.load(directory + str(epoch) + '_numpy_w_vh_.npy')
        w_v = np.load(directory + str(epoch) + '_numpy_w_v_.npy')
        w_h = np.load(directory + str(epoch) + '_numpy_w_h_.npy')
        err = np.load(directory + str(epoch) + '_numpy_err_.npy')

        #
        activities_epochs.append(epoch)
        activities_mse.append(err)


        #######################################################
        # positive phase
        # g_train_h = 1. / (1 + np.exp(-(np.dot(w_vh.T, _train) + w_h)))
        h_test = 1. / (1 + np.exp(-(np.dot(w_vh.T, _test) + w_h)))

        # sample hidden activity
        h_test1 = 1. * (h_test > np.random.rand(hidden_neurons, h_test.shape[1]))
        h_test1 = np.transpose(h_test1)
        h_test1 = np.asarray(sum(h_test1))

        # add to list bin
        test_hidden_activities_bin.append(h_test1)

        # add to list
        h_test2 = np.transpose(h_test)
        h_test2 = np.asarray(sum(h_test2))
        test_hidden_activities.append(h_test2)

        #######################################################
        # positive phase
        # g_train_h = 1. / (1 + np.exp(-(np.dot(w_vh.T, _train) + w_h)))
        h_test = 1. / (1 + np.exp(-(np.dot(w_vh.T, _train) + w_h)))

        # sample hidden activity
        h_test1 = 1. * (h_test > np.random.rand(hidden_neurons, h_test.shape[1]))
        h_test1 = np.transpose(h_test1)
        h_test1 = np.asarray(sum(h_test1))

        # add to list bin
        train_hidden_activities_bin.append(h_test1)

        # add to list
        h_test2 = np.transpose(h_test)
        h_test2 = np.asarray(sum(h_test2))
        train_hidden_activities.append(h_test2)

    # store to file
    test_hidden_activities = np.asarray(test_hidden_activities)
    test_hidden_activities_bin = np.asarray(test_hidden_activities_bin)
    train_hidden_activities = np.asarray(train_hidden_activities)
    train_hidden_activities_bin = np.asarray(train_hidden_activities_bin)
    activities_epochs = np.asarray(activities_epochs)
    activities_mse = np.asarray(activities_mse)

    np.save(directory + 'test_hidden_activities', test_hidden_activities)
    np.save(directory + 'test_hidden_activities_bin', test_hidden_activities_bin)
    np.save(directory + 'train_hidden_activities', train_hidden_activities)
    np.save(directory + 'train_hidden_activities_bin', train_hidden_activities_bin)
    np.save(directory + 'activities_epochs', activities_epochs)
    np.save(directory + 'activities_mse', activities_mse)


if __name__ == '__main__':
    print(plt.style.available)
    #plot_training_error(hidden_neurons=HIDDEN_NEURONS)

    build_hidden_activities(hidden_neurons=HIDDEN_NEURONS, start_epoch=0, end_epoch=3551, skip=50)

