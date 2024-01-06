from re2py import re_to_post, post_to_nfa
import argparse


def plot(re, ofile):
    nfa = post_to_nfa(re_to_post(re))
    graph = nfa.graph()
    graph.format = "svg"
    svg = graph.pipe("utf-8")
    with open(ofile, "w") as o:
        o.write(svg)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("re")
    parser.add_argument("ofile")
    args = parser.parse_args()
    re = args.re
    ofile = args.ofile
    plot(re, ofile)
