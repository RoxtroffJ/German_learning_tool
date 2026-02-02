import tkinter as tk
from typing import Callable, List

from tree import Tree, Path

class TreeSelectionState:
    """State tracking for the selection of things in a tree structure.

    Each tree node stores a `NodeData`. Leaves represent selectable items and
    count toward parent `nb_selected_leafs`. Non-leaf nodes represent "select
    all" buttons.
    """
    
    class _NodeData:
        """Tracked data for a tree node in `TreeSelectionState`."""
        def __init__(self):
            self.user_selected = False
            self.selected = tk.BooleanVar(value=False)
            self.nb_selected_leafs = tk.IntVar(value=0)
            self.deleted = False

    def __init__(self):
        self._tree = Tree(TreeSelectionState._NodeData())

    # --- tree helpers -------------------------------------------------
    def _sub_tree(self, path: Path) -> Tree[_NodeData]:
        return self._tree.node_at(path)

    def _node(self, path: Path) -> _NodeData:
        return self._sub_tree(path).value

    def _check_deleted(self, path: Path):
        node = self._node(path)
        if node.deleted:
            raise ValueError(f"Node at path {path.indices} has been deleted")
        return node

    def get(self, path: Path) -> tuple[bool, int]:
        """Returns the selected state of the node at `path`."""
        node = self._check_deleted(path)
        return (node.selected.get(), node.nb_selected_leafs.get())

    def children_paths(self, path: Path) -> List[Path]:
        """Returns the list of child paths for the node at `path`."""
        self._check_deleted(path)
        return self._tree.children_paths(path)

    # --- adding nodes ------------------------------------------------
    def add_node(self, parent_path: Path, selected_callback: Callable[[bool], None] | None = None, nb_callback: Callable[[int], None] | None = None) -> Path:
        """Add a node under `parent_path`. Returns the full path to the new node.

        `parent_path` is a list of child indices from the root; empty list
        refers to the root.
        """
        self._check_deleted(parent_path)
        new_data = TreeSelectionState._NodeData()

        new_path = self._tree.add_child_at(parent_path, new_data)
        self.set_callbacks(new_path, selected_callback, nb_callback)
        return new_path

    def delete_node(self, path: Path):
        """Deletes the node at `path`."""
        
        node = self._node(path)

        # Delete children
        for child in self.children_paths(path):
            self.delete_node(child)

        # Deselect all
        self.deselect_all_callback(path)

        # Mark as deleted
        node.deleted = True
        
        # Remove all callbacks
        for a,id in node.selected.trace_info():
            node.selected.trace_remove(a, id) # type: ignore
        for a,id in node.nb_selected_leafs.trace_info():
            node.nb_selected_leafs.trace_remove(a, id) # type: ignore
        

    # --- adding callbacks to nodes -------------------------------
    def set_callbacks(self, path: Path, selected_callback: Callable[[bool], None] | None = None, nb_callback: Callable[[int], None] | None = None):
        """Add a callback to the node at `path`.

        The callback is called with two arguments: the new selected value
        (bool) and the number of selected leafs under this node (int).
        """
        node = self._check_deleted(path)

        if selected_callback is not None:
            node.selected.trace_add("write", lambda a,b,c: selected_callback(node.selected.get()))
        if nb_callback is not None:
            node.nb_selected_leafs.trace_add("write", lambda a,b,c: nb_callback(node.nb_selected_leafs.get()))

    def set_double_callback(self, path: Path, callback: Callable[[bool, int], None]):
        """Add a callback to the node at `path`.

        The callback is called with two arguments: the new selected value
        (bool) and the number of selected leafs under this node (int).
        """
        node = self._check_deleted(path)

        node.selected .trace_add("write", lambda a,b,c: callback(node.selected.get(), node.nb_selected_leafs.get()))
        node.nb_selected_leafs.trace_add("write", lambda a,b,c: callback(node.selected.get(), node.nb_selected_leafs.get()))

    def tracker_vars(self, path: Path) -> tuple[tk.BooleanVar, tk.IntVar]:
        """Returns the tracker variables for the node at `path`."""
        node = self._check_deleted(path)

        bool_var = tk.BooleanVar()
        int_var = tk.IntVar()

        node.selected.trace_add("write", lambda a,b,c: bool_var.set(node.selected.get()))
        node.nb_selected_leafs.trace_add("write", lambda a,b,c: int_var.set(node.nb_selected_leafs.get()))

        return (bool_var, int_var)

    def tracker_vars_formatted(self, path: Path, format: Callable[[int], str] = lambda x: "(" + str(x) + ")" if x != 0 else "") -> tuple[tk.BooleanVar, tk.StringVar]:
        """Returns the tracker variables for the node at `path`.

        The second variable is formatted using the provided function.
        """
        node = self._check_deleted(path)

        bool_var = tk.BooleanVar()
        str_var = tk.StringVar()

        node.selected.trace_add("write", lambda a,b,c: bool_var.set(node.selected.get()))
        node.nb_selected_leafs.trace_add("write", lambda a,b,c: str_var.set(format(node.nb_selected_leafs.get())))

        return (bool_var, str_var)
    # --- selection logic ---------------------------------------------
    def select_all_callback(self, path: Path):
        """Callback for a select-all button."""
        self._check_deleted(path)
        tree = self._sub_tree(path)
        node = tree.value

        # If any ancestor is currently a select-all, clear it first so that
        # descendants get their `user_selected` copied from the visible
        # `selected` state. This ensures the clicked node's toggle acts on
        # the correct base user state.
        if node.selected.get() and not node.user_selected:
            self._clear_parent_select_all_upwards(path)

        # Toggle user selection for this node and set its selected state
        new_val = not node.selected.get()
        node.user_selected = new_val

        # If turning on -> select all descendants. If turning off -> revert
        # descendants to their own user_selected state.
        delta = self._propagate_to_descendants(path, set_to=new_val)

        # Update counts on the path up to root
        self._update_counts_upwards(path, delta)

    def _propagate_to_descendants(self, path: Path, set_to: bool) -> int:

        try:
            self._check_deleted(path)
        except ValueError:
            return 0

        node = self._sub_tree(path)
        
        def recurse(t: Tree[TreeSelectionState._NodeData]) -> int:
            delta = 0

            # Update this node
            data = t.value

            new_val = set_to or data.user_selected
            
            # Update and count descendants if updated
            if new_val != data.selected.get():
                for c in t.children:
                    delta += recurse(c)
        

            data.nb_selected_leafs.set(data.nb_selected_leafs.get() + delta)
            
            if t.is_leaf():
                old_val = data.selected.get()
                if old_val and not new_val:
                    delta -= 1
                elif not old_val and new_val:
                    delta += 1
            data.selected.set(new_val)
            
            return delta

        delta = recurse(node)
        return delta

    def _clear_parent_select_all_upwards(self, path: Path):
        nodes = self._tree.all_on_path(path)
        nodes.pop()  # Remove self

        for node in nodes: # Look until parent
            data = node.value

            if data.selected.get():
                # Clear this select-all
                data.selected.set(False)
                data.user_selected = False

                # Propagate user_selected to descendants
                for c in node.children:
                    cdata = c.value
                    cdata.selected.set(True)
                    cdata.user_selected = True

    def _update_counts_upwards(self, path: Path, delta: int):
        nodes = self._tree.all_on_path(path)
        nodes.pop()  # Remove self

        for node in nodes:
            data = node.value
            data.nb_selected_leafs.set(data.nb_selected_leafs.get() + delta)

    def deselect_all_callback(self, path: Path):
        """Callback to deselect all items under the node at `path`."""
        self._check_deleted(path)
        node = self._sub_tree(path)

        def recurse(t: Tree[TreeSelectionState._NodeData]) -> int:
            delta = 0

            # Update this node
            data = t.value
            
            for c in t.children:
                delta += recurse(c)

            data.nb_selected_leafs.set(0)
            
            if t.is_leaf():
                old_val = data.selected.get()
                if old_val:
                    delta -= 1
            data.selected.set(False)
            data.user_selected = False
            
            return delta
        
        delta = recurse(node)

        self._update_counts_upwards(path, delta)