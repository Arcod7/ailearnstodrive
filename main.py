import pygame
import pygame as pyg
import random
import time
import numpy as np


def angle_to_direction(angle, strength=1.0):
    return np.cos(angle)*strength, -np.sin(angle)*strength


SCREEN_SIZE = (1260, 680)

# - Init pygame -
pyg.init()
pyg.mouse.set_visible(True)
screen = pyg.display.set_mode(SCREEN_SIZE)
pyg.display.set_caption("Car racing")


# - Background -
# background = pyg.transform.smoothscale(pyg.image.load('assets/background_race.png').convert_alpha(),
#                                        (SCREEN_SIZE[0], SCREEN_SIZE[1]))

background = pyg.Rect((0, 0), SCREEN_SIZE)

TRACK = pyg.transform.smoothscale(pyg.image.load('assets/track.png').convert_alpha(), SCREEN_SIZE)
TRACK_rect = TRACK.get_rect()

TRACK_BORDER = pyg.transform.smoothscale(pyg.image.load('assets/track_border.png').convert_alpha(), SCREEN_SIZE)
TRACK_BORDER_rect = TRACK_BORDER.get_rect()
TRACK_BORDER_MASK = pyg.mask.from_surface(TRACK_BORDER)

FINISH_LINE = pyg.transform.rotate(pyg.transform.smoothscale(pyg.image.load('assets/Finish-Line-Transparent-PNG.png')
                                                             .convert_alpha(), (85, 70)), 90)
FINISH_LINE_rect = FINISH_LINE.get_rect()
FINISH_LINE_rect.x, FINISH_LINE_rect.y = SCREEN_SIZE[0]/2-30, 14
FINISH_LINE_MASK = pyg.mask.from_surface(FINISH_LINE)

# Font init
pygame.font.init()
MYFONT = pygame.font.SysFont('Comic Sans MS', 30)


class Car:

    def __init__(self, spawn_pos, img, speed=0.8, friction=0.91):
        self.image = img

        # - Position -
        self.spawn_pos = (spawn_pos[0], spawn_pos[1])
        self.rect = self.image.get_rect()
        self.rect.x = self.spawn_pos[0]
        self.rect.y = self.spawn_pos[1]
        self.angle = 0
        self.angle_rad = 0

        self.pos = np.array([self.spawn_pos[0], self.spawn_pos[1]])
        self.velocity = np.array([0.0, 0.0])
        self.acceleration = np.array([0.0, 0.0])

        self.previous_pos = self.pos.copy()

        self.friction = friction
        self.speed = speed

        self.acceleration_power = 1

        self.show()

    def show(self):
        screen.blit(self.image, self.rect)

    def show_rotated(self):

        # Rotation
        rot_image = pyg.transform.rotate(self.image, self.angle)
        rot_rect = rot_image.get_rect(center=self.rect.center)

        # Show
        screen.blit(rot_image, rot_rect)


    def get_pos(self):
        return self.rect.x, self.rect.y


    def move_and_show(self, t=0.0):
        self.show_rotated()

        if self.collide(TRACK_BORDER_MASK):
            self.bounce(t)
            return
        if self.collide(FINISH_LINE_MASK, FINISH_LINE_rect.x, FINISH_LINE_rect.y):
            if self.velocity[0] < 0:
                self.bounce(t)
                return
            else:
                print('finish_line colliding')

        self.move_acceleration(t=t)


    def move_acceleration(self, t=0.0):

        # Frictions force
        self.velocity *= self.friction

        # Speed
        self.velocity = self.velocity + self.acceleration * t
        self.pos = self.pos + self.velocity * t

        self.rect.x = self.pos[0]
        self.rect.y = self.pos[1]

    def collide(self, mask, x=0.0, y=0.0):
        car_mask = pyg.mask.from_surface(self.image)
        offset = (round(self.pos[0] - x), round(self.pos[1] - y))
        return mask.overlap(car_mask, offset)

    def bounce(self, t):
        self.velocity = -1.1 * self.velocity + random.uniform(-0.2, 0.2)
        self.acceleration = self.acceleration/10
        for _ in range(2):
            self.move_acceleration(t=t)



class PlayerCar(Car):
    def __init__(self):
        super().__init__(spawn_pos=(SCREEN_SIZE[0]/2+30, 35), img=pyg.transform.smoothscale(
                         pyg.image.load('assets/player_car.png').convert_alpha(), (40, 25)), speed=0.4)

    def acceleration_from_2_keys_pressed(self, keys):
        # Acceleration according to the keys pressed in 2 directions (change only angle)

        if keys:

            # Change direction
            if not (keys[pyg.K_LEFT] and keys[pyg.K_RIGHT]):
                if keys[pyg.K_RIGHT]:
                    self.angle -= 1
                elif keys[pyg.K_LEFT]:
                    self.angle += 1

                self.angle %= 360
                self.angle_rad = np.deg2rad(self.angle)

            # Move forward
            if keys[pyg.K_UP]:
                # Acceleration thanks to angle
                self.acceleration = np.array(angle_to_direction(self.angle_rad, self.speed))

                # The longer you press, the faster you go
                self.acceleration_power += 1
                self.acceleration *= self.acceleration_power ** 0.1

                # print(self.acceleration_power, self.acceleration_power**0.1)

            # Move backward
            elif keys[pyg.K_DOWN]:
                self.acceleration = -np.array(angle_to_direction(self.angle_rad, self.speed))/2

            # Reset acceleration when not accelerating
            else:
                self.acceleration_power = 1
                self.acceleration.fill(0)

    def eyes(self, show_eyes=False):
        # Take off non assignment bug
        x, y = 0, 0

        # 0 = front ; +pi = back
        angles_to_check = (-1, 0, 1)
        for i in angles_to_check:
            x, y = angle_to_direction(self.angle_rad + i)
            while not self.collide(TRACK_BORDER_MASK, -x, -y) and (-SCREEN_SIZE[0] < x < SCREEN_SIZE[0]
                                                                   or -SCREEN_SIZE[1] < y < SCREEN_SIZE[0]):
                if show_eyes:
                    shooting_eyes = self.image.copy()
                    shooting_eyes.set_alpha(50)
                    screen.blit(shooting_eyes, (self.rect.x + x, self.rect.y + y))

                x *= 1.2
                y *= 1.2

            if show_eyes:
                acceleration = MYFONT.render(str(round((x ** 2 + y ** 2) ** 0.5)) + " pixels", False, (0, 0, 0))
                screen.blit(acceleration, (20, 50 + i * 30))

        return x, y


class ComputerCar(Car):
    def __init__(self, path=None):
        super().__init__(spawn_pos=(SCREEN_SIZE[0]/2+30, 65), img=pyg.transform.smoothscale(
                         pyg.image.load('assets/computer_car.png').convert_alpha(), (40, 25)), speed=0.6)
        if path is None:
            path = []
        self.path = path

    def draw_points(self):
        for point in self.path:
            pyg.draw.circle(screen, (250, 0, 250), point, 5)


my_car = PlayerCar()
computer = ComputerCar([(771, 76), (814, 90), (860, 102), (902, 116), (946, 132), (946, 132), (1002, 160), (1052, 186),
                        (1090, 212), (1134, 254), (1150, 296), (1157, 339), (1153, 386), (1138, 434), (1118, 468),
                        (1100, 495), (1075, 523), (1046, 541), (1009, 562), (966, 580), (898, 600), (834, 610),
                        (797, 609), (727, 615), (728, 615), (661, 616), (593, 613), (517, 607), (433, 598),
                        (348, 578), (275, 546), (191, 504), (137, 462), (110, 420), (79, 362), (61, 289),
                        (84, 210), (134, 165), (201, 133), (267, 113), (343, 96), (420, 70), (500, 67)])


clock = pyg.time.Clock()
FPS = 60
TARGET_FPS = 60
prev_time = time.time()
dt = 0


running = True
while running:
    # --- Essentials ---

    # Update screen
    pyg.display.flip()

    # --- Time and framerate ---

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

    # --- Show background ---

    # - Greenish Background -
    pyg.draw.rect(screen, (100, 200, 50), background)

    # - Track -
    screen.blit(TRACK, TRACK_rect)
    screen.blit(TRACK_BORDER, TRACK_BORDER_rect)
    screen.blit(FINISH_LINE, FINISH_LINE_rect)

    # --- Cars ---

    # - Car eye -
    my_car.eyes(show_eyes=True)

    # - Car movement -
    # Player input
    my_car.acceleration_from_2_keys_pressed(pyg.key.get_pressed())

    # Move car
    my_car.move_and_show(t=framerate_adjuster)
    #computer.move_and_show(t=framerate_adjuster)









    # --- Others ---

    # Draw points in the circuit that computer could follow
    computer.draw_points()


#print(computer.path)
pyg.quit()
