import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Generic, Type, TypeVar, cast, overload

from guilib import PADDING
from guilib.pages import HeaderedPage, Page, PageSwitcher

_P = TypeVar("_P", bound=Page, covariant=True)
_P2 = TypeVar("_P2", bound=Page, covariant=True)

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

    def __init__(
            self, 
            page_switcher: PageSwitcher[HeaderedPage[_P]], *, 
            sticky: str = "NSEW", 
            root_page_maker: Callable[[tk.Misc, str], _RT] | None = None
    ):
        self._page_switcher = page_switcher

        self._sticky = sticky
        self._root = cast(_RT, page_switcher.create_page(sticky=sticky, page_maker=root_page_maker))

    def get_root(self) -> _RT:
        """Returns the root page with its precise type `_RT`."""
        return self._root

    @property
    def page_switcher(self):
        """Returns the underlying PageSwitcher."""
        return self._page_switcher

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
            
            self.back_confirm = back_confirm
            self.home_confirm = home_confirm

            if sticky is None:
                sticky = tree_page._sticky

            # Initialize itself as a new page in the page switcher
            base_page = tree_page._page_switcher.create_page(sticky=sticky, page_maker=page_maker)

            self.__dict__.update(base_page.__dict__)

            self.__header_sticky = header_sticky or base_page.header_sticky
            
            # Header frame

            header_frame = self._header_frame
            
            if back:

                def callback():
                    if self.back_confirm is None or self.back_confirm():
                        tree_page._page_switcher.show_page(parent)

                # Back button to parent
                back_button = ttk.Button(header_frame, text="Back", command=callback)
                back_button.grid(column=0, row=0, padx=PADDING, sticky="W")
            else:
                back_button = None

            if home:
                # Home button to root
                def callback():
                    if self.home_confirm is None or self.home_confirm():
                        tree_page._page_switcher.show_page(tree_page._root)

                home_button = ttk.Button(header_frame, text="Home", command=callback)
                home_button.grid(column=1, row=0, padx=PADDING, sticky="W")
            else:
                home_button = None

            sub_header = ttk.Frame(header_frame)
            sub_header.grid(column=2, row=0, sticky=self.__header_sticky)

            header_frame.columnconfigure(2, weight=1)

            self._sub_header_frame = sub_header
            self.home_button = home_button
            self.back_button = back_button
        
        def header_frame(self):
            return self._sub_header_frame

        @property
        def header_sticky(self) -> str:
            """Returns the header sticky."""
            return self.__header_sticky
    
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
        page_maker: Callable[[tk.Misc, str], _HP2]) -> "TreePages.TreeSubPage[_HP2]": ...

    def create_subpage(
        self, parent: Page, 
        sticky: str | None = None, 
        back: bool = True, home: bool = False, 
        back_confirm: Callable[[], bool] | None = None,
        home_confirm: Callable[[], bool] | None = None,
        page_maker: Callable[[tk.Misc, str], _HP2] | None = None
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
