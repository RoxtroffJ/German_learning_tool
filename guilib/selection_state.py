import tkinter as tk
from typing import Callable, List

from tree import Tree

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

    def __init__(self):
        self._tree = Tree(TreeSelectionState._NodeData())

    # --- tree helpers -------------------------------------------------
    def _sub_tree(self, path: List[int]) -> Tree[_NodeData]:
        return self._tree.node_at(path)

    def _node(self, path: List[int]) -> _NodeData:
        return self._sub_tree(path).value

    def children_paths(self, path: List[int]) -> List[List[int]]:
        """Returns the list of child paths for the node at `path`."""
        return self._tree.children_paths(path)

    # --- adding nodes ------------------------------------------------
    def add_node(self, parent_path: List[int], selected_callback: Callable[[bool], None] | None = None, nb_callback: Callable[[int], None] | None = None) -> List[int]:
        """Add a node under `parent_path`. Returns the full path to the new node.

        `parent_path` is a list of child indices from the root; empty list
        refers to the root.
        """
        new_data = TreeSelectionState._NodeData()

        new_path = self._tree.add_child_at(parent_path, new_data)
        self.set_callbacks(new_path, selected_callback, nb_callback)
        return new_path

    # --- adding callbacks to nodes -------------------------------
    def set_callbacks(self, path: List[int], selected_callback: Callable[[bool], None] | None = None, nb_callback: Callable[[int], None] | None = None):
        """Add a callback to the node at `path`.

        The callback is called with two arguments: the new selected value
        (bool) and the number of selected leafs under this node (int).
        """
        node = self._node(path)

        if selected_callback is not None:
            node.selected.trace_add("write", lambda a,b,c: selected_callback(node.selected.get()))
        if nb_callback is not None:
            node.nb_selected_leafs.trace_add("write", lambda a,b,c: nb_callback(node.nb_selected_leafs.get()))

    def tracker_vars(self, path: List[int]) -> tuple[tk.BooleanVar, tk.IntVar]:
        """Returns the tracker variables for the node at `path`."""
        node = self._node(path)

        bool_var = tk.BooleanVar()
        int_var = tk.IntVar()

        node.selected.trace_add("write", lambda a,b,c: bool_var.set(node.selected.get()))
        node.nb_selected_leafs.trace_add("write", lambda a,b,c: int_var.set(node.nb_selected_leafs.get()))

        return (bool_var, int_var)

    def tracker_vars_formatted(self, path: List[int], format: Callable[[int], str] = lambda x: "(" + str(x) + ")" if x != 0 else "") -> tuple[tk.BooleanVar, tk.StringVar]:
        """Returns the tracker variables for the node at `path`.

        The second variable is formatted using the provided function.
        """
        node = self._node(path)

        bool_var = tk.BooleanVar()
        str_var = tk.StringVar()

        node.selected.trace_add("write", lambda a,b,c: bool_var.set(node.selected.get()))
        node.nb_selected_leafs.trace_add("write", lambda a,b,c: str_var.set(format(node.nb_selected_leafs.get())))

        return (bool_var, str_var)
    # --- selection logic ---------------------------------------------
    def select_all_callback(self, path: List[int]):
        """Callback for a select-all button."""
        
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

    def _propagate_to_descendants(self, path: List[int], set_to: bool):
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

    def _clear_parent_select_all_upwards(self, path: List[int]):
        node = self._sub_tree([])
        
        for depth in range(len(path)): # Look until parent
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
                
            node = node.children[path[depth]]

    def _update_counts_upwards(self, path: List[int], delta: int):
        node = self._sub_tree([])

        for depth in range(len(path)):
            data = node.value
            data.nb_selected_leafs.set(data.nb_selected_leafs.get() + delta)

            node = node.children[path[depth]]

    def deselect_all_callback(self, path: List[int]):
        """Callback to deselect all items under the node at `path`."""
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