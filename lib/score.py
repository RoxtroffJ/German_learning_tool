from pathlib import Path
import tempfile
import struct

SCORE_LIFETIME = 0.95

class Score:
    """Internal data structure for vocabulary question score storage."""
    def __init__(self, total: int = 0, correct: int = 0, streak: int = 0, score: float = 0.0):
        self.correct = correct
        self.total = total
        self.streak = streak
        self._score = score
    

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Score):
            return False
        return (self.total == other.total and
                self.correct == other.correct and
                self.streak == other.streak and
                self._score == other._score)
    
    @property
    def score(self) -> float:
        """Calculates and returns the score based on total, correct, and streak."""
        return min(self._score, 0.95)
    
    @property
    def average(self) -> float:
        """Returns the average score (correct/total)."""
        return self._score
    
    def update(self, correct: bool):
        """Updates the score based on whether the answer was correct."""
        self.total += 1
        self._score = self._score * SCORE_LIFETIME
        if correct:
            self.correct += 1
            self.streak += 1
            self._score += (1.0 - SCORE_LIFETIME)
        else:
            self.streak = 0
            

class ScoreFile:
    """Handles loading and saving of vocabulary score files."""
    
    def __init__(self, folder: Path, name: str, scores: list[Score] | None = None):
        self.__folder = folder
        self.__name = name
        self.__filepath = self._filepath_for_name(name)
        self.scores: list[Score] = scores if scores is not None else []
    
    def _filepath_for_name(self, name: str) -> Path:
        return self.__folder / f"{name}.voc_score"

    @classmethod
    def load(cls, folder: Path, name: str) -> "ScoreFile":
        """Loads a vocabulary score file."""
        
        score_file = cls(folder, name)
        filepath = score_file.__filepath

        # Binary files encoding with version header

        if not filepath.exists():
            return score_file  # no scores yet

        # Read header line (text) then read the remaining binary block
        with open(filepath, "rb") as f:
            header = f.readline()
            if not header:
                return score_file
            version = header.strip().decode("utf-8")
            if version == "0":
                return ScoreFile0.load(folder, name).upgrade_to_1()
            if version != "1":
                raise ValueError(f"Unsupported vocabulary score file version: {version}")

            data = f.read()

        RECORD_SIZE = 14  # 2 bytes total, 2 bytes correct, 2 bytes streak, 8 bytes double

        def _parse_chunk(chunk: bytes):
            total = int.from_bytes(chunk[0:2], byteorder="big")
            correct = int.from_bytes(chunk[2:4], byteorder="big")
            streak = int.from_bytes(chunk[4:6], byteorder="big")
            score_val = struct.unpack('<d', chunk[6:14])[0]
            return Score(total, correct, streak, score_val)

        # Prefer the new contiguous-record format (multiple of RECORD_SIZE).
        if len(data) % RECORD_SIZE == 0:
            for i in range(len(data) // RECORD_SIZE):
                chunk = data[i * RECORD_SIZE:(i + 1) * RECORD_SIZE]
                score_file.scores.append(_parse_chunk(chunk))
            return score_file

        # Fallback: old files used a newline after each record (15 bytes per record).
        sep_size = RECORD_SIZE + 1
        if len(data) % sep_size == 0:
            # likely newline-separated records
            for i in range(len(data) // sep_size):
                rec = data[i * sep_size:(i + 1) * sep_size]
                # take first RECORD_SIZE bytes and ignore separator
                chunk = rec[:RECORD_SIZE]
                score_file.scores.append(_parse_chunk(chunk))
            return score_file

        # Last resort: remove newline bytes and try to parse contiguous records
        cleaned = data.replace(b"\n", b"")
        if len(cleaned) % RECORD_SIZE == 0 and len(cleaned) > 0:
            for i in range(len(cleaned) // RECORD_SIZE):
                chunk = cleaned[i * RECORD_SIZE:(i + 1) * RECORD_SIZE]
                score_file.scores.append(_parse_chunk(chunk))
            return score_file

        # If still malformed, parse as many full records as possible and warn
        if len(cleaned) >= RECORD_SIZE:
            n = len(cleaned) // RECORD_SIZE
            for i in range(n):
                chunk = cleaned[i * RECORD_SIZE:(i + 1) * RECORD_SIZE]
                score_file.scores.append(_parse_chunk(chunk))
            leftover = len(cleaned) - n * RECORD_SIZE
            if leftover:
                print(f"Warning: skipping {leftover} trailing bytes in {filepath}")
            return score_file

        # Nothing parseable
        return score_file
    
    def save(self):
        """Saves the vocabulary score file to its filepath."""
        # Renames if needed
        new_filepath = self._filepath_for_name(self.__name)
        if new_filepath != self.__filepath:
            try:
                self.__filepath.rename(new_filepath)
            except:
                pass
            self.__filepath = new_filepath

        with tempfile.NamedTemporaryFile("wb", dir=self.__filepath.parent, delete=False) as f:
            f.write(b"1\n")  # version header (text line)
            for s in self.scores:
                total_bytes = s.total.to_bytes(2, byteorder="big")
                correct_bytes = s.correct.to_bytes(2, byteorder="big")
                streak_bytes = s.streak.to_bytes(2, byteorder="big")
                score_bytes = struct.pack('<d', s.score)
                # write each record as contiguous 14 bytes (no newline separators)
                f.write(total_bytes + correct_bytes + streak_bytes + score_bytes)
            f.flush()
            temp_name = f.name
        # Move temp file to final location
        temp_path = Path(temp_name)
        temp_path.replace(self.__filepath)

    def check_saved(self) -> bool:
        """Checks if the current in-memory scores match the saved file."""
        if not self.__filepath.exists():
            return False
        
        try:
            saved_file = ScoreFile.load(self.__folder, self.__name)
        except:
            return False
        return self == saved_file

    def delete(self):
        """Deletes the vocabulary score file."""
        try:
            self.__filepath.unlink()
        except:
            pass

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ScoreFile):
            return False
        if self.__name != other.__name:
            return False
        if len(self.scores) != len(other.scores):
            return False
        for a, b in zip(self.scores, other.scores):
            if a != b:
                return False
        return True

    @property
    def name(self) -> str:
        """Returns the name of the vocabulary score file."""
        return self.__name
    
    @name.setter
    def name(self, new_name: str):
        """Renames the vocabulary score file."""
        self.__name = new_name




class ScoreFile0:
    """Updates from version 0 to 1"""
    
    def __init__(self, folder: Path, name: str, scores: list[Score] | None = None):
        self.__folder = folder
        self.__name = name
        self.__filepath = self._filepath_for_name(name)
        self.scores: list[Score] = scores if scores is not None else []
    
    def _filepath_for_name(self, name: str) -> Path:
        return self.__folder / f"{name}.voc_score"

    @classmethod
    def load(cls, folder: Path, name: str) -> "ScoreFile0":
        """Loads a vocabulary score file."""
        
        score_file = cls(folder, name)
        filepath = score_file.__filepath

        # Binary files encoding with version header

        if not filepath.exists():
            return score_file  # no scores yet

        with open(filepath, "rb") as f:
            lines = f.readlines()

        version = lines[0].strip().decode("utf-8")
        if version != "0":
            raise ValueError(f"Unsupported vocabulary score file version: {version}")
        
        for line in lines[1:]:
            # line = line.strip() # Causes problems
            # Each line is 3 16 bits binary integers: total, correct, streak with no separator
            if len(line) != 7: # 2 bytes * 3 + 1 byte newline
                print(f"Warning: skipping malformed line in {filepath}: {line}")
                continue

            total = int.from_bytes(line[0:2], byteorder="big")
            correct = int.from_bytes(line[2:4], byteorder="big")
            streak = int.from_bytes(line[4:6], byteorder="big")

            score = Score(total, correct, streak)
            score_file.scores.append(score)
        
        return score_file

    @property
    def name(self) -> str:
        """Returns the name of the vocabulary score file."""
        return self.__name
    
    @name.setter
    def name(self, new_name: str):
        """Renames the vocabulary score file."""
        self.__name = new_name
    
    def upgrade_to_1(self) -> ScoreFile:
        """Upgrades this score file to version 1."""
        print(f"Upgrading score file {self.__filepath.name} to version 1")
        new_scores: list[Score] = []
        for s in self.scores:
            new_score = Score(s.total, s.correct, s.streak, s.correct / s.total if s.total > 0 else 0.0)
            new_scores.append(new_score)
        return ScoreFile(self.__folder, self.__name, new_scores)