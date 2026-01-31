from typing import Generic, TypeVar

# Declare a covariant type variable T and use it as the element type of list[T].
# This should cause Pylance/pyright to report an error because T is used
# in a mutable position (list[T] is mutable).
T = TypeVar("T", covariant=True)

class Foo(Generic[T]):
    def __init__(self, value: list[T]) -> None:
        self.value = value

class Bar(Foo[T], Generic[T]):
    def __init__(self, foo: Foo[T]) -> None:
        super().__init__(foo.value)
        self._foo = foo

    def illegal(self, value: T) -> None:
        self._foo.value.append(value)
    