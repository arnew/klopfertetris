# sim/tetris_sim.py
import time

class InputState:
    def __init__(self, das_frames=12, arr_frames=1):
        self.left_held = False
        self.right_held = False
        self.left_counter = 0
        self.right_counter = 0
        self.das = das_frames
        self.arr = arr_frames

    def press_left(self):
        self.left_held = True
        self.left_counter = 0

    def release_left(self):
        self.left_held = False
        self.left_counter = 0

    def press_right(self):
        self.right_held = True
        self.right_counter = 0

    def release_right(self):
        self.right_held = False
        self.right_counter = 0

class TetrisSim:
    def __init__(self, rules_engine, level=0, lock_delay=0.5):
        self.rules = rules_engine
        self.level = level
        self.lock_delay = lock_delay
        self.fall_speed = self.level_to_delay(level)
        self.lock_timer = 0.0
        self.input = InputState()
        self.last_lines = 0

    def level_to_delay(self, level):
        base = 1.0
        return max(0.03, base * (0.8 ** level))

    # input wrappers
    def move(self, dx):
        # attempt move once
        if dx < 0:
            if self.rules.fits(self.rules.x - 1, self.rules.y, self.rules.rotation):
                self.rules.x -= 1
                self.lock_timer = 0.0
        elif dx > 0:
            if self.rules.fits(self.rules.x + 1, self.rules.y, self.rules.rotation):
                self.rules.x += 1
                self.lock_timer = 0.0

    def rotate(self):
        if self.rules.try_rotate():
            self.lock_timer = 0.0

    def soft_drop(self):
        # single cell soft drop call (caller controls repeat rate)
        if self.rules.fits(self.rules.x, self.rules.y + 1, self.rules.rotation):
            self.rules.y += 1
            self.lock_timer = 0.0
            return True
        # cannot move down
        return False

    def hard_drop(self):
        while self.rules.fits(self.rules.x, self.rules.y + 1, self.rules.rotation):
            self.rules.y += 1
        # lock immediately
        self.rules.lock_piece()
        cleared = self.rules.clear_lines()
        self.lock_timer = 0.0
        self.last_lines = cleared

    def update_input_autorepeat(self):
        # left
        if self.input.left_held:
            if self.input.left_counter == 0:
                self.move(-1)
            elif self.input.left_counter > self.input.das and \
                 (self.input.left_counter - self.input.das) % self.input.arr == 0:
                self.move(-1)
            self.input.left_counter += 1
        else:
            self.input.left_counter = 0

        # right
        if self.input.right_held:
            if self.input.right_counter == 0:
                self.move(1)
            elif self.input.right_counter > self.input.das and \
                 (self.input.right_counter - self.input.das) % self.input.arr == 0:
                self.move(1)
            self.input.right_counter += 1
        else:
            self.input.right_counter = 0

    def update(self, dt, soft_hold=False):
        """
        dt: seconds since last update
        soft_hold: boolean, whether soft drop key is held (accelerates gravity)
        """
        # handle input autorepeat
        self.update_input_autorepeat()

        # gravity (soft-drop accelerates)
        delay = self.fall_speed * (0.1 if soft_hold else 1.0)
        if not hasattr(self, "_fall_acc"):
            self._fall_acc = 0.0
        self._fall_acc += dt
        if self._fall_acc >= delay:
            self._fall_acc -= delay
            if self.rules.fits(self.rules.x, self.rules.y + 1, self.rules.rotation):
                self.rules.y += 1
                self.lock_timer = 0.0
            else:
                # start/increment lock timer
                self.lock_timer += delay
                if self.lock_timer >= self.lock_delay:
                    self.rules.lock_piece()
                    cleared = self.rules.clear_lines()
                    self.last_lines = cleared
                    self.lock_timer = 0.0
