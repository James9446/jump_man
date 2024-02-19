# LCD Reference
# Guide: https://penguintutor.com/electronics/pico-lcd
# GitHub Repo: https://github.com/dhalbert/CircuitPython_LCD/tree/main

# BUTTONS Reference
# https://www.youtube.com/watch?v=nYA4PVljE4Q&list=PL9VJ9OpT-IPSsQUWqQcNrVJqy4LhBjPX2&index=42


import board
import busio
import time
import digitalio
from adafruit_debouncer import Button
from lcd.lcd import LCD, CursorMode
from lcd.i2c_pcf8574_interface import I2CPCF8574Interface

# Button Setup
# blue button
blue_button_input = digitalio.DigitalInOut(board.GP15)
blue_button_input.switch_to_input(pull=digitalio.Pull.UP)
blue_button = Button(blue_button_input, value_when_pressed = False)

# left button
left_button_input = digitalio.DigitalInOut(board.GP6)
left_button_input.switch_to_input(pull=digitalio.Pull.UP)
left_button = Button(left_button_input, value_when_pressed = False)

# right button
right_button_input = digitalio.DigitalInOut(board.GP7)
right_button_input.switch_to_input(pull=digitalio.Pull.UP)
right_button = Button(right_button_input, value_when_pressed = False)

# jump button
jump_button_input = digitalio.DigitalInOut(board.GP8)
jump_button_input.switch_to_input(pull=digitalio.Pull.UP)
jump_button = Button(jump_button_input, value_when_pressed = False)

# Pin definitions
# I2C used for LCD Display
i2c_scl = board.GP5
i2c_sda = board.GP4
i2c_address = 0x27 # 39 decimal

# LCD display info
cols = 20
rows = 4

# Setup LCD display
i2c = busio.I2C(scl=i2c_scl, sda=i2c_sda)
interface = I2CPCF8574Interface(i2c, i2c_address)
lcd = LCD(interface, num_rows=rows, num_cols=cols)
lcd.set_cursor_mode(CursorMode.HIDE)

# Jump Man Sprites - Custom Characters 
jump_man_jumping = bytearray([0b11111,0b10101,0b11111,0b11111,0b00100,0b00101,0b11111,0b10000])
jump_man_standing = bytearray([0b00000,0b11111,0b10101,0b11111,0b11111,0b00100,0b01110,0b11011])
jump_man_dead = bytearray([0b00000,0b01110,0b10101,0b11011,0b01110,0b01110,0b00000,0b00000])
lcd.create_char(0, jump_man_standing)
lcd.create_char(1, jump_man_jumping)
lcd.create_char(2, jump_man_dead)

# Level Sprites - Custom Characters
platform = bytearray([0b11111,0b11111,0b11111,0b11111,0b00100,0b11111,0b11111,0b11111])
heart = bytearray([0b00000,0b00000,0b01010,0b11111,0b11111,0b01110,0b00100,0b00000])
enemy = bytearray([0b00000,0b01110,0b11111,0b10101,0b11111,0b11111,0b10101,0b00000])
lcd.create_char(3, platform)
lcd.create_char(4, heart)
lcd.create_char(5, enemy)


LEVEL_SPRITES = {
    'pl': 3,
    'hr': 4,
}

LEVEL = [
    ['hr', 'hr', 'hr', None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, '*'],
    [None, None, None, None, 'pl', 'pl', 'pl', 'pl', None, 'pl', 'pl', 'pl', 'pl', 'pl', 'pl', 'pl', 'pl', 'pl', 'pl', 'pl'],
    [None, None, None, 'pl', None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]
]

LEVEL_GOAL = (0, 19)

def load_level(level):
  for i in range(0, len(level)):
      for j in range(0, len(level[i])):
          if level[i][j]:
            lcd.set_cursor_pos(i, j)
            if level[i][j] in LEVEL_SPRITES:
                sprite = LEVEL_SPRITES[level[i][j]]
                lcd.write(sprite)
            # if level[i][j] == 'pl':
            #     sprite = LEVEL_SPRITES[level[i][j]]
            #     lcd.write(sprite)
            else:
                lcd.print(level[i][j])

class GameMechanics:
    def __init__(self, type, pos, sprites):
        self.type = type  # supported types: jump_man, movable_object, enemy
        self.pos = pos
        self.sprites = sprites
        self.other_game_objects = []
        self.jumping = False
        self.time_frame_duration = 0.5  ### !!! change this to a parameter after testing is complete
        self.last_time_frame = 0

    def set_cursor(self):
        lcd.set_cursor_pos(self.pos[0], self.pos[1])
    
    def display_sprite(self, sprite):
        self.set_cursor()
        sprite_value = self.sprites[sprite]
        if isinstance(sprite_value, str):
            lcd.print(sprite_value)
        else:
            lcd.write(sprite_value)

    def delete_sprite(self):
        self.set_cursor()
        lcd.print(' ')

    def increment_time_frame(self):
        time_diff = time.monotonic() - self.last_time_frame
        if time_diff > self.time_frame_duration:
            self.last_time_frame = time.monotonic() 
            return True
        else:
            return False

    def move_right(self):
        if self.pos[1] != 19 and not self.blocked('right'):
            self.delete_sprite()
            self.pos[1] += 1
            self.display_sprite('default')

    def move_left(self):
        if self.pos[1] != 0 and not self.blocked('left'):
            self.delete_sprite()
            self.pos[1] -= 1
            self.display_sprite('default')
    
    def jump(self):
        if self.pos[0] != 0 and not self.blocked('up') and not self.jumping:
            # self.jump_started = time.monotonic()
            self.jumping = True
            self.last_time_frame = time.monotonic()

            self.delete_sprite()
            self.pos[0] -= 1
            self.display_sprite('falling')
    
    def push(self, object, direction):
        if direction == 'right':
            object.move_right()
        if direction == 'left':
            object.move_left()

    def detect_object(self, direction):
        row = self.pos[0]
        col = self.pos[1]
        if direction == 'right':
            col += 1
        if direction == 'left':
            col -= 1
        if direction == 'up':
            row -= 1
        if direction == 'down':
            row += 1
        for object in self.other_game_objects:
            if object.pos[0] == row and object.pos[1] == col:
                return object
        return None
    
    def blocked(self, direction):
        row = self.pos[0]
        col = self.pos[1]
        if direction == 'right':
            col += 1
        if direction == 'left':
            col -= 1
        if direction == 'up':
            row -= 1
        if LEVEL[row][col] and LEVEL[row][col] != '*':
            return True
        else:
            return False

    def gravity(self):
        if not self.on_floor():
            self.delete_sprite()
            self.pos[0] += 1
            self.display_sprite('falling')
        else:
            self.display_sprite('default')
        
    def on_floor(self):
        if self.pos[0] == 3:
            return True
        row = self.pos[0] + 1
        col = self.pos[1]
        if LEVEL[row][col] or self.detect_object('down'):
            return True
        else:
            return False



# JumpMan Class 
class JumpMan(GameMechanics):
    def __init__(self, type, pos, sprites):
        self.air_movement_count = 0
        self.air_movement_max = 2
        super().__init__(type, pos, sprites)
    
    def move_right(self):
        if self.air_movement_count >= self.air_movement_max and self.jumping:
            return
        object = self.detect_object('right')
        if object and object.type == 'movable_object':
            self.push(object, 'right')
        elif self.pos[1] != 19 and not self.blocked('right'):
            self.delete_sprite()
            self.pos[1] += 1
            if not self.on_floor():
                if not self.jumping:
                    self.air_movement_count = self.air_movement_max
                else:
                    self.air_movement_count += 1
                self.jumping = True
                self.display_sprite('falling')
                self.last_time_frame = time.monotonic()
            else:
                self.display_sprite('default')
        
    def move_left(self):
        if self.air_movement_count >= self.air_movement_max and self.jumping:
            return
        object = self.detect_object('left')
        if object and object.type == 'movable_object':
            self.push(object, 'left')
        elif self.pos[1] != 0 and not self.blocked('left'):
            self.delete_sprite()
            self.pos[1] -= 1
            if not self.on_floor():
                if not self.jumping:
                    self.air_movement_count = self.air_movement_max
                else:
                    self.air_movement_count += 1
                self.jumping = True
                self.display_sprite('falling')
                self.last_time_frame = time.monotonic()
            else:
                self.display_sprite('default')
    
    def detect_collision(self):
        for object in self.other_game_objects:
            if object.type == 'enemy' and object.pos == self.pos:
                print('You Died!')
                jump_man.display_sprite('dead')
                time.sleep(2)
                lcd.clear()
                lcd.print('Level Complete')
                time.sleep(3)
                lcd.clear()
                load_level(LEVEL)
                jump_man.pos = [3, 0]
                jump_man.display_sprite('default')


# Movable Object Class
class MovableObject(GameMechanics):
    def __init__(self, type, pos, sprites):
        super().__init__(type, pos, sprites)
    
    def move_right(self):
        object = self.detect_object('right')
        if object and object.type == 'enemy':
            return
        elif object and object.type == 'movable_object':
            self.push(object, 'right')
        elif self.pos[1] != 19 and not self.blocked('right'):
            self.delete_sprite()
            self.pos[1] += 1
            self.display_sprite('default')
        
    def move_left(self):
        object = self.detect_object('left')
        if object and object.type == 'enemy':
            return
        elif object and object.type == 'movable_object':
            self.push(object, 'left')
        elif self.pos[1] != 0 and not self.blocked('left'):
            self.delete_sprite()
            self.pos[1] -= 1
            self.display_sprite('default')



# Enemy Class
class Enemy(GameMechanics):
    def __init__(self, type, pos, sprites, range):
        self.range = range
        self.right_range = pos[1] + self.range
        self.left_range = pos[1] - self.range
        self.patrol_direction = 'right'
        super().__init__(type, pos, sprites)
    
    def update_pos(self):
        if self.patrol_direction == 'right':
            object = self.detect_object('right')
            if (object and object.type == 'movable_object') or self.pos[1] == 19 or self.blocked('right'):
                self.patrol_direction = 'left'
            else:
                self.move_right()
        elif self.patrol_direction == 'left':
            object = self.detect_object('left')
            if (object and object.type == 'movable_object') or self.pos[1] == 0 or self.blocked('left'):
                self.patrol_direction = 'right'
            else:
                self.move_left()
        if self.pos[1] == self.right_range:
            self.patrol_direction = 'left'
        if self.pos[1] == self.left_range:
            self.patrol_direction = 'right'
    

jump_man = JumpMan(
    'jump_man',
    [3, 0], 
    {
        'default': 0, 
        'falling': 1,
        'dead': 2
    }
)

movable_platform_0 = MovableObject(
    'movable_object',
    [3, 2],
    {
        'default': 'O', 
        'falling': 'O'
    }
)

movable_platform_1 = MovableObject(
    'movable_object',
    [0, 6],
    {
        'default': 'O', 
        'falling': 'O'
    }
)

movable_platform_2 = MovableObject(
    'movable_object',
    [3, 13],
    {
        'default': 'O', 
        'falling': 'O'
    }
)

enemy = Enemy(
    'enemy',
    [3, 16],
    {
        'default': 5, 
        'falling': 5
    },
    10
)

jump_man.other_game_objects = [
    movable_platform_0,
    movable_platform_1,
    movable_platform_2,
    enemy
]

movable_platform_0.other_game_objects = [
    jump_man,
    enemy,
    movable_platform_1,
    movable_platform_2,
]

movable_platform_1.other_game_objects = [
    jump_man,
    enemy,
    movable_platform_0,
    movable_platform_2,
]

movable_platform_2.other_game_objects = [
    jump_man,
    enemy,
    movable_platform_0,
    movable_platform_1,
]

enemy.other_game_objects = [
    jump_man,
    movable_platform_0,
    movable_platform_1,
    movable_platform_2,
]



def main():
    load_level(LEVEL)
    jump_man.display_sprite('default')
    movable_platform_0.display_sprite('default')
    movable_platform_1.display_sprite('default')
    movable_platform_2.display_sprite('default')
    enemy.display_sprite('default')
    TIME_DELAY = 0.5
    last_time = 0
    while True:
        left_button.update()
        right_button.update()
        jump_button.update()
        blue_button.update()

        if blue_button.pressed:
            print(f'{jump_man.air_movement_count =}')
            print(f'{jump_man.air_movement_max =}')
            print(f'{jump_man.jumping =}')
            print(f'{jump_man.pos =}')
            lcd.clear()
            load_level(LEVEL)
            jump_man.pos = [3, 0]
            jump_man.display_sprite('default')
            movable_platform_0.pos = [3, 2]
            movable_platform_0.display_sprite('default')
            movable_platform_1.pos = [0, 6]
            movable_platform_1.display_sprite('default')
            movable_platform_2.pos = [3, 13]
            movable_platform_2.display_sprite('default')
            enemy.display_sprite('default')


        # death check
        jump_man.detect_collision()

         # button input
        if left_button.pressed: 
            jump_man.move_left()
        if right_button.pressed: 
            jump_man.move_right()
        if jump_button.pressed: 
            jump_man.jump()
      

        # win check
        if jump_man.pos[0] == LEVEL_GOAL[0] and jump_man.pos[1] == LEVEL_GOAL[1]:
            time.sleep(0.5)
            lcd.clear()
            lcd.print('Level Complete')
            time.sleep(3)
            lcd.clear()
            load_level(LEVEL)
            jump_man.pos = [3, 0]
            jump_man.display_sprite('default')

        if jump_man.increment_time_frame():
            jump_man.gravity()

        if jump_man.on_floor():
            jump_man.jumping = False
            jump_man.air_movement_count = 0

        if enemy.increment_time_frame():
            enemy.update_pos()

        if movable_platform_0.increment_time_frame():
            movable_platform_0.gravity()
        
        if movable_platform_1.increment_time_frame():
            movable_platform_1.gravity()
        
        if movable_platform_2.increment_time_frame():
            movable_platform_2.gravity()
        

       

if __name__ == '__main__':
    main()