from re2py import re_to_post, post_to_nfa, match
from pathlib import Path
import argparse


def plot(re, s, odir):
    nfa = post_to_nfa(re_to_post(re))
    graph = nfa.graph()
    graph.format = "svg"
    history = []
    match(graph.nodes[graph.entry], s, history)
    svg_list = []
    node_config = []
    for i in range(graph.number_of_nodes()):
        color = "black"
        shape = "oval"
        label = graph.get_label(i)
        node_config.append(
            {
                "name": label,
                "color": color,
                "shape": shape,
                "label": label,
            }
        )
    for states in history:
        for i in range(graph.number_of_edges()):
            config = node_config[i]
            if i in states:
                graph.node(
                    i,
                    config["color"],
                    config["shape"],
                    config["label"],
                    fillcolor="red",
                )
            else:
                graph.node(i, config["color"], config["shape"], config["label"])
        svg_list.append(graph.pipe("utf-8"))
    for idx, svg in enumerate(svg_list):
        with open(Path(odir) / f"{idx}.svg", "w") as o:
            o.write(svg)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("re")
    parser.add_argument("s")
    parser.add_argument("odir")
    args = parser.parse_args()
    re = args.re
    s = args.s
    odir = args.odir
    plot(re, s, odir)
