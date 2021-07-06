import pygame
import pygame.freetype
from pygame.freetype import Font
from pygame import math
from pygame.math import Vector2 as vec2
from pygame import draw
from pygame import Color, Surface, Rect
import random

# TODO: Update https://www.reddit.com/user/EishLekker/ if you write a solver algorithm that solves from current state.

c_gray = lambda v: (v,v,v)

# Set up the global variables

black   = c_gray(0)
white   = c_gray(255)
midgray = c_gray(127)
lightgray = c_gray(200)
red     = (255,0,0)
green   = (0,255,0)
blue    = (0,0,255)

screen : pygame.Surface = None
courier_new : Font= None
number_sizes : list[Rect] = None
peg_surf : Surface = None

def lerp(a,b,t):
    if t <= 0:
        return a
    if t >= 1:
        return b
    return a + (b - a) * t

class HanoiDisk:
    __slots__ = ('value','surface', 'draw_size')

    def __init__(self, value, color=(255,255,255)):
        self.value = value
        self.draw_size = ((value + 1) * 15, 20)
        self.surface = pygame.Surface(self.draw_size)
        self.draw_surface(color)

    def __lt__(self, other):
        return self.value < other.value
    
    def __gt__(self, other):
        return self.value > other.value
    
    def draw_surface(self, color=(255,255,255)):
        self.surface.fill((255,255,255))
        draw_rect = (0,0, self.surface.get_width(), self.surface.get_height())

        draw.rect(self.surface, color, draw_rect)
        draw.rect(self.surface, black, draw_rect, 1)

        center = (draw_rect[2] / 2, draw_rect[3] / 2)
        text_size = number_sizes[self.value]
        text_offset = (center[0] - (text_size[0] / 2), center[1] - (text_size[1] / 2))
        courier_new.render_to(self.surface, text_offset, str(self.value), black)
    
    def blit(self, surf, anchorPos):
        # anchor pos should be the bottom middle
        offset = (self.draw_size[0] / 2, self.draw_size[1])
        surf.blit(self.surface, (anchorPos[0] - offset[0], anchorPos[1] - offset[1]))
    
    @property
    def width(self):
        return self.draw_size[0]

    @property
    def height(self):
        return self.draw_size[1]

class HanoiPeg:
    __slots__ = ('disks',)

    def __init__(self):
        self.disks = list()
    
    def pop(self) -> HanoiDisk:
        return self.disks.pop()
    
    def push(self, disk : HanoiDisk):
        self.disks.append(disk)
    
    def popto(self, peg):
        peg.push(self.pop())
    
    def draw(self, surf, pos):
        surf.blit(peg_surf, pos)
        if len(self.disks) == 0:
            return
        disk_pos = vec2(pos[0] + 115, pos[1] + 260)
        for disk in self.disks:
            disk.blit(surf, disk_pos)
            disk_pos.y -= disk.height
    
    def clear(self):
        self.disks.clear()

    @property
    def count(self) -> int:
        return len(self.disks)

    @property
    def top(self) -> HanoiDisk:
        if len(self.disks) > 0:
            return self.disks[-1]
        return None

class Towers:
    __slots__ = ('pegs', 'disk_count', 'last_moved_peg', 'last_moved_disk')
    peg_rects = (
        pygame.Rect(35, 50, 230, 270), 
        pygame.Rect(335, 50, 230, 270),
        pygame.Rect(635, 50, 230, 270)
        )
    
    peg_positions = (
        (35, 50),
        (335, 50),
        (635, 50)
    )

    def __init__(self, disk_count):
        self.last_moved_peg = None
        self.last_moved_disk = None
        self.disk_count = disk_count
        self.pegs = (HanoiPeg(), HanoiPeg(), HanoiPeg())
        for disk in (HanoiDisk(disk_count - i) for i in range(disk_count)):
            self.pegs[0].push(disk)
    
    def reset(self):
        self.pegs[0].clear()
        self.pegs[1].clear()
        self.pegs[2].clear()
        for disk in (HanoiDisk(self.disk_count - i) for i in range(self.disk_count)):
            self.pegs[0].push(disk)
    
    def set_disk_count(self, disk_count):
        self.disk_count = disk_count
        self.reset()
    
    def game_won(self) -> bool:
        return self.pegs[0].count == 0 and self.pegs[1].count == 0 and self.pegs[2].count > 0
    
    def can_move(self, fromPeg, toPeg):
        if self.pegs[fromPeg].count == 0:
            return False
        if self.pegs[toPeg].count == 0:
            return True
        return self.pegs[fromPeg].top < self.pegs[toPeg].top
    
    def try_move(self, fromPeg, toPeg):
        if self.can_move(fromPeg, toPeg):
            self.pegs[toPeg].push(self.pegs[fromPeg].pop())
            self.last_moved_disk = self.pegs[toPeg].top
            self.last_moved_peg = toPeg
            return True
        return False
    
    def draw(self, surf):
        self.pegs[0].draw(surf, Towers.peg_positions[0])
        self.pegs[1].draw(surf, Towers.peg_positions[1])
        self.pegs[2].draw(surf, Towers.peg_positions[2])
        if self.last_moved_peg is not None:
            disk_rect = self.get_disk_rect(self.last_moved_peg, self.pegs[self.last_moved_peg].count-1)
            draw.rect(screen, (255, 0, 0), disk_rect, 1)
    
    def get_disk_rect(self, peg_index : int, disk_index : int) -> Rect:
        if peg_index < 0 or peg_index >= 3 or disk_index < 0:
            return Rect(0,0,0,0)
        peg = self.pegs[peg_index]

        if disk_index >= len(peg.disks):
            return Rect(0,0,0,0)

        disk = peg.disks[disk_index]
        
        disk_size = disk.draw_size

        # disk_pos = vec2(pos[0] + 115, pos[1] + 260)
        # To get the disk rect, we need to iterate through the disks, adding up the heights.
        peg_rect = Towers.peg_rects[peg_index]
    
        disk_bottom = 0
        
        for i in range(disk_index):
            disk_bottom += peg.disks[i].draw_size[1]
        
        return Rect(peg_rect.x + 115 - (disk_size[0] // 2), peg_rect.y + 260 - disk_bottom - disk_size[1], disk_size[0], disk_size[1])


    def valid_moves(self):
        moves = []
        for from_index in range(3):
            for to_index in (_ for _ in range(3) if _ != from_index):
                if self.can_move(from_index, to_index):
                    moves.append((from_index, to_index))
        return moves
    
    def randomize(self, cycles = None):
        if cycles is None:
            cycles = (2**self.disk_count-1) * 4
        for i in range(cycles):
            self.try_move(*random.choice(self.valid_moves()))
    
    def calc_next_move(self):
        # The goal is to find the largest peg and its location.
        # In order to move two disks from one peg to another (a to b) where the pegs are a, b, c:
        #   move from a to c
        #   move from a to b
        #   move from c to b
        # In order to move a larger disk onto a peg with only smaller disks:
        # where larger disk is on peg b, the smaller disks on peg c, and the largest disk on peg a:
        # Use the algorithm for two disks to move the top two disks from peg c to peg a.
        # Move the disk from peg b to peg c
        # Move the two disks back to peg c from peg a
        return
    
    def __getitem__(self, index):
        return self.pegs[index]

class TowersGame:
    pass

def main():
    # The code below is written intentionally "badly", as an exercize.
    # The idea is that the main() method will serve as if it is an independant script.
    # The entirety of the programs logic will fit inside this one method.
    # Why? Because I've gone mad with power!

    # imports

    pygame.init()
    pygame.display.set_caption('Towers of Hanoi')
    global screen, courier_new, number_sizes, peg_surf
    screen = pygame.display.set_mode([900, 600])
    courier_new = pygame.freetype.SysFont('Courier New', 14)
    number_sizes = [courier_new.get_rect(str(i)).size for i in range(31)]
    peg_surf = Surface((230, 270), pygame.SRCALPHA)

    tick = None
    clock = pygame.time.Clock()
    time_delta = 0.0

    peg_surf.fill((0,0,0,0))

    success_window_rect = pygame.Rect(150, 100, 600, 400)

    draw.rect(peg_surf, black, (110, 0, 10, 260))
    draw.rect(peg_surf, black, (0, 260, 230, 10))
    
    towers = Towers(3)

    clicked_peg = None
    down_peg = None
    up_peg = None
    key_down_peg = None


    mouse_events = {pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION}
    last_mouse_down : bool = False
    mouse_down : bool = False
    mouse_pos = pygame.mouse.get_pos()

    disk_count = 3
    move_count = 0

    last_moved_disk = None

    # Run until the user asks to quit
    running = True
    
    # This is the success flag. This is True when the player has won (by getting all 
    # the disks to the right-most peg).
    # If this is set to True, we will stop doing input for the game and show a window overlay.
    GameSuccess = False
    ShowSuccess = False

    def GameWon():
        GameSuccess = True
        ShowSuccess = True

    def ResetGame():
        GameSuccess = False
        ShowSuccess = False
        move_count = 0
        towers.reset()

    # class definitions

    class ClickRect:
        # Captures all mouse events (except scroll) when the mouse is within rect
        def __init__(self, rect, callback):
            if type(rect) == tuple:
                rect = pygame.Rect(*rect)
            self.rect = rect
            self.callback = callback
        
        def event(self, event):
            self.callback(self, event)
        
        def has(self, pos):
            self.rect.collidepoint(pos)

    # function defintions

    # draw_btn variables
    button_color = Color(210,210,210)
    button_hover_color = c_gray(200)
    button_pressed_color = c_gray(190)
    button_disabled_color = c_gray(150)

    success_window_color = (220, 220, 220)

    def label(text, rect : Rect, size = 0, font : Font = courier_new, **kwargs):
        if type(text) != str:
            text = str(text)
        if type(rect) == tuple:
            rect = pygame.Rect(*rect)
        text_rect = font.get_rect(text, size=size)
        half_size = (text_rect.size[0] / 2, text_rect.size[1] / 2)
        text_pos = (rect.center[0] - half_size[0], rect.center[1] - half_size[1])
        font.render_to(screen, text_pos, text, black, size = size, **kwargs)

    def button(text, rect : pygame.Rect, size=0, font : Font = courier_new, disabled = False, **kwargs) -> bool:
        if type(rect) == tuple:
            rect = pygame.Rect(*rect)
        
        result = False

        if disabled:
            draw.rect(screen, button_disabled_color, rect)
            draw.rect(screen, black, rect, 1)
            result = False
        else:
            if rect.collidepoint(mouse_pos):
                if mouse_down:
                    if not last_mouse_down:
                        result = True
                    draw.rect(screen, button_pressed_color, rect)
                    draw.rect(screen, black, rect, 1)
                else:
                    draw.rect(screen, button_hover_color, rect)
                    draw.rect(screen, black, rect, 1)
            else:
                draw.rect(screen, button_color, rect)
                draw.rect(screen, black, rect, 1)
        label(text, rect, size, font, **kwargs)
        return result

    while running:
        tick = clock.tick()
        time_delta = tick / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        # Did the user click the window close button?

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_down = True
                down_peg = None
                not_clicked = True
                for i, peg_rect in enumerate(Towers.peg_rects):
                    if peg_rect.collidepoint(mouse_pos):
                        not_clicked = False
                        down_peg = i
                        if clicked_peg is None:
                            clicked_peg = i
                        elif clicked_peg != i:
                            if not GameSuccess and towers.try_move(clicked_peg, i):
                                clicked_peg = None
                                move_count += 1
                        break
                if not_clicked:
                    clicked_peg = None
                    key_down_peg = None
            elif event.type == pygame.MOUSEBUTTONUP:
                mouse_down = False
                up_peg = None
                for i, peg_rect in enumerate(Towers.peg_rects):
                    if peg_rect.collidepoint(mouse_pos):
                        up_peg = i
                        if down_peg is not None and up_peg is not None and down_peg != up_peg:
                            if not GameSuccess and towers.try_move(down_peg, up_peg):
                                down_peg = None
                                up_peg = None
                                clicked_peg = None
                                move_count += 1
            elif event.type == pygame.KEYDOWN:
                peg_index = None
                if event.key == pygame.K_a:
                    peg_index = 0
                elif event.key == pygame.K_s:
                    peg_index = 1
                elif event.key == pygame.K_d:
                    peg_index = 2
                if peg_index is not None and key_down_peg is None and towers.pegs[peg_index].count > 0:
                    key_down_peg = peg_index
                elif peg_index is not None and key_down_peg is not None and peg_index != key_down_peg:
                    if not GameSuccess and towers.try_move(key_down_peg, peg_index):
                        move_count += 1
                    key_down_peg = None
                elif peg_index is not None and key_down_peg is not None and peg_index == key_down_peg:
                    key_down_peg = None

        # Check if the game has been won.
        if towers.game_won():
            GameSuccess = True

        # Fill the background with white
        screen.fill(white)

        for i, peg_rect in enumerate(Towers.peg_rects):
            if key_down_peg == i or peg_rect.collidepoint(mouse_pos):
                draw.rect(screen, lightgray, peg_rect, 1)

        towers.draw(screen)

        if button('Reset', Rect(10,10,100,30), disabled=GameSuccess):
            towers.reset()
            move_count = 0

        label(disk_count, Rect(140, 10, 40, 30), 14)

        if disk_count < 12 and button('+', Rect(180, 10, 15, 15), 14, disabled=GameSuccess):
            disk_count += 1
            towers.set_disk_count(disk_count)
            move_count = 0

        if disk_count > 3 and button('-', Rect(180, 25, 15, 15), 14, disabled=GameSuccess):
            disk_count -= 1
            towers.set_disk_count(disk_count)
            move_count = 0

        label(f'Moves: {move_count}/{2**disk_count-1}', Rect(240, 10, 100, 30))

        if button('Random', Rect(360, 10, 100, 30), disabled=GameSuccess):
            towers.randomize()
        
        if GameSuccess:
            draw.rect(screen, success_window_color, success_window_rect)
            draw.rect(screen, black, success_window_rect, 1)
            label("Game Won!", (success_window_rect.x + 30, success_window_rect.y + 30, 400, 50))

            if button("Reset", (success_window_rect.x + (success_window_rect.width / 2) - 146, success_window_rect.y + success_window_rect.height - 50, 292, 42)):
                GameSuccess = False
                towers.reset()
                move_count = 0

        pygame.display.flip()
        last_mouse_down = mouse_down
    pygame.quit()

if __name__ == '__main__':
    main()