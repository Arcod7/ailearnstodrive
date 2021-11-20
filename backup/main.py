import pygame
import pygame as pyg
import random
import time
import numpy as np
from utils import sign, bilinear_interpolation


SCREEN_SIZE = (1260, 680)

# - Init pygame -
pyg.init()
pyg.mouse.set_visible(True)
screen = pyg.display.set_mode(SCREEN_SIZE)
pyg.display.set_caption("Car racing")


# - Background -
# background = pyg.transform.smoothscale(pyg.image.load('../assets/background_race.png').convert_alpha(),
#                                        (SCREEN_SIZE[0], SCREEN_SIZE[1]))

background = pyg.Rect((0, 0), SCREEN_SIZE)

TRACK = pyg.transform.smoothscale(pyg.image.load('../assets/track.png').convert_alpha(), SCREEN_SIZE)

TRACK_BORDER = pyg.transform.smoothscale(pyg.image.load('../assets/track_border.png').convert_alpha(), SCREEN_SIZE)
TRACK_BORDER_MASK = pyg.mask.from_surface(TRACK_BORDER)

FINISH_LINE = pyg.transform.rotate(pyg.transform.smoothscale(
                                   pyg.image.load('../assets/Finish-Line-Transparent-PNG.png').convert_alpha(), (85, 70))
                                   , 90)
FINISH_LINE_rect = FINISH_LINE.get_rect()
FINISH_LINE_rect.x, FINISH_LINE_rect.y = SCREEN_SIZE[0]/2-30, 14
FINISH_LINE_MASK = pyg.mask.from_surface(FINISH_LINE)


class Car:

    def __init__(self, spawn_pos, img, speed=0.8, friction=0.95):
        self.image = img

        # - Position -
        self.spawn_pos = (spawn_pos[0], spawn_pos[1])
        self.rect = self.image.get_rect()
        self.rect.x = self.spawn_pos[0]  # on change la position du monstre dans le rect
        self.rect.y = self.spawn_pos[1]
        self.angle = 0

        self.pos = np.array([self.spawn_pos[0], self.spawn_pos[1]])
        self.velocity = np.array([0.0, 0.0])
        self.acceleration = np.array([0.0, 0.0])

        self.previous_pos = self.pos.copy()

        self.friction = friction
        self.speed = speed

        self.show()

    def show(self):
        screen.blit(self.image, self.rect)

    def show_wacceleration(self):
        # Angle
        velocity_x = self.velocity[0]
        velocity_y = self.velocity[1]

        if velocity_x == velocity_y:
            if velocity_x == 0:
                velocity_x, velocity_y = 0, 0
            else:
                velocity_x, velocity_y = sign(velocity_x), sign(velocity_y)
        elif abs(velocity_x) > abs(velocity_y):
            velocity_y = velocity_y / abs(velocity_x)
            velocity_x = sign(velocity_x)
        else:
            velocity_x = velocity_x / abs(velocity_y)
            velocity_y = sign(velocity_y)

        if velocity_y > 0:
            self.angle = bilinear_interpolation(velocity_x, velocity_y, [(1, 1, -45), (-1, 1, -135),
                                                                         (1, 0, 0), (-1, 0, -180)])
        elif velocity_y < 0:
            self.angle = bilinear_interpolation(velocity_x, velocity_y, [(1, 0, 0), (-1, 0, 180),
                                                                         (1, -1, 45), (-1, -1, 135)])
        # Rotation
        rot_image = pyg.transform.rotate(self.image, self.angle)
        rot_rect = rot_image.get_rect(center=self.rect.center)

        # Show
        screen.blit(rot_image, rot_rect)


    def get_pos(self):
        return self.rect.x, self.rect.y


    def move_and_show(self, wacceleration=False, t=0.0):
        self.show_wacceleration()

        if self.collide(TRACK_BORDER_MASK):
            self.bounce(t)
            return
        if self.collide(FINISH_LINE_MASK, FINISH_LINE_rect.x, FINISH_LINE_rect.y):
            if self.velocity[0] < 0:
                self.bounce(t)
                return
            else:
                print('finish_line colliding')

        if wacceleration:
            self.move_acceleration(t=t)
        else:
            self.move_simple(pyg.key.get_pressed())
            self.show()


    def move_simple(self, keys):
        speed = 4
        if keys[pyg.K_UP] and keys[pyg.K_DOWN]:
            pass
        else:
            if keys[pyg.K_UP]:
                self.pos[1] -= speed
            elif keys[pyg.K_DOWN]:
                self.pos[1] += speed
        if keys[pyg.K_LEFT] and keys[pyg.K_RIGHT]:
            pass
        else:
            if keys[pyg.K_RIGHT]:
                self.pos[0] += speed
            elif keys[pyg.K_LEFT]:
                self.pos[0] -= speed

        self.rect.x = self.pos[0]
        self.rect.y = self.pos[1]


    def move_acceleration(self, t=0.0):

        # Frictions force
        self.velocity *= self.friction

        # Speed
        self.velocity = self.velocity + self.acceleration * t
        self.pos = self.pos + self.velocity * t

        self.rect.x = self.pos[0]
        self.rect.y = self.pos[1]

    def collide(self, mask, x=0, y=0):
        car_mask = pyg.mask.from_surface(self.image)
        offset = (int(self.pos[0] - x), int(self.pos[1] - y))
        return mask.overlap(car_mask, offset)

    def bounce(self, t):
        self.velocity = -1.0 * self.velocity + random.uniform(-0.2, 0.2)
        self.acceleration = self.acceleration/10
        for _ in range(2):
            self.move_acceleration(t=t)




class PlayerCar(Car):
    def __init__(self):
        super().__init__(spawn_pos=(SCREEN_SIZE[0]/2+30, 35), img=pyg.transform.smoothscale(
                         pyg.image.load('../assets/player_car.png').convert_alpha(), (40, 25)), speed=0.6)


    def acceleration_from_keys_pressed(self, keys):
        # Acceleration according to the keys pressed
        x, y = 0.0, 0.0
        if keys:
            if not (keys[pyg.K_UP] and keys[pyg.K_DOWN]):
                if keys[pyg.K_UP]:
                    y = -self.speed
                elif keys[pyg.K_DOWN]:
                    y = self.speed
            if not (keys[pyg.K_LEFT] and keys[pyg.K_RIGHT]):
                if keys[pyg.K_RIGHT]:
                    x = self.speed
                elif keys[pyg.K_LEFT]:
                    x = -self.speed
        self.acceleration = np.array([x, y])


class ComputerCar(Car):
    def __init__(self, path=[]):
        super().__init__(spawn_pos=(SCREEN_SIZE[0]/2+30, 65), img=pyg.transform.smoothscale(
                         pyg.image.load('../assets/computer_car.png').convert_alpha(), (40, 25)), speed=0.6)
        self.path = path

    def draw_points(self):
        for point in self.path:
            pyg.draw.circle(screen, (250, 0, 250), point, 5)


my_car = PlayerCar()
computer = ComputerCar([(771, 76), (814, 90), (860, 102), (902, 116), (946, 132), (946, 132), (1002, 160), (1052, 186), (1090, 212), (1134, 254), (1150, 296), (1157, 339), (1153, 386), (1138, 434), (1118, 468), (1100, 495), (1075, 523), (1046, 541), (1009, 562), (966, 580), (898, 600), (834, 610), (797, 609), (727, 615), (728, 615), (661, 616), (593, 613), (517, 607), (433, 598), (348, 578), (275, 546), (191, 504), (137, 462), (110, 420), (79, 362), (61, 289), (84, 210), (134, 165), (201, 133), (267, 113), (343, 96), (420, 70), (500, 67)])
car_moving = False

clock = pyg.time.Clock()
FPS = 60
TARGET_FPS = 60
prev_time = time.time()
dt = 0


running = True
while running:

    # Limit framerate
    clock.tick(FPS)
    # Compute delta time
    now = time.time()
    dt = now - prev_time
    prev_time = now

    framerate_adjuster = dt * TARGET_FPS

    # --- Events ---
    for event in pyg.event.get():

        # - Quit -
        if event.type == pyg.QUIT:
            running = False
            break

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pyg.mouse.get_pos()
            computer.path.append(pos)

    # Draw points
    computer.draw_points()

    # - Car movement -

    # Player input
    my_car.acceleration_from_keys_pressed(pyg.key.get_pressed())

    # Move car
    my_car.move_and_show(wacceleration=True, t=framerate_adjuster)
    computer.move_and_show(wacceleration=True, t=framerate_adjuster)


    # Show car
    # my_car.show()

    # Update screen
    pyg.display.flip()

    # - Background -
    pyg.draw.rect(screen, (100, 200, 50), background)
    # screen.blit(background, background.get_rect())

    # - Track -
    screen.blit(TRACK, TRACK.get_rect())
    screen.blit(TRACK_BORDER, TRACK_BORDER.get_rect())
    screen.blit(FINISH_LINE, FINISH_LINE_rect)

print(computer.path)
pyg.quit()
