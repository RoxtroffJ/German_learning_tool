from typing import TypeVar, Generic

T = TypeVar('T')

class Tree(Generic[T]):
    """A class to manage tree-like structures"""

    def __init__(self, value: T):
        self.value = value
        self.children: list[Tree[T]] = []
    
    def add_child(self, child_value: T):
        """Adds a child node with the given value."""
        child_node = Tree(child_value)

        idx = len(self.children)

        self.children.append(child_node)
        return idx

    def node_at(self, path: list[int]) -> 'Tree[T]':
        """Return the node at the given path (list of child indices). Empty path -> self (root)."""
        node: Tree[T] = self
        for i in path:
            node = node.children[i]
        return node

    def add_child_at(self, path: list[int], child_value: T):
        """Add a child to the node at `path`. Returns the index of the new child."""
        parent = self.node_at(path)
        path.append(parent.add_child(child_value))
        return path
    
    def is_leaf(self):
        """Returns True if the node has no children."""
        return len(self.children) == 0
    
    def is_leaf_at(self, path: list[int]):
        """Returns True if the node at `path` has no children."""
        node = self.node_at(path)
        return node.is_leaf()

    def all_on_path(self, path: list[int]):
        """Returns a list of all nodes on the path from root to the node at `path`, inclusive."""
        nodes: list[Tree[T]] = []
        node: Tree[T] = self
        nodes.append(node)
        for i in path:
            node = node.children[i]
            nodes.append(node)
        return nodes
    
    def children_paths(self, path: list[int]) -> list[list[int]]:
        """Returns the list of child paths for the node at `path`."""
        node = self.node_at(path)
        return [path + [i] for i in range(len(node.children))]