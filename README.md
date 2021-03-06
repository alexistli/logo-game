# logo-game

`logo-game` is an app composed of a TCP server in python and a client in node.js used for testing.

The python server is implementing a simple protocol very loosely inspired by LOGO.
When a client connects, it will be able to send simple commands to the server to draw on a canvas.
It will also call ask the server to render the current canvas.

## Approach

The server side is handled by `sockerserver` library which is available in the Python Standard Library.

A Canvas class handles the canvas, the rendering and the drawing operations.

A Cursor class handles the cursor related operations. Canvas is loaded in the cursor to initialize
cursor boundaries.

A LogoHandler class whose parent class BaseRequestHandler is imported from `sockerserver`.
LogoHandler is the request handler class for our server.
It is instantiated once per connection to the server, and overrides
the setup() and handle() methods of the BaseRequestHandler to implement communication to the client.

## Installation

### Server

Requirements:
- Python 3.8

Install Server:

```bash
$ pip install numpy
```

@TODO: Make the project installable

### Client

Requirements:
- Latest version of node.js

Install Client:

```bash
$ cd client
$ npm install
```

## Usage

### Server

Run the python server in a console:

```bash
$ cd server
$ python main.py
```

### Client

It will connect to your server, run several commands and verify the output.

Run the tests:

```bash
$ cd client
$ npm test
```

## Improvements

- Getting rid of Numpy and implementing native python buffer object available in the Standard Library.
- Moving cursor boundaries to Canvas class, makes little sense to have boundaries for the cursor.
