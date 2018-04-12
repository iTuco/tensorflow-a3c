#!/usr/bin/env python3

import unittest

import numpy as np
import tensorflow as tf

from utils import create_copy_ops, entropy, rewards_to_discounted_returns


class TestMiscUtils(unittest.TestCase):

    def test_returns_easy(self):
        r = [0, 0, 0, 5]
        discounted_r = rewards_to_discounted_returns(r, discount_factor=0.99)
        np.testing.assert_array_almost_equal(discounted_r,
                                             [0.99 ** 3 * 5,
                                              0.99 ** 2 * 5,
                                              0.99 ** 1 * 5,
                                              0.99 ** 0 * 5])

    def test_returns_hard(self):
        r = [1, 2, 3, 4]
        discounted_r = rewards_to_discounted_returns(r, discount_factor=0.99)
        expected = [1 + 0.99 * 2 + 0.99 ** 2 * 3 + 0.99 ** 3 * 4,
                    2 + 0.99 * 3 + 0.99 ** 2 * 4,
                    3 + 0.99 * 4,
                    4]
        np.testing.assert_array_almost_equal(discounted_r, expected)


class TestEntropy(unittest.TestCase):

    def setUp(self):
        self.sess = tf.Session()

    def test_basic(self):
        logits = [1., 2., 3., 4.]
        probs = np.exp(logits) / np.sum(np.exp(logits))
        expected_entropy = -np.sum(probs * np.log(probs))
        actual_entropy = self.sess.run(entropy(logits))
        np.testing.assert_approx_equal(actual_entropy, expected_entropy,
                                       significant=4)

    def test_batch(self):
        # shape is 2 (batch size) x 4
        logits = [[1., 2., 3., 4.],
                  [1., 2., 2., 1.]]
        probs = np.exp(logits) / np.sum(np.exp(logits), axis=1, keepdims=True)
        expected_entropy = -np.sum(probs * np.log(probs), axis=1, keepdims=True)
        actual_entropy = self.sess.run(entropy(logits))
        np.testing.assert_allclose(actual_entropy, expected_entropy, atol=1e-4)

    def test_gradient_descent(self):
        logits = tf.Variable([1., 2., 3., 4., 5.])
        neg_ent = -entropy(logits)
        train_op = tf.train.AdamOptimizer().minimize(neg_ent)
        self.sess.run(tf.global_variables_initializer())
        for i in range(10000):
            self.sess.run(train_op)
        expected = [0.2, 0.2, 0.2, 0.2, 0.2]  # maximum entropy distribution
        actual = self.sess.run(tf.nn.softmax(logits))
        np.testing.assert_allclose(actual, expected, atol=1e-4)


class TestCopyNetwork(unittest.TestCase):

    def test(self):
        sess = tf.Session()

        inits = {}
        inits['from_scope'] = {}
        inits['to_scope'] = {}
        inits['from_scope']['w1'] = np.array([1.0, 2.0]).astype(np.float32)
        inits['from_scope']['w2'] = np.array([3.0, 4.0]).astype(np.float32)
        inits['to_scope']['w1'] = np.array([5.0, 6.0]).astype(np.float32)
        inits['to_scope']['w2'] = np.array([7.0, 8.0]).astype(np.float32)

        scopes = ['from_scope', 'to_scope']

        variables = {}
        for scope in scopes:
            with tf.variable_scope(scope):
                w1 = tf.Variable(inits[scope]['w1'], name='w1')
                w2 = tf.Variable(inits[scope]['w2'], name='w2')
                variables[scope] = {'w1': w1, 'w2': w2}
        copy_ops = create_copy_ops(from_scope='from_scope', to_scope='to_scope')

        sess.run(tf.global_variables_initializer())

        """
        Check that the variables start off being what we expect them to.
        """
        for scope in scopes:
            for var_name, var in variables[scope].items():
                actual = sess.run(var)
                if 'w1' in var_name:
                    expected = inits[scope]['w1']
                elif 'w2' in var_name:
                    expected = inits[scope]['w2']
                np.testing.assert_equal(actual, expected)

        sess.run(copy_ops)

        """
        Check that the variables in from_scope are untouched.
        """
        for var_name, var in variables['from_scope'].items():
            actual = sess.run(var)
            if 'w1' in var_name:
                expected = inits['from_scope']['w1']
            elif 'w2' in var_name:
                expected = inits['from_scope']['w2']
            np.testing.assert_equal(actual, expected)

        """
        Check that the variables in to_scope have been modified.
        """
        for var_name, var in variables['to_scope'].items():
            actual = sess.run(var)
            if 'w1' in var_name:
                expected = inits['from_scope']['w1']
            elif 'w2' in var_name:
                expected = inits['from_scope']['w2']
            np.testing.assert_equal(actual, expected)


if __name__ == '__main__':
    unittest.main()
