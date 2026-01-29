import tkinter as tk
from tkinter import ttk
from typing import Callable, Generic, TypeVar

from guilib import *

class Page:
    """A Frame, but with extra functionality"""
    def __init__(self, root: tk.Misc, sticky: str = "NSEW"):
        full_frame = ttk.Frame(root)

        self.__full_frame = full_frame
        # remember where this page was last gridded so we can restore
        # weights when hiding without touching unrelated rows/columns
        self.__last_grid: tuple[int, int, int, int] | None = None
        self._root = root
        self.__sticky = sticky

    def frame(self):
        """Returns the main frame in which you draw."""
        return self.__full_frame
    
    def display_page(self):
        """Display the page."""
        self._display_page_at()

    def hide_page(self):
        """Hide the page."""
        self.__full_frame.grid_remove()
        # Reset only the specific column/row weights that were set when
        # the page was displayed. Avoid resetting all columns on the
        # root which can create unexpected empty space elsewhere.
        if self.__last_grid is not None:
            col, row, colspan, rowspan = self.__last_grid
            if colspan == 1:
                try:
                    self._root.columnconfigure(col, weight=0)
                except Exception:
                    pass
            if rowspan == 1:
                try:
                    self._root.rowconfigure(row, weight=0)
                except Exception:
                    pass
    
    def _display_page_at(self, column: int = 0, row: int = 0, columnspan: int = 1, rowspan: int = 1) -> tuple[int, int]:
        """Display the page at given grid position, and returns the column and row span used."""
        self.__full_frame.grid(column=column, row=row, columnspan=columnspan, rowspan=rowspan, sticky=self.__sticky)
        # remember where we were gridded so hide_page can undo weights
        self.__last_grid = (column, row, columnspan, rowspan)
        if columnspan == 1:
            self._root.columnconfigure(column, weight=1)
        if rowspan == 1:
            self._root.rowconfigure(row, weight=1)
        
        return columnspan, rowspan


class HeaderedPage(Page):
    """A page with a header frame on top."""
    def __init__(self, page: Page, header_sticky: str = "EW"):
        self._root = page._root
        
        self.__main_page = page

        self._header_frame = ttk.Frame(self._root)

        self.__header_sticky = header_sticky

    def frame(self):
        """Returns the main frame in which you draw."""
        return self.__main_page.frame()
    
    def header_frame(self):
        """Returns the header frame in which you can draw."""
        return self._header_frame
    
    def _display_page_at(self, column: int = 0, row: int = 0, columnspan: int = 1, rowspan: int = 1) -> tuple[int, int]:
        """Display the page at given grid position, and returns the column and row span used."""

        header_rowspan = 1
        main_rowspan = max(rowspan - header_rowspan, 1)

        main_columnspan, main_rowspan = self.__main_page._display_page_at(column, row + header_rowspan, columnspan, main_rowspan)
        
        self._header_frame.grid(column=column, row=row, columnspan=main_columnspan, rowspan=header_rowspan, sticky=self.__header_sticky)
        
        return main_columnspan, main_rowspan + header_rowspan
    
    def hide_page(self):
        """Hide the page."""
        self.__main_page.hide_page()
        self._header_frame.grid_remove()

P = TypeVar("P", bound=Page)

class PageSwitcher(Generic[P]):
    """Manages page display in a root component. Allows to switch to a new page easily. 
    Does not stores the pages, this is up to you."""
    
    def __init__(self, root: tk.Misc, page_maker: Callable[[tk.Misc, str], P] = Page):
        self.root = root
        self.__current_page = None
        self.__page_maker = page_maker
    

    def create_page(self, sticky: str = "NSEW"):
        """Creates a new page in the root component and returns it."""

        page = self.__page_maker(self.root, sticky)

        return page
    
    def show_page(self, page: Page):
        """Shows the page. Undefined behaviour if the page has not been created in the root component."""

        if self.__current_page is not None:
            self.__current_page.hide_page()
        
        page.display_page()
        self.__current_page = page



class TreePages(Generic[P]):
    """Class to help with pages in a tree structure, where each page can have multiple subpages.
    Works together with PageManager.
    Each page has options to go back to the parent page or to the root page.
    """

    def __init__(self, page_switcher: PageSwitcher[P], sticky: str = "NSEW"):
        self._page_switcher = page_switcher

        self._sticky = sticky
        self._root = page_switcher.create_page(sticky=sticky)
        
    
    def get_root(self):
        """Returns the root page."""
        return self._root            

    class TreeSubPage(HeaderedPage):
        """A subpage created by TreePages."""
        def __init__(self, tree_page: "TreePages[P]", parent: Page, sticky: str | None = None, header_sticky: str | None = None, back: bool = True, home: bool = False):
            if sticky is None:
                sticky = tree_page._sticky

            super().__init__(tree_page._page_switcher.create_page(sticky=sticky), header_sticky= header_sticky if header_sticky is not None else "EW")

            # Header frame

            header_frame = self._header_frame
            
            if back:
                # Back button to parent
                back_button = ttk.Button(header_frame, text="Back", command=lambda: tree_page._page_switcher.show_page(parent))
                back_button.grid(column=0, row=0, padx=PADDING, sticky="W")
            else:
                back_button = None

            if home:
                # Home button to root
                home_button = ttk.Button(header_frame, text="Home", command=lambda: tree_page._page_switcher.show_page(tree_page._root))
                home_button.grid(column=1, row=0, padx=PADDING, sticky="W")
            else:
                home_button = None

            sub_header = ttk.Frame(header_frame)
            sub_header.grid(column=2, row=0, sticky=(header_sticky or "EW"))

            header_frame.columnconfigure(2, weight=1)

            self._sub_header_frame = sub_header
            self.home_button = home_button
            self.back_button = back_button
        
        def header_frame(self):
            return self._sub_header_frame

    def create_subpage(self, parent: Page, sticky: str | None = None, back: bool = True, home: bool = False):
        """
        Creates a subpage of the given parent page.
        Undefined behaviour if the parent page has not been created in the root component.
        """
        
        return self.TreeSubPage(self, parent, sticky=sticky, back=back, home=home)

