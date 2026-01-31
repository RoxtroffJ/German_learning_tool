#import tkinter as tk
from tkinter import ttk

from guilib import *
from guilib import selection_buttons
from guilib.pages import *
from guilib.tree_selection_state import *

from tree import Path as TreePath

from lib.vocabulary import *

_HP = TypeVar("_HP", bound=HeaderedPage[Any], covariant=True)

class VocabularySelectionPage(selection_buttons.HeaderedWithSelectAll[TreePages.TreeSubPage[_HP]], Generic[_HP]):
    """A page to select the vocabulary questions sets."""

    def __init__(
            self, 
            menu_treer: TreePages[_HP, Page], 
            parent: Page, 
            selection_state: TreeSelectionState, 
            parent_path: TreePath, 
            sticky: str | None = "NSEW", 
            back: bool = True, 
            home: bool = False
    ):
        """Creates a vocabulary selection page in a TreePages structure."""

        # Register vocabulary section in the selection state
        self._path = selection_state.add_node(parent_path)

        # Create the page
        page = menu_treer.create_subpage(parent, sticky=sticky, back=back, home=home)

        frame = page.frame()

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
        
        scrollable_frame_area = ttk.Frame(frame)
        scrollable_frame_area.grid(column=0, row=1, sticky="NSEW")

        frame.rowconfigure(1, weight=1)


        scrollbar_page = ScrollablePage(scrollable_frame_area)

        scrollbar_page.display_page()
        scrollable_frame = scrollbar_page.frame()

        # Buttons for each set

        scrollable_frame.columnconfigure(0, weight=1)

        for idx, qset_name in enumerate(sorted(self.sets.keys())):
            (qset, path) = self.sets[qset_name]

            # Create a fresh Path object from indices to avoid any mutation/share
            p = TreePath(path.indices)

            btn = ttk.Button(scrollable_frame, text=qset_name, command = lambda p=p: selection_state.select_all_callback(p))
            # Center the button within the full-width grid cell.
            btn.grid(column=0, row=idx, pady=(0, PADDING))

            selection_buttons.stylify_button(
                btn,
                selection_state,
                p,
            )
        
        page_with_select_all = selection_buttons.HeaderedWithSelectAll(
            page,
            selection_state,
            self._path,
        )

        self.__dict__.update(page_with_select_all.__dict__)

