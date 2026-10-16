import curses
import random
import time


W, H = 10, 20

SCORES = {
    0: 0,
    1: 100,
    2: 300,
    3: 500,
    4: 800,
}

SHAPES = [
    [(-1, 0), (-2, 0), (0, 0), (1, 0)],
    [(0, -1), (-1, -1), (-1, 0), (0, 0)],
    [(-1, 0), (-1, 1), (0, 0), (0, -1)],
    [(0, 0), (-1, 0), (0, 1), (-1, -1)],
    [(0, 0), (0, -1), (0, 1), (-1, -1)],
    [(0, 0), (0, -1), (0, 1), (1, -1)],
    [(0, 0), (0, -1), (0, 1), (-1, 0)],
]

BOARD_X = 2
BOARD_Y = 5

MIN_ROWS = BOARD_Y + H + 4
MIN_COLS = 48


class Tetris:
    def __init__(self):
        self.reset()

    def reset(self):
        self.board = [[0] * W for _ in range(H)]
        self.score = 0
        self.lines = 0
        self.game_over = False
        self.spawn()

    def spawn(self):
        shape_index = random.randrange(len(SHAPES))

        self.piece = [
            (x + W // 2, y + 1)
            for x, y in SHAPES[shape_index]
        ]
        self.colour = shape_index + 1

        if not self.valid(self.piece):
            self.game_over = True

    def valid(self, piece):
        for x, y in piece:
            if not (0 <= x < W and 0 <= y < H):
                return False

            if self.board[y][x]:
                return False

        return True

    def move(self, dx, dy):
        candidate = [
            (x + dx, y + dy)
            for x, y in self.piece
        ]

        if self.valid(candidate):
            self.piece = candidate
            return True

        return False

    def rotate(self):
        pivot_x, pivot_y = self.piece[0]

        candidate = [
            (
                pivot_x - (y - pivot_y),
                pivot_y + (x - pivot_x),
            )
            for x, y in self.piece
        ]

        if self.valid(candidate):
            self.piece = candidate

    def lock_piece(self):
        touched_top = any(y == 0 for _, y in self.piece)

        for x, y in self.piece:
            self.board[y][x] = self.colour

        remaining = [
            row[:] for row in self.board
            if not all(row)
        ]

        cleared = H - len(remaining)

        self.board = (
            [[0] * W for _ in range(cleared)]
            + remaining
        )

        self.score += SCORES[cleared]
        self.lines += cleared

        if touched_top:
            self.game_over = True
        else:
            self.spawn()

    def step_down(self):
        if not self.move(0, 1):
            self.lock_piece()

    def hard_drop(self):
        while self.move(0, 1):
            pass

        self.lock_piece()


def setup_colours():
    if not curses.has_colors():
        return False

    curses.start_color()

    colours = [
        curses.COLOR_CYAN,
        curses.COLOR_YELLOW,
        curses.COLOR_GREEN,
        curses.COLOR_RED,
        curses.COLOR_BLUE,
        curses.COLOR_MAGENTA,
        curses.COLOR_WHITE,
    ]

    for pair_id, colour in enumerate(colours, start=1):
        curses.init_pair(
            pair_id,
            colour,
            curses.COLOR_BLACK,
        )

    return True


def draw(screen, game, use_colours):
    screen.erase()

    screen.addstr(0, BOARD_X, "TERMINAL TETRIS", curses.A_BOLD)
    screen.addstr(
        2,
        BOARD_X,
        f"Score: {game.score}   Lines: {game.lines}",
    )

    border = "+" + "--" * W + "+"

    screen.addstr(BOARD_Y - 1, BOARD_X, border)

    for y in range(H):
        screen.addstr(BOARD_Y + y, BOARD_X, "|")
        screen.addstr(
            BOARD_Y + y,
            BOARD_X + 1 + W * 2,
            "|",
        )

    screen.addstr(BOARD_Y + H, BOARD_X, border)

    def draw_cell(x, y, colour):
        attribute = curses.A_BOLD

        if use_colours:
            attribute |= curses.color_pair(colour)

        screen.addstr(
            BOARD_Y + y,
            BOARD_X + 1 + x * 2,
            "[]",
            attribute,
        )

    # Locked pieces
    for y, row in enumerate(game.board):
        for x, colour in enumerate(row):
            if colour:
                draw_cell(x, y, colour)

    # Active piece
    if not game.game_over:
        for x, y in game.piece:
            draw_cell(x, y, game.colour)

    screen.addstr(
        BOARD_Y + H + 2,
        BOARD_X,
        "A/D: move  W: rotate  S: down",
    )
    screen.addstr(
        BOARD_Y + H + 3,
        BOARD_X,
        "Space: drop  R: restart  Q: quit",
    )

    if game.game_over:
        message_y = BOARD_Y + H // 2

        # Clear a small area over the board
        for offset in range(-1, 3):
            screen.addstr(
                message_y + offset,
                BOARD_X + 1,
                " " * (W * 2),
            )

        message = "GAME OVER"
        restart = "R: restart"

        screen.addstr(
            message_y,
            BOARD_X + 1 + (W * 2 - len(message)) // 2,
            message,
            curses.A_BOLD,
        )
        screen.addstr(
            message_y + 1,
            BOARD_X + 1 + (W * 2 - len(restart)) // 2,
            restart,
        )

    screen.refresh()


def main(screen):
    try:
        curses.curs_set(0)
    except curses.error:
        pass

    screen.keypad(True)
    screen.nodelay(True)

    use_colours = setup_colours()
    game = Tetris()

    last_fall = time.monotonic()

    while True:
        rows, cols = screen.getmaxyx()

        # Pause gameplay while the terminal is too small
        if rows < MIN_ROWS or cols < MIN_COLS:
            screen.erase()

            message = (
                f"Resize to {MIN_COLS} cols x {MIN_ROWS} rows. Q quits."
            )

            if rows > 0 and cols > 1:
                screen.addnstr(0, 0, message, cols - 1)

            screen.refresh()

            key = screen.getch()
            if key in (ord("q"), ord("Q")):
                break

            last_fall = time.monotonic()
            time.sleep(0.05)
            continue

        # Process queued input without waiting for a key
        key = screen.getch()

        while key != -1:
            if key in (ord("q"), ord("Q")):
                return

            if key in (ord("r"), ord("R")):
                game.reset()
                last_fall = time.monotonic()

            elif not game.game_over:
                if key in (curses.KEY_LEFT, ord("a"), ord("A")):
                    game.move(-1, 0)

                elif key in (
                    curses.KEY_RIGHT,
                    ord("d"),
                    ord("D"),
                ):
                    game.move(1, 0)

                elif key in (
                    curses.KEY_UP,
                    ord("w"),
                    ord("W"),
                ):
                    game.rotate()

                elif key in (
                    curses.KEY_DOWN,
                    ord("s"),
                    ord("S"),
                ):
                    game.step_down()
                    last_fall = time.monotonic()

                elif key == ord(" "):
                    game.hard_drop()
                    last_fall = time.monotonic()

            key = screen.getch()

        now = time.monotonic()
        fall_delay = max(0.08, 0.55 - game.lines * 0.005)

        if not game.game_over and now - last_fall >= fall_delay:
            game.step_down()
            last_fall = now

        draw(screen, game, use_colours)
        time.sleep(1 / 60)


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass