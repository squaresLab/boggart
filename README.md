# Hulk

[![Build Status](https://travis-ci.com/squaresLab/Hulk.svg?branch=master)](https://travis-ci.com/squaresLab/Hulk)

Hulk is a microservices-based system for mutation testing of code written
in arbitrary languages. Hulk is built on top of the small-but-mighty Rooibos,
a language-independent platform for source code transformation.

## Installation

```
$ pip install hulk --user
```

## Supported Languages

Currently, Hulk comes prepackaged with a collection of mutation operators
that target programs written in the following languages:

* C
* C++

## Extending Hulk

### Adding support for other programming languages

```
...

languages:
  ...
  - name: php
    file_endings: .php

...
```

### Adding new mutation operators
