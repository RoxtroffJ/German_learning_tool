import argparse
import tkinter as tk
from tkinter import ttk

from guilib.tree_selection_state import TreeSelectionState


def build_ui_for_node(parent_frame: tk.Frame | ttk.Frame, tree: TreeSelectionState, path: list[int], name: str | None = None):
    """Recursively build UI for the node at `path` in `tree`."""
    frame = ttk.Frame(parent_frame)
    frame.pack(anchor="w", padx=10)

    cb_var, lbl_var = tree.tracker_vars_formatted(path)

    cb = ttk.Checkbutton(
        frame,
        text=(name or "(group)"),
        variable=cb_var,
        command = lambda: tree.select_all_callback(path)
    )
    cb.pack(side="left")

    # Show count for non-leaf nodes
    count_lbl = ttk.Label(frame, textvariable=lbl_var)
    count_lbl.pack(side="left", padx=(6, 0))

    # Recurse for children

    for idx, child_path in enumerate(tree.children_paths(path)):
        # For leaves, show a simple name
        child_name = f"{name}.{idx}" if name else f"node{idx}"
        build_ui_for_node(frame, tree, child_path, child_name)


def main(auto_close: bool):
    root = tk.Tk()
    root.title("SelectionState Demo")

    state = TreeSelectionState()

    # Build a sample tree: two categories with leaves
    cat1 = state.add_node([])
    state.add_node(list(cat1))
    state.add_node(list(cat1))
    state.add_node(list(cat1))

    cat2 = state.add_node([])
    state.add_node(list(cat2))
    state.add_node(list(cat2))

    main_frame = ttk.Frame(root, padding=10)
    main_frame.pack(fill="both", expand=True)

    build_ui_for_node(main_frame, state, [], "root")

    if auto_close:
        # Auto-close after 1s for automated testing
        root.after(1000, root.destroy)

    root.mainloop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto-close", action="store_true")
    args = parser.parse_args()
    main(auto_close=args.auto_close)