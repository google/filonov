[![PyPI](https://img.shields.io/pypi/v/filonov?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/filonov)
[![Downloads PyPI](https://img.shields.io/pypi/dw/filonov?logo=pypi)](https://pypi.org/project/filonov/)

# Installing filonov

## Create and activate virtual environment

/// tab | pip
```bash
python -m venv .venv
source .venv/bin/activate
```
///

/// tab | uv
```bash
uv venv
source .venv/bin/activate
```
///

## Installation

/// tab | pip
```python
pip install filonov
```
///

/// tab | uv
```python
uv add filonov
```
///

###  with UI support

In order to interact with data generation pipeline of `filonov` via UI you need install additional dependencies.

/// tab | pip
```python
pip install filonov[ui]
```
///

/// tab | uv
```python
uv add filonov[ui]
```
///

###  with server support

In order to call `filonov` via API you need install additional dependencies.

/// tab | pip
```python
pip install filonov[server]
```
///

/// tab | uv
```python
uv add filonov[server]
```
///
