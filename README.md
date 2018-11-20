# TORrents

## Setup

Install pipenv and python3, then:

```
pipenv install
```

## Usage

The three entrypoints to the application are `tracker.py`, `client.py` and `node.py`.

### Tracker

To start an instance of the tracker, run:

```
(venv shell)$ python tracker.py
```

### Client

```
(venv shell)$ python client.py <path-to-list-of-files>
```

where `<path-to-list-of-files>` can be `client/a.json` or
`client/b.json` etc.
