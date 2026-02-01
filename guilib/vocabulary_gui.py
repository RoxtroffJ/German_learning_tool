import tkinter as tk
from tkinter import ttk

from guilib import *
from guilib import selection_buttons
from guilib.pages import *
from guilib.tree_selection_state import *

from tree import Path as TreePath

import lib.vocabulary as lvoc

_HP = TypeVar("_HP", bound=HeaderedPage[Any], covariant=True)

class VocabularySelectionPage(selection_buttons.HeaderedWithSelectAll[TreePages.TreeSubPage[_HP]], Generic[_HP]):
    """A page to select the vocabulary questions sets."""
        
    def __init__(
            self, 
            menu_treer: TreePages[_HP, Page], 
            parent: Page, 
            selection_state: TreeSelectionState, 
            parent_path: TreePath, 
            sticky: str | None = "EW", 
            back: bool = True, 
            home: bool = False
    ):
        """Creates a vocabulary selection page in a TreePages structure."""

        # Register vocabulary section in the selection state
        self._path = selection_state.add_node(parent_path)
        self._selection_state = selection_state

        # Create the page
        page = menu_treer.create_subpage(parent, sticky=sticky, back=back, home=home)

        frame = page.frame

        # Load the sets
        self.__question_sets = lvoc.QuestionSet.load_all()

        # Register each set in the selection state
        self.sets: dict[str, tuple[lvoc.QuestionSet, TreePath]] = {}

        # Label
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="Vocabulary Sets:").grid(column=0, row=0, pady=PADDING)

        # Scrollable frame for the buttons
        
        scrollable_frame_area = ttk.Frame(frame)

        scrollable_frame_area.grid(column=0, row=1, sticky="NSEW")

        frame.rowconfigure(1, weight=1)


        scrollbar_page = ScrollablePage(scrollable_frame_area)

        scrollbar_page.display_page()
        scrollable_frame = scrollbar_page.frame

        self.__buttons_frame = scrollable_frame

        # Buttons for each set

        scrollable_frame.columnconfigure(0, weight=1)

        for qset in self.__question_sets:
            self.add_set(qset)
        
        page_with_select_all = selection_buttons.HeaderedWithSelectAll(
            page,
            selection_state,
            self._path,
        )

        self.__dict__.update(page_with_select_all.__dict__)

    def add_set(self, qset: lvoc.QuestionSet) -> None:
        """Adds a new question set to the selection page."""
        if qset.name in self.sets:
            # Replace existing set
            self.sets[qset.name] = (qset, self.sets[qset.name][1])
            return
        
        # Register in selection state
        path = self._selection_state.add_node(self._path)
        self.sets[qset.name] = qset, path

        # Add button to GUI
        button_frame = self.__buttons_frame

        btn = ttk.Button(button_frame, text=qset.name, command = lambda : self._selection_state.select_all_callback(path))
        # Center the button within the full-width grid cell.
        btn.grid(column=0, pady=(0, PADDING))

        selection_buttons.stylify_button(
            btn,
            self._selection_state,
            path,
        )

    def select_all_button(self, root: tk.Misc) -> ttk.Button:
        """Returns the 'Select All' button."""
        return selection_buttons.select_all_button(
            root,
            self._selection_state,
            self._path
        )

class SetPage(Page):
    """A page displaying the contents of a vocabulary set."""
    
    class _Row(ttk.Frame):
        """A row displaying a question-answer pair."""
        
        def __init__(self, parent: tk.Misc, question: lvoc.Question, editable: tk.BooleanVar, on_delete: Callable[[], None]):
            super().__init__(parent)
            
            self._on_delete = on_delete

            self.columnconfigure(0, weight=1)
            self.columnconfigure(1, weight=1)
            
            self._question_var = tk.StringVar(value=question.question)
            self._answer_var = tk.StringVar(value=question.answer)

            # Map questions and answers var to those of question itself
            def on_var_change() -> None:
                question.reset_with(self._question_var.get(), self._answer_var.get())
            self._question_var.trace_add("write", lambda a,b,c: on_var_change())
            self._answer_var.trace_add("write", lambda a,b,c: on_var_change())

            self._editable_var = editable

            self._question_entry = ttk.Entry(self, textvariable=self._question_var)
            self._question_entry.grid(column=0, row=0, sticky="EW", padx=PADDING, pady=PADDING)
            self._answer_entry = ttk.Entry(self, textvariable=self._answer_var)
            self._answer_entry.grid(column=1, row=0, sticky="EW", padx=PADDING, pady=PADDING)

            self._editable_var.trace_add("write", lambda a,b,c: self.make_editable(self._editable_var.get()))

            self._delete_button = ttk.Button(self, text="✕", width=2, command=self._on_delete)

        def make_editable(self, editable: bool) -> None:
            """Switches the row to editable or non-editable mode."""
            state = "normal" if editable else "readonly"
            self._question_entry.config(state=state)
            self._answer_entry.config(state=state)

            if editable:
                self._delete_button.grid(column=2, row=0, padx=PADDING, pady=PADDING)
            else:
                self._delete_button.grid_forget()
        
        def delete_row(self):
            """Deletes this row."""
            self._on_delete()
            self.destroy()

    def __init__(self, root: tk.Misc, set: lvoc.QuestionSet, sticky: str = "NSEW", editable: bool = False):
        super().__init__(root, sticky)
        self.editable = tk.BooleanVar(value=editable)
        self.__set = set

        # Create dictionnary int, question of questions in set.questions
        # so we can manage deletions easily
        self._questions: dict[int, lvoc.Question] = {}
        self._next_free_index = len(self._questions)
        self._unused_indices: list[int] = []

        self.__set_needs_rebuild = False

        frame = self.frame

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        scrollbar_page = ScrollablePage(frame)
        scrollbar_page.display_page()

        self._scrollable_frame = scrollbar_page.frame
        self._scrollable_frame.columnconfigure(0, weight=1)

        # Add existing questions
        for question in set.questions:
            self.add_question(question)

    def add_question(self, question: lvoc.Question) -> None:
        """Adds a new row to the set page."""

        # Determine index
        if len(self._unused_indices) > 0:
            index = self._unused_indices.pop()
        else:
            index = self._next_free_index
            self._next_free_index += 1
        
        # Add GUI

        def on_delete():
            del self._questions[index]
            self._unused_indices.append(index)
            self.__set_needs_rebuild = True
        row = SetPage._Row(
            self._scrollable_frame,
            question,
            self.editable,
            on_delete
        )
        row.grid(column=0, sticky="EW")

        # Add storage and mapping
        self._questions[index] = question
        self.__set.add_question(question)

    @property
    def set(self) -> lvoc.QuestionSet:
        """Returns the vocabulary set displayed in this page."""
        if self.__set_needs_rebuild:
            # Rebuild the set questions from current questions
            self.__set.clear_all_questions()
            for question in self._questions.values():
                self.__set.add_question(question)
            self.__set_needs_rebuild = False
        return self.__set

    def check_saved(self) -> bool:
        """Checks if the current in-memory set matches the saved file."""
        return self.set.check_saved()
    
    def save(self) -> None:
        """Saves the current set to file."""
        self.set.save()

    





