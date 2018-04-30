# boggart 

[![Build Status](https://travis-ci.org/squaresLab/boggart.svg?branch=master)](https://travis-ci.org/squaresLab/boggart)
[![Coverage Status](https://coveralls.io/repos/github/squaresLab/boggart/badge.svg?branch=master)](https://coveralls.io/github/squaresLab/boggart?branch=master)
[![Maintainability](https://api.codeclimate.com/v1/badges/4fb3632c3c3c6d935e1b/maintainability)](https://codeclimate.com/github/squaresLab/boggart/maintainability)

boggart is a microservices-based service for mutation testing of code written
in arbitrary languages. boggart is built on top of the small-but-mighty Rooibos,
a language-independent platform for source code transformation.

## Installation

To ensure isolation, we strongly recommend that users install boggart to a
dedicated
[virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/):

```
$ python3.6 -m venv env-boggart
$ . env-boggart/bin/activate
```

To download and install the latest stable release from PyPI:

```
(env-boggart) $ pip install --upgrade boggart
```

Or, to build from source:

```
(env-boggart) $ cd boggart
(env-boggart) $ pip install --upgrade .
```

## Supported Languages

Currently, boggart comes prepackaged with a collection of mutation operators
that target programs written in the following languages:

* C
* C++

## Extending boggart

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
