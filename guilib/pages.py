import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Generic, Type, TypeVar, overload
from typing import cast

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


_P = TypeVar("_P", bound=Page, covariant=True)

class HeaderedPage(Generic[_P], Page):
    """A page with a header frame on top."""
    def __init__(self, page: _P, header_sticky: str = "EW"):
        self._root = page._root

        self.__main_page: _P = page

        self._header_frame = ttk.Frame(self._root)

        self.__header_sticky = header_sticky

    @property
    def inner_page(self) -> _P:
        """Returns the inner main page."""
        return self.__main_page

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

    def frame(self):
        """Returns the main frame in which you draw."""
        return self.__main_page.frame()
    
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

_P2 = TypeVar("_P2", bound=Page, covariant=True)

class PageSwitcher(Generic[_P]):
    """Manages page display in a root component. Allows to switch to a new page easily. 
    Does not stores the pages, this is up to you."""
    
    def __init__(self, root: tk.Misc, page_maker: Callable[[tk.Misc, str], _P] = Page):
        self.root = root
        self.__current_page = None
        self._page_maker = page_maker
    
    @overload
    def create_page(self, *, sticky: str = ..., page_maker: None = ...) -> _P: ...
    @overload
    def create_page(self, *, sticky: str = ..., page_maker: Callable[[tk.Misc, str], _P2]) -> _P2: ...

    def create_page(self, sticky: str = "NSEW", page_maker: Callable[[tk.Misc, str], _P2] | None = None) -> _P | _P2:
        """Creates a new page in the root component and returns it."""

        pager = page_maker if page_maker is not None else self._page_maker
        
        page = pager(self.root, sticky)

        return page


    def show_page(self, page: Page):
        """Shows the page. Undefined behaviour if the page has not been created in the root component."""

        if self.__current_page is not None:
            self.__current_page.hide_page()
        
        page.display_page()
        self.__current_page = page

_HP = TypeVar("_HP", bound=HeaderedPage[Any], covariant=True)
_RT = TypeVar("_RT", bound=Page, covariant=True)

_S = TypeVar("_S", bound="TreePages[Any, Any]", covariant=True)

_HP2 = TypeVar("_HP2", bound=HeaderedPage[Any], covariant=True)

class TreePages(Generic[_HP, _RT]):
    """Class to help with pages in a tree structure, where each page can have multiple subpages.
    Works together with PageManager.
    Each page has options to go back to the parent page or to the root page.
    """

    @overload
    def __new__(
        cls: Type["TreePages[_HP, _HP]"], 
        page_switcher: PageSwitcher[_HP], *, 
        sticky: str = ..., 
        root_page_maker: None = ...
    ) -> "TreePages[_HP, _HP]": ...
    
    @overload
    def __new__(
        cls: Type["TreePages[_HP, _RT]"], 
        page_switcher: PageSwitcher[_HP], *, 
        sticky: str = ..., 
        root_page_maker: Callable[[tk.Misc, str], _RT]
    ) -> "TreePages[_HP, _RT]": ...
    
    def __new__(
            cls: Type[_S], 
            page_switcher: PageSwitcher[HeaderedPage[_P]], *, 
            sticky: str = "NSEW", 
            root_page_maker: Callable[[tk.Misc, str], _RT] | None = None
        ) -> _S:
        
        # runtime implementation compatible with the overloads: return instance of `cls` (type S)
        return cast(_S, object.__new__(cast(Type[object], cls)))

    def __init__(self, page_switcher: PageSwitcher[HeaderedPage[_P]], *, sticky: str = "NSEW", root_page_maker: Callable[[tk.Misc, str], _RT] | None = None):
        self._page_switcher = page_switcher

        self._sticky = sticky
        self._root = page_switcher.create_page(sticky=sticky, page_maker=root_page_maker)

    def get_root(self):
        """Returns the root page with its precise type `_RT`."""
        return self._root

    class TreeSubPage(HeaderedPage[Any], Generic[_HP2]):
        """A subpage created by TreePages."""
        @overload
        def __init__(
                self, 
                tree_page: "TreePages[_HP2, Page]", 
                parent: Page, 
                *,
                sticky: str | None = None, 
                header_sticky: str | None = None, 
                back: bool = True, 
                home: bool = False,
                back_confirm: Callable[[], bool] | None = None,
                home_confirm: Callable[[], bool] | None = None,
                page_maker: None = None
        ) -> None: ...
        @overload
        def __init__(
                self, 
                tree_page: "TreePages[HeaderedPage[Any], Page]", 
                parent: Page, 
                *,
                sticky: str | None = None, 
                header_sticky: str | None = None, 
                back: bool = True, 
                home: bool = False,
                back_confirm: Callable[[], bool] | None = None,
                home_confirm: Callable[[], bool] | None = None,
                page_maker: Callable[[tk.Misc, str], _HP2]
        ) -> None: ...

        def __init__(
                self, 
                tree_page: "TreePages[_HP2, Page] | TreePages[HeaderedPage[Any], Page]", 
                parent: Page, 
                sticky: str | None = None, 
                header_sticky: str | None = None, 
                back: bool = True, 
                home: bool = False,
                back_confirm: Callable[[], bool] | None = None,
                home_confirm: Callable[[], bool] | None = None,
                page_maker: Callable[[tk.Misc, str], HeaderedPage[_P2]] | None = None
        ):
            
            if sticky is None:
                sticky = tree_page._sticky

            # Initialize itself as a new page in the page switcher
            self.__dict__.update(tree_page._page_switcher.create_page(sticky=sticky, page_maker=page_maker).__dict__)

            # Header frame

            header_frame = self._header_frame
            
            if back:

                def callback():
                    if back_confirm is None or back_confirm():
                        tree_page._page_switcher.show_page(parent)

                # Back button to parent
                back_button = ttk.Button(header_frame, text="Back", command=callback)
                back_button.grid(column=0, row=0, padx=PADDING, sticky="W")
            else:
                back_button = None

            if home:
                # Home button to root
                def callback():
                    if home_confirm is None or home_confirm():
                        tree_page._page_switcher.show_page(tree_page._root)

                home_button = ttk.Button(header_frame, text="Home", command=callback)
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

    
    @overload
    def create_subpage(
        self, parent: Page, *,
        sticky: str | None = ..., 
        back: bool = ..., home: bool = ..., 
        back_confirm: Callable[[], bool] | None = ...,
        home_confirm: Callable[[], bool] | None = ...,
        page_maker: None = ...) -> "TreePages.TreeSubPage[_HP]": ...

    @overload
    def create_subpage(
        self, parent: Page, *,
        sticky: str | None = ..., 
        back: bool = ..., home: bool = ..., 
        back_confirm: Callable[[], bool] | None = ...,
        home_confirm: Callable[[], bool] | None = ...,
        page_maker: Callable[[tk.Misc, str], HeaderedPage[_HP2]]) -> "TreePages.TreeSubPage[_HP2]": ...

    def create_subpage(
        self, parent: Page, 
        sticky: str | None = None, 
        back: bool = True, home: bool = False, 
        back_confirm: Callable[[], bool] | None = None,
        home_confirm: Callable[[], bool] | None = None,
        page_maker: Callable[[tk.Misc, str], HeaderedPage[_HP2]] | None = None
    ):
        """
        Creates a subpage of the given parent page.
        Undefined behaviour if the parent page has not been created in the root component.
        """
        
        return self.TreeSubPage(
            self, 
            parent, 
            sticky=sticky, 
            back=back, 
            home=home, 
            back_confirm=back_confirm, 
            home_confirm=home_confirm, 
            page_maker=page_maker)


