import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import tkinter as tk
from tkinter import ttk

from guilib import *
from guilib.pages import *
import guilib.settings_gui as settings_gui
import guilib.vocabulary_gui as vocabulary_gui
from guilib.tree_selection_state import TreeSelectionState
import guilib.selection_buttons as selection_buttons
from guilib.question_gui import QuestionDrawer, QuestionnerPage, ToQuestionDrawer

from tree import Path

main, settings = init_gui()

selection_state = TreeSelectionState()

to_question_drawer_list: list[ToQuestionDrawer] = []
menu_pager = None
menu_treer = None
menu_page = None

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

	def callback():
		if menu_pager is not None:
			mper = menu_pager
		else:
			return
		if menu_treer is not None:
			mt = menu_treer
		else:
			return
		if menu_page is not None:
			mp = menu_page
		else:
			return
		
		question_drawers: list[QuestionDrawer] = []
		for to_qd in to_question_drawer_list:
			question_drawers.extend(to_qd.to_question_drawers())
		if len(question_drawers) == 0:
			return

		def empty_callback():
			mper.show_page(mp)
		
		def pager(root: tk.Misc, sticky: str):
			page = QuestionnerPage(
				root, 
				sticky, 
				question_list=question_drawers, 
				empty_callback=empty_callback
			)
			return HeaderedPage(page)

		question_page = mt.create_subpage(
			mp,
			page_maker=pager
		)
		mper.show_page(question_page)

	start_button = ttk.Button(footer_frame, command=callback)
	start_button.grid(column=0, row=0, pady=PADDING, padx=PADDING, sticky="EW")

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
menu_treer = TreePages(menu_pager, sticky="NSEW")

# Pages

menu_page = menu_treer.get_root()
menu_frame = menu_page.frame


vocab_page = vocabulary_gui.VocabularySelectionPage(
	menu_treer,
	menu_page,
	selection_state,
	Path([]),
	no_go_page_maker=no_foot_page_maker
)
to_question_drawer_list.append(vocab_page)

grammar_page = menu_treer.create_subpage(menu_page, home=True)
grammar_frame = grammar_page.frame
grammar_frame.columnconfigure(0, weight=1)

settings_page = settings_gui.settings_tree_page(settings_gui.load_settings(), menu_treer, menu_page, home=True, page_maker=no_foot_page_maker)

# Functions to switch between frames
def show_vocab():
	if menu_pager is not None:
		menu_pager.show_page(vocab_page)

def show_grammar():
	if menu_pager is not None:
		menu_pager.show_page(grammar_page)

def show_settings():
	if menu_pager is not None:
		menu_pager.show_page(settings_page)

# Menu contents
ttk.Label(menu_frame, text="Choose an activity:").grid(column=0, row=0, pady=PADDING)
voc_button = ttk.Button(menu_frame, text="Vocabulary Practice", command=show_vocab)
voc_button.grid(column=0, row=1, padx=PADDING, pady=PADDING, sticky="ew")
voc_select_all = vocab_page.select_all_button(menu_frame)
voc_select_all.grid(column=1, row=1, padx=PADDING, pady=PADDING, sticky="ew")

ttk.Button(menu_frame, text="Grammar Exercises", command=show_grammar).grid(column=0, row=2, padx=PADDING, pady=PADDING, sticky="ew")

selection_buttons.select_all_button(menu_frame, selection_state, Path([])).grid(column=0, row=3, columnspan=2, padx=PADDING, pady=PADDING, sticky="ew")

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