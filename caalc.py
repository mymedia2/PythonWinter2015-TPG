#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, unicode_literals
import readline
import sys
import tpg
import itertools
import argparse

# Скорее всего, это дело стоит вынести в отдельный модуль или
# поискать уже готовые решения. В этом месте стоит хранть лишь
# те функции, которые критичны для работы данного приложения.
PY2 = sys.version_info[0] == 2
if PY2:
    input = raw_input

def make_op(s):
    return {
        '+': lambda x,y: x+y,
        '-': lambda x,y: x-y,
        '*': lambda x,y: x*y,
        '/': lambda x,y: x/y,
        '&': lambda x,y: x&y,
        '|': lambda x,y: x|y,
    }[s]

class Vector(list):
    def __init__(self, *argp, **argn):
        super(Vector, self).__init__(*argp, **argn)

    def __str__(self):
        return "[" + " ".join(str(c) for c in self) + "]"

    def __repr__(self):
        return self.__class__.__name__ + "(" + repr(list(self)) + ")"

    def __op(self, a, op):
        try:
            return self.__class__(op(s,e) for s,e in zip(self, a))
        except TypeError:
            return self.__class__(op(c,a) for c in self)

    def __add__(self, a): return self.__op(a, lambda c,d: c+d)
    def __sub__(self, a): return self.__op(a, lambda c,d: c-d)
    def __mul__(self, a): return self.__op(a, lambda c,d: c*d)
    def __div__(self, a): return self.__op(a, lambda c,d: c/d)
    def __rmul__(self, a): return self.__op(a, lambda c,d: d*c)
    def __rdiv__(self, a): return self.__op(a, lambda c,d: d/c)

    def __and__(self, a):
        try:
            return sum(self * a)
        except TypeError:
            return self.__class__(c and a for c in self)

    def __or__(self, a):
        try:
            return self.__class__(itertools.chain(self, a))
        except TypeError:
            return self.__class__(c or a for c in self)

class MatrixError(ArithmeticError):
    pass

class Matrix(Vector):
    def __init__(self, vect):
        super(Matrix, self).__init__(vect)
        for i in range(len(self) - 1):
            if len(self[i]) != len(self[i + 1]):
                raise MatrixError("Wrong dimension of matrix")
        for i in range(len(self)):
            self[i] = Vector(self[i])
        self.rows, self.columns = self.m, self.n = len(self), len(self[0])

    def __str__(self):
        # 😵  :dizzy_face:
        width = [ max(map(lambda el: len(str(el)), col)) for col in self.by_columns() ]
        return "(" + "|\n ".join(" ".join("{0:^{1}}".format(str(el), w+1)[:-1] for el, w in zip(s, width)) for s in self) + ")"

    def __mul__(self, other):
        if self.__class__ is not other.__class__:
            return super(Matrix, self).__mul__(other)
        if self.columns != other.rows:
            raise MatrixError("Inconsistent matrix dimensions")
        c = list()
        for row in self.by_rows():
            t = list()
            for col in other.by_columns():
                t.append(row & col)
            c.append(t)
        matrix = Matrix(c)
        if matrix.rows == matrix.columns == 1:
            return matrix[0][0]
        return matrix

    def by_columns(self):
        for j in range(len(self[0])):
            yield Vector( self[i][j] for i in range(len(self)) )

    by_rows = Vector.__iter__

class Calc(tpg.Parser):
    r"""

    separator spaces: '\s+' ;
    separator comment: '#.*' ;

    token fnumber: '\d+[.]\d*' float ;
    token dnumber: '\d+' int ;
    token op0: '[+-]' make_op ;
    token op1: '[\|&]' make_op ;
    token op2: '[*/]' make_op ;
    token id: '\w+' ;

    START/e -> Operator $e=None$ | Expr/e | $e=None$ ;
    Operator -> Assign ;
    Assign -> id/i '=' Expr/e $Vars[i]=e$ ;
    Expr/t -> Fact/t ( ( op0/op | op1/op ) Fact/f $t=op(t,f)$ )* ;
    Fact/f -> Compl/f ( op2/op Compl/a $f=op(f,a)$ )* ;
    Compl/a ->   Vector/a | Matrix/a | Atom/a | SgnAtom/a ;
    Atom/a ->   id/i ( check $i in Vars$ | error $"Undefined variable '{}'".format(i)$ ) $a=Vars[i]$
              | Number/a
              | '\(' Expr/a '\)' ;
    Number/n -> fnumber/n | dnumber/n ;
    SgnAtom/a -> ( op0/op )? Atom/a $a=op(0,a) if op else a$ ;
    Vector/$Vector(a)$ -> '\[' '\]' $a=[]$ | '\[' Exprs/a '\]' ;
    Matrix/$Matrix(a)$ ->   '\(' Expr/t Exprs/e '\)' $a=[[t]+e]$ 
                          | '\(' Exprs/t $a=[t]$ ('\|' Exprs/e $a.append(e)$ )+ '\)' ;
    Exprs/v -> Expr/a Exprs/t $v=[a]+t$ | Expr/a $v=[a]$ ;

    """

def interactive_inputer(prompt=""):
    try:
        while True:
            yield input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()

Vars={}

def app():
    calc = Calc()
    PS1="--> "

    parser = argparse.ArgumentParser()
    parser.add_argument('file', nargs='?', type=open)
    args = parser.parse_args()

    if not args.file:
        if sys.stdin.isatty():
            args.file = interactive_inputer(PS1)
        else:
            args.file = sys.stdin

    for line in args.file:
        try:
            res = calc(line)
            if res is not None:
                print(res)
        except BaseException as err:
            print(err, file=sys.stderr)

if __name__ == "__main__":
    app()
