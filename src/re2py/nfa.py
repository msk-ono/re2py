from collections import namedtuple
from typing import List, Optional
from enum import Enum
from graphviz import Digraph

"""Provides regular expression matching operations.

Using non-deterministic finite-state automaton (NFA) to implement matching.
This module is implemented with a great deal of reference to an article
https://swtch.com/~rsc/regexp/regexp1.html.
"""


def re_to_post(re: str) -> str:
    """Convert a regular expression to postfix notation"""
    post = ""

    nalt = 0
    natom = 0
    Paren = namedtuple("Paren", ["nalt", "natom"])
    paren = list()

    for c in re:
        if c == "(":
            if natom > 1:
                natom -= 1
                post += "."
            p = Paren(nalt, natom)
            paren.append(p)
            nalt = 0
            natom = 0
        elif c == "|":
            if natom == 0:
                raise RuntimeError("no atom before alt '|'")
            while True:
                natom -= 1
                if natom == 0:
                    break
                post += "."
            nalt += 1
        elif c == ")":
            if len(paren) == 0:
                raise RuntimeError("no open parenthesis")
            if natom == 0:
                raise RuntimeError("no atom in parenthesis")
            while True:
                natom -= 1
                if natom == 0:
                    break
                post += "."
            while True:
                if nalt == 0:
                    break
                post += "|"
                nalt -= 1
            p = paren.pop()
            nalt = p.nalt
            natom = p.natom
            natom += 1
        elif c == "*" or c == "+" or c == "?":
            if natom == 0:
                raise RuntimeError(f"no atom before '{c}'")
            post += c
        else:
            if natom > 1:
                natom -= 1
                post += "."
            post += c
            natom += 1

    if len(paren) > 0:
        raise RuntimeError("unclosed parenthesis")
    while True:
        natom -= 1
        if natom == 0:
            break
        post += "."
    while True:
        if nalt == 0:
            break
        post += "|"
        nalt -= 1

    return post


class StateType(Enum):
    OUT = 0
    SPLIT = 1
    MATCH = 2


class Graph:
    def __init__(self, graph: Digraph, nodes=None, edges=None, entry=None, match=None):
        self.graph = graph
        self.nodes = nodes
        self.edges = edges
        self.entry = entry
        self.match = match

    def number_of_nodes(self):
        return len(self.nodes)

    def number_of_edges(self):
        return len(self.edges)

    def node(self, id: int, color, shape, label, fillcolor="transparent"):
        self.graph.node(
            f"{self.nodes[id]._name()}",
            color=color,
            shape=shape,
            label=label,
            style="filled",
            fillcolor=fillcolor,
        )

    def get_label(self, id: int):
        if id == self.entry:
            return "start"
        elif id == self.match:
            return "end"
        else:
            return f"s{id}"

    def render(self, ofile):
        self.graph.render(ofile)

    def pipe(self, encoding):
        return self.graph.pipe(encoding=encoding)

    @property
    def format(self):
        return self.graph.format

    @format.setter
    def format(self, f):
        self.graph.format = f


class State:
    def __init__(self, type: StateType, id: int):
        self.type: StateType = type
        self.id: int = id
        self.last_list: int = -1

    def __str__(self):
        if self.is_out():
            return f"OUT(ID: {self.id}, CHAR: {self.char}, NEXT: {self.out.id})"
        elif self.is_split():
            return f"SPLIT(ID: {self.id}, CHAR: {self.char}, NEXT0: {self.out.id}, NEXT1: {self.out1.id})"
        else:
            return "MATCH"

    def is_out(self) -> bool:
        return self.type == StateType.OUT

    def is_split(self) -> bool:
        return self.type == StateType.SPLIT

    def is_match(self) -> bool:
        return self.type == StateType.MATCH

    def _name(self):
        if self.is_out():
            return f"{self.id}_{self.char}"
        elif self.is_split():
            return f"{self.id}_{self.char}"
        else:
            return f"{self.id}_match"

    def graph(self) -> Graph:
        stack = [self]
        graph = Digraph(format="png")
        states = dict()
        edges = list()
        entry = None
        match = None

        def get_label(id):
            if id == entry:
                return "start"
            elif id == match:
                return "end"
            else:
                return f"s{id}"

        while len(stack) > 0:
            e = stack.pop()
            if e.id in states.keys():
                continue

            if entry is None:
                entry = e.id
            if e.is_match():
                match = e.id

            states[e.id] = e
            graph.node(f"{e._name()}", label=get_label(e.id))
            if e.is_out():
                e0 = e.out
                graph.edge(f"{e._name()}", f"{e0._name()}", label=f"{e.char}")
                edges.append((e.id, e0.id))
                stack.append(e0)
            elif e.is_split():
                e0 = e.out
                graph.edge(f"{e._name()}", f"{e0._name()}", label=f"{e.char}")
                edges.append((e.id, e0.id))
                stack.append(e0)
                e1 = e.out1
                graph.edge(f"{e._name()}", f"{e1._name()}", label=f"{e.char}")
                edges.append((e.id, e1.id))
                stack.append(e1)

        return Graph(graph, states, edges, entry, match)


class PtrList:
    def __init__(self, s: State, v: int):
        self.next: PtrList = None
        self.s: State = s
        self.v: int = v


class Frag:
    def __init__(self, s: State, ptrl: PtrList):
        self.start: State = s
        self.out: PtrList = ptrl


def _patch(ptrl: PtrList, s: State):
    while True:
        if ptrl.v == 0:
            ptrl.s.out = s
        else:
            ptrl.s.out1 = s

        if ptrl.next is not None:
            ptrl = ptrl.next
        else:
            break


def _append(ptrl1: PtrList, ptrl2: PtrList) -> PtrList:
    old = ptrl1
    while True:
        if ptrl1.next is not None:
            ptrl1 = ptrl1.next
        else:
            ptrl1.next = ptrl2
            break
    return old


def post_to_nfa(post: str) -> State:
    stack: List[Frag] = list()
    nstate = 0

    def create_state(type: StateType, nstate: int, out=None, out1=None, char=None):
        s = State(type, nstate)
        if type == StateType.OUT:
            s.out = out
            s.char = char
        elif type == StateType.SPLIT:
            s.out = out
            s.out1 = out1
            s.char = char
        nstate += 1
        return s, nstate

    for c in post:
        if c == ".":
            e2 = stack.pop()
            e1 = stack.pop()
            _patch(e1.out, e2.start)
            stack.append(Frag(e1.start, e2.out))
        elif c == "|":
            e2 = stack.pop()
            e1 = stack.pop()
            s, nstate = create_state(
                StateType.SPLIT, nstate, out=e1.start, out1=e2.start, char="|"
            )
            stack.append(Frag(s, _append(e1.out, e2.out)))
        elif c == "?":
            e = stack.pop()
            s, nstate = create_state(
                StateType.SPLIT, nstate, out=e.start, out1=None, char="?"
            )
            stack.append(Frag(s, _append(e.out, PtrList(s, 1))))
        elif c == "*":
            e = stack.pop()
            s, nstate = create_state(
                StateType.SPLIT, nstate, out=e.start, out1=None, char="*"
            )
            _patch(e.out, s)
            stack.append(Frag(s, PtrList(s, 1)))
        elif c == "+":
            e = stack.pop()
            s, nstate = create_state(
                StateType.SPLIT, nstate, out=e.start, out1=None, char="+"
            )
            _patch(e.out, s)
            stack.append(Frag(e.start, PtrList(s, 1)))
        else:
            s, nstate = create_state(StateType.OUT, nstate, out=None, char=c)
            stack.append(Frag(s, PtrList(s, 0)))
    e = stack.pop()
    assert len(stack) == 0
    match, _ = create_state(StateType.MATCH, nstate)
    _patch(e.out, match)
    return e.start


class SList:
    def __init__(self):
        # SList only stores StateType.OUT
        self.s = []
        self.id = 0


def _add_state(slist: SList, s: State):
    if s.last_list == slist.id:
        return

    s.last_list = slist.id

    if s.is_split():
        # Follow unlabeled arrows
        _add_state(slist, s.out)
        _add_state(slist, s.out1)
        return

    slist.s.append(s)


def _step(clist: SList, c: str):
    nlist = SList()
    nlist.id = clist.id + 1

    for s in clist.s:
        if s.is_out() and s.char == c:
            _add_state(nlist, s.out)

    return nlist


def _is_match_any(slist: SList):
    for s in slist.s:
        if s.is_match():
            return True
    return False


def match(start: State, s: str, history: Optional[List[List[int]]] = None) -> bool:
    clist = SList()
    _add_state(clist, start)
    for c in s:
        clist = _step(clist, c)
        if history is not None:
            history.append([s.id for s in clist.s])
    return _is_match_any(clist)
