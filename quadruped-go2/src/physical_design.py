import numpy as np

MATRIX_P = np.array([[140.6434, 0, 0, 0, 0, 0, 5.3276, 0, 0, 0],
                     [0, 134.7596, 0, 0, 0, 0, 0, 6.6219, 0, 0],
                     [0, 0, 134.7596, 0, 0, 0, 0, 0, 6.622, 0],
                     [0, 0, 0, 49.641, 0, 0, 0, 0, 0, 6.8662],
                     [0, 0, 0, 0, 11.1111, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 3.3058, 0, 0, 0, 0],
                     [5.3276, 0, 0, 0, 0, 0, 3.6008, 0, 0, 0],
                     [0, 6.6219, 0, 0, 0, 0, 0, 3.6394, 0, 0],
                     [0, 0, 6.622, 0, 0, 0, 0, 0, 3.6394, 0],
                     [0, 0, 0, 6.8662, 0, 0, 0, 0, 0, 4.3232]])

bP = np.array([[140.1190891, 0, 0, -0, -0, 0, 3.7742345, -0, 0, -0],
               [0, 2.3e-06, 0, -0, -0, 0, 0, 1.4e-06, 0, 0],
               [0, 0, 2.3e-06, 0, -0, 0, 0, 0, 1.4e-06, 0],
               [-0, -0, 0, 467.9872184, 0, -0, -0, -0, 0, 152.9259161],
               [-0, -0, -0, 0, 2.9088242, 0, -0, -0, -0, 0],
               [0, 0, 0, -0, 0, 1.9e-06, -0, 0, 0, -0],
               [3.7742345, 0, 0, -0, -0, -0, 0.3773971, 0, 0, -0],
               [-0, 1.4e-06, 0, -0, -0, 0, 0, 1e-06, 0, -0],
               [0, 0, 1.4e-06, 0, -0, 0, 0, 0, 1e-06, 0],
               [-0, 0, 0, 152.9259161, 0, -0, -0, -0, 0, 155.2407021]]) * 1

DEFAULT_KP = np.array([[0, 0, 0, 0, 0, 0],
                       [0, 0, 0, 0, 0, 0],
                       [0, 0, 128, 0, 0, 0],
                       [0, 0, 0, 83, -25, -2],
                       [0, 0, 0, -33, 80, 2],
                       [0, 0, 0, 1, 0, 80]])

DEFAULT_KD = np.array([[39, 0, 0, 0, 0, 0],
                       [0, 35, 0, 0, 0, 0],
                       [0, 0, 35, 0, 0, 0],
                       [0, 0, 0, 37, -1, -9],
                       [0, 0, 0, -1, 37, 9],
                       [0, 0, 0, 0, 0, 40]])

