# --- imports ---
import random
import pygame
import math
import sys
import follow_algorithm

# --- definitions ---
pygame.init()
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Follow Human simulation")
clock = pygame.time.Clock()
burst_timer = 0
distance = follow_algorithm.distance
angle_to_steer = follow_algorithm.angle_to_steer

# Colors
BG = (30, 130, 30)
PLAYER_COLOR = (220, 40, 40)
AI_COLOR = (40, 100, 220)
DEBUG = (255, 255, 255)

# --- functions ---
class Car:
    def __init__(self, x, y, color, is_player=False):
        self.pos = [x, y]
        self.angle = 0.0  # 0 = up
        self.speed = 0.0
        self.max_speed = 4.0
        self.acceleration = 0.1
        self.friction = 0.06
        self.rotation_speed = 1.5
        self.is_player = is_player
        self.color = color
        self.surface = self._make_sprite(color)

        # For scripted car
        self.turn_timer = 0
        self.turn_dir = 1
        self.turn_speed = 3

    def _make_sprite(self, color):
        """Create a small triangle car pointing up."""
        W = H = 60
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        cx, cy = W // 2, H // 2
        pygame.draw.polygon(s, color, [(cx, 10), (cx + 15, H - 10), (cx - 15, H - 10)])
        return s

    def update(self, keys=None):
        """Update movement — player or scripted."""
        if self.is_player:
            self._update_player(keys)
        else:
            self._update_scripted()

        # Apply movement
        rad = math.radians(self.angle)
        fx, fy = math.sin(rad), -math.cos(rad)
        self.pos[0] += fx * self.speed
        self.pos[1] += fy * self.speed 

        # friction
        self.speed *= 0.99

        # Wrap around screen
        self.pos[0] %= WIDTH
        self.pos[1] %= HEIGHT

    def _update_player(self, action):
        global burst_timer

        # Acceleration
        if action["up"]:
            self.speed += self.acceleration
        if action["down"]:
            self.speed -= self.acceleration
        # limit speed
        self.speed = max(-self.max_speed, min(self.max_speed, self.speed))

        # Steering only when moving
        if abs(self.speed) > 0.1:
            if action["left"]:
                steer = -self.rotation_speed * (abs(self.speed) / self.max_speed)
                if self.speed < 0:
                    steer *= -1
                self.angle += steer
            if action["right"]:
                steer = self.rotation_speed * (abs(self.speed) / self.max_speed)
                if self.speed < 0:
                    steer *= -1
                self.angle += steer

        self.angle %= 360

        
        action = { "up": False, "down": False, "left": False, "right": False }

        if distance > 200:  
            action["up"] = True   # full speed far away
        
        elif distance > 120:
            burst_timer = (burst_timer + 1) % 20
            action["up"] = burst_timer < 10  # ON for 10 frames, OFF for 10

        else:
            # Close enough — full stop
            action = { "up": False, "down": False, "left": False, "right": False }

        return action

    def _update_scripted(self):
        """Simple AI pattern: drive forward, then turn."""

        self.turn_timer += 1

        self.speed = self.turn_speed
        if self.turn_timer % 90 == 0:
            if random.randint(0, 10) > 8:
                self.turn_speed = 0
            else:
                self.turn_speed = 3

        # Turning every 3 second logic

        if self.turn_timer % 180 == 0:  # every 3 seconds at 60fps
            self.turn_dir *= -1  # alternate direction
        self.angle += self.turn_dir * 1.1  # smooth turning
        self.angle %= 360

    def draw(self, surf, debug=False):
        rotated = pygame.transform.rotate(self.surface, -self.angle)
        rect = rotated.get_rect(center=self.pos)
        surf.blit(rotated, rect.topleft)

    def generate_action_from_pressing_keys(self):

        keys = pygame.key.get_pressed()
        action = {"up": False, "down": False, "left": False, "right": False}
        if keys[pygame.K_UP]:
            action["up"] = True
        if keys[pygame.K_DOWN]:
            action["down"] = True
        if keys[pygame.K_LEFT]:
            action["left"] = True
        if keys[pygame.K_RIGHT]:
            action["right"] = True
        return action

    def generate_action_from_self_follow(self, ai_car):
        """
        Replace with your own follow other car code
        """
        action = {"up": False, "down": False, "left": False, "right": False}
        for key in action:
            action[key] = random.choice([True, False])
        return

# --- Setup ---
player_car = Car(WIDTH // 3, HEIGHT // 2, PLAYER_COLOR, is_player=True)
ai_car = Car(2 * WIDTH // 3, HEIGHT // 2, AI_COLOR, is_player=False)
font = pygame.font.SysFont(None, 22)

# --- Main Loop ---
while True:
    # listen for quit game window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # calculate action for follow car
    # action = player_car.generate_action_from_pressing_keys()
    #action = {"up": True, "down": False, "left": False, "right": False}
    # action = player_car.generate_action_from_self_follow()
    #action = player_car.generate_action_from_pressing_keys() 
    action = follow_algorithm.calculate_car_action(player_car.angle, player_car.pos, ai_car.pos)

    #shouldI turn or not(other car postiioton)
    #shoudl I gas or revvwes(other car)
    # Update movement for both cars
    player_car.update(action)
    ai_car.update()

    # --- Draw ---
    screen.fill(BG)
    player_car.draw(screen, debug=True)
    ai_car.draw(screen, debug=True)

    info_text = f"Distance: {distance:.2f} px  Angle: {angle_to_steer:.2f} deg"
    text_surface = font.render(info_text, True, (255,255,255))
    screen.blit(text_surface, (20, 20))

    pygame.display.flip()
    
    distance = follow_algorithm.distance
    angle_to_steer = follow_algorithm.angle_to_steer

    # animation speed
    clock.tick(60)