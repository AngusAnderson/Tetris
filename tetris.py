import pygame
from copy import deepcopy
from random import choice, randrange

from music import render_song_bytes


# Window and board
W, H = 10, 20
TILE = 45
HEADER_HEIGHT = 80

BOARD_WIDTH = W * TILE
BOARD_HEIGHT = H * TILE
GAME_RES = BOARD_WIDTH, BOARD_HEIGHT + HEADER_HEIGHT
FPS = 60

# Movement timing, in milliseconds
MOVE_INITIAL_DELAY = 180
MOVE_REPEAT_DELAY = 75

# Score awarded for clearing multiple lines at once
LINE_SCORES = {
    0: 0,
    1: 100,
    2: 300,
    3: 500,
    4: 800,
}


pygame.mixer.pre_init(
    frequency=44100,
    size=-16,
    channels=1,
    buffer=512,
)
pygame.init()

game_sc = pygame.display.set_mode(GAME_RES)
pygame.display.set_caption("Tetris")
clock = pygame.time.Clock()

font = pygame.font.Font(None, 32)
small_font = pygame.font.Font(None, 24)
large_font = pygame.font.Font(None, 56)

music_sound = pygame.mixer.Sound(buffer=render_song_bytes())
music_channel = music_sound.play(loops=-1)
if music_channel is not None:
    music_channel.set_volume(0.5)

muted = False


figure_pos = [
    [(-1, 0), (-2, 0), (0, 0), (1, 0)],
    [(0, -1), (-1, -1), (-1, 0), (0, 0)],
    [(-1, 0), (-1, 1), (0, 0), (0, -1)],
    [(0, 0), (-1, 0), (0, 1), (-1, -1)],
    [(0, 0), (0, -1), (0, 1), (-1, -1)],
    [(0, 0), (0, -1), (0, 1), (1, -1)],
    [(0, 0), (0, -1), (0, 1), (-1, 0)],
]

figures = [
    [
        pygame.Rect(x + W // 2, y + 1, 1, 1)
        for x, y in positions
    ]
    for positions in figure_pos
]

grid = [
    pygame.Rect(
        x * TILE,
        HEADER_HEIGHT + y * TILE,
        TILE,
        TILE,
    )
    for x in range(W)
    for y in range(H)
]


def get_colour():
    return (
        randrange(30, 256),
        randrange(30, 256),
        randrange(30, 256),
    )


def new_piece():
    return deepcopy(choice(figures)), get_colour()


def valid_position(piece, board):
    """Check every block without allowing negative board indexing."""
    for block in piece:
        if not 0 <= block.x < W:
            return False

        if not 0 <= block.y < H:
            return False

        if board[block.y][block.x]:
            return False

    return True


def clear_lines(board):
    """Remove full rows and add empty rows at the top."""
    remaining_rows = [
        row[:] for row in board
        if not all(row)
    ]

    cleared = H - len(remaining_rows)
    empty_rows = [[0 for _ in range(W)] for _ in range(cleared)]

    return empty_rows + remaining_rows, cleared


def draw_block(x, y, colour):
    rect = pygame.Rect(
        x * TILE + 1,
        HEADER_HEIGHT + y * TILE + 1,
        TILE - 2,
        TILE - 2,
    )
    pygame.draw.rect(game_sc, colour, rect)


def draw_centred_text(text, text_font, colour, centre_y):
    surface = text_font.render(text, True, colour)
    rect = surface.get_rect(
        center=(BOARD_WIDTH // 2, centre_y)
    )
    game_sc.blit(surface, rect)


# Initial game state
field = [[0 for _ in range(W)] for _ in range(H)]
figure, colour = new_piece()

score = 0
total_lines = 0
game_over = False

fall_timer = 0
move_direction = 0
next_move_time = 0

running = True

while running:
    dt = clock.tick(FPS)
    now = pygame.time.get_ticks()
    rotate = False

    # One-off actions
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            elif event.key == pygame.K_m:
                muted = not muted

                if music_channel is not None:
                    music_channel.set_volume(0 if muted else 0.5)

            elif game_over and event.key == pygame.K_r:
                field = [[0 for _ in range(W)] for _ in range(H)]
                figure, colour = new_piece()

                score = 0
                total_lines = 0
                game_over = False

                fall_timer = 0
                move_direction = 0
                next_move_time = 0

            elif not game_over:
                if event.key in (pygame.K_w, pygame.K_UP):
                    rotate = True

    if not running:
        break

    # Read held keys after processing events
    keys = pygame.key.get_pressed()

    if not game_over:
        # Horizontal movement
        left = keys[pygame.K_a] or keys[pygame.K_LEFT]
        right = keys[pygame.K_d] or keys[pygame.K_RIGHT]

        direction = int(right) - int(left)
        dx = 0

        if direction == 0:
            move_direction = 0
            next_move_time = 0

        elif direction != move_direction:
            # Move immediately on a new press or direction change
            dx = direction
            move_direction = direction
            next_move_time = now + MOVE_INITIAL_DELAY

        elif now >= next_move_time:
            dx = direction
            next_move_time = now + MOVE_REPEAT_DELAY

        if dx:
            candidate = [block.move(dx, 0) for block in figure]

            if valid_position(candidate, field):
                figure = candidate

        # Rotate around the first block, without moving the pivot
        if rotate:
            pivot_x = figure[0].x
            pivot_y = figure[0].y
            candidate = deepcopy(figure)

            for block in candidate:
                relative_x = block.x - pivot_x
                relative_y = block.y - pivot_y

                block.x = pivot_x - relative_y
                block.y = pivot_y + relative_x

            if valid_position(candidate, field):
                figure = candidate

        # Gravity and held soft drop
        soft_drop = (
            keys[pygame.K_s]
            or keys[pygame.K_DOWN]
            or keys[pygame.K_SPACE]
        )

        normal_fall_delay = max(80, 550 - total_lines * 5)
        fall_delay = 35 if soft_drop else normal_fall_delay

        fall_timer += dt

        if fall_timer >= fall_delay:
            fall_timer = 0

            candidate = [block.move(0, 1) for block in figure]

            if valid_position(candidate, field):
                figure = candidate

            else:
                # Lock the current piece, preserving its colour
                for block in figure:
                    field[block.y][block.x] = colour

                # Apply your top-border rule before clearing rows
                touched_top = any(block.y == 0 for block in figure)

                field, cleared = clear_lines(field)
                score += LINE_SCORES[cleared]
                total_lines += cleared

                if touched_top:
                    game_over = True

                else:
                    figure, colour = new_piece()

                    # Also lose if the spawn area is blocked
                    if not valid_position(figure, field):
                        game_over = True

    # Background
    game_sc.fill((0, 0, 0))

    # Header above the playing grid
    pygame.draw.rect(
        game_sc,
        (25, 25, 35),
        (0, 0, BOARD_WIDTH, HEADER_HEIGHT),
    )

    score_surface = font.render(
        f"Score: {score}", True, (255, 255, 255)
    )
    lines_surface = small_font.render(
        f"Lines: {total_lines}", True, (190, 190, 205)
    )
    mute_surface = small_font.render(
        "M: unmute" if muted else "M: mute",
        True,
        (190, 190, 205),
    )

    game_sc.blit(score_surface, (15, 12))
    game_sc.blit(lines_surface, (15, 48))
    game_sc.blit(
        mute_surface,
        (BOARD_WIDTH - mute_surface.get_width() - 15, 48),
    )

    # Grid
    for rect in grid:
        pygame.draw.rect(game_sc, (40, 40, 40), rect, 1)

    # Landed blocks
    for y, row in enumerate(field):
        for x, block_colour in enumerate(row):
            if block_colour:
                draw_block(x, y, block_colour)

    # Falling piece
    if not game_over:
        for block in figure:
            draw_block(block.x, block.y, colour)

    # Top border of the playing area
    pygame.draw.line(
        game_sc,
        (150, 150, 170),
        (0, HEADER_HEIGHT),
        (BOARD_WIDTH, HEADER_HEIGHT),
        2,
    )

    # Game-over overlay
    if game_over:
        overlay = pygame.Surface(
            (BOARD_WIDTH, BOARD_HEIGHT),
            pygame.SRCALPHA,
        )
        overlay.fill((0, 0, 0, 190))
        game_sc.blit(overlay, (0, HEADER_HEIGHT))

        centre_y = HEADER_HEIGHT + BOARD_HEIGHT // 2

        draw_centred_text(
            "GAME OVER",
            large_font,
            (255, 90, 90),
            centre_y - 55,
        )
        draw_centred_text(
            f"Final score: {score}",
            font,
            (255, 255, 255),
            centre_y,
        )
        draw_centred_text(
            "Press R to restart",
            small_font,
            (210, 210, 220),
            centre_y + 45,
        )

    pygame.display.flip()

pygame.quit()