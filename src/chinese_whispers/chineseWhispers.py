##
## @author bltzz
##
## This class holds the game logic for chinese whispers
## 
##

#imports
import random
import csv

#class def
POINTS_FOR_CORRECT_ANSWER = 10
PROB_FOR_ONE_WORD_DOWN = 0.33
PROB_FOR_SAME_WORD = 0.66
PROB_FOR_ONE_WORD_UP = 1

class ChineseWhispers:

    def __init__(self, uuid):
        self.uuid = uuid
        self.word_understood = ""
    
    def listenToNeighbour(self, word_spoken):
        self.word_understood = word_spoken
        pass

    def tellWordToNeighbour(self, word_understood):
        prop = random.random()
        #print(prop)
        # find word in list
        line = self.findWordInWordList(word_understood)
        if line == None:
            return None
        index = line.index(word_understood)
        # go up/down / stay
        if index == 0:
            if prop < PROB_FOR_ONE_WORD_DOWN:
                return line[len(line) - 1]
            elif prop >= PROB_FOR_ONE_WORD_DOWN and prop < PROB_FOR_SAME_WORD:
                return line[0]
            else:
                return line[1]
        elif index == len(line) - 1:
            if prop < PROB_FOR_ONE_WORD_DOWN:
                return line[index - 1]
            elif prop >= PROB_FOR_ONE_WORD_DOWN and prop < PROB_FOR_SAME_WORD:
                return line[index]
            else:
                return line[0]
        else:
            if prop < PROB_FOR_ONE_WORD_DOWN:
                return line[index - 1]
            elif prop >= PROB_FOR_ONE_WORD_DOWN and prop < PROB_FOR_SAME_WORD:
                return line[index]
            else:
                return line[index + 1]
        # pass word to neighbour
        pass

    def findWordInWordList(self, word):
        with open('../../data/Rhymes.csv', mode ='r')as file:
            csvFile = csv.reader(file)
            for lines in csvFile:
                if (lines.__contains__(word)):
                    return lines
    