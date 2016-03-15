
from __future__ import division
import numpy as np
from data_handling import load_features_and_labels

hidden_neurons = 2000
epoch = 300
directory = "../DataSetICFHR2012/features/rbm_"


def load_rbm_model_features_and_labels():
    global epoch, hidden_neurons, directory

    # load features
    g_train, g_train_label, g_test, g_test_label, g_feature_name = load_features_and_labels()
    _train = np.transpose(np.asarray(g_train))
    _test = np.transpose(np.asarray(g_test))

    # load model
    directory += str(hidden_neurons) + '/_' + str(epoch)
    w_vh = np.load(directory + '_numpy_w_vh_.npy')
    w_v = np.load(directory + '_numpy_w_v_.npy')
    w_h = np.load(directory + '_numpy_w_h_.npy')
    err = np.load(directory + '_numpy_err_.npy')

    # positive phase
    g_train_h = 1. / (1 + np.exp(-(np.dot(w_vh.T, _train) + w_h)))
    g_test_h = 1. / (1 + np.exp(-(np.dot(w_vh.T, _test) + w_h)))

    # sample hiddens
    #g_train_h = 1. * (g_train_h > np.random.rand(hidden_neurons, g_train_h.shape[1]))
    #g_test_h = 1. * (g_test_h > np.random.rand(hidden_neurons, g_test_h.shape[1]))

    # transpose
    g_train_h = np.transpose(g_train_h)
    g_test_h = np.transpose(g_test_h)

    # print info
    print "Hidden Units: " + str(hidden_neurons)
    print "Generative error: " + str(err)
    print "Epoch: " + str(epoch)

    return g_train_h, g_train_label, g_test_h, g_test_label, g_feature_name

