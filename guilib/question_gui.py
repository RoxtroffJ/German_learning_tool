"""Manages the question GUI page."""

from abc import ABC, abstractmethod

import tkinter as tk

from tkinter import Misc, ttk
from typing import Callable

from guilib import PADDING
from guilib.pages import Page

class CallOnce:
    """Utility class to ensure a callable is only called once."""
    def __init__(self, func: Callable[[], None]):
        self._func = func
        self._called = False

    def __call__(self) -> None:
        if not self._called:
            self._func()
            self._called = True

class QuestionDrawer(ABC):
    """
    A page that displays a question to the user.

    When the user answers the question, the `on_answered` callback is called.
    When the question is deleted, the `on_deleted` callback is called. This ensures the question is not displayed anymore.
    """
    @abstractmethod
    def draw(self, root: Misc, on_answered: CallOnce) -> None:
        """Draws the question on the given root widget. 
        When the question is answered, the `on_answered` callback should be called, and the probability updated (and saved).
        When the question is deleted, the `on_deleted` callback should be called. This ensures the question is not displayed anymore.
        
        Resulting frame must not be influenced by other calls."""
        ...

    @abstractmethod
    def get_probability(self) -> float:
        """Returns the probability as a float."""
        ...
    @abstractmethod
    def get_average(self) -> float:
        """Returns the average score as a float between 0 and 1."""
        ...

class QuestionnerPage(Page):
    """A page that shows questions to the user.
    The probabilities must be consistent with each other (ie same scale).
    """
    def __init__(self, root: Misc, sticky: str = "NSEW", question_list: list[QuestionDrawer] = [], empty_callback: Callable[[], None] | None = None):
        super().__init__(root, sticky)

        self.__question_list = question_list
        self.__deleted_questions: set[int] = set()
        self.__empty_callback = empty_callback
        self.progress_var = tk.DoubleVar(value=0.0)
        
        self._curr_question_frame: ttk.Frame | None = None

        separator = ttk.Separator(self.frame, orient="horizontal")

        separator.grid(column=0, row=1, sticky="EW", pady=PADDING)
        
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        self.frame.rowconfigure(2, weight=1)

        # If an initial non-empty question list was provided, start showing questions
        if len(self.__question_list) > 0:
            self._change_question()
        else:
            if self.__empty_callback is not None:
                self.__empty_callback()

    def _pull_question(self) -> QuestionDrawer:
        """Pulls a question from the weighted question list."""

        from random import choices

        weights = [question.get_probability() for question in self.__question_list]

        sum_denom = sum(weights)
        sum_numer = sum([question.get_probability() * question.get_average() for question in self.__question_list])

        self.progress_var.set(0.0 if sum_denom == 0 else sum_numer / sum_denom)

        while True:
            idx, selected_question = choices(list(enumerate(self.__question_list)), weights=weights, k=1)[0]
            if idx not in self.__deleted_questions:
                break

        return selected_question

    def _change_question(self):
        """Changes the current question to a new one."""
        
        if len(self.__deleted_questions) == len(self.__question_list):
            if self.__empty_callback is not None:
                self.__empty_callback()
            return

        # Update current question
        question_drawer = self._pull_question()

        # Regrid current question frame
        if self._curr_question_frame is not None:
            self._curr_question_frame.grid(column=0, row=0, sticky="NSEW")

        frame = ttk.Frame(self.frame)
        self._curr_question_frame = frame

        frame.grid(column=0, row=2, sticky="NSEW")


        question_drawer.draw(frame, on_answered=CallOnce(self._change_question))

    
    @property
    def question_list(self) -> list[QuestionDrawer]:
        """The list of questions."""
        return self.__question_list
    
    @question_list.setter
    def question_list(self, new_list: list[QuestionDrawer]) -> None:
        """Sets the list of questions, and resets the display"""
        
        self.__question_list = new_list
        
        if self._curr_question_frame is not None:
            self._curr_question_frame.destroy()
            self._curr_question_frame = None
        
        self.__deleted_questions.clear()
        self._change_question()


class ToQuestionDrawer(ABC):
	"""Interface for classes that can be converted to QuestionDrawer."""

	@abstractmethod
	def to_question_drawers(self) -> list["QuestionDrawer"]:
		"""Returns a list of QuestionDrawers."""
		...
