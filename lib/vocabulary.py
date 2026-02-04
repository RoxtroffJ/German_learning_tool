from pathlib import Path

import tempfile

from lib.score import Score, ScoreFile

from enum import Enum

VOC_FOLDER = Path.cwd() / "data" / "vocabulary"
VOC_SCORES_FOLDER = Path.cwd() / "scores" / "vocabulary"

VOC_FOLDER.mkdir(parents=True, exist_ok=True)
VOC_SCORES_FOLDER.mkdir(parents=True, exist_ok=True)



class Gender(Enum):
    """Enumeration of German noun genders."""
    MASCULINE = "M"
    FEMININE = "F"
    NEUTRAL = "N"
    PLURAL = "P"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_str(cls, s: str) -> "Gender":
        for gender in cls:  
            if gender.value == s:
                return gender
        raise ValueError(f"Unknown gender string: {s}")

class _QuestionData:
    """Internal data structure for vocabulary question storage."""
    def __init__(self, question: str, answer: str):
        self.question = question
        self.answer = answer

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _QuestionData):
            return False
        return self.question == other.question and self.answer == other.answer



class _VocabularyFile:
    """Handles loading and saving of vocabulary files."""
    
    @staticmethod
    def _filepath_for_name(name: str) -> Path:
        return VOC_FOLDER / f"{name}.voc"
    
    def __init__(self, name: str, questions: list[_QuestionData] | None = None):
        self.__name = name
        self.__filepath = self._filepath_for_name(name)
        self.questions: list[_QuestionData] = questions if questions is not None else []


    @classmethod
    def load(cls, name: str) -> "_VocabularyFile":
        """Loads a vocabulary file."""

        vocab_file = cls(name)
        filepath = vocab_file.__filepath

        if not filepath.exists():
            return vocab_file  # empty file

        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        version = lines[0].strip()
        if version != "0":
            raise ValueError(f"Unsupported vocabulary file version: {version}")
        
        for line in lines[1:]:
            def fail_msg():
                print(f"Warning: skipping malformed line in {filepath}: {line.rstrip('\r\n')}")

            # Use rstrip to only remove trailing newline characters so leading
            # tabs (which denote an empty question) are preserved. Split only
            # on the first tab so answers may contain tabs.
            parts = line.rstrip('\r\n').split("\t", 1)
            if len(parts) < 2:
                fail_msg()
                continue

            question = parts[0].strip()
            answer = parts[1].strip()

            data = _QuestionData(question, answer)
            vocab_file.questions.append(data)

        return vocab_file
    
    def save(self):
        """Saves the vocabulary file to its filepath."""

        # Renames if needed
        new_filepath = self._filepath_for_name(self.__name)
        if new_filepath != self.__filepath:
            try:
                self.__filepath.rename(new_filepath)
            except:
                pass
            self.__filepath = new_filepath

        

        with tempfile.NamedTemporaryFile("w", dir=self.__filepath.parent, encoding="utf-8", delete=False) as f:
            f.write("0\n")  # version
            for q in self.questions:
                line = f"{q.question}\t{q.answer}\n"
                f.write(line)
            
            f.flush()
            temp_name = f.name
        # Move temp file to final location
        temp_path = Path(temp_name)
        temp_path.replace(self.__filepath)

    def check_saved(self) -> bool:
        """Checks if the current in-memory questions match the saved file."""
        if not self.__filepath.exists():
            return False
        try:
            saved_file = _VocabularyFile.load(self.__name)
        except:
            return False
        return self == saved_file

    def delete(self):
        """Deletes the vocabulary file."""
        try:
            self.__filepath.unlink()
        except:
            pass

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _VocabularyFile):
            return False
        if self.__name != other.__name:
            return False
        if len(self.questions) != len(other.questions):
            return False
        for a, b in zip(self.questions, other.questions):
            if a != b:
                return False
        return True

    @property
    def name(self) -> str:
        """Returns the name of the vocabulary file."""
        return self.__name
    
    @name.setter
    def name(self, new_name: str):
        """Renames the vocabulary file."""
        self.__name = new_name




class Question:
    """Represents a single vocabulary question."""
    def __init__(self, data: _QuestionData | None = None, score: Score | None = None):
        self._data = data if data is not None else _QuestionData("", "")
        self._score = score if score is not None else Score()
    

    def add_to_files(self, voc_file: _VocabularyFile, score_file: ScoreFile):
        """Adds this question to the given vocabulary and score files."""
        voc_file.questions.append(self._data)
        score_file.scores.append(self._score)

    @property
    def question(self) -> str:
        """Returns the question string."""
        return self._data.question
    
    @property
    def answer(self) -> str:
        """Returns the answer string."""
        return self._data.answer

    @property
    def score(self) -> float:
        """Returns the question score."""
        score = self._score
        return score.score
    
    def average(self) -> float:
        """Returns the average score (correct/total) for this question."""
        return self._score.average

    def score_str(self) -> str:
        """Returns a string representation of the question score."""
        if self._score.total == 0:
            return "No attempts"
        percentage = (self._score.average) * 100
        return f"{percentage:.1f}%, Streak: {self._score.streak}"
    
    def update_score(self, correct: bool):
        """Updates the question score based on whether the answer was correct."""
        self._score.update(correct)

    def reset_with(self, question: str, answer: str):
        """Resets the question and answer strings, as well as score in place."""
        self._data.question = question
        self._data.answer = answer
        self._score = Score()

class QuestionSet:

    new_set_name = "Enter a name"

    """Represents a set of vocabulary questions with their scores."""
    def __init__(self, name: str | None = None):
        # Preserve empty-string names. Only use the placeholder when name is None.
        self._name = name if name is not None else self.new_set_name
        
        self._vocab_file = _VocabularyFile.load(self._name)
        self._score_file = ScoreFile.load(VOC_SCORES_FOLDER, self._name)

        # Ensure scores list matches questions list
        while len(self._score_file.scores) < len(self._vocab_file.questions):
            self._score_file.scores.append(Score())
        
        # Save scores if needed
        if not self._score_file.check_saved():
            self._score_file.save()
        
    @property
    def questions(self) -> list[Question]:
        """Returns the list of vocabulary questions with their scores."""
        vocab_questions: list[Question] = []
        for data, score in zip(self._vocab_file.questions, self._score_file.scores):
            vocab_questions.append(Question(data, score))
        return vocab_questions
    
    @property
    def name(self) -> str:
        """Returns the name"""
        return self._name

    @name.setter
    def name(self, new_name: str):
        """Sets a new name for the vocabulary set, renaming the underlying files."""
        self._vocab_file.name = new_name
        self._score_file.name = new_name
        self._name = new_name

    def add_question(self, question: Question):
        """Adds a new vocabulary question to the set."""
        question.add_to_files(self._vocab_file, self._score_file)

    def save(self):
        """Saves the vocabulary set to its files.
        
        Raises exception if name is new_set_name.
        """

        if self._name == self.new_set_name:
            raise ValueError(f"Name '{self.new_set_name}' is reserved.")

        self._vocab_file.save()
        self._score_file.save()
        
    def restore(self):
        self.__dict__.update(QuestionSet(self._name).__dict__)

    def delete(self):
        """Deletes the vocabulary set files."""
        self._vocab_file.delete()
        self._score_file.delete()

    def clear_all_questions(self):
        """Clears all questions from the set."""
        self._vocab_file.questions.clear()
        self._score_file.scores.clear()

    @classmethod
    def load_all(cls):
        """Loads all vocabulary sets from the vocabulary folder."""
        vocab_sets: list[QuestionSet] = []
        for filepath in VOC_FOLDER.glob("*.voc"):
            try:
                # Derive the set name by stripping the literal suffix '.voc'
                # from the filename. This ensures a file named '.voc'
                # produces an empty string name (instead of '.voc').
                filename = filepath.name
                if filename.endswith(".voc"):
                    name = filename[:-4]
                else:
                    raise ValueError(f"Invalid vocabulary file name: {filename}")

                vocab_set = cls(name)
                vocab_sets.append(vocab_set)
            except Exception as e:
                print(f"Error loading vocabulary set from {filepath}: {e}")
                continue
        return vocab_sets
    
    def check_saved(self) -> bool:
        """Checks if the current in-memory set matches the saved file."""
        if self._name == self.new_set_name:
            return False
        return self._vocab_file.check_saved() and self._score_file.check_saved()
    
