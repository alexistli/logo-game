#!/usr/bin/env python3
"""
TCP server in python implementing a simple protocol very loosely inspired by LOGO.
When a client connects, it will be able to send simple commands to the server to draw on a canvas.
It will also call ask the server to render the current canvas.
"""

# Standard library imports
from socketserver import StreamRequestHandler, TCPServer
from typing import Tuple

# Third party imports
import numpy as np
import numpy.typing as npt


class Canvas:
    """The canvas that the client will draw on by sending commands."""

    upper_left_corner = "\u2554"
    upper_right_corner = "\u2557"
    lower_right_corner = "\u255d"
    lower_left_corner = "\u255a"
    horizontal = "\u2550"
    vertical = "\u2551"

    def __init__(self, cols: int, rows: int):
        self.cols = cols
        self.rows = rows
        # canvas is a Numpy array as it implements the buffer protocol
        self.canvas = np.array([[" " for col in range(cols)] for row in range(rows)])

    def framed_canvas(self) -> np.ndarray:
        """Returns the canvas with the frame applied.

        The frame uses characters from the Unicode box-drawing character set.
        """
        # creating the upper border array
        upper_border = list(
            Canvas.upper_left_corner
            + Canvas.horizontal * 30
            + Canvas.upper_right_corner
        )
        # creating the lower border array
        lower_border = list(
            Canvas.lower_left_corner
            + Canvas.horizontal * 30
            + Canvas.lower_right_corner
        )
        # creating the vertical border as an array of arrays of dimension (1, 30)
        vertical_border = np.array(list(Canvas.vertical * 30))

        # creating a new array including the frame borders
        framed = np.r_[
            [upper_border],
            np.c_[vertical_border, self.canvas, vertical_border],
            [lower_border],
        ]
        return framed

    def render(self) -> str:
        """Renders the canvas with the frame applied.

        Each line is separated by \r\n.
        The final line is followed by \r\n\r\n to indicate the end of the command.
        Note: final "\r\n" is managed by the handler().
        """

        rendered_canvas = (
            "\r\n".join(("".join(row) for row in self.framed_canvas())) + "\r\n"
        )
        return rendered_canvas

    def draw(self, x: int, y: int) -> None:
        """Draws a star "*" on canvas at (x,y) coordinates.

        Args:
            x: x coordinate on the canvas
            y: y coordinate on the canvas
        """

        # Draws a star
        self.canvas[y][x] = "*"

    def erase(self, x: int, y: int) -> None:
        """Erases by leaving a whitespace " " on canvas at (x,y) coordinates.

        Args:
            x: x coordinate on the canvas
            y: y coordinate on the canvas
        """

        # Erases by leaving a whitespace
        self.canvas[y][x] = " "


class Cursor:
    """The cursor bound to the canvas and used to navigate and draw
    on the canvas.
    """

    # 8 possibles directions are mapped using a polar coordonates system (compass like):
    # top is 0°, left is 90°, bottom is 180°, right is 270°, etc...
    # For each key the value is a tuple of cartesian directions:
    # Example: (1, 0) means (y=1, x=0) so it corresponds to up, which is 0°
    # (0, -1) means (y=0, x=-1) so it corresponds to right, which is 270°
    directions = {
        0: (-1, 0),
        45: (-1, 1),
        90: (0, 1),
        135: (1, 1),
        180: (1, 0),
        225: (1, -1),
        270: (0, -1),
        315: (-1, -1),
    }
    brush_modes = ("hover", "draw", "eraser")

    def __init__(self, x: int, y: int, direction: int, brush_mode: str):
        self.x = x
        self.y = y
        self.direction = direction
        self._brush_mode = brush_mode

    @property
    def brush_mode(self) -> str:
        """Getter and Setter methods for the brush_mode attribute."""

        return self._brush_mode

    @brush_mode.setter
    def brush_mode(self, mode: str) -> None:
        if mode not in Cursor.brush_modes:
            raise ValueError(
                "Invalid brush mode. Must be one of: {', '.join((*Cursor.brush_modes,))}"
            )
        self._brush_mode = mode

    def _rotate(self, step: int) -> None:
        """Does the rotation calculation."""

        # new direction is calculated and normalized to not excess 360
        new_direction = (self.direction + step * 45) % 360

        # direction attribute is made to be always positive
        if new_direction < 0:
            new_direction = 360 - new_direction

        self.direction = new_direction

    def rotate(self, rotation: str, n: int) -> None:
        """Rotates n times in left (counter-clockwise) or right (clockwise) rotations.

        Normalized rotation is clockwise.
        A counter-clockwise rotation will be converted to a negative rotation.

        Example: a rotation ("left", 3) will be converted to ("right", -3).
        """

        if rotation == "left":
            self._rotate(-n)
        elif rotation == "right":
            self._rotate(n)

    def get_coords(self) -> str:
        """Returns a stringified tuple of (x, y) coords, space is removed."""

        return str((self.x, self.y)).replace(" ", "")

    def increment(self, position: int, step: int, min: int, max: int) -> int:
        """Ensures that moves are within boundaries of the canvas.

        Args:
            position: x/y coordinate on the canvas
            step: step that is asked to move the x/y coordinate
            min: x/y min coordinate on the canvas
            max: x/y max coordinate on the canvas
        """

        if not step:
            return position
        if position + step > max:
            return position
        elif position + step < min:
            return position
        else:
            return position + step

    def move(self, n: int) -> None:
        """Move n steps in current direction and executes drawing actions."""
        
        # Initializes previous_pos with out of range values.
        previous_pos = (self.x_max + 1, self.y_max + 1)

        # Testing previous_pos against the current coordinates.
        # Stationarity means we reached a border and we should stop.
        # Also a security against huge n values given with the steps <n> command.
        while n > 0 and previous_pos != (self.x, self.y):
            n -= 1

            if self.brush_mode == "draw":
                self.canvas.draw(self.x, self.y)
            elif self.brush_mode == "erase":
                self.canvas.erase(self.x, self.y)

            # Memorizes cursor coordinates before executing move.
            previous_pos = (self.x, self.y)

            self.x = self.increment(
                self.x, Cursor.directions[self.direction][1], self.x_min, self.x_max
            )
            self.y = self.increment(
                self.y, Cursor.directions[self.direction][0], self.y_min, self.y_max
            )

    def load_canvas(self, canvas: "Canvas") -> None:
        """Helper to initialize a cursor's boundaries based on the canvas properties."""

        self.x_min = 0
        self.y_min = 0
        self.x_max = canvas.rows - 1
        self.y_max = canvas.cols - 1
        self.canvas = canvas


class LogoHandler(StreamRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and overrides
    the setup() and handle() methods to implement communication to the client.
    """

    def handle(self) -> None:
        """handle() method is listening to the socket and handles commands and responses."""

        print(f"\nNew connection from {self.client_address[0]}")
        print("Commands:")

        # instantiate cursor
        self.cursor = Cursor(15, 15, 0, "draw")
        # instantiate canvas
        self.canvas = Canvas(30, 30)
        # initialize ou cursor boundaries based on the canvas properties.
        self.cursor.load_canvas(self.canvas)

        # Hello!
        self.wfile.write(b"hello\r\n")

        while True:
            # self.request is the TCP socket connected to the client
            data = self.rfile.readline().strip().decode()

            if not data:
                break

            # shows in console the data received
            print(f"> {data}")

            # converts data to coommand along its parameter
            command, step = generate_command_parameters(data)

            if command == "coord":
                # writes back to the client the current coordinates
                self.wfile.write((self.cursor.get_coords() + "\r\n").encode())
            elif command == "render":
                # writes back to the client the current coordinates
                rendered_canvas = self.canvas.render() + "\r\n"
                self.wfile.write(rendered_canvas.encode())
                # prints the rendered canvas to the console
                print(rendered_canvas)
            elif command == "steps":
                # steps command value defaulted to 1 if no value is given
                self.cursor.move(step)
            elif command == "right":
                # right command value defaulted to 1 if no value is given
                self.cursor.rotate(command, step)
            elif command == "left":
                # left command value defaulted to 1 if no value is given
                self.cursor.rotate(command, step)
            elif command in Cursor.brush_modes:
                # changes brush mode
                self.cursor.brush_mode = command
            elif command == "quit":
                # not necessary as client closes the socket,
                # thus closing the connection for the server
                break


def generate_command_parameters(command: str) -> Tuple[str, int]:
    """Helper function to generate parameters from commands passed as string.

    A command string is converted to a (action: str, step: int) tuple.
    Pattern is:
        command is an "action step" string than we can split and unpack
        if commmand is a one-word string, step is defaulted to 1
    """

    # try to split and unpack the command string
    try:
        action, step = command.split(" ")
    # NameError is raised if not enough values to unpack,
    # thus we know the command must be one-word and we default step to 1
    except ValueError:
        action = command
        step = "1"
    # return a tuple of (action: str, step: int)
    return (action, int(step))

if __name__ == "__main__":
    # host and port are hardcoded to match client's config (hardcoded)
    HOST, PORT = "localhost", 8124

    # Create the server, binding to localhost on port 8124
    with TCPServer((HOST, PORT), LogoHandler) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C (unix) / Ctrl-D (windows)
        server.serve_forever()
