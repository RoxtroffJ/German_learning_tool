"""Manages the question GUI page."""

from abc import ABC, abstractmethod
from tkinter import Misc, ttk
from typing import Callable

from guilib.pages import Page
from guilib.pages import PageSwitcher

class QuestionDrawer(ABC):
    """
    A page that displays a question to the user.

    When the user answers the question, the `on_answered` callback is called.
    """
    @abstractmethod
    def draw(self, root: Misc, on_answered: Callable[[], None] | None = None) -> None:
        """Draws the question on the given root widget. 
        When the question is answered, the `on_answered` callback should be called, and the probability updated (and saved).
        
        Can be called multiple times."""
        ...

    @abstractmethod
    def get_probability(self) -> float:
        """Returns the probability as a float."""
        ...

class QuestionnerPage(Page):
    """A page that shows questions to the user.
    The probabilities must be consistent with each other (ie same scale).
    """
    def __init__(self, root: Misc, sticky: str = "NSEW", question_list: list[QuestionDrawer] = []):
        super().__init__(root, sticky)

        self.__question_list = question_list

        curr_question_frame = ttk.Frame(self.frame)
        self._curr_page_switcher = PageSwitcher(curr_question_frame)

        prev_question_frame = ttk.Frame(self.frame)
        self._prev_page_switcher = PageSwitcher(prev_question_frame)

        curr_question_frame.grid(column=0, row=0, sticky="NSEW")
        prev_question_frame.grid(column=0, row=1, sticky="NSEW")
        
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=0)

        self._current_question_drawer: QuestionDrawer | None = None


    def _pull_question(self) -> QuestionDrawer:
        """Pulls a question from the weighted question list."""

        from random import choices

        weights = [question.get_probability() for question in self.__question_list]

        selected_question = choices(self.__question_list, weights=weights, k=1)[0]

        return selected_question

    def _change_question(self):
        """Changes the current question to a new one."""
        new_question_page = self._curr_page_switcher.create_page()
        prev_question_page = self._prev_page_switcher.create_page()
        
        # Update previous question
        if self._current_question_drawer is not None:
            self._current_question_drawer.draw(prev_question_page.frame)
            self._prev_page_switcher.show_page(prev_question_page)
        
        # Update current question
        self._current_question_drawer = self._pull_question()
        self._current_question_drawer.draw(new_question_page.frame, on_answered=self._change_question)
        self._curr_page_switcher.show_page(new_question_page)
    
    @property
    def question_list(self) -> list[QuestionDrawer]:
        """The list of questions."""
        return self.__question_list
    
    @question_list.setter
    def question_list(self, new_list: list[QuestionDrawer]) -> None:
        """Sets the list of questions, and resets the display"""
        self.__question_list = new_list
        self._change_question()
        self._prev_page_switcher.remove_current_page()  