# TORrents
##[Explore the TORrents docs »](https://theonionbay.github.io/TORrents/)

## Setup

Install pipenv and python3, then:

```
pipenv install
```

## Unit Test
To run all unit test in the, run the command

```
python -m unittest discover
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

### Node

```
(venv shell)$ python node.py <ip>
```
Where `<ip>` is the public ip of the machine.