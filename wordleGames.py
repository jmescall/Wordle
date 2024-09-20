from collections import Counter
import fileAccess
from multiprocessing import Pool

class LetterResultOptions:
    '''Enums for the different colors which appear after a wordle guess'''
    Grey = 0
    Yellow = 1
    Green = 2

class WordleOption:
    '''An object to represent a possible guess/solution to a wordle puzzle'''
    
    word: str
    '''The word that is guessed'''

    letters: dict[str, int]
    '''The frequencies of letters in `word`, useful for repeated calculations'''

    def __init__(self, word: str) -> None:
        self.word = word
        self.letters = Counter(word)
        return

class GuessResult:
    '''Result of a guess during a wordle game'''

    guess: WordleOption
    '''The `WordleOption` object representing what was guessed'''

    result: list[int]
    '''List of `LetterResultOption` enum values representing the result of the guess'''

    def __init__(self, guess: WordleOption, result: list[int]) -> None:
        self.guess = guess
        self.result = result.copy()
        return

class WordleGame:
    '''The base wordle game which will naively guess what could be a valid solution and a user must enter the colors resulting from each guess.'''

    guessed_letters = list[str | None]
    '''List we build with the correct letters based on the current game'''
    
    wrong_placed_letters = list[set[str]]
    '''Sets of letters which are in the word, but not valid for a given place in the solution'''
    
    remaining_options = set[WordleOption] 
    '''Set of wordle options which could be the solution to the current game'''
    
    guess_results: list[GuessResult] 
    '''List of guesses and their results'''

    bad_letters = set[str]
    '''Set of letters which do not appear in the wordle solution at all'''

    def __init__(self) -> None:
        # Set up the trackers
        self.guessed_letters = [None for _ in range(5)]
        self.wrong_placed_letters = [set() for _ in range(5)]
        self.guess_results = []
        self.bad_letters = set()

        # Store all of the possible words to guess
        if not self._storeOptions():
            return

        return

    def _storeOptions(self) -> bool:
        ''' Iterate through the valid wordle guesses file and store each word in `self.remaining_options` '''
        self.remaining_options = set()

        try: # read from the current directory of the file
            file = open(fileAccess.sameDirFilePath("WordleWords.txt"), "r") 
        except:
            print("No options to guess from. Quiting...")
            return False

        for word in file:
            option = word.strip("\n")
            self.remaining_options.add(WordleOption(option))
        
        return True

    def filterOptions(self, guessed_counts: dict[str, int], result_counts: dict[str]) -> None:
        ''' Filters the current game's `remaining_options` based off the last guess and its results.
        :param guessed_counts: Frequencies of letters in the last guess
        :param result_counts: Frequencies of letters in the solution based off the last guess
        '''
    
        for option in list(self.remaining_options):
            if not WordleUtils._isValidOption(option, guessed_counts, result_counts, self.guessed_letters, self.wrong_placed_letters, self.bad_letters):
                self.remaining_options.remove(option)
        
        return

    def playGame(self) -> None:
        ''' Let the current model play Wordle. '''

        while len(self.guess_results) < 6:
            next_guess = self._getNextGuess()
            results = self._submitGuess(next_guess)
            self.guess_results.append(GuessResult(next_guess, results))

            # If the whole array is greens, we are done
            if Counter(results).get(LetterResultOptions.Green, 0) == 5:
                print("We correctly guessed the wordle in " + str(len(self.guess_results)) + " guesses: " + next_guess.word)
                return

            self._updateOptions()
        
        print("We failed to guess the wordle correctly.")
        return

    def _getNextGuess(self) -> WordleOption:
        for option in self.remaining_options:
            return option
        return WordleOption("aaaaa") # safety
    
    def _submitGuess(self, next_guess: WordleOption) -> list[int]:
        ''' Defaults to printing the next guess to the screen and asking the user to input the colors for the previous guess.
            To be overridden to process automatically.'''
        
        # Say the guess and get the result
        print("Our next guess for the wordle solution is: " + next_guess.word)

        # Ask the user for how the last ouput guess did
        delimited_colors = input("Use the guess above and enter the colors delimited by a comma below. \n")
        
        # Replace the strings in the color array with the corresponding enum values
        color_str_array = delimited_colors.lower().split(",")
        # Convert the string values into the enum values
        color_int_array = [self._mapColorToEnum(color_str_array[i]) for i in range(len(color_str_array)) ]

        return color_int_array
    
    def _mapColorToEnum(self, color: str) -> int:
        ''' Takes in a color name and outputs the enum valeu for it
        :param color: 'green', 'yellow', or 'grey' '''

        if color == "green":
            return LetterResultOptions.Green
        
        if color == "yellow":
            return LetterResultOptions.Yellow
        
        return LetterResultOptions.Grey

    def _updateOptions(self) -> None:
        ''' Filters the game's remaining possible solutions based on the last guess's result'''

        # store the counts of letters it could be and where letters are
        word, res = self.guess_results[-1].guess.word, self.guess_results[-1].result
        result_counts = WordleUtils.updateCountsHelper(word, res, self.guessed_letters, self.wrong_placed_letters, self.bad_letters)
        
        # pass in the counts of the letters for which we guessed
        guessed_counts = self.guess_results[-1].guess.letters.copy()

        self.filterOptions(guessed_counts, result_counts)
        return

class WordleUtils:
    '''Utilities which can be used for most wordle games'''

    def updateCountsHelper(word: str, result: list[int], guessed_letters: list[str | None], wrong_placed_letters: list[set[str]], bad_letters: set[str]) -> dict[str: int]:
        '''Returns a dictionary of the results of a given guess. Note that this also modifies `guessed_letters`, `wrong_placed_letters`, and `bad_letters` appropriately.'''
        
        result_counts = {}

        for i, (char, color) in enumerate(zip(word, result)):
            if color == LetterResultOptions.Green:
                guessed_letters[i] = char 
                result_counts[char] = result_counts.get(char, 0) + 1
            elif color == LetterResultOptions.Yellow:
                wrong_placed_letters[i].add(char)
                result_counts[char] = result_counts.get(char, 0) + 1
            else:
                result_counts[char] = result_counts.get(char, 0)
        
        for char, count in result_counts.items():
            if count == 0:
                bad_letters.add(char)

        # update wrongly_placed_letters for cases where multiple of the same letter appear in the guess, but less than that appear in the solution
        for i, (char, color) in enumerate(zip(word, result)):
            if color == LetterResultOptions.Grey and result_counts[char] > 0:
                wrong_placed_letters[i].add(char)
        
        return result_counts

    def validateGuess(guess: WordleOption, solution: WordleOption) -> list[int]:
        ''' Takes a wordle option as a guess and a wordle option as a solution and returns a result array.
        '''
        results = [LetterResultOptions.Grey for _ in range(5)]
        sol_letters = solution.letters.copy()

        # One pass for the Greens
        for i in range(len(guess.word)):
            if solution.word[i] == guess.word[i]:
                results[i] = LetterResultOptions.Green
                sol_letters[guess.word[i]] -= 1
        
        # One pass for the Yellows
        for i in range(len(guess.word)):
            if results[i] == LetterResultOptions.Green: # safeguard against duplicate letters, don't overwrite green
                continue
            if guess.word[i] in sol_letters and sol_letters[guess.word[i]] > 0:
                results[i] = LetterResultOptions.Yellow
                sol_letters[guess.word[i]] -= 1

        return results
    
    def _isValidOption(
        option: WordleOption,
        guessed_counts: dict[str, int], 
        result_counts: dict[str], 
        guessed_letters: list[str | None],
        wrong_placed_letters: list[set[str]],
        bad_letters: set[str]) -> bool:
        ''' Returns true if the given wordle option could be a valid solution for the current game
        :param option: The wordle option to consider if it could be a valid solution
        :param guessed_counts: Frequencies of letters in the last guess
        :param result_counts: Frequencies of letters in the solution based off the last guess
        :param guessed_letters: A list populated with letters (guessed in the correct positions) or None
        :param wrong_placed_letters: A list of letters that exist in the solution, but not in the correct place
        :param bad_letters: A set of letters which do not exist in the solution at all '''
        
        for i, option_char in enumerate(option.word):
            # restrict the words to matching letters
            if option_char in bad_letters:
                return False
            if guessed_letters[i] and guessed_letters[i] != option_char:
                return False
            if option_char in wrong_placed_letters[i]:
                return False
            
            # remove words that have letter frequencies greater than that in the word
            if guessed_counts.get(option_char, 0) >= option.letters[option_char]:
                if result_counts[option_char] != option.letters[option_char]:
                    return False
            elif guessed_counts.get(option_char, 0) > 0:
                if result_counts[option_char] != guessed_counts[option_char]:
                    return False
        
        for char, count in result_counts.items():
            if count > 0 and char not in option.letters:
                return False
            
        # make sure the word contains the letters that were wrongly placed
        for i in range(5):
            for letter in wrong_placed_letters[i]:
                if letter not in option.letters:
                    return False
        
        return True
        
class AutoNaiveWordle(WordleGame):
    '''Wordle game which can be simulated by entering the solution, narrated through the terminal.'''
    
    solution: WordleOption
    ''' The solution to the wordle game. Not looked at when making guesses'''

    def playGame(self) -> None:
        sol = input("Please enter the solution to the wordle for the computer to play below \n")
        
        if len(sol) != 5:
            print("The solution entered is not a valid solution. Quitting...")
        for char in sol:
            if not char.isalpha():
                print("The solution contained a character which is not a letter. Quitting...")
                return 

        self.solution = WordleOption(sol)
        return super().playGame()
    
    def _submitGuess(self, next_guess: WordleOption) -> list[int]:
        '''Process the guess by returning a list of the `LetterResultOption` enum values when compared to the solution'''
        print("Our next guess for the wordle is: " + next_guess.word)
        return WordleUtils.validateGuess(next_guess, self.solution)

class BasicWordleCompletion(WordleGame):
    '''A wordle game which will simulate guessing until the solution is found. No narration in the terminal.
       Override `_getNextGuess` to no longer naively pick what could be a valid solution from `remaining_options`'''

    solution: WordleOption
    '''The solution to the wordle game. Not considered when making guesses by the model'''

    def __init__(self, solution: str) -> None:
        self.solution = WordleOption(solution)
        super().__init__()
        return
    
    def playGame(self) -> None:
        while True:
            next_guess = self._getNextGuess()
            results = self._submitGuess(next_guess)
            self.guess_results.append(GuessResult(next_guess, results))

            # If the whole array is greens, we are done
            if Counter(results).get(LetterResultOptions.Green, 0) == 5:
                return

            self._updateOptions()
        
        return

    def _submitGuess(self, next_guess: WordleOption) -> list[int]:
        return WordleUtils.validateGuess(next_guess, self.solution)