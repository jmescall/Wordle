from collections import Counter, defaultdict
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
    
    guess_results: list[GuessResult] 
    '''List of guesses and their results'''
    
    remaining_options = set[WordleOption] 
    '''Set of wordle options which could be the solution to the current game'''

    remaining_map = list[dict[str: WordleOption]]
    ''' A list of the remaining options by character placement '''

    def __init__(self, file_name: str = "WordleWords.txt") -> None:
        # Set up the trackers
        self.guess_results = []

        # Store all of the possible words to guess
        if not self._storeOptions(file_name):
            return

        return

    def _storeOptions(self, file_name: str) -> bool:
        ''' Iterate through the valid wordle guesses file and store each word in `self.remaining_options` and `self.remaining_map` '''
        self.remaining_options = set()
        self.remaining_map = [defaultdict(set) for _ in range(5)]


        try: # read from the current directory of the file
            file = open(fileAccess.sameDirFilePath(file_name), "r") 
        except:
            print("No options to guess from. Quiting...")
            return False

        for line in file:
            word = line.strip("\n")
            option = WordleOption(word)
            self.remaining_options.add(option)
            for i, char in enumerate(word):
                self.remaining_map[i][char].add(option)
        
        return True
    
    def createMap(self) -> list[dict[str: set[WordleOption]]]:
        ''' Returns a new `remaining_map` based on `self.remaining_options` '''
        remaining_map = [defaultdict(set) for _ in range(5)]
        for option in self.remaining_options:
            word = option.word
            for i, char in enumerate(word):
                remaining_map[i][char].add(option)
        return remaining_map
    
    def _updateOptions(self) -> None:
        ''' Filters the game's remaining possible solutions based on the last guess's result'''
        guess, result = self.guess_results[-1].guess, self.guess_results[-1].result
        self.remaining_options = WordleUtils.filter(self.remaining_options, self.remaining_map, guess, result)
        self.remaining_map = self.createMap() # update the map with the new remaining options
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

class WordleUtils:
    '''Utilities which can be used for most wordle games'''

    def filterOnCounts(valid_remaining: set[WordleOption], guessed_counts: dict[str: int], result_counts: dict[str: int]) -> None:
        ''' Based on the counts of characters guessed and counts based on the colors remove options '''
        remove_zeros = set()
        for char, count in result_counts.items():
            if count == 0:
                for i in range(5):
                    remove_zeros.update(remove_zeros)
        valid_remaining.difference_update(remove_zeros)
        
        for option in list(valid_remaining):
            for guessed_char in guessed_counts.keys():
                # if our last guess had the same or more of a shared letter, but the result showed a different count, remove the option because this can't be the solution
                if guessed_counts[guessed_char] >= option.letters.get(guessed_char, 0):
                    if result_counts[guessed_char] != option.letters[guessed_char]:
                        valid_remaining.remove(option)
                        break 
                # if our last guess had less (but more than zero) of a letter than this word, then the result should have the same count if this option is the solution
                elif option.letters.get(guessed_char, 0) > 0:
                    if result_counts[guessed_char] != guessed_counts[guessed_char]:
                        valid_remaining.remove(option)
                        break
        
        return

    def filterOnColor(valid_remaining: set[WordleOption], remaining_map: list[dict[str: set[WordleOption]]], guess_word: str, result: list[int], result_counts: dict[str: int]) -> None:
        ''' Iterate through the characters of the guess and tehe colors assigned to each character to update counts and remove previous options '''
        invalid_remove = set()

        for i, (char, color) in enumerate(zip(guess_word, result)):
            if color == LetterResultOptions.Green:
                valid_remaining.intersection_update(remaining_map[i][char])
                result_counts[char] = result_counts.get(char, 0) + 1
            elif color == LetterResultOptions.Yellow:
                invalid_remove.update(remaining_map[i][char])
                result_counts[char] = result_counts.get(char, 0) + 1
            else:
                invalid_remove.update(remaining_map[i][char])
                result_counts[char] = result_counts.get(char, 0)
        
        valid_remaining.difference_update(invalid_remove)
        return


    def filter(remaining_options: set[WordleOption], remaining_map: list[dict[str: set[WordleOption]]], guess: WordleOption, result: list[int]) -> set[WordleOption]:
        ''' Return a new set of options based on the guess and the result '''
        valid_remaining = remaining_options.copy()
        guessed_counts = guess.letters.copy()
        result_counts = {}
        
        # Note that filterOncolor updates result_counts, and both filterOnColor and filterOnCounts update valid_remaining
        WordleUtils.filterOnColor(valid_remaining, remaining_map, guess.word, result, result_counts)
        WordleUtils.filterOnCounts(valid_remaining , guessed_counts, result_counts)

        return valid_remaining

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

    def __init__(self, solution: str, file_name: str = "WordleWords.txt") -> None:
        self.solution = WordleOption(solution)
        super().__init__(file_name)
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