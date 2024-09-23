from wordleGames import *
from math import log2
from multiprocessing import Pool
from functools import reduce
import time

''' Entropy Based Wordle Completion Model '''

class EntropyWordleCompletion(BasicWordleCompletion):
    '''Simulates a wordle game given the correct answer and tries to minimize the number of guesses by calculating possible guesses' entropies.
       Don't instantiate this class within this file or it may screw up the multithreading abilities. '''

    use_threads: bool
    '''True if we should multithread for calculating the entropies. Defaults to `True` but is unnecessary for small dictionaries of words'''

    def __init__(self, solution: str, multithread: bool = True, file_name: str = "WordleWords.txt") -> None:
        self.use_threads = multithread
        super().__init__(solution, file_name)
        return

    def _getPossibleColorings(self) -> list[list[int]]:
        '''Returns an array of possible colorings if the option were to be guessed'''
        
        possible_results = [[]]

        for i in range(5):
            next_colors = []
            for color_combo in possible_results:
                if len(self.remaining_map[i]) == 1:
                    next_colors.append(color_combo + [LetterResultOptions.Green])
                else:
                    next_colors.append(color_combo + [LetterResultOptions.Green])
                    next_colors.append(color_combo + [LetterResultOptions.Yellow])
                    next_colors.append(color_combo + [LetterResultOptions.Grey])
            
            possible_results = next_colors[:]

        return possible_results

    def _calcEntropy(self, wordle_option: WordleOption, result: list[int]) -> float:
        ''' Given a `wordle_option` as a guess and the list of colors from that guess in `result`, calculate the information entropy we would gain '''
        filtered_options = WordleUtils.filter(self.remaining_options, self.remaining_map, wordle_option, result)
        P = len(filtered_options) / len(self.remaining_options)
        
        if P == 0:
            return 0.0
        return -P * log2(P)
    
    def _getEntropiesForRemaining(self) -> list[tuple[WordleOption, float]]:
        entropies = []

        if self.use_threads:
            with Pool() as pool:
                entropies = pool.map(getEntropy, [(self, wo) for wo in self.remaining_options]) 
        else:
            entropies = [getEntropy((self, wo)) for wo in self.remaining_options]
        
        return entropies

    def _getNextGuess(self) -> WordleOption:
        # start timer
        start = time.perf_counter()
        
        entropies = self._getEntropiesForRemaining()
        next_guess, next_entropy = None, -1
        
        for wordle_option, entropy in entropies:
            if entropy > next_entropy:
                next_entropy = entropy
                next_guess = wordle_option

        # end timer
        finish = time.perf_counter()
        # print('Entropy calculations took {} seconds'.format(finish - start))

        # safety 
        if not next_guess:
            next_guess = WordleOption("aaaaa")

        print(next_guess.word, next_entropy)
        return next_guess


''' Static Helper Methods '''

def isValidColoring(word: str, coloring: list[int]) -> bool:
    '''Checks if for a given word the coloring shouldn't be possible. Currently only ensures yellow colors come earlier in the word'''
    yellows = set()
    for char, color in list(zip(word, coloring))[::-1]:
        if char in yellows and color == LetterResultOptions.Grey:
            return False
        if color == LetterResultOptions.Yellow:
            yellows.add(char)
    return True

def getEntropy(args: tuple['EntropyWordleCompletion', WordleOption]) -> tuple[WordleOption, float]:
    '''Returns the average entropy for a given wordle guess during a given wordle game'''
    current_game, wordle_option = args

    possible_results = current_game._getPossibleColorings()

    entropy = 0.0
    for res in possible_results:
        if not isValidColoring(wordle_option.word, res):
            continue
        entropy += current_game._calcEntropy(wordle_option, res)

    return (wordle_option, entropy)