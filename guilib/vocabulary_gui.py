import tkinter as tk
from tkinter import ttk

from guilib import *
from guilib import selection_buttons
from guilib.pages import *
from guilib.tree_selection_state import *

from tree import Path as TreePath

from lib.vocabulary import *

_HP = TypeVar("_HP", bound=HeaderedPage[Any], covariant=True)

class VocabularySelectionPage(TreePages.TreeSubPage[_HP], Generic[_HP]):
    """A page to select the vocabulary questions sets."""

    def __init__(
            self, 
            menu_treer: TreePages[_HP, Page], 
            parent: Page, 
            selection_state: TreeSelectionState, 
            parent_path: TreePath, 
            sticky: str | None = None, 
            back: bool = True, 
            home: bool = False
    ):
        """Creates a vocabulary selection page in a TreePages structure."""

        # Register vocabulary section in the selection state
        self._path = selection_state.add_node(parent_path)

        # Create the page
        page = menu_treer.create_subpage(parent, sticky=sticky, back=back, home=home)
        self.__dict__.update(page.__dict__)

        frame = self.frame()

        # Load the sets
        question_sets = QuestionSet.load_all()

        # Register each set in the selection state
        self.sets: dict[str, tuple[QuestionSet, TreePath]] = {}

        for qset in question_sets:
            path = selection_state.add_node(self._path)
            # store an independent Path value (use .indices which already copies)
            self.sets[qset.name] = qset, TreePath(path.indices)

        # Label
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="Vocabulary Sets:").grid(column=0, row=0, pady=PADDING)

        # Scrollable frame for the buttons
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview) # type: ignore
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.columnconfigure(0, weight=1)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(column=0, row=1, sticky="NSEW")
        scrollbar.grid(column=1, row=1, sticky="NS")
        frame.rowconfigure(1, weight=1)

        # Buttons for each set
        for idx, qset_name in enumerate(sorted(self.sets.keys())):
            (qset, path) = self.sets[qset_name]

            # Create a fresh Path object from indices to avoid any mutation/share
            p = TreePath(path.indices)

            btn = ttk.Button(scrollable_frame, text=qset_name, command = lambda p=p: selection_state.select_all_callback(p))
            btn.grid(column=0, row=idx, pady=(0, PADDING), sticky="EW")

            selection_buttons.stylify_button(
                btn,
                selection_state,
                p,
            )

