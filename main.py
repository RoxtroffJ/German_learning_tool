import tkinter as tk
from tkinter import ttk

PADDING = 5

main = tk.Tk()
main.title("German Learning Tool")

main.columnconfigure(0, weight=1)
main.rowconfigure(0, weight=1)

# Frames

menu_frame = ttk.Frame(main, padding="10 10 10 10")
menu_frame.grid(column=0, row=0, sticky="EW")
menu_frame.columnconfigure(0, weight=1)

vocab_frame = ttk.Frame(main, padding="10 10 10 10")
vocab_frame.grid(column=0, row=0, sticky="NSEW")
vocab_frame.columnconfigure(0, weight=1)
vocab_frame.rowconfigure(0, weight=1)

grammar_frame = ttk.Frame(main, padding="10 10 10 10")
grammar_frame.grid(column=0, row=0, sticky="NSEW")
grammar_frame.columnconfigure(0, weight=1)
grammar_frame.rowconfigure(0, weight=1)

listen_frame = ttk.Frame(main, padding="10 10 10 10")
listen_frame.grid(column=0, row=0, sticky="NSEW")
listen_frame.columnconfigure(0, weight=1)
listen_frame.rowconfigure(0, weight=1)


# Functions to switch between frames
def show_vocab():
	menu_frame.grid_remove()
	vocab_frame.grid()


def show_menu():
	vocab_frame.grid_remove()
	grammar_frame.grid_remove()
	listen_frame.grid_remove()
	menu_frame.grid()


def show_grammar():
	menu_frame.grid_remove()
	grammar_frame.grid()


def show_listen():
	menu_frame.grid_remove()
	listen_frame.grid()



# Menu contents
ttk.Label(menu_frame, text="Choose an activity:").grid(column=0, row=0, pady=PADDING)
ttk.Button(menu_frame, text="Vocabulary Practice", command=show_vocab).grid(column=0, row=1, pady=PADDING, sticky="ew")
ttk.Button(menu_frame, text="Grammar Exercises", command=show_grammar).grid(column=0, row=2, pady=PADDING, sticky="ew")
ttk.Button(menu_frame, text="Listening Comprehension", command=show_listen).grid(column=0, row=3, pady=PADDING, sticky="ew")
ttk.Button(menu_frame, text="Exit", command=main.quit).grid(column=0, row=4, pady=PADDING, sticky="ew")


# Vocab activity contents
ttk.Label(vocab_frame, text="Vocabulary Practice Activity (Coming Soon!)").grid(column=0, row=0, pady=PADDING)
ttk.Button(vocab_frame, text="Go back", command=show_menu).grid(column=0, row=1, pady=PADDING, sticky="ew")


# Grammar activity contents (dummy)
ttk.Label(grammar_frame, text="Grammar Exercises (Coming Soon!)").grid(column=0, row=0, pady=PADDING)
ttk.Button(grammar_frame, text="Go back", command=show_menu).grid(column=0, row=1, pady=PADDING, sticky="ew")


# Listening activity contents (dummy)
ttk.Label(listen_frame, text="Listening Comprehension (Coming Soon!)").grid(column=0, row=0, pady=PADDING)
ttk.Button(listen_frame, text="Go back", command=show_menu).grid(column=0, row=1, pady=PADDING, sticky="ew")

# Start with menu visible
vocab_frame.grid_remove()
grammar_frame.grid_remove()
listen_frame.grid_remove()


main.mainloop()