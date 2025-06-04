"""
Unit tests for the FunctionCallManager
"""
import unittest
import time
from ConfederatedApp import FunctionCallManager


def thread_safe_add(a:int,b:int)->int:
    """
    Basic, simple target test function
    """
    return a+b


def thread_safe_raise()->None:
    """
    Target test function to test exceptions.
    """
    raise ValueError("Intentional thread exception")


def process_safe_multiply(a:int,b:int)->int:
    """
    Basic, simple target test function
    """
    time.sleep(0.1)
    return a*b


def process_safe_raise()->None:
    """
    Target test function to test exceptions.
    """
    raise RuntimeError("Intentional process exception")


class TestFunctionCallManager(unittest.TestCase): # pylint: disable=no-member
    """
    Unit tests for the FunctionCallManager
    """

    def setUp(self)->None:
        """
        Configure the tests
        """
        self.manager=FunctionCallManager(num_threads=2,num_processes=2)
        self.manager.addFunction(
            thread_safe_add,'add',threadsafe=True)
        self.manager.addFunction(
            thread_safe_raise,'raise_thread',threadsafe=True)
        self.manager.addFunction(
            process_safe_multiply,'multiply',threadsafe=False)
        self.manager.addFunction(
            process_safe_raise,'raise_process',threadsafe=False)

    def test_threadsafe_function(self)->None:
        """
        Test a threadsafe(multiprocessing) function
        """
        result=self.manager.call("add",[2,3],{})
        self.assertEqual(result,5)

    def test_threadsafe_exception(self)->None:
        """
        Test a threadsafe(multiprocessing) function
        that raises an exception
        """
        with self.assertRaises(ValueError) as context:
            self.manager.call("raise_thread",[],{})
        self.assertEqual(str(context.exception),"Intentional thread exception")

    def test_processsafe_function(self)->None:
        """
        Test a threadsafe(threading) function
        """
        result=self.manager.call("multiply",[4,5],{})
        self.assertEqual(result,20)

    def test_processsafe_exception(self)->None:
        """
        Test a threadsafe(threading) function
        that raises an exception
        """
        with self.assertRaises(RuntimeError) as context:
            self.manager.call("raise_process",[],{})
        self.assertIn("Intentional process exception",str(context.exception))

    def test_parallel_calls(self)->None:
        """
        Test function calls happening in parallel
        """
        results=[]
        for i in range(10):
            if i%2==0:
                results.append(self.manager.call("add",[i,i+1],{}))
            else:
                results.append(self.manager.call("multiply",[i,i+2],{}))
        expected=[1,3,5,15,9,35,13,63,17,99]
        self.assertEqual(results,expected)


if __name__=="__main__":
    unittest.main() # pylint: disable=no-member
