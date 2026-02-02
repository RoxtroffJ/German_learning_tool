import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as tkmsgbox

from guilib import *
from guilib.pages import *

from lib.settings import *

def load_settings() -> Settings:
    """Loads and applies the settings from the settings file."""
    settings = Settings.load()
    apply_settings(settings)
    return settings

_HP = TypeVar("_HP", bound=HeaderedPage[Any], covariant=True)

def settings_tree_page(
        settings: Settings, 
        menu_treer: TreePages[HeaderedPage[Any], Page], 
        parent: Page, 
        *,
        sticky: str | None = None, 
        back: bool = True, 
        home: bool = False, 
        page_maker: Callable[[tk.Misc, str], _HP]
) -> TreePages.TreeSubPage[_HP]:
    """Creates a TreePages for settings pages."""
    # Save confirmation dialog
    def exit_confirm() -> bool:
        if not settings.needs_saving():
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
            settings.save()
        else:
            settings.restore()
            apply_settings(settings)
        return True

    # Create the page
    page = menu_treer.create_subpage(parent, sticky=sticky, back=back, home=home, back_confirm=exit_confirm, home_confirm=exit_confirm, page_maker=page_maker)

    frame = page.frame
    _draw_settings_frame(frame, settings)

    return page


def _draw_settings_frame(parent: tk.Misc, settings: Settings):
    """Draws the settings frame contents in parent.
    Assumes parent is empty.
    """
    parent.columnconfigure(0, weight=1)

    ttk.Label(parent, text="Settings").grid(column=0, row=0, pady=PADDING)

    # Theme selection
    ttk.Label(parent, text="Select Theme:").grid(column=0, row=1, pady=PADDING)
    style = ttk.Style()
    theme_combobox = ttk.Combobox(parent, values=style.theme_names(), state="readonly")

    theme_combobox.grid(column=0, row=2, pady=PADDING)
    theme_combobox.set(style.theme_use())

    def on_theme_selected(event: tk.Event):
        theme = theme_combobox.get()
        _apply_theme(theme)
        settings.edit_theme(theme)

    theme_combobox.bind("<<ComboboxSelected>>", on_theme_selected)

    return parent


def _apply_theme(theme: str):
    """Applies the given theme to the application."""
    style = ttk.Style()
    style.theme_use(theme)
    set_custom_styles()

def apply_settings(settings: Settings):
    """Applies the given settings to the application."""
    _apply_theme(settings.theme)