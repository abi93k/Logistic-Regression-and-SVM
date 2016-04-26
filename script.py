import numpy as np
import numpy.matlib
from scipy.io import loadmat
from scipy.optimize import minimize
from scipy.misc import logsumexp
from sklearn.svm import SVC
import pickle

def preprocess():
    """ 
     Input:
     Although this function doesn't have any input, you are required to load
     the MNIST data set from file 'mnist_all.mat'.

     Output:
     train_data: matrix of training set. Each row of train_data contains 
       feature vector of a image
     train_label: vector of label corresponding to each image in the training
       set
     validation_data: matrix of training set. Each row of validation_data 
       contains feature vector of a image
     validation_label: vector of label corresponding to each image in the 
       training set
     test_data: matrix of training set. Each row of test_data contains 
       feature vector of a image
     test_label: vector of label corresponding to each image in the testing
       set
    """

    mat = loadmat('mnist_all.mat')  # loads the MAT object as a Dictionary

    n_feature = mat.get("train1").shape[1]
    n_sample = 0
    for i in range(10):
        n_sample = n_sample + mat.get("train" + str(i)).shape[0]
    n_validation = 1000
    n_train = n_sample - 10 * n_validation

    # Construct validation data
    validation_data = np.zeros((10 * n_validation, n_feature))
    for i in range(10):
        validation_data[i * n_validation:(i + 1) * n_validation, :] = mat.get("train" + str(i))[0:n_validation, :]

    # Construct validation label
    validation_label = np.ones((10 * n_validation, 1))
    for i in range(10):
        validation_label[i * n_validation:(i + 1) * n_validation, :] = i * np.ones((n_validation, 1))

    # Construct training data and label
    train_data = np.zeros((n_train, n_feature))
    train_label = np.zeros((n_train, 1))
    temp = 0
    for i in range(10):
        size_i = mat.get("train" + str(i)).shape[0]
        train_data[temp:temp + size_i - n_validation, :] = mat.get("train" + str(i))[n_validation:size_i, :]
        train_label[temp:temp + size_i - n_validation, :] = i * np.ones((size_i - n_validation, 1))
        temp = temp + size_i - n_validation

    # Construct test data and label
    n_test = 0
    for i in range(10):
        n_test = n_test + mat.get("test" + str(i)).shape[0]
    test_data = np.zeros((n_test, n_feature))
    test_label = np.zeros((n_test, 1))
    temp = 0
    for i in range(10):
        size_i = mat.get("test" + str(i)).shape[0]
        test_data[temp:temp + size_i, :] = mat.get("test" + str(i))
        test_label[temp:temp + size_i, :] = i * np.ones((size_i, 1))
        temp = temp + size_i

    # Delete features which don't provide any useful information for classifiers
    sigma = np.std(train_data, axis=0)
    index = np.array([])
    for i in range(n_feature):
        if (sigma[i] > 0.001):
            index = np.append(index, [i])
    train_data = train_data[:, index.astype(int)]
    validation_data = validation_data[:, index.astype(int)]
    test_data = test_data[:, index.astype(int)]

    # Scale data to 0 and 1
    train_data /= 255.0
    validation_data /= 255.0
    test_data /= 255.0

    return train_data, train_label, validation_data, validation_label, test_data, test_label


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))

def softmax(z):
   numerator = np.exp(z);
   denominator = np.sum(numerator,axis=1);
   denominator = denominator.reshape((numerator.shape[0],1))
   return numerator/denominator;

def blrObjFunction(initialWeights, *args):
    """
    blrObjFunction computes 2-class Logistic Regression error function and
    its gradient.

    Input:
        initialWeights: the weight vector (w_k) of size (D + 1) x 1 
        train_data: the data matrix of size N x D
        labeli: the label vector (y_k) of size N x 1 where each entry can be either 0 or 1 representing the label of corresponding feature vector

    Output: 
        error: the scalar value of error function of 2-class logistic regression
        error_grad: the vector of size (D+1) x 1 representing the gradient of
                    error function
    """
    train_data, labeli = args

    n_data = train_data.shape[0]
    n_features = train_data.shape[1]
    error = 0
    error_grad = np.zeros((n_features + 1, 1))

    w = initialWeights.reshape((n_features+1,1))

    x = np.hstack((np.ones((n_data,1)),train_data))
    theta = sigmoid(np.dot(x,w))

    error = labeli * np.log(theta) + (1.0 - labeli) * np.log(1.0 - theta)
    error = -1 * np.sum(error)
    error = error/n_data

    error_grad = (theta - labeli) * x
    error_grad = np.sum(error_grad, axis=0)/n_data

    return error, error_grad


def blrPredict(W, data):
    """
     blrObjFunction predicts the label of data given the data and parameter W 
     of Logistic Regression
     
     Input:
         W: the matrix of weight of size (D + 1) x 10. Each column is the weight 
         vector of a Logistic Regression classifier.
         X: the data matrix of size N x D
         
     Output: 
         label: vector of size N x 1 representing the predicted label of 
         corresponding feature vector given in data matrix

    """

    n_data = data.shape[0];

    label = np.zeros((n_data, 1))

    x = np.hstack((np.ones((n_data, 1)),data))

    label = sigmoid(np.dot(x, W))
    label = np.argmax(label, axis=1)
    label = label.reshape((n_data,1))

    return label


def mlrObjFunction(params, *args):
    """
    mlrObjFunction computes multi-class Logistic Regression error function and
    its gradient.

    Input:
        initialWeights: the weight vector of size (D + 1) x 1
        train_data: the data matrix of size N x D
        labeli: the label vector of size N x 1 where each entry can be either 0 or 1
                representing the label of corresponding feature vector

    Output:
        error: the scalar value of error function of multi-class logistic regression
        error_grad: the vector of size (D+1) x 10 representing the gradient of
                    error function
    """
    train_data, labeli = args

    n_data = train_data.shape[0]
    n_feature = train_data.shape[1]
    error = 0
    error_grad = np.zeros((n_feature + 1, n_class))

    w = params.reshape((n_feature+1,n_class))

    x = np.hstack((np.ones((n_data,1)),train_data))

    theta = softmax(np.dot(x,w))

    error = np.sum(labeli*np.log(theta))
    error = (-1.0) * error
    error = (error/x.shape[0])

    error_grad = np.subtract(theta,labeli)
    error_grad = np.dot(error_grad.T,x).T
    error_grad = error_grad/n_data
    error_grad = error_grad.flatten()
    
    return error, error_grad

def mlrPredict(W, data):
    """
     mlrObjFunction predicts the label of data given the data and parameter W
     of Logistic Regression

     Input:
         W: the matrix of weight of size (D + 1) x 10. Each column is the weight
         vector of a Logistic Regression classifier.
         X: the data matrix of size N x D

     Output:
         label: vector of size N x 1 representing the predicted label of
         corresponding feature vector given in data matrix

    """
    label = np.zeros((data.shape[0], 1))
    n_data = data.shape[0];

    x = np.hstack((np.ones((n_data, 1)),data))

    theta = softmax(np.dot(x,W))

    label = np.argmax(theta,axis=1);
    label = label.reshape((n_data,1))
    
    return label

"""
Script for Logistic Regression
"""
print('\n\n--------------BLR-------------------\n\n')

train_data, train_label, validation_data, validation_label, test_data, test_label = preprocess()

# number of classes
n_class = 10

# number of training samples
n_train = train_data.shape[0]

# number of features
n_feature = train_data.shape[1]

Y = np.zeros((n_train, n_class))
for i in range(n_class):
    Y[:, i] = (train_label == i).astype(int).ravel()

W = pickle.load(open('params.pickle', 'rb'))
# Find the accuracy on Training Dataset
predicted_label = blrPredict(W, train_data)
print('Training set Accuracy:' + str(100 * np.mean((predicted_label == train_label).astype(float))) + '%')

# Find the accuracy on Validation Dataset
predicted_label = blrPredict(W, validation_data)
print('Validation set Accuracy:' + str(100 * np.mean((predicted_label == validation_label).astype(float))) + '%')

# Find the accuracy on Testing Dataset
predicted_label = blrPredict(W, test_data)
print('Testing set Accuracy:' + str(100 * np.mean((predicted_label == test_label).astype(float))) + '%')

"""
Script for Support Vector Machine


print('\n\n--------------SVM-------------------\n\n')

flatten_train_label=train_label.flatten()

print("\nLinear Kernel \n")

clf=SVC(kernel="linear")
clf.fit(train_data,flatten_train_label)
train_acc=clf.score(train_data, train_label)
val_acc=clf.score(validation_data,validation_label)
test_acc=clf.score(test_data, test_label)
print('Training set Accuracy:' + str(100 * train_acc) + '%')
print('Validation set Accuracy:' + str(100 * val_acc) + '%')
print('Testing set Accuracy:' + str(100 * test_acc) + '%')

print("\nRBF Kernel - Gamma = 1 \n")

clf=SVC(gamma=1)
clf.fit(train_data,flatten_train_label)
train_acc=clf.score(train_data, train_label)
val_acc=clf.score(validation_data,validation_label)
test_acc=clf.score(test_data, test_label)
print('Training set Accuracy:' + str(100 * train_acc) + '%')
print('Validation set Accuracy:' + str(100 * val_acc) + '%')
print('Testing set Accuracy:' + str(100 * test_acc) + '%')

print("\nRBF Kernel - Gamma = 0 \n")

clf=SVC()
clf.fit(train_data,flatten_train_label)
train_acc=clf.score(train_data, train_label)
val_acc=clf.score(validation_data,validation_label)
test_acc=clf.score(test_data, test_label)
print('Training set Accuracy:' + str(100 * train_acc) + '%')
print('Validation set Accuracy:' + str(100 * val_acc) + '%')
print('Testing set Accuracy:' + str(100 * test_acc) + '%')

c_list = [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

for c in c_list:    
    print("\nRBF Kernel - Gamma = 0 & C = "+str(c)+" \n")
    clf=SVC(C=c)
    clf.fit(train_data,flatten_train_label)
    train_acc=clf.score(train_data, train_label)
    val_acc=clf.score(validation_data,validation_label)
    test_acc=clf.score(test_data, test_label)
    print('Training set Accuracy:' + str(100 * train_acc) + '%')
    print('Validation set Accuracy:' + str(100 * val_acc) + '%')
    print('Testing set Accuracy:' + str(100 * test_acc) + '%')
"""
"""
Script for Extra Credit Part
"""
print('\n\n--------------MLR-------------------\n\n')

# FOR EXTRA CREDIT ONLY

W_b = pickle.load(open('params_bonus.pickle', 'rb'))

# Find the accuracy on Training Dataset
predicted_label_b = mlrPredict(W_b, train_data)
print('Training set Accuracy:' + str(100 * np.mean((predicted_label_b == train_label).astype(float))) + '%')

# Find the accuracy on Validation Dataset
predicted_label_b = mlrPredict(W_b, validation_data)
print('Validation set Accuracy:' + str(100 * np.mean((predicted_label_b == validation_label).astype(float))) + '%')

# Find the accuracy on Testing Dataset
predicted_label_b = mlrPredict(W_b, test_data)
print('Testing set Accuracy:' + str(100 * np.mean((predicted_label_b == test_label).astype(float))) + '%')

