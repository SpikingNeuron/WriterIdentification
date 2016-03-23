"""
This file contains code for benchmarking the scores on test data-set
"""
from source.utility.data_handling import load_features_and_labels
from source.generate_new_representation import rbm_representation, pca_representation
from joblib import Parallel, delayed
import gc
import multiprocessing
import time
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import SGDClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.svm import SVC
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectFromModel
from sklearn.metrics import f1_score
from collections import namedtuple

# global variables
g_train = None
g_train_label = None
g_test = None
g_test_label = None
g_feature_name = None
PARALLEL_SUPPORT = False

# special memory structure to be used by multi threaded code
parallel_mem_struct = namedtuple(
    'parallel_mem_struct',
    [
        'classifier_title',
        'new_representation',
        'train_score',
        'test_score',
        'identification_rate',
        'top_features',
        'time_taken'
    ]
)

g_classifiers = {
    #"Logistic Regression": LogisticRegression(),
    #"SGD": SGDClassifier(),
    #"Gaussian Naive Bayes": GaussianNB(),
    "1 Nearest Neighbors": KNeighborsClassifier(1),
    #"2 Nearest Neighbors": KNeighborsClassifier(2),
    #"3 Nearest Neighbors": KNeighborsClassifier(3),
    "Linear Discriminant Analysis": LinearDiscriminantAnalysis(),
    "Quadratic Discriminant Analysis": QuadraticDiscriminantAnalysis(),
    "SVM Linear": SVC(kernel="linear", C=0.025),
    "SVM RBF": SVC(gamma=2, C=1),
    "Decision Tree": DecisionTreeClassifier(),
    #"AdaBoost 10": AdaBoostClassifier(n_estimators=10),
    #"AdaBoost 100": AdaBoostClassifier(n_estimators=100),
    #"AdaBoost 1000": AdaBoostClassifier(n_estimators=1000),
    "Random Forest 10": RandomForestClassifier(n_estimators=10),
    "Random Forest 100": RandomForestClassifier(n_estimators=100),
    "Random Forest 1000": RandomForestClassifier(n_estimators=1000),
    "Random Forest 10000": RandomForestClassifier(n_estimators=10000),
    "Extra Trees 10": ExtraTreesClassifier(n_estimators=10),
    "Extra Trees 100": ExtraTreesClassifier(n_estimators=100),
    "Extra Trees 1000": ExtraTreesClassifier(n_estimators=1000),
    "Extra Trees 10000": ExtraTreesClassifier(n_estimators=10000),
    #"Gradient Boosting 10": GradientBoostingClassifier(n_estimators=10),
    #"Gradient Boosting 100": GradientBoostingClassifier(n_estimators=100),
    #"Gradient Boosting 1000": GradientBoostingClassifier(n_estimators=1000),
    "Pipe SVC LDA": Pipeline([('feature_selection', SelectFromModel(LinearSVC())), ('classification', LinearDiscriminantAnalysis())]),
    "Pipe SVC Extra Trees 1000": Pipeline([('feature_selection', SelectFromModel(LinearSVC())), ('classification', ExtraTreesClassifier(n_estimators=1000))]),
}


def get_classifier_dict():
    """
    This method creates couple of classifiers that will be used for training.
    This is the place where you decide which classifiers to use.
    Populate the dictionary accordingly.
    :return: dictionary
    :rtype: dict
    """
    dictionary = {
        "Logistic Regression": LogisticRegression(),
        "SGD": SGDClassifier(),
        "Gaussian Naive Bayes": GaussianNB(),
        "1 Nearest Neighbors": KNeighborsClassifier(1),
        "Linear Discriminant Analysis": LinearDiscriminantAnalysis(),
        "Quadratic Discriminant Analysis": QuadraticDiscriminantAnalysis(),
        "SVM Linear": SVC(kernel="linear", C=0.025),
        "SVM RBF": SVC(gamma=2, C=1),
        "Decision Tree": DecisionTreeClassifier(),
        "Random Forest 10": RandomForestClassifier(n_estimators=10),
        "Random Forest 100": RandomForestClassifier(n_estimators=100),
        "Extra Trees 10": ExtraTreesClassifier(n_estimators=10),
        "Extra Trees 100": ExtraTreesClassifier(n_estimators=100),
        "Pipe SVC LDA": Pipeline([('feature_selection', SelectFromModel(LinearSVC())), ('classification', LinearDiscriminantAnalysis())]),
        "Pipe SVC Extra Trees 100": Pipeline([('feature_selection', SelectFromModel(LinearSVC())), ('classification', ExtraTreesClassifier(n_estimators=100))]),
    }

    dictionary_small = {
        "Pipe SVC LDA": Pipeline([('feature_selection', SelectFromModel(LinearSVC())), ('classification', LinearDiscriminantAnalysis())]),
        "Linear Discriminant Analysis": LinearDiscriminantAnalysis(),
    }
    return dictionary


def execute_classifier(classifier, classifier_title, new_representation):
    """
    Special generic method that can take any classifier and execute it.
    It also reports the score on provided dataset.
    This method is specially designed to exploit multiprocessor usage in trying different classifiers independently.
    :param classifier:
    :type classifier:
    :param classifier_title:
    :type classifier_title:
    :param new_representation:
    :type new_representation:
    :return:
    :rtype:
    """
    print('Performing training for `' + classifier_title + '` classifier with `' + new_representation +
          '` representation ...')
    start_time = time.time()
    classifier.fit(g_train, g_train_label)
    train_predictions = classifier.predict(g_train)
    test_predictions = classifier.predict(g_test)
    train_score = f1_score(g_train_label, train_predictions, average='micro')
    test_score = f1_score(g_test_label, test_predictions, average='micro')
    end_time = time.time()
    time_taken = end_time - start_time
    identification_rate = (sum(g_test_label == test_predictions)/g_test_label.shape[0])*100

    top_features = ''
    if False:
        if type(classifier) is ExtraTreesClassifier \
                or type(classifier) is RandomForestClassifier:
            top_feat = np.argsort(classifier.feature_importances_)
            for i in top_feat:
                top_features += str(i) + ' '
        else:
            top_features += 'NA'
    else:
        top_features += 'NA'

    return parallel_mem_struct(
        classifier_title=classifier_title,
        new_representation=new_representation,
        train_score=train_score,
        test_score=test_score,
        identification_rate=identification_rate,
        top_features=top_features,
        time_taken=time_taken
    )


def save_parallel_mem_struct(parallel_mem_struct_list, report_type):
    """
    Save the parallel memory structure for further reporting
    :param report_type: ['As it is' 'RBM' 'PCA' 'LDA']
    :type report_type: str
    :param parallel_mem_struct_list:
    :type parallel_mem_struct_list: list
    :return:
    :rtype:
    """
    f_out = open("../documentation/Report_" + report_type + ".txt", "w")
    for parallel_mem_struct_ in parallel_mem_struct_list:
        f_out.write(parallel_mem_struct_.classifier_title + "\n")
        f_out.write(parallel_mem_struct_.new_representation + "\n")
        f_out.write(str(parallel_mem_struct_.train_score) + "\n")
        f_out.write(str(parallel_mem_struct_.test_score) + "\n")
        f_out.write(str(parallel_mem_struct_.identification_rate) + "\n")
        f_out.write(str(parallel_mem_struct_.top_features) + "\n")
        f_out.write(str(parallel_mem_struct_.time_taken) + "\n")
    f_out.close()

    pass


def print_parallel_mem_struct(report_type):
    """
    Load and print parallel memory structure
    :param report_type: which report you want to print ['As it is' 'RBM' 'PCA' 'LDA' 'all']
    :type report_type: str
    :return:
    :rtype:
    """
    pass


def run_parallel_with_as_it_is_representation():
    """
    Run machine learning algorithms in parallel with as it is representation.
    :return:
    :rtype:
    """
    # global vars to set
    global g_train, g_train_label, g_test, g_test_label, g_feature_name
    new_representation = 'As it is'

    # garbage collection
    gc.collect()

    # fetch meta info
    num_cores = multiprocessing.cpu_count()
    classifier_dict = get_classifier_dict()

    # load default representation
    g_train, g_train_label, g_test, g_test_label, g_feature_name = load_features_and_labels()

    # storage of results
    training_jobs_results = []

    # launch threads
    if PARALLEL_SUPPORT:
        Parallel(n_jobs=num_cores)(delayed(execute_classifier)(classifier_dict[title], title, new_representation)
                                   for title in classifier_dict)
    else:
        for title in classifier_dict:
            res = execute_classifier(
                classifier=classifier_dict[title],
                classifier_title=title,
                new_representation=new_representation
            )
            training_jobs_results.append(res)

    # save results
    save_parallel_mem_struct(training_jobs_results, new_representation)

    # garbage collection
    g_train = None
    g_train_label = None
    g_test = None
    g_test_label = None
    g_feature_name = None
    training_jobs_results = None
    gc.collect()


def run_parallel_with_RBM_representation():
    """
    Run machine learning algorithms in parallel with RBM representation.
    :return:
    :rtype:
    """
    # global vars to set
    global g_train, g_train_label, g_test, g_test_label, g_feature_name
    new_representation = 'RBM'

    # garbage collection
    gc.collect()

    # fetch meta info
    num_cores = multiprocessing.cpu_count()
    classifier_dict = get_classifier_dict()

    # load default representation
    g_train, g_train_label, g_test, g_test_label, g_feature_name = rbm_representation(4000, 3550)

    # storage of results
    training_jobs_results = []

    # launch threads
    if PARALLEL_SUPPORT:
        Parallel(n_jobs=num_cores)(delayed(execute_classifier)(classifier_dict[title], title, new_representation)
                                   for title in classifier_dict)
    else:
        for title in classifier_dict:
            res = execute_classifier(
                classifier=classifier_dict[title],
                classifier_title=title,
                new_representation=new_representation
            )
            training_jobs_results.append(res)

    # save results
    save_parallel_mem_struct(training_jobs_results, new_representation)

    # garbage collection
    g_train = None
    g_train_label = None
    g_test = None
    g_test_label = None
    g_feature_name = None
    training_jobs_results = None
    gc.collect()


def run_parallel_with_PCA_representation():
    """
    Run machine learning algorithms in parallel with PCA representation.
    :return:
    :rtype:
    """
    # global vars to set
    global g_train, g_train_label, g_test, g_test_label, g_feature_name
    new_representation = 'RBM'

    # garbage collection
    gc.collect()

    # fetch meta info
    num_cores = multiprocessing.cpu_count()
    classifier_dict = get_classifier_dict()

    # load default representation
    g_train, g_train_label, g_test, g_test_label, g_feature_name = rbm_representation(4000, 3550)

    # storage of results
    training_jobs_results = []

    # launch threads
    if PARALLEL_SUPPORT:
        Parallel(n_jobs=num_cores)(delayed(execute_classifier)(classifier_dict[title], title, new_representation)
                                   for title in classifier_dict)
    else:
        for title in classifier_dict:
            res = execute_classifier(
                classifier=classifier_dict[title],
                classifier_title=title,
                new_representation=new_representation
            )
            training_jobs_results.append(res)

    # save results
    save_parallel_mem_struct(training_jobs_results, new_representation)

    # garbage collection
    g_train = None
    g_train_label = None
    g_test = None
    g_test_label = None
    g_feature_name = None
    training_jobs_results = None
    gc.collect()


def run_parallel_with_LDA_representation():
    """
    Run machine learning algorithms in parallel with LDA representation.
    :return:
    :rtype:
    """
    # global vars to set
    global g_train, g_train_label, g_test, g_test_label, g_feature_name
    new_representation = 'RBM'

    # garbage collection
    gc.collect()

    # fetch meta info
    num_cores = multiprocessing.cpu_count()
    classifier_dict = get_classifier_dict()

    # load default representation
    g_train, g_train_label, g_test, g_test_label, g_feature_name = rbm_representation(4000, 3550)

    # storage of results
    training_jobs_results = []

    # launch threads
    if PARALLEL_SUPPORT:
        Parallel(n_jobs=num_cores)(delayed(execute_classifier)(classifier_dict[title], title, new_representation)
                                   for title in classifier_dict)
    else:
        for title in classifier_dict:
            res = execute_classifier(
                classifier=classifier_dict[title],
                classifier_title=title,
                new_representation=new_representation
            )
            training_jobs_results.append(res)

    # save results
    save_parallel_mem_struct(training_jobs_results, new_representation)

    # garbage collection
    g_train = None
    g_train_label = None
    g_test = None
    g_test_label = None
    g_feature_name = None
    training_jobs_results = None
    gc.collect()


def main():
    """
    Main method responsible to call the machine learning algorithms in parallel
    :return:
    :rtype:
    """
    run_parallel_with_as_it_is_representation()
    run_parallel_with_RBM_representation()
    # run_parallel_with_PCA_representation()
    # run_parallel_with_LDA_representation()


if __name__ == "__main__":
    main()

