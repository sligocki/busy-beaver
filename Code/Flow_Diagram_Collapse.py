"""
Convert TM transition table into state "flow diagram" digraph and then
attempt to collapse via the following rules:

1. Remove any self-edges.
2. Remove any duplicate edges.
3. If a node has out-degree 1, replace that node with edges from all in-degree neighbors to the single out-degree neighbor.

Repeat until none of these rules apply. They show the graph (which may be trivial).
"""

import argparse
from pathlib import Path

import networkit as nk

import IO


def ttable_to_digraph(ttable):
  num_states = len(ttable)
  graph = nk.Graph(num_states + 1, directed=True)
  for state_in, row in enumerate(ttable):
    for symbol_in, cell in enumerate(row):
      symbol_out, dir_out, state_out = cell
      # +1 so that Halt (-1) becomes 0 (all nodes must be pos ints).
      graph.addEdge(state_in+1, state_out+1)
  return graph

def collapse_graph(graph):
  old_num_nodes = old_num_edges = None
  while not (graph.numberOfNodes() == old_num_nodes and
             graph.numberOfEdges() == old_num_edges):
    old_num_nodes = graph.numberOfNodes()
    old_num_edges = graph.numberOfEdges()

    graph.removeSelfLoops()
    graph.removeMultiEdges()

    # Collapse nodes with out-degree 1 (or 0).
    for node in graph.iterNodes():
      if graph.degreeOut(node) <= 1:
        for out_node in graph.iterNeighbors(node):
          for in_node in graph.iterInNeighbors(node):
            graph.addEdge(in_node, out_node)
        graph.removeNode(node)
        break

  return graph

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm_file", type=Path)
  parser.add_argument("--line-num", "-n", type=int)
  args = parser.parse_args()
  
  if args.line_num == None:
    # Multi-TM use-case
    num_structured = 0
    num_total = 0
    with open(args.tm_file) as infile:
      for record in IO.IO(infile, None):
        graph = ttable_to_digraph(record.ttable)
        graph = collapse_graph(graph)
        num_total += 1
        if graph.numberOfNodes() == 0:
          num_structured += 1

        if num_total % 100_000 == 0:
          print(f"... {num_structured:_} / {num_total:_} = {num_structured / num_total:.0%}")
      print(f"Structured TMs: {num_structured:_} / {num_total:_} = {num_structured / num_total:.0%}")

  else:
    # Single TM use-case
    ttable = IO.load_TTable_filename(args.tm_file, args.line_num)
    graph = ttable_to_digraph(ttable)
    graph = collapse_graph(graph)
    print(f"Collapsed to graph: {graph.numberOfNodes():_} nodes / {graph.numberOfEdges():_} edges")

if __name__ == "__main__":
  main()
