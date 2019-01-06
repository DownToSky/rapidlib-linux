"""
This is an example file for prepraing SVM for RAPID(C)
"""

from Classes import *  # import the parent class and other classes from the file Classes.py
from cs231n.data_utils import load_CIFAR10
from cs231n.classifiers import LinearSVM
import numpy as np
import pickle


class appMethods(AppMethods):
    """ application specific class inherited from class AppMethods
    Please keep the name of the class to be appMethods since it will be used in RAPID(C) to create an instance of
    this class
    """
    data_path = "/home/liuliu/Research/mara_bench/machine_learning/cs231n/datasets/cifar-10-batches-py"

    def __init__(self, name, obj_path):
        """ Initialization with app name
        :param name:
        """
        AppMethods.__init__(self, name, obj_path)
        self.training_units = 1

    def cleanUpAfterEachRun(self, configs=None):
        learningRate = 100*1e-7
        regular = 25000
        batch = 500
        if configs is not None:
            for config in configs:
                name = config.knob.set_name
                if name == "learningRate":
                    learningRate = float(config.val) * 1e-7
                elif name == "regular":
                    regular = config.val  # retrieve the setting for each
                    # knob
                elif name == "batch":
                    batch = config.val  # retrieve the setting for each knob

        # backup the generated output to another location
        self.moveFile("./model_svm.p",
                      "./training_outputs/output_" + str(float(learningRate) * 1e7) + "_" + str(int(regular)) + "_" + str(
                          int(batch)) + ".txt")

    # helper function to assembly the command
    def getCommand(self, configs=None):
        learningRate = 100*1e-7
        regular = 25000
        batch = 500
        if configs is not None:
            for config in configs:
                name = config.knob.set_name
                if name == "learningRate":
                    learningRate = float(config.val) * 1e-7
                elif name == "regular":
                    regular = config.val  # retrieve the setting for each
                    # knob
                elif name == "batch":
                    batch = config.val  # retrieve the setting for each knob
        return [self.obj_path,
                "--lr",
                str(learningRate),
                "--reg",
                str(regular),
                "--batch",
                str(batch),
                "--train"]

    # helper function to evaluate the QoS
    def getQoS(self):
        X_train, y_train, X_test, y_test = load_CIFAR10(self.data_path)

        X_test = np.reshape(X_test, (X_test.shape[0], -1))
        X_train = np.reshape(X_train, (X_train.shape[0], -1))

        mean_image = np.mean(X_train, axis=0)

        X_test -= mean_image
        X_test = np.hstack([X_test, np.ones((X_test.shape[0], 1))])
        svm = LinearSVM()
        svm.W = pickle.load(open("./model_svm.p", "rb"))
        y_test_pred = svm.predict(X_test)
        test_accuracy = np.mean(y_test == y_test_pred)
        print test_accuracy
        return test_accuracy
