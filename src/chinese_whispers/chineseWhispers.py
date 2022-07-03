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
        # go up/down/stay
        if prop < PROB_FOR_ONE_WORD_DOWN: # go one word up in word list
            return line[(index - 1) % len(line)] # use modulo to implement the list as ring
        elif prop >= PROB_FOR_ONE_WORD_DOWN and prop < PROB_FOR_SAME_WORD: # stay at same position in word list
            return line[index]
        else: # go one word up in word list
            return line[(index + 1) % len(line)] # use modulo to implement the list as ring
        # pass word to neighbour
        pass

    def findWordInWordList(self, word):
        with open('../../data/Rhymes.csv', mode ='r')as file:
            csvFile = csv.reader(file)
            lines_with_word = [] # Some words appear in more than one word list. Need to capture all of them
            for lines in csvFile:
                if (lines.__contains__(word)):
                    lines_with_word.append(lines)
            print(lines_with_word)
            try:
                return random.choice(lines_with_word) # Select a random word list that contains the word
            except IndexError:
                return None