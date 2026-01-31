from typing import TypeVar, Generic

T = TypeVar('T', contravariant=True)

class Path:
    """Represents paths in the trees."""

    def __init__(self, indices: list[int]):
        self._indices = indices
    
    @property
    def indices(self) -> list[int]:
        """Returns the list of indices representing the path."""
        return self._indices.copy()
    
    def __add__(self, other: 'Path') -> 'Path':
        """Concatenates two paths."""
        return Path(self._indices + other._indices)

class Tree(Generic[T]):
    """A class to manage tree-like structures"""

    def __init__(self, value: T):
        self.value = value
        self.children: list[Tree[T]] = []
    
    def add_child(self, child_value: T) -> Path:
        """Adds a child node with the given value."""
        child_node = Tree(child_value)

        idx = len(self.children)

        self.children.append(child_node)
        return Path([idx])

    def node_at(self, path: Path) -> 'Tree[T]':
        """Return the node at the given path (list of child indices). Empty path -> self (root)."""
        node: Tree[T] = self
        for i in path.indices:
            node = node.children[i]
        return node

    def add_child_at(self, path: Path, child_value: T) -> Path:
        """Add a child to the node at `path`. Returns the index of the new child."""
        parent = self.node_at(path)

        return path + parent.add_child(child_value)
    
    def is_leaf(self) -> bool:
        """Returns True if the node has no children."""
        return len(self.children) == 0
    
    def is_leaf_at(self, path: Path) -> bool:
        """Returns True if the node at `path` has no children."""
        node = self.node_at(path)
        return node.is_leaf()

    def all_on_path(self, path: Path) -> list['Tree[T]']:
        """Returns a list of all nodes on the path from root to the node at `path`, inclusive."""
        nodes: list[Tree[T]] = []
        node: Tree[T] = self
        nodes.append(node)
        for i in path.indices:
            node = node.children[i]
            nodes.append(node)
        return nodes
    
    def children_paths(self, path: Path) -> list[Path]:
        """Returns the list of child paths for the node at `path`."""
        node = self.node_at(path)
        return [path + Path([i]) for i in range(len(node.children))]