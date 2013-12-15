#!/usr/bin/python2
# -*- coding: utf-8 -*-
# $File: pygmm.py
# $Date: Sun Dec 15 14:55:42 2013 +0000
# $Author: Xinyu Zhou <zxytim[at]gmail[dot]com>

from ctypes import *
import os
from os import path
from numpy import array


dirname = path.dirname(path.abspath(__file__))

pygmm = cdll.LoadLibrary(path.join(dirname, '../lib/pygmm.so'))

class GMMParameter(Structure):
    _fields_ = [("nr_instance", c_int),
            ("nr_dim", c_int),
            ("nr_mixture", c_int),
            ("min_covar", c_double),
            ("nr_iteration", c_int),
            ("concurrency", c_int)]

#pygmm.train_model.argtypes = [c_char_p, POINTER(POINTER(c_double)), POINTER(GMMParameter)]
pygmm.score_all.restype = c_double
pygmm.score_instance.restype = c_double

for num, var in enumerate(['COVTYPE_SPHEREICAL', 'COVTYPE_DIAGONAL',
    'COVTYPE_FULL']):
    exec("{} = {}" . format(var, num))

class GMM(object):
    def __init__(self, nr_mixture = 10,
            covariance_type = COVTYPE_DIAGONAL,
            min_covar = 1e-3,
            nr_iteration = 200,
            concurrency = 8):
        self.nr_mixture = nr_mixture
        self.min_covar = min_covar
        self.nr_iteration = nr_iteration
        self.concurrency = concurrency
        self.covariance_type = covariance_type

        self.gmm = pygmm.new_gmm(c_int(nr_mixture), c_int(covariance_type))


    def _fill_param_from_model_file(self, model_file):
        with open(model_file) as f:
            self.nr_mixture = int(f.readline().rstrip())

    @staticmethod
    def load(model_file):
        gmm = GMM()
        gmm._fill_param_from_model_file(model_file)
        gmm.gmm = pygmm.load(c_char_p(model_file))
        return gmm

    def dump(self, model_file):
        pygmm.dump(self.gmm, c_char_p(model_file))


    def _double_array_python_to_ctype(self, X_py):
        X_c = []
        for x in X_py:
            xs = (c_double * len(x))(*x)
            X_c.append(xs)
        X_c = (POINTER(c_double) * len(X_c))(*X_c)
        return X_c

    def _gen_param(self, X):
        param = GMMParameter()
        param.nr_mixture = c_int(self.nr_mixture)
        param.min_covar = c_double(self.min_covar)
        param.nr_iteration = c_int(self.nr_iteration)
        param.concurrency = c_int(self.concurrency)
        param.nr_instance = c_int(len(X))
        param.nr_dim = c_int(len(X[0]))
        return param

    def fit(self, X):
        X_c = self._double_array_python_to_ctype(X)
        param = self._gen_param(X)
        param_ptr = pointer(param)
        pygmm.train_model(self.gmm, X_c, param_ptr)

    def score(self, X):
        X_c = self._double_array_python_to_ctype(X)
        param = self._gen_param(X)
        prob = (c_double * len(X))(*([0.0] * len(X)))
        pygmm.score_batch(self.gmm, X_c, prob, param.nr_instance, param.nr_dim, \
                param.concurrency)
        return array(list(prob))


# vim: foldmethod=marker

