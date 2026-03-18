from collections.abc import Callable, Iterable

type List[A] = Iterable[A]


def unit[A](a: A) -> List[A]:
    yield a


def zero[A]() -> List[A]:
    return iter(())


def bind[A, B](xs: List[A], f: Callable[[A], List[B]]) -> List[B]:
    for x in xs:
        yield from f(x)


def choice[A](*xss: List[A]) -> List[A]:
    for xs in xss:
        yield from xs
