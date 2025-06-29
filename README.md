# A puzzle for the July 2025 ACTS in Romania

More info about the camp: https://lp.jetbrains.com/acts-romania-2025/

Some space tourists from Tau Ceti have arrived on Earth and are asking for your help!  They accidentally deleted the
binary of their landing software. They've still got the source code, but they're not programmers and have no idea how to
get it running. What's worse, their spaceship computer uses a strange tree-based bytecode, and they forgot their
compiler at home. At least they brought all the documentation. They even have an interpreter for the bytecode, though
it's got a dummy implementation of the instruction that communicates with the ship memory banks.

Help them by translating their program into a program that their ship will understand!  Since landing a spaceship is a time-sensitive activity, the goal is for the program you generate to run in as few steps as possible.

During the camp, I'll give a lecture and introduce some algorithms that will help with this, and I'll be around for the
first half to answer questions.  You can also reach me on Discord via `jesyspa`.


## This repository

Here you'll find:
- The landing program that the aliens need to get working: `landing.ufo`
- A simulator for the bytecode their computer uses: `simulator.py`

In the `examples/` directory, there are a number of other UFO language programs
that may be useful testcases for your compiler.

## UFO: Source Language

The landing program is written in the Universal Functional Operations language.
It's a very versatile program and needs the data it gets from the ship computer
to land the spacecraft correctly.

The language works as follows.
Every expression is either an integer, variable, or of the form `(f a b c...)`.
For the last, `f` determines how the expression should behave.
The rules are as follows; 
- At the top level, every expression has to be of the form `(define name foo)`,
  and indicates that `name` is shorthand for `foo`.
- `(lambda (x y z) body)` is a function that takes `x`, `y`, `z` and returns `body`.
  - Note: `body` is a single expression.
- In other cases, `(f a b c)` evaluates all of `f`, `a`, `b`, `c` and then calls `f` with `a, b, c` as arguments.
  - Symbolically: `((lambda (x y) body) a b)` becomes `body[x -> a, y -> b]`.

There are a number of built-in functions.
We use `n` and `m` when the parameter has to be a number.
- Each mathematical operators `op` in `{+, -, *, /}` takes `n` and `m` and returns `n op m`.
- `print` takes `n` and `x`, prints `n` (treated as an ASCII value) and returns `x`.
- `if` takes `n`, `x`, `y`, returns `x` if `n` is 0 and `y` if cond is `1`.
  - So 0 represents true and 1 represents false.  The aliens don't know why you're confused.
  - Since `if` is just a function, *all* arguments are evaluated, as with any other function.
- `Q` takes `n`, sends it to the flight module, and returns the number it gets as a response.

To execute a UFO program, run the expression defined as `main`.
The final state is whatever this expression evaluates to.
For example, the following program will evaluate to 1:
```
(define four (+ 2 2))
(define main (- four 3))
```

The aliens have a number of other example programs, for which they do have compiled
versions.

## Tree: Bytecode

The ship computer executes instructions in a bytecode that operates on trees.
The instructions are kept in an array, and the computer state consists of an
instruction pointer and a tree.

The trees consist of binary nodes (denoted `:+:`), empty (nil) nodes, and integers.
For example: `(nil :+: 5) :+: 7`.
We use `n` and `m` to denote when a node has to be an integer.
We let `:+:` associate to the left, so the above example can be written `nil :+: 5 :+: 7`.

The instructions are as follows.
We describe them by giving the starting tree, the resulting tree, and the side effects.

- `quit`: shut down the computation.
  - Not recommended until landing is complete.
- `jump`: `xs :+: n ~> xs` and set the instruction pointer to `n`.
- `left`: `xs :+: ys ~> xs`
- `right`: `xs :+: ys ~> ys`
- `rec_left`: `xs :+: n ~> xs :+: xs'` where `xs'` is `xs` with `n` applications of `left`.
  - `n` can be zero: `xs :+: 0 ~> xs :+: xs`
- `left_on_right`: `xs :+: (ys :+: zs) ~> xs :+: ys`
- `right_on_right`: `xs :+: (ys :+: zs) ~> xs :+: zs`
- `pair`: `xs :+: ys :+: zs ~> xs :+: (ys :+: zs)`
- `unpair`: `xs :+: (ys :+: zs) ~> xs :+: ys :+: zs`
- `pick`: Depends on top value:
  - `xs :+: ys :+: zs :+: 0 ~> zs`
  - `xs :+: ys :+: zs :+: 1 ~> ys`
- `add`: `xs :+: n :+: m ~> xs :+: (m + n)`
- `sub`: `xs :+: n :+: m ~> xs :+: (m - n)`
- `mul`: `xs :+: n :+: m ~> xs :+: (m * n)`
- `div`: `xs :+: n :+: m ~> xs :+: (m / n)`
- `print`: `xs :+: n ~> xs` and print `n` as an ASCII character
- `Q`: `xs :+: n ~> xs :+: result` where `result` is obtained from ship memory
- `nil`: `xs ~> xs :+: nil`
- a number `n`: `xs ~> xs :+: n`

Initially, the tree is nil and the instruction pointer is 0.
Every instruction except `jump` and `quit` increments the instruction pointer.
If the instruction pointer is out of bounds, the program terminates.

If the interpreter ends in a state of the form `xs :+: n`
(that is, a tree where the right-hand side is a number),
we treat `n` as the result of the computation.

For example, the following code mimics the UFO example above and also
evaluates to 12:

```
// initial state: nil
3       // nil :+: 3
2       // nil :+: 3 :+: 2
2       // nil :+: 3 :+: 2 :+: 2
add     // nil :+: 3 :+: 4
sub     // nil :+: 12
```

You can run the simulator as follows:
```sh
python simulator.py [file.tree]
```

Optionally, you can pass test data to use for the implementation of `Q` using `-Q datafile.Q`.
