import tkinter as tk
from tkinter import ttk

PADDING = 5

class Page:
    """A Frame, but with extra functionality"""
    def __init__(self, frame: ttk.Frame | tk.Frame, sticky: str = "NSEW"):
        self._frame = frame
        self.sticky = sticky
    
    def frame(self):
        """Returns the frame in which you draw."""
        return self._frame
    
    def full_frame(self):
        """Returns the full frame, including things that are not in the standard frame. Use this one to display."""
        return self._frame
        

class PageSwitcher:
    """Manages page display in a root component. Allows to switch to a new page easily. 
    Does not stores the pages, this is up to you."""
    
    def __init__(self, root: tk.Misc):
        self.root = root
        self.__current_page = None
    

    def create_page(self, sticky: str = "NSEW"):
        """Creates a new page in the root component and returns it."""

        frame = ttk.Frame(self.root)

        page = Page(frame, sticky=sticky)

        return page
    
    def show_page(self, page: Page):
        """Shows the page. Undefined behaviour if the page has not been created in the root component."""

        if self.__current_page is not None:
            self.__current_page.full_frame().grid_remove()
        
        page.full_frame().grid(column=0, row=0, sticky=page.sticky)
        self.__current_page = page



class TreePages:
    """Class to help with pages in a tree structure, where each page can have multiple subpages.
    Works together with PageManager.
    Each page has options to go back to the parent page or to the root page.
    """

    def __init__(self, page_switcher: PageSwitcher, sticky: str = "NSEW"):
        self._page_switcher = page_switcher

        self._sticky = sticky
        self._root = page_switcher.create_page(sticky=sticky)
        
    
    def get_root(self):
        """Returns the root page."""
        return self._root            

    class __TreeSubPage(Page):
        """A subpage created by TreePages."""
        def __init__(self, tree_page: "TreePages", parent: Page, sticky: str | None = None, back: bool = True, home: bool = False):
            if sticky is None:
                sticky = tree_page._sticky

            sub_page = tree_page._page_switcher.create_page(sticky="NSEW")
            self.sticky = "NSEW"

            main_frame = sub_page.frame()
            if back:
                # Back button to parent
                back_button = ttk.Button(main_frame, text="Back", command=lambda: tree_page._page_switcher.show_page(parent))
                back_button.grid(column=0, row=0, padx=PADDING, pady=PADDING, sticky="W")
            else:
                back_button = None

            if home:
                # Home button to root
                home_button = ttk.Button(main_frame, text="Home", command=lambda: tree_page._page_switcher.show_page(tree_page._root))
                home_button.grid(column=1 if back else 0, row=0, padx=PADDING, pady=PADDING, sticky="E")
            else:
                home_button = None

            row = 1 if back or home else 0

            frame = ttk.Frame(main_frame)
            frame.grid(column=0, row=row, sticky=sticky, columnspan=2)

            main_frame.columnconfigure(0, weight=1)
            main_frame.rowconfigure(row, weight=1)

            self._frame = main_frame
            self._sub_frame = frame

        def frame(self):
            return self._sub_frame
        
        def full_frame(self):
            return self._frame

    def create_subpage(self, parent: Page, sticky: str | None = None, back: bool = True, home: bool = False):
        """
        Creates a subpage of the given parent page.
        Undefined behaviour if the parent page has not been created in the root component.
        """
        
        return self.__TreeSubPage(self, parent, sticky=sticky, back=back, home=home)