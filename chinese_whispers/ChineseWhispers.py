##
## @author bltzz
##
## This class holds the game logic for chinese whispers
## 
##

#imports
import random

#class def

class ChineseWhispers:
    POINTS_FOR_CORRECT_ANSWER = 10
    PROB_FOR_ONE_WORD_DOWN = 0.33
    PROB_FOR_SAME_WORD = 0.66
    PROB_FOR_ONE_WORD_UP = 1

    def __init__(self, uuid):
        self.uuid = uuid
        self.word_understood = ""
    
    def listenToNeighbour(self, word_spoken):
        self.word_understood = word_spoken
        pass

    def tellWordToNeighbour(self):
        prop = random.random()
        # find word in list
        # go one up/down / stay
        # pass word to neighbour
        pass

    def findWordInWordList(self, word):


if __name__ == "__main__":
    game = ChineseWhispers(123)
    game.tellWordToNeighbour()
    