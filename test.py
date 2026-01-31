import tkinter as tk
from tkinter import ttk

from guilib import *
from guilib.pages import ScrollablePage


# Example App
root = tk.Tk()
root.title("Scrollable Frame Example")
#root.geometry("400x300")
scrollable = ScrollablePage(root, sticky="NEW")
scrollable.display_page()

# Show border of scrollable frame for DEBUG
scrollable.frame().config(borderwidth=2, relief="groove")

for i in range(100):
    ttk.Button(scrollable.frame(), text=f"Button {i+1}").grid(row=i, column=0, pady=5)
    ttk.Label(scrollable.frame(), text=f"Label {i+1}").grid(row=i, column=1, pady=5, sticky="EW")

scrollable.frame().columnconfigure(0, weight=1)


root.mainloop()

