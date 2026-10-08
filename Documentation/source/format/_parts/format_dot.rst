**In command line:** ``-t/--fileType dot``

DOT is the plain-text graph language of Graphviz. Pyntacle reads it with
pygraphviz, which must be installed. Nodes are named by their DOT ids, so a
node declared on its own line with no edge is kept as an isolated node. With
``-w`` every edge needs a numeric ``weight`` attribute; if no edge has one,
every edge gets weight 1 and a warning says so.

.. code-block:: text

   graph G {
       A; B; C; D;
       A -- B [weight=0.7];
       A -- C [weight=0.3];
       B -- C [weight=0.9];
   }

A file declared ``digraph`` is read as undirected unless ``-d`` is given.
