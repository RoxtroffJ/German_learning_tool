import tkinter as tk

from typing import Callable, Generic, TypeVar, overload

from guilib.pages import Page

_P = TypeVar("_P", bound=Page, covariant=True)
_P2 = TypeVar("_P2", bound=Page, covariant=True)

class PageSwitcher(Generic[_P]):
    """Manages page display in a root component. Allows to switch to a new page easily. 
    Does not stores the pages, this is up to you."""
    
    def __init__(self, root: tk.Misc, page_maker: Callable[[tk.Misc, str], _P] = Page):
        self.__root = root
        self.__current_page = None
        self._page_maker = page_maker
    
    @overload
    def create_page(self, *, sticky: str = ..., page_maker: None = ...) -> _P: ...
    @overload
    def create_page(self, *, sticky: str = ..., page_maker: Callable[[tk.Misc, str], _P2]) -> _P2: ...

    def create_page(self, sticky: str = "NSEW", page_maker: Callable[[tk.Misc, str], _P2] | None = None):
        """Creates a new page in the root component and returns it."""

        pager = page_maker if page_maker is not None else self._page_maker
        
        page = pager(self.__root, sticky)

        return page


    def show_page(self, page: Page):
        """Shows the page. Undefined behaviour if the page has not been created in the root component."""

        if self.__current_page is not None:
            self.__current_page.hide_page()
        
        page.display_page()
        self.__current_page = page