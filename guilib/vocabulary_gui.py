import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkmsgbox

from typing import Callable, Generic, TypeVar, Any

from guilib import PADDING
from guilib import selection_buttons
from guilib.pages import ScrollablePage, HeaderedPage, Page, TreePages
from guilib.tree_selection_state import TreeSelectionState

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
            home: bool = False,
            no_go_page_maker: Callable[[tk.Misc, str], HeaderedPage[Any]] | None = None
    ):
        """Creates a vocabulary selection page in a TreePages structure."""
        self.__menu_treer = menu_treer
        self.__no_go_page_maker = no_go_page_maker
        self.__back = back
        self.__home = home

        # Register vocabulary section in the selection state
        self._path = selection_state.add_node(parent_path)
        self._selection_state = selection_state

        # Create the page
        page = menu_treer.create_subpage(parent, sticky=sticky, back=back, home=home)

        frame = page.frame

        # Load the sets
        question_sets = lvoc.QuestionSet.load_all()
        question_sets.sort(key=lambda qs: qs.name)

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

        self.__buttons_frame = ttk.Frame(scrollable_frame)
        self.__buttons_frame.grid(column=0, row=0)

        scrollable_frame.columnconfigure(0, weight=1)

        # Buttons for each set (sorted alphabetically)

        for qset in question_sets:
            self.add_set(qset)
        
        # Add set button
        def add_set_callback() -> None:
            new_set = lvoc.QuestionSet(name="New Set")
            self.add_set(new_set)
        add_set_button = ttk.Button(frame, text="Add New Set", command=add_set_callback)
        add_set_button.grid(column=0, row=2, pady=PADDING)

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

        idx = len(self.sets) - 1

        btn = ttk.Button(button_frame, text=qset.name, command = lambda : self._selection_state.select_all_callback(path))
        # Center the button within the full-width grid cell.
        btn.grid(column=0, row=idx, padx=PADDING, pady=PADDING)

        selection_buttons.stylify_button(
            btn,
            self._selection_state,
            path,
        )

        # Edit button
        def __edit_callback():
            new_page = self.__menu_treer.create_subpage(
                self,
                sticky="NSEW",
                back=self.__back,
                home=self.__home,
                page_maker=self.__no_go_page_maker
            )
            
            set_page = SetPage(
                new_page.frame,
                qset,
                sticky="NSEW",
                editable=True
            )

            def exit_confirm() -> bool:
                if set_page.check_saved():
                    return True
                
                result = tkmsgbox.askyesnocancel(
                    title="Unsaved Changes",
                    message="You have unsaved changes. Do you want to save them before exiting?",
                    icon="warning"
                )

                if result is None:
                    return False
                if result:
                    try:
                        set_page.save()
                    except ValueError as e:
                        tkmsgbox.showerror(
                            title="Save Error",
                            message=str(e),
                            icon="error"
                        )
                        return False
                else:
                    set_page.restore()
                return True

            new_page.back_confirm = exit_confirm
            new_page.home_confirm = exit_confirm

            set_page.display_page()
            self.__menu_treer.page_switcher.show_page(new_page)

            btn.config(textvariable=set_page.name_var)
        
        edit_btn = ttk.Button(button_frame, text="Edit", command=__edit_callback)
        edit_btn.grid(column=1, row=idx, pady=PADDING, padx=PADDING)




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
            
            self._delete_button = ttk.Button(self, text="✕", width=2, command=self.delete_row)

            self._editable_var.trace_add("write", lambda a,b,c: self.make_editable(self._editable_var.get()))
            self.make_editable(self._editable_var.get())

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

        self.name_var = tk.StringVar(value=set.name)
        def _callback(a: str, b: str, c: str) -> None:
            self.__set.name = self.name_var.get()
        self.name_var.trace_add("write", _callback)

        # Create dictionnary int, question of questions in set.questions
        # so we can manage deletions easily
        self._questions: dict[int, lvoc.Question] = {}
        self._next_free_index = len(self._questions)
        self._unused_indices: list[int] = []

        self.__set_needs_rebuild = False
        
        frame = self.frame

        # Draw name
        name_frame = ttk.Frame(frame)
        name_frame.grid(column=0, row=0, sticky="EW")
        name_frame.columnconfigure(1, weight=1)
        ttk.Label(name_frame, text="Set Name:").grid(column=0, row=0, padx=PADDING, pady=PADDING)
        name_entry = ttk.Entry(name_frame, textvariable=self.name_var)
        name_entry.grid(column=1, row=0, sticky="EW", padx=PADDING, pady=PADDING)

        self.editable.trace_add("write", lambda a,b,c: name_entry.config(state="normal" if self.editable.get() else "readonly"))

        # Draw questions

        questions_frame = ttk.Frame(frame)
        questions_frame.grid(column=0, row=1, sticky="NSEW")

        scrollbar_page = ScrollablePage(questions_frame)
        scrollbar_page.display_page()

        self._scrollable_frame = scrollbar_page.frame
        self._scrollable_frame.columnconfigure(0, weight=1)

        # Add existing questions
        for question in set.questions:
            self.add_question(question, add_to_list=True, add_to_set=False)

        # Add a add-question button
        def add_question_callback() -> None:
            new_question = lvoc.Question()
            self.add_question(new_question, add_to_list=True, add_to_set=True)
        add_question_button = ttk.Button(frame, text="Add Question", command=add_question_callback)

        def add_question_button_position() -> None:
            if self.editable.get():
                add_question_button.grid(column=0, row=2, pady=PADDING)
            else:
                add_question_button.grid_forget()
        add_question_button_position()
        self.editable.trace_add("write", lambda a,b,c: add_question_button_position())

        # Make frame growable
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

    def add_question(self, question: lvoc.Question, add_to_list: bool, add_to_set: bool) -> None:
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
        if add_to_list:
            self._questions[index] = question
        if add_to_set:
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

    def restore(self) -> None:
        """Restores the set from file."""
        self.set.restore()
        # Rebuild the page
        for widget in self._scrollable_frame.winfo_children():
            widget.destroy()
        self._questions.clear()
        self._next_free_index = 0
        self._unused_indices.clear()
        for question in self.set.questions:
            self.add_question(question, add_to_list=True, add_to_set=False)
        self.__set_needs_rebuild = False
    





