import tkinter as tk
from tkinter import ttk

from guilib import *
from guilib.pages import *
import guilib.settings_gui as settings


main = tk.Tk()
main.title("German Learning Tool")

menu_pager = PageSwitcher(main, page_maker = lambda root, sticky: HeaderedPage(Page(root, sticky), header_sticky="EW"))
menu_treer = TreePages(menu_pager, sticky="EW")

# Frames

menu_page = menu_treer.get_root()
menu_frame = menu_page.frame()
menu_frame.columnconfigure(0, weight=1)

vocab_page = menu_treer.create_subpage(menu_page, home=True)
vocab_frame = vocab_page.frame()
vocab_frame.columnconfigure(0, weight=1)

grammar_page = menu_treer.create_subpage(menu_page, home=True)
grammar_frame = grammar_page.frame()
grammar_frame.columnconfigure(0, weight=1)

settings_page = settings.settings_tree_page(settings.load_settings(), menu_treer, menu_page, home=True)

# Functions to switch between frames
def show_vocab():
	menu_pager.show_page(vocab_page)

def show_grammar():
	menu_pager.show_page(grammar_page)

def show_settings():
	menu_pager.show_page(settings_page)

# Menu contents
ttk.Label(menu_frame, text="Choose an activity:").grid(column=0, row=0, pady=PADDING)
ttk.Button(menu_frame, text="Vocabulary Practice", command=show_vocab).grid(column=0, row=1, pady=PADDING, sticky="ew")
ttk.Button(menu_frame, text="Grammar Exercises", command=show_grammar).grid(column=0, row=2, pady=PADDING, sticky="ew")
ttk.Button(menu_frame, text="Exit", command=main.quit).grid(column=0, row=4, pady=PADDING, sticky="ew")

# Menu header
menu_header = menu_page.header_frame()
menu_header.columnconfigure(0, weight=1)

ttk.Label(menu_header, text="German Learning Tool").grid(column=0, row=0, padx=PADDING, sticky="W")
ttk.Button(menu_header, text="Settings", command=show_settings).grid(column=1, row=0, padx=PADDING, sticky="E")

# Vocab activity contents
ttk.Label(vocab_frame, text="Vocabulary Practice Activity (Coming Soon!)").grid(column=0, row=0, pady=PADDING)

# Grammar activity contents (dummy)
ttk.Label(grammar_frame, text="Grammar Exercises (Coming Soon!)").grid(column=0, row=0, pady=PADDING)

# Start with menu visible
menu_pager.show_page(menu_page)

main.mainloop()