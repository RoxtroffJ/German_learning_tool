import tkinter as tk
from tkinter import ttk

from guilib import *
from guilib.pages import *
import guilib.settings_gui as settings_gui
import guilib.vocabulary_gui as vocabulary_gui
from guilib.tree_selection_state import TreeSelectionState
import guilib.selection_buttons as selection_buttons
from tree import Path


main, settings = init_gui()

selection_state = TreeSelectionState()

def no_foot_page_maker(root: tk.Misc, sticky: str):
	page = Page(root, sticky)
	header_page = HeaderedPage(page, header_sticky="EW")

	return header_page

def menu_page_maker(root: tk.Misc, sticky: str):
	page = Page(root, sticky)
	footer_page = FooteredPage(page, footer_sticky="EW")
	header_footer_page = HeaderedPage(footer_page, header_sticky="EW")

	footer_frame = footer_page.footer_frame()
	footer_frame.columnconfigure(0, weight=1)

	start_button = ttk.Button(footer_frame)
	start_button.grid(column=0, row=0, pady=PADDING)

	def formatter(selected: bool, nb_selected: int) -> str:
		if nb_selected == 0:
			# Disable button if nothing selected
			start_button.config(state = tk.DISABLED)
			return "Start"
		else:
			# Enable button
			start_button.config(state = tk.NORMAL)
			return f"Start ({nb_selected} selected)"

	selection_buttons.stylify_button(
		start_button, 
		selection_state, 
		Path([]),
		label_format=formatter
	)


	return header_footer_page

menu_pager = PageSwitcher(main, page_maker=menu_page_maker)
menu_treer = TreePages(menu_pager, sticky="EW")

# Pages

menu_page = menu_treer.get_root()
menu_frame = menu_page.frame()
menu_frame.columnconfigure(0, weight=1)

vocab_page = vocabulary_gui.VocabularySelectionPage(
	menu_treer,
	menu_page,
	selection_state,
	Path([])
)

grammar_page = menu_treer.create_subpage(menu_page, home=True)
grammar_frame = grammar_page.frame()
grammar_frame.columnconfigure(0, weight=1)

settings_page = settings_gui.settings_tree_page(settings_gui.load_settings(), menu_treer, menu_page, home=True, page_maker=no_foot_page_maker)

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

# Grammar activity contents (dummy)
ttk.Label(grammar_frame, text="Grammar Exercises (Coming Soon!)").grid(column=0, row=0, pady=PADDING)

# Start with menu visible
menu_pager.show_page(menu_page)

main.mainloop()