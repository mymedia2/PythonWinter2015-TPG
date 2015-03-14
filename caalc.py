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
        list.__init__(self, *argp, **argn)

    def __str__(self):
        return "[" + " ".join(str(c) for c in self) + "]"

    def __op(self, a, op):
        try:
            return self.__class__(op(s,e) for s,e in zip(self, a))
        except TypeError:
            return self.__class__(op(c,a) for c in self)

    def __add__(self, a): return self.__op(a, lambda c,d: c+d)
    def __sub__(self, a): return self.__op(a, lambda c,d: c-d)
    def __div__(self, a): return self.__op(a, lambda c,d: c/d)
    def __mul__(self, a): return self.__op(a, lambda c,d: c*d)

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

class Matrix(Vector):
    def __init__(self, vect):
        super(self.__class__, self).__init__(vect)
        for i in range(len(self) - 1):
            if len(self[i]) != len(self[i + 1]):
                raise AttributeError("Inconsistent matrix dimensions")
        for i in range(len(self)):
            self[i] = Vector(self[i])

    def __str__(self):
        return "(" + "|\n ".join(" ".join(str(el) for el in s) for s in self) + ")"

    def __mul__(self, b):
        a = self
        if type(a) is not type(b):
            return super(self.__class__, self).__mul__(b)
            return b * a
        c = []
        for i in range(len(a)):
            c.append([None]*len(b[0]))
        for i in range(len(a)):
            for j in range(len(b[0])):
                c[i][j] = sum(a[i][s]*b[s][j] for s in range(len(a[i])))
        if len(c) == 1 and len(c[0]) == 1:
            return c[0][0]
        return self.__class__(c)

class Calc(tpg.Parser):
    r"""

    separator spaces: '\s+' ;
    separator comment: '#.*' ;

    token fnumber: '\d+[.]\d*' float ;
    token number: '\d+' int ;
    token op1: '[|&+-]' make_op ;
    token op2: '[*/]' make_op ;
    token id: '\w+' ;

    START/e -> Operator $e=None$ | Expr/e | $e=None$ ;
    Operator -> Assign ;
    Assign -> id/i '=' Expr/e $Vars[i]=e$ ;
    Expr/t -> Fact/t ( op1/op Fact/f $t=op(t,f)$ )* ;
    Fact/f -> Atom/f ( op2/op Atom/a $f=op(f,a)$ )* ;
    Atom/a ->   Vector/a | Matrix/a
              | id/i ( check $i in Vars$ | error $"Undefined variable '{}'".format(i)$ ) $a=Vars[i]$
              | fnumber/a
              | number/a
              | '\(' Expr/a '\)' ;
    Vector/$Vector(a)$ -> '\[' '\]' $a=[]$ | '\[' Atoms/a '\]' ;
    Matrix/$Matrix(a)$ ->   '\(' Atom/t Atoms/e '\)' $a=[[t]+e]$ 
                          | '\(' Atoms/t $a=[t]$ ('\|' Atoms/e $a.append(e)$ )+ '\)' ;
    Atoms/v -> Atom/a Atoms/t $v=[a]+t$ | Atom/a $v=[a]$ ;

    """

calc = Calc()
Vars={}
PS1='--> '

def interactive_inputer(prompt=""):
    try:
        while True:
            yield input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()

parser = argparse.ArgumentParser()
parser.add_argument('files', nargs='?', type=open, default=interactive_inputer(PS1))
args = parser.parse_args()

for line in args.files:
    try:
        res = calc(line)
        if res is not None:
            print(res)
    except BaseException as err:
        print(err, file=sys.stderr)
