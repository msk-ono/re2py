# re2py

Implementation of Ruxx Cox's https://swtch.com/~rsc/regexp/regexp1.html in python

## How to use

See `tests/` and `examples/`.

## Visualize in SVG format

### NFA

REGEX  = `a(bb)+a`

![](images/nfa.svg)

### Match process

REGEX  = `a(bb)+a`
STRING = `abbbba`

![](images/0.svg) ![](images/1.svg) ![](images/2.svg) ![](images/3.svg) ![](images/4.svg) ![](images/5.svg)
