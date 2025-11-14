# input_handler.py
import pygame

class InputHandler:
    def __init__(self):
        pygame.joystick.init()
        self.joysticks = []
        for i in range(pygame.joystick.get_count()):
            j = pygame.joystick.Joystick(i)
            j.init()
            self.joysticks.append(j)

    def poll(self):
        # returns dict of actions: left/right/rotate/soft/hard/start/quit
        actions = {"left":False,"right":False,"rotate":False,"soft":False,"hard":False,"start":False,"quit":False}
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                actions["quit"] = True
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_LEFT: actions["left"]=True
                elif ev.key == pygame.K_RIGHT: actions["right"]=True
                elif ev.key == pygame.K_UP: actions["rotate"]=True
                elif ev.key == pygame.K_DOWN: actions["soft"]=True
                elif ev.key == pygame.K_SPACE: actions["hard"]=True
                elif ev.key == pygame.K_RETURN: actions["start"]=True
            elif ev.type == pygame.JOYBUTTONDOWN:
                # map some buttons generically
                if ev.button == 0: actions["rotate"]=True
                elif ev.button == 1: actions["hard"]=True
                elif ev.button == 2: actions["soft"]=True
            elif ev.type == pygame.JOYHATMOTION:
                hat = ev.value
                if hat[0] < 0: actions["left"]=True
                if hat[0] > 0: actions["right"]=True
                if hat[1] < 0: actions["soft"]=True
                if hat[1] > 0: actions["rotate"]=True
        return actions
