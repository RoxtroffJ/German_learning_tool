import math
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

    # Score exponent selection
    ttk.Label(parent, text="Select Score Lifetime:").grid(column=0, row=3, pady=PADDING)
    score_exponent_spinbox = tk.Spinbox(parent, from_=0.001, to=10**9, increment=1, width=5)
    score_exponent_spinbox.grid(column=0, row=4, pady=PADDING)
    score_exponent_spinbox.delete(0, tk.END)  # type: ignore
    score_exponent_spinbox.insert(0, str(settings.score_exponent))

    def on_score_exponent_changed():
        try:
            exponent = float(score_exponent_spinbox.get())
            _apply_score_exponent(exponent)
            settings.edit_score_memory(exponent)
        except ValueError:
            pass

    score_exponent_spinbox.config(command=on_score_exponent_changed)

    # Insistence exponent selection
    ttk.Label(parent, text="Select Insistence:").grid(column=0, row=5, pady=PADDING)
    insistence_exponent_spinbox = tk.Spinbox(parent, from_=1, to=10, increment=0.1, width=5)
    insistence_exponent_spinbox.grid(column=0, row=6, pady=PADDING)
    insistence_exponent_spinbox.delete(0, tk.END)  # type: ignore
    insistence_exponent_spinbox.insert(0, str(settings.insistence_exponent))

    def on_insistence_exponent_changed():
        try:
            exponent = float(insistence_exponent_spinbox.get())
            _apply_insistence_exponent(exponent)
            settings.edit_insistence_exponent(exponent)
        except ValueError:
            pass

    insistence_exponent_spinbox.config(command=on_insistence_exponent_changed)

    return parent


def _apply_theme(theme: str):
    """Applies the given theme to the application."""
    style = ttk.Style()
    style.theme_use(theme)
    set_custom_styles()

def _apply_score_exponent(exponent: float):
    """Applies the given score exponent to the application."""
    import lib.score as score
    
    score.SCORE_LIFETIME = math.exp(-1 / exponent)

def _apply_insistence_exponent(exponent: float):
    """Applies the given insistence exponent to the application."""
    import guilib.question_gui as question_gui

    question_gui.INSISTENCE = exponent

def apply_settings(settings: Settings):
    """Applies the given settings to the application."""
    _apply_theme(settings.theme)
    _apply_score_exponent(settings.score_exponent)
    _apply_insistence_exponent(settings.insistence_exponent)