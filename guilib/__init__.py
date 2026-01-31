import tkinter as tk
import tkinter.ttk as ttk

PADDING = 5

def init_gui():
	main = tk.Tk()
	main.title("German Learning Tool")

	# Import here to avoid circular import during package initialization
	import guilib.settings_gui as settings_gui

	settings = settings_gui.load_settings()

	# Add a button style for success and outline success similar to bootstrap
	set_custom_styles()

	return main, settings

def set_custom_styles():
	"""Adds custom styles to the ttk Style."""
	style = ttk.Style()

	style.configure("Success.TButton", foreground="white", background="#28a745")
	style.map("Success.TButton",
		foreground=[('active', 'white')],
		background=[('active', '#218838')]
	)
	style.configure("OutlineSuccess.TButton", foreground="#28a745")
	style.map("OutlineSuccess.TButton",
		foreground=[('active', 'white')],
		background=[('active', '#28a745')]
	)