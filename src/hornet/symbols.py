from functools import lru_cache

from hornet.expressions import Expression, Name

__all__ = [
    "_",
    "append",
    "arithmetic_equal",
    "arithmetic_not_equal",
    "atomic",
    "call",
    "cut",
    "equal",
    "fail",
    "findall",
    "greater",
    "ignore",
    "integer",
    "join",
    "length",
    "let",
    "listing",
    "lwriteln",
    "maplist",
    "member",
    "nl",
    "nonvar",
    "numeric",
    "once",
    "real",
    "repeat",
    "reverse",
    "select",
    "smaller",
    "throw",
    "transpose",
    "true",
    "unequal",
    "univ",
    "var",
    "write",
    "writeln",
]
__getattr__ = lru_cache(Name)
_ = Name("_")
append: Expression = Name("append")
arithmetic_equal: Expression = Name("arithmetic_equal")
arithmetic_not_equal: Expression = Name("arithmetic_not_equal")
atomic: Expression = Name("atomic")
call: Expression = Name("call")
cut: Expression = Name("cut")
equal: Expression = Name("equal")
fail: Expression = Name("fail")
findall: Expression = Name("findall")
greater: Expression = Name("greater")
ignore: Expression = Name("ignore")
integer: Expression = Name("integer")
join: Expression = Name("join")
length: Expression = Name("length")
let: Expression = Name("let")
listing: Expression = Name("listing")
lwriteln: Expression = Name("lwriteln")
maplist: Expression = Name("maplist")
member: Expression = Name("member")
nl: Expression = Name("nl")
nonvar: Expression = Name("nonvar")
numeric: Expression = Name("numeric")
once: Expression = Name("once")
real: Expression = Name("real")
repeat: Expression = Name("repeat")
reverse: Expression = Name("reverse")
select: Expression = Name("select")
smaller: Expression = Name("smaller")
throw: Expression = Name("throw")
transpose: Expression = Name("transpose")
true: Expression = Name("true")
unequal: Expression = Name("unequal")
univ: Expression = Name("univ")
var: Expression = Name("var")
write: Expression = Name("write")
writeln: Expression = Name("writeln")
