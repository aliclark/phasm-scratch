# phasm-scratch
Some initial module and library code and a test program for Phasm.

Phasm is a generic assembler or binary generation language that can be found at here: https://github.com/aliclark/phasm

program.psm is a basic example of what the code looks like.

To compile, first copy (I'm sorry :-() compiler.py and common.py into
this directory and run:

```
./compiler.py <program.psm >program
chmod +x program
hexdump -C program

# and if you're happy it's not a virus
./program; echo $?
```

It's still at a very early stage, so lots of things will get better,
like ELF output, sharing of code, use of the compiler, opcodes, etc..

phasm-manifest.conf is an aspiration to a basic dependency definition
file.

Enjoy! Patches welcome :)
