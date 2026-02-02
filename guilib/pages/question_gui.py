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
    When the question is deleted, the `on_deleted` callback is called. This ensures the question is not displayed anymore.
    """
    @abstractmethod
    def draw(self, root: Misc, on_answered: Callable[[], None] | None = None, on_deleted: Callable[[], None] | None = None) -> None:
        """Draws the question on the given root widget. 
        When the question is answered, the `on_answered` callback should be called, and the probability updated (and saved).
        When the question is deleted, the `on_deleted` callback should be called. This ensures the question is not displayed anymore.
        
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
    def __init__(self, root: Misc, sticky: str = "NSEW", question_list: list[QuestionDrawer] = [], empty_callback: Callable[[], None] | None = None):
        super().__init__(root, sticky)

        self.__question_list = question_list
        self.__deleted_questions: set[int] = set()
        self.__empty_callback = empty_callback
        curr_question_frame = ttk.Frame(self.frame)
        self._curr_page_switcher = PageSwitcher(curr_question_frame)

        prev_question_frame = ttk.Frame(self.frame)
        self._prev_page_switcher = PageSwitcher(prev_question_frame)

        curr_question_frame.grid(column=0, row=0, sticky="NSEW")
        prev_question_frame.grid(column=0, row=1, sticky="NSEW")
        
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=0)

        self._current_question_drawer: tuple[QuestionDrawer, int] | None = None


    def _pull_question(self) -> tuple[QuestionDrawer, int]:
        """Pulls a question from the weighted question list."""

        from random import choices

        weights = [question.get_probability() for question in self.__question_list]

        while True:
            idx, selected_question = choices(list(enumerate(self.__question_list)), weights=weights, k=1)[0]
            if idx not in self.__deleted_questions:
                break

        return selected_question, idx

    def _change_question(self):
        """Changes the current question to a new one."""
        new_question_page = self._curr_page_switcher.create_page()
        prev_question_page = self._prev_page_switcher.create_page()
        
        # Update previous question
        if self._current_question_drawer is not None:
            question_drawer, question_idx = self._current_question_drawer
            def __on_delete():
                self.__deleted_questions.add(question_idx)
                self._prev_page_switcher.remove_current_page()

            question_drawer.draw(prev_question_page.frame, on_answered=None, on_deleted=__on_delete)
            self._prev_page_switcher.show_page(prev_question_page)
        
        if len(self.__deleted_questions) == len(self.__question_list):
            if self.__empty_callback is not None:
                self.__empty_callback()
            return

        # Update current question
        question_drawer, idx = self._pull_question()

        def __on_delete():
            self.__deleted_questions.add(idx)
            self._curr_page_switcher.remove_current_page()
            self._current_question_drawer = None
            self._change_question()

        self._current_question_drawer = (question_drawer, idx)
        question_drawer.draw(new_question_page.frame, on_answered=self._change_question, on_deleted=__on_delete)
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