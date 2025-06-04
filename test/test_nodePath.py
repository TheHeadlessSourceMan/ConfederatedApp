"""
Unit tests for the TestNodePaths
"""
import unittest
from ConfederatedApp import NodePath


class TreeNode:
    """
    A generic tree for testing
    """
    def __init__(self,name:str):
        self.name=name
        self.parent=None
        self.root=self
        self.children=[]

    def add_child(self,child):
        """
        Add a child node to the tree
        """
        child.parent=self
        child.root=self.root
        self.children.append(child)


class TestNodePaths(unittest.TestCase): # pylint: disable=no-member
    """
    Unit tests for the TestNodePaths
    """

    def setUp(self)->None:
        """
        Configure the tests
        """
        self.root=TreeNode("home")
        self.user1=TreeNode("user1")
        self.data=TreeNode("data")
        self.thing=TreeNode("thing")
        self.file1=TreeNode("file1.exe")
        self.file2=TreeNode("file2.dll")
        # link em up
        self.root.add_child(self.user1)
        self.user1.add_child(self.data)
        self.data.add_child(self.thing)
        self.thing.add_child(self.file1)
        self.thing.add_child(self.file2)

    def test_glob_all_exe_files(self):
        """
        Test wildcards like *.exe
        """
        np=NodePath('user1/data/thing/*.exe')
        results1=list(np.search(self.root))
        self.assertEqual(results1[0],self.file1)

    def test_simple_relative_path(self):
        """
        Test basic path navigation
        """
        np=NodePath('user1/data/thing/file1.exe')
        results1=list(np.search(self.root))
        self.assertEqual(results1[0],self.file1)
        np=NodePath('../file2.dll')
        results2=list(np.search(results1))
        self.assertEqual(results2[0],self.file2)
        np=NodePath('/user1/data/thing/file1.exe')
        results3=list(np.search(results2))
        self.assertEqual(results3[0],self.file1)

if __name__=="__main__":
    unittest.main() # pylint: disable=no-member
