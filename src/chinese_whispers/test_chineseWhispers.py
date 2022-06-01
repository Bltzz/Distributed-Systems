##
## @author bltzz
##
## This class holds the unittests for chinese whispers
## 
##

import unittest
from chineseWhispers import ChineseWhispers

class TestChineseWhispers(unittest.TestCase):
    
    def test_findWordInWordList(self):
        game = ChineseWhispers(123)
        res = game.findWordInWordList("fan")
        self.assertEqual(res, ["man","fan","pan","van","can"])
        res = game.findWordInWordList("Ben")
        self.assertEqual(res, ["bet","bed","Ben","be"])

    def test_tellWordToNeighbour(self):
        game = ChineseWhispers(123)
        res = game.tellWordToNeighbour("not_in_list")
        self.assertEqual(res, None)
        res = game.tellWordToNeighbour("lad")
        self.assertIn(res,["lad","sad","mad"])
        res = game.tellWordToNeighbour("lag")
        self.assertIn(res,["lag","rag","bag"])
        res = game.tellWordToNeighbour("sat")
        self.assertIn(res,["sad","sat","sag"])

    def test_listenToNeighbour(self):
        game = ChineseWhispers(123)
        game.listenToNeighbour("ThisIsATest")
        self.assertEqual(game.word_understood, "ThisIsATest")