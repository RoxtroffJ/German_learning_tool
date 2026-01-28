import tkinter as tk
from tkinter import ttk

from guilib import *


main = tk.Tk()
main.title("German Learning Tool")

main.columnconfigure(0, weight=1)
main.rowconfigure(0, weight=1)

menu_pager = PageSwitcher(main)
menu_treer = TreePages(menu_pager, sticky="EW")

# Frames

menu_page = menu_treer.get_root()
menu_frame = menu_page.frame()
menu_frame.columnconfigure(0, weight=1)

vocab_page = menu_treer.create_subpage(menu_page)
vocab_frame = vocab_page.frame()
vocab_frame.columnconfigure(0, weight=1)

grammar_page = menu_treer.create_subpage(menu_page)
grammar_frame = grammar_page.frame()
grammar_frame.columnconfigure(0, weight=1)

# Functions to switch between frames
def show_vocab():
	menu_pager.show_page(vocab_page)

def show_grammar():
	menu_pager.show_page(grammar_page)



# Menu contents
ttk.Label(menu_frame, text="Choose an activity:").grid(column=0, row=0, pady=PADDING)
ttk.Button(menu_frame, text="Vocabulary Practice", command=show_vocab).grid(column=0, row=1, pady=PADDING, sticky="ew")
ttk.Button(menu_frame, text="Grammar Exercises", command=show_grammar).grid(column=0, row=2, pady=PADDING, sticky="ew")
ttk.Button(menu_frame, text="Exit", command=main.quit).grid(column=0, row=4, pady=PADDING, sticky="ew")


# Vocab activity contents
ttk.Label(vocab_frame, text="Vocabulary Practice Activity (Coming Soon!)").grid(column=0, row=0, pady=PADDING)

# Grammar activity contents (dummy)
ttk.Label(grammar_frame, text="Grammar Exercises (Coming Soon!)").grid(column=0, row=0, pady=PADDING)

# Start with menu visible
menu_pager.show_page(menu_page)


main.mainloop()