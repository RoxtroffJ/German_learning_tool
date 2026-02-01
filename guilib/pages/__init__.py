import tkinter as tk
from tkinter import ttk
from typing import Generic, TypeVar

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

    @property
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


_P = TypeVar("_P", bound=Page, covariant=True)

class HeaderedPage(Generic[_P], Page):
    """A page with a header frame on top."""
    def __init__(self, page: _P, header_sticky: str = "EW"):
        self._root = page._root

        self.__main_page: _P = page

        self._header_frame = ttk.Frame(self._root)

        self.__header_sticky = header_sticky

    @property
    def header_sticky(self) -> str:
        """Returns the header sticky."""
        return self.__header_sticky

    @property
    def inner_page(self) -> _P:
        """Returns the inner main page."""
        return self.__main_page

    @property
    def frame(self):
        """Returns the main frame in which you draw."""
        return self.__main_page.frame
    
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

class FooteredPage(Generic[_P], Page):
    """A page with a footer frame on bottom."""
    def __init__(self, page: _P, footer_sticky: str = "EW"):
        self._root = page._root

        self.__main_page: _P = page

        self._footer_frame = ttk.Frame(self._root)

        self.__footer_sticky = footer_sticky

    @property
    def inner_page(self) -> _P:
        """Returns the inner main page."""
        return self.__main_page
    @property
    def frame(self):
        """Returns the main frame in which you draw."""
        return self.__main_page.frame
    
    def footer_frame(self):
        """Returns the footer frame in which you can draw."""
        return self._footer_frame
    
    def _display_page_at(self, column: int = 0, row: int = 0, columnspan: int = 1, rowspan: int = 1) -> tuple[int, int]:
        """Display the page at given grid position, and returns the column and row span used."""

        footer_rowspan = 1
        main_rowspan = max(rowspan - footer_rowspan, 1)

        main_columnspan, main_rowspan = self.__main_page._display_page_at(column, row, columnspan, main_rowspan)
        
        self._footer_frame.grid(column=column, row=row + main_rowspan, columnspan=main_columnspan, rowspan=footer_rowspan, sticky=self.__footer_sticky)
        
        return main_columnspan, main_rowspan + footer_rowspan
    
    def hide_page(self):
        """Hide the page."""
        self.__main_page.hide_page()
        self._footer_frame.grid_remove()


from guilib.pages.page_switcher import *


from guilib.pages.tree_pages import *


from guilib.pages.scrollable import *