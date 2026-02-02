import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkmsgbox

from typing import Callable, Generic, TypeVar, Any

from guilib import PADDING
from guilib import selection_buttons
from guilib.pages import ScrollablePage, HeaderedPage, Page, TreePages
from guilib.tree_selection_state import TreeSelectionState

from guilib.pages.question_gui import QuestionDrawer as QD

from tree import Path as TreePath

import lib.vocabulary as lvoc

_HP = TypeVar("_HP", bound=HeaderedPage[Any], covariant=True)

_DELETE_BUTTON_WIDTH = 2

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
        self.__idx = 0

        self.__selected: set[TreePath] = set()

        self.__buttons: dict[TreePath, list[tk.Misc]] = {}

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
        self.sets: dict[TreePath, lvoc.QuestionSet] = {}

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
            self.add_new_set()
        add_set_button = ttk.Button(frame, text="Add New Set", command=add_set_callback)
        add_set_button.grid(column=0, row=2, pady=PADDING)

        page_with_select_all = selection_buttons.HeaderedWithSelectAll(
            page,
            selection_state,
            self._path,
        )

        self.__dict__.update(page_with_select_all.__dict__)

    def add_set(self, qset: lvoc.QuestionSet, name_var: tk.StringVar | None = None) -> TreePath:
        """Adds a new question set to the selection page."""
        
        # Register in selection state
        path = self._selection_state.add_node(self._path)

        def __select_callback(selected: bool):
            self.__selected.add(path) if selected else self.__selected.discard(path)

        self._selection_state.set_callbacks(path, selected_callback=__select_callback)
        
        self.sets[path] = qset

        # Add button to GUI
        button_frame = self.__buttons_frame

        idx = self.__idx
        self.__idx += 1

        btn = ttk.Button(button_frame, text=qset.name, command = lambda : self._selection_state.select_all_callback(path))
        if name_var is not None:
            btn.config(textvariable=name_var)
        
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
                    message="You have unsaved changes.",
                    detail="Do you want to save them before exiting?",
                    icon="warning"
                )

                if result is None:
                    return False
                if result:
                    try:
                        self._guarded_save(set_page.set, path, set_page.name_var)
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

        delete_btn = ttk.Button(button_frame, text="✕", command=lambda: self.delete_set(path, warn=True, delete_files=True), width=_DELETE_BUTTON_WIDTH)
        delete_btn.grid(column=2, row=idx, pady=PADDING, padx=PADDING)

        self.__buttons[path] = [btn, edit_btn, delete_btn]
        return path

    def add_new_set(self) -> TreePath:
        """
        Adds a new empty question set to the selection page.
        Will automatically show the edit page for the new set, and closing forces saving or deleting the new set.
        """
        new_set = lvoc.QuestionSet()
        name_var = tk.StringVar(value=new_set.name)
        path = self.add_set(new_set, name_var=name_var)
        # Build and show edit page
        new_page = self.__menu_treer.create_subpage(
            self,
            sticky="NSEW",
            back=self.__back,
            home=self.__home,
            page_maker=self.__no_go_page_maker
        )
        
        set_page = SetPage(
            new_page.frame,
            new_set,
            sticky="NSEW",
            editable=True,
            name_var=name_var
        )

        def exit_confirm() -> bool:
            if set_page.check_saved():
                return True
            
            try:
                if set_page.set.name == lvoc.QuestionSet.new_set_name:
                    # Rename 
                    set_page.name_var.set("New Set")
                self._guarded_save(set_page.set, path, set_page.name_var)
                return True
            except ValueError as e:
                result = tkmsgbox.askyesno(
                    title="Save Error",
                    message=f"Could not save: {e}",
                    detail="Delete the new set instead?",
                    icon="warning",
                    default=tkmsgbox.NO
                )
                if result:
                    self.delete_set(path, warn=False, delete_files=True)
                    return True
                else:
                    return False

        new_page.back_confirm = exit_confirm
        new_page.home_confirm = exit_confirm

        set_page.display_page()
        self.__menu_treer.page_switcher.show_page(new_page)

        # Finally add the set to the selection page
        return path
        
    def delete_set(self, set_path: TreePath, warn: bool = True, delete_files: bool = False) -> None:
        if set_path not in self.sets:
            return
        
        set_name = self.sets[set_path].name

        if warn:
            result = tkmsgbox.askyesno(
                title="Delete Set",
                message=f"Delete '{set_name}'?",
                detail="This action cannot be undone.",
                icon="warning",
                default=tkmsgbox.NO
            )
            if not result:
                return
        if delete_files:
            self.sets[set_path].delete()

        
        self._selection_state.delete_node(set_path)
        del self.sets[set_path]
        for widget in self.__buttons[set_path]:
            widget.destroy()
        del self.__buttons[set_path]

    def _guarded_save(self, set: lvoc.QuestionSet, path: TreePath, name_var: tk.StringVar | None = None):
        """
        Checks for name conflicts before saving the given set at path.
        """
        class SaveError(Exception):
            pass

        try:
            for other_path, other_set in self.sets.items():
                if other_path != path and other_set.name == set.name:
                    raise SaveError(f"A set named '{set.name}' already exists.")
                
            set.save()
        except SaveError:
            # Ask if override or rename
            result = tkmsgbox.askyesno(
                title="File Already Exists",
                message=f"Set '{set.name}' already exists.",
                detail="Do you want to overwrite it?",
                icon="warning",
                default=tkmsgbox.NO
            )
            if result:
                for other_path, other_set in list(self.sets.items()):
                    if other_path != path and other_set.name == set.name:
                        self.delete_set(other_path, warn=False, delete_files=True)
                set.save()
            else:
                # Find available name
                base_name = set.name
                idx = 1
                while True:
                    new_name = f"{base_name} ({idx})"
                    conflict = False
                    for other_path, other_set in self.sets.items():
                        if other_path != path and other_set.name == new_name:
                            conflict = True
                            break
                    if not conflict:
                        break
                    idx += 1
                if name_var is not None:
                    name_var.set(new_name)
                set.name = new_name
                set.save()
        self.sets[path] = set

    def select_all_button(self, root: tk.Misc) -> ttk.Button:
        """Returns the 'Select All' button."""
        return selection_buttons.select_all_button(
            root,
            self._selection_state,
            self._path
        )

    def to_question_drawers(self) -> list["QuestionDrawer"]:
        """Returns a list of QuestionDrawers for all selected sets."""
        question_drawers: list[QuestionDrawer] = []
        for path in self.__selected:
            if path in self.sets:
                qset = self.sets[path]
                set_with_delete = SetWithDelete(qset)
                for idx in range(len(qset.questions)):
                    qd = QuestionDrawer(
                        question_idx=idx,
                        question_set=set_with_delete
                    )
                    question_drawers.append(qd)
        return question_drawers

class SetPage(Page):
    """A page displaying the contents of a vocabulary set."""
    
    class Row(ttk.Frame):
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
            
            self._delete_button = ttk.Button(self, text="✕", width=_DELETE_BUTTON_WIDTH, command=self.delete_row)

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

    def __init__(
            self, 
            root: tk.Misc, 
            set: lvoc.QuestionSet,
            sticky: str = "NSEW", 
            editable: bool = False, 
            name_var: tk.StringVar | None = None
    ):
        super().__init__(root, sticky)

        # Use SetWithDelete to manage questions and deletions
        self._set_helper = SetWithDelete(set)

        self.editable = tk.BooleanVar(value=editable)

        self.name_var = name_var or tk.StringVar(value=set.name)
        def _callback(a: str, b: str, c: str) -> None:
            self.set.name = self.name_var.get()
        self.name_var.trace_add("write", _callback)
        
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

        # Add existing questions (build rows from helper's stored questions)
        for idx, question in self._set_helper.question_items():
            def make_on_delete(i: int):
                return lambda: (self._set_helper.delete_question(i))
            row = SetPage.Row(
                self._scrollable_frame,
                question,
                self.editable,
                make_on_delete(idx)
            )
            row.grid(column=0, sticky="EW")

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
        # Add to helper (which returns an index) and create a GUI row
        index = self._set_helper.add_question(question, _add_to_list=add_to_list, _add_to_set=add_to_set)

        def on_delete():
            self._set_helper.delete_question(index)
        row = SetPage.Row(
            self._scrollable_frame,
            question,
            self.editable,
            on_delete
        )
        row.grid(column=0, sticky="EW")

    @property
    def set(self) -> lvoc.QuestionSet:
        """Returns the vocabulary set displayed in this page."""
        return self._set_helper.set

    def check_saved(self) -> bool:
        """Checks if the current in-memory set matches the saved file."""
        return self._set_helper.check_saved()

    def restore(self) -> None:
        """Restores the set from file."""
        self._set_helper.restore()
        # Rebuild the page
        for widget in self._scrollable_frame.winfo_children():
            widget.destroy()
        for idx, question in self._set_helper.question_items():
            def make_on_delete(i: int):
                return lambda: (self._set_helper.delete_question(i))
            row = SetPage.Row(
                self._scrollable_frame,
                question,
                self.editable,
                make_on_delete(idx)
            )
            row.grid(column=0, sticky="EW")
    
# Export the logic of sets supporting deletion from SetPage to own class
class SetWithDelete():
    """A QuestionSet that supports addition and deletion of its questions."""
    
    def __init__(self, set: lvoc.QuestionSet):
        self.__set = set
        self._questions: dict[int, lvoc.Question] = {}
        self._next_free_index = len(self._questions)
        self._unused_indices: list[int] = []

        self.__set_needs_rebuild = False

        # Add existing questions
        for question in set.questions:
            self.add_question(question, _add_to_list=True, _add_to_set=False)

    def add_question(self, question: lvoc.Question, _add_to_list: bool = True, _add_to_set: bool = True):
        # Determine index
        if len(self._unused_indices) > 0:
            index = self._unused_indices.pop()
        else:
            index = self._next_free_index
            self._next_free_index += 1
        
        # Add storage and mapping
        if _add_to_list:
            self._questions[index] = question
        if _add_to_set:
            self.__set.add_question(question)
        return index
    
    def delete_question(self, index: int):
        del self._questions[index]
        self._unused_indices.append(index)
        self.__set_needs_rebuild = True
    
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

    def restore(self) -> None:
        """Restores the set from file."""
        self.set.restore()

        self._questions.clear()
        self._next_free_index = 0
        self._unused_indices.clear()
        for question in self.set.questions:
            self.add_question(question, _add_to_list=True, _add_to_set=False)
        self.__set_needs_rebuild = False
    
    def check_saved(self) -> bool:
        """Checks if the current in-memory set matches the saved file."""
        return self.set.check_saved()

    def question_items(self):
        """Returns a list of (index, question) pairs for current questions."""
        return list(self._questions.items())
    
    def get_question(self, index: int) -> lvoc.Question:
        """Returns the question at the given index."""
        return self._questions[index]

# QD for a page.
# Supports edition and deletion of questions, with edititon of the set the questions belong to.
# Saves at each answer and modification of question.
class QuestionDrawer(QD):
    """A question drawer for vocabulary questions."""
    
    def __init__(
            self,
            question_idx: int,
            question_set: SetWithDelete,
    ):
        super().__init__()
        self._question_idx = question_idx
        self._question_set = question_set
        self._answered = False

    def get_probability(self) -> float:
        """Returns the probability as a float."""
        score = self._question_set.get_question(self._question_idx).score

        return 1 / (score + 1)
    
    def draw(self, root: tk.Misc, on_answered: Callable[[], None] | None = None, on_deleted: Callable[[], None] | None = None) -> None:
        """Draws the question on the given root widget. 
        When the question is answered, the `on_answered` callback should be called, and the probability updated (and saved).
        When the question is deleted, the `on_deleted` callback should be called. This ensures the question is not displayed anymore.
        
        Can be called multiple times."""
        
        # First we show a frame of the question with an Entry for the answer.
        # On submission, we check the answer, update the score, save the set, and call on_answered.
        # Now the answer is displayed instead of the entry (with a correct/incorrect indication).
        # An edit button is also showed, which would show a SetPage.Row to edit or delete the question.
        # Finally, if the answer is wrong but is the answer of another question, we show that question too.
        
        # Clear root
        for w in root.winfo_children():
            w.destroy()

        question = self._question_set.get_question(self._question_idx)

        # Top: question text
        question_frame = ttk.Frame(root)
        question_frame.grid(column=0, row=0, sticky="EW")

        q_label = ttk.Label(question_frame, text=question.question + " :")
        q_label.grid(column=0, row=0, sticky="W", padx=PADDING, pady=PADDING)

        entry_var = tk.StringVar()
        answer_entry = ttk.Entry(root, textvariable=entry_var)
        answer_entry.grid(column=0, row=1, sticky="EW", padx=PADDING, pady=PADDING)

        # Container for result / edit area
        result_frame = ttk.Frame(root)
        result_frame.grid(column=0, row=2, sticky="NSEW", padx=PADDING, pady=PADDING)
        result_frame.columnconfigure(0, weight=1)

        def do_save():
            try:
                self._question_set.set.save()
            except ValueError as e:
                tkmsgbox.showerror(title="Save Error", message=str(e), icon="error")

        def clear_result_frame():
            for w in result_frame.winfo_children():
                w.destroy()

        def handle_submit():
            given = entry_var.get().strip()
            correct_answer = question.answer.strip()

            correct = (given.lower() == correct_answer.lower())
            clear_result_frame()

            if not correct:
                # Check if there is a question with same question:
                for _, other_question in self._question_set.question_items():
                    if other_question.question.strip().lower() == given.lower():
                        label = ttk.Label(result_frame, text=f"Correct but please give another word.", foreground="orange")
                        label.grid(column=0, row=0, sticky="W", padx=PADDING, pady=PADDING)
                        return

                # Check if there is a question with same answer:
                other_questions: list[str] = []
                for _, other_question in self._question_set.question_items():
                    if other_question.answer.strip().lower() == given.lower():
                        other_questions.append(other_question.question)
                
                if len(other_questions) > 0:
                    clear_result_frame()
                    label = ttk.Label(result_frame, text=f"'{given}' is correct for:", foreground="red")
                    label.grid(column=0, row=1, sticky="W", padx=PADDING, pady=PADDING)

                    for idx, oq in enumerate(other_questions):
                        if idx == len(other_questions) - 1:
                            sep = "."
                        else:
                            sep = ","
                        
                        oq_label = ttk.Label(result_frame, text=f"'{oq}'" + sep, foreground="red")
                        oq_label.grid(column=idx + 1, row=1, sticky="W", padx=PADDING, pady=PADDING)
                    
                # Incorrect answer
                label = ttk.Label(result_frame, text=f"Incorrect. Correct answer: '{correct_answer}'", foreground="red")
                label.grid(column=0, row=0, sticky="W", padx=PADDING, pady=PADDING, columnspan=max(len(other_questions), 1))
            else:
                label = ttk.Label(result_frame, text="Correct!", foreground="green")
                label.grid(column=0, row=0, sticky="W", padx=PADDING, pady=PADDING)
            
            # Update score
            question.update_score(correct)
            do_save()

            # Disable entry
            answer_entry.config(state="disabled")

            # Add edit button

            edit_btn = ttk.Button(question_frame)
            edit_btn.grid(column=0, row=1, padx=PADDING, pady=PADDING)

            def edit_callback():
                def on_deleted():
                    self._question_set.delete_question(self._question_idx)
                    do_save()
                    if on_deleted is not None:
                        on_deleted()
                
                row = SetPage.Row(
                    question_frame,
                    question,
                    tk.BooleanVar(value=True),
                    on_deleted
                )
                row.grid(column=0, row=0, sticky="EW")

                def confirm_callback():
                    row.make_editable(False)
                    edit_btn.config(text="Edit", command=edit_callback)
                
                edit_btn.config(text="Confirm", command=confirm_callback)
            edit_btn.config(text="Edit", command=edit_callback)

            # Call on_answered callback after updating
            if on_answered is not None:
                on_answered()


        submit_btn = ttk.Button(root, text="Submit", command=handle_submit)
        submit_btn.grid(padx=PADDING, pady=PADDING)

        # Allow pressing Enter to submit
        answer_entry.bind("<Return>", lambda e: handle_submit())

        # Give focus to entry
        answer_entry.focus_set()