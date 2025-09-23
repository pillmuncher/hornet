from hornet.terms import *

{Variable(name='A'): Variable(name='A!0'),
 Variable(name='B'): Variable(name='B!1'),
 Variable(name='C'): Variable(name='C!2')}
{Variable(name='C!3462'): 2,
 Variable(name='X!3463'): Atom(name='x'),
 Variable(name='U!3461'): Atom(name='x'),
 Variable(name='A!3464'): 1,
 Variable(name='U!3379'): Pow(args=(Atom(name='x'), 2)),
 Variable(name='A!3381'): Mul(args=(Mul(args=(Variable(name='C!3462'),
                                              Variable(name='A!3464'))),
                                    Pow(args=(Variable(name='U!3461'),
                                              Sub(args=(Variable(name='C!3462'),
                                                        1)))))),
 Variable(name='U!3623'): Atom(name='x'),
 Variable(name='V!3624'): 9,
 Variable(name='X!3625'): Atom(name='x'),
 Variable(name='C!3378'): 2,
 Variable(name='A!3626'): 1,
 Variable(name='X!3380'): Atom(name='x'),
 Variable(name='B!1'): Add(args=(Variable(name='A!3100'),
                                 Variable(name='B!3101'))),
 Variable(name='A!0'): Variable(name='A!154'),
 Variable(name='C!2'): Variable(name='A!3965'),
 Variable(name='V!3420'): 2,
 Variable(name='A!3965'): Add(args=(Variable(name='A!3100'),
                                    Variable(name='B!3101'))),
 Variable(name='U!3097'): Add(args=(Pow(args=(Atom(name='x'), -3)),
                                    Mul(args=(2,
                                              Pow(args=(Atom(name='x'), 2)))))),
 Variable(name='X!3099'): Atom(name='x'),
 Variable(name='B!3101'): Mul(args=(Variable(name='C!3576'),
                                    Variable(name='A!3579'))),
 Variable(name='A!154'): Add(args=(Add(args=(Pow(args=(Atom(name='x'), -3)),
                                             Mul(args=(2,
                                                       Pow(args=(Atom(name='x'),
                                                                 2)))))),
                                   Mul(args=(7, Add(args=(Atom(name='x'), 9)))))),
 Variable(name='V!3098'): Mul(args=(7, Add(args=(Atom(name='x'), 9)))),
 Variable(name='A!3100'): Add(args=(Variable(name='A!3165'),
                                    Variable(name='B!3166'))),
 Variable(name='V!3487'): 2,
 Variable(name='X!3685'): Atom(name='x'),
 Variable(name='V!3813'): 9,
 Variable(name='X!3265'): Atom(name='x'),
 Variable(name='X!3291'): Atom(name='x'),
 Variable(name='V!3289'): -3,
 Variable(name='U!3263'): Atom(name='x'),
 Variable(name='A!3266'): 1,
 Variable(name='V!3618'): 7,
 Variable(name='C!3264'): -3,
 Variable(name='C!3750'): 9,
 Variable(name='X!3751'): Atom(name='x'),
 Variable(name='X!3489'): Atom(name='x'),
 Variable(name='A!3579'): Add(args=(Variable(name='A!3626'),
                                    Variable(name='B!3627'))),
 Variable(name='U!3577'): Add(args=(Atom(name='x'), 9)),
 Variable(name='X!3578'): Atom(name='x'),
 Variable(name='C!3576'): 7,
 Variable(name='X!3164'): Atom(name='x'),
 Variable(name='A!3165'): Mul(args=(Mul(args=(Variable(name='C!3264'),
                                              Variable(name='A!3266'))),
                                    Pow(args=(Variable(name='U!3263'),
                                              Sub(args=(Variable(name='C!3264'),
                                                        1)))))),
 Variable(name='U!3162'): Pow(args=(Atom(name='x'), -3)),
 Variable(name='B!3166'): Mul(args=(Variable(name='C!3378'),
                                    Variable(name='A!3381'))),
 Variable(name='V!3163'): Mul(args=(2, Pow(args=(Atom(name='x'), 2)))),
 Variable(name='B!3627'): 0}
            # Base constants
            case int() | bool() | float() | complex():
                return term

            # Unary operators
            case Invert(operand=a):
                v = eval_resolvable(a, subst)
                assert not isinstance(v, bool | float | complex)
                return ~v
            case UAdd(operand=a):
                return +eval_resolvable(a, subst)
            case USub(operand=a):
                return -eval_resolvable(a, subst)

            # Binary operators
            case LShift(left=l, right=v):
                vl = eval_resolvable(l, subst)
                assert not isinstance(vl, float | complex)
                vr = eval_resolvable(v, subst)
                assert not isinstance(vr, float | complex)
                return vl << vr
            case RShift(left=l, right=v):
                vl = eval_resolvable(l, subst)
                assert not isinstance(vl, float | complex)
                vr = eval_resolvable(v, subst)
                assert not isinstance(vr, float | complex)
                return vl >> vr
            case BitOr(left=l, right=v):
                vl = eval_resolvable(l, subst)
                assert not isinstance(vl, float | complex)
                vr = eval_resolvable(v, subst)
                assert not isinstance(vr, float | complex)
                return vl | vr
            case BitXor(left=l, right=v):
                vl = eval_resolvable(l, subst)
                assert not isinstance(vl, float | complex)
                vr = eval_resolvable(v, subst)
                assert not isinstance(vr, float | complex)
                return vl ^ vr
            case BitAnd(left=l, right=v):
                vl = eval_resolvable(l, subst)
                assert not isinstance(vl, float | complex)
                vr = eval_resolvable(v, subst)
                assert not isinstance(vr, float | complex)
                return vl & vr
            case Add(left=l, right=v):
                return eval_resolvable(l) + eval_resolvable(v, subst)
            case Sub(left=l, right=v):
                return eval_resolvable(l) - eval_resolvable(v, subst)
            case Mul(left=l, right=v):
                return eval_resolvable(l) * eval_resolvable(v, subst)
            case Div(left=l, right=v):
                return eval_resolvable(l) / eval_resolvable(v, subst)
            case FloorDiv(left=l, right=v):
                vl = eval_resolvable(l, subst)
                assert not isinstance(vl, complex)
                vr = eval_resolvable(v, subst)
                assert not isinstance(vr, complex)
                return vl // vr
            case Mod(left=l, right=v):
                vl = eval_resolvable(l, subst)
                assert not isinstance(vl, complex)
                vr = eval_resolvable(v, subst)
                assert not isinstance(vr, complex)
                return vl % vr
            case Pow(left=l, right=v):
                return eval_resolvable(l) ** eval_resolvable(v, subst)
