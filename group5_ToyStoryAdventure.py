from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import sys


# Game state
game_state = "menu"  # "menu", "level_select", "fade", "playing", "game_over"
fade_alpha = 0
fade_timer = 0
selected_level = 1  # Which level player chose (1, 2, or 3)
current_level = 1  # Currently playing level

# Level display
show_level_text = True
level_text_timer = 0
level_text_duration = 600  # 10 seconds at 60 FPS

# Level-specific configurations
level_configs = {
    1: {
        'total_rooms': 7,  # 6 regular rooms (0-5) + 1 boss room (6)
        'wall_color': (0.3, 0.5, 0.8),  # Blue walls
        'floor_color': (0.4, 0.4, 0.4),  # Gray floor
        'enemy_color': (0.2, 0.8, 0.2),  # Green army men
        'enemy_name': 'green_army',
        'boss_name': 'potato_head',
        'rescue_character': 'jessie',
        'special_powers_enabled': False,  # No Jessie/Buzz powers
        'enemy_min': 5,
        'enemy_max': 10
    },
    2: {
        'total_rooms': 10,  # 9 regular rooms (0-8) + 1 boss room (9)
        'wall_color': (0.2, 0.7, 0.3),  # Green walls
        'floor_color': (0.4, 0.4, 0.4),  # Gray floor
        'enemy_color': (0.9, 0.2, 0.2),  # Red monkeys
        'enemy_name': 'red_monkey',
        'boss_name': 'lotso',
        'rescue_character': 'buzz',
        'special_powers_enabled': 'jessie_only',  # Only Jessie power, no Buzz
        'enemy_min': 5,
        'enemy_max': 15
    },
    3: {
        'total_rooms': 15,
        'wall_color': (0.4, 0.4, 0.4),
        'floor_color': (0.3, 0.3, 0.3),
        'enemy_color': (0.6, 0.6, 0.65),
        'enemy_name': 'benson',
        'boss_name': 'gabby',
        'rescue_character': 'bo_peep',
        'special_powers_enabled': True,
        'enemy_min': 5,
        'enemy_max': 20
    }
}

# Game over state
game_over_timer = 0
woody_fade_alpha = 1.0  # 1.0 (visible) to 0.0 (invisible)
show_game_over_text = False

# Room system
current_room = 0
total_rooms = 7  # Will be updated based on level
room_width = 600
room_length = 600

# Collectibles - stars and hats
# Generate which rooms have items (stars: 80%, hats: 50-60%)
random.seed(42)  # Fixed seed for consistent generation
rooms_with_stars = set()
rooms_with_hats = set()

# Coin and score system (initialize before use)
woody_score = 0
room_coins = {}  # Dictionary mapping room number to list of coin positions
collected_coins = set()  # Set of (room, coin_index) tuples

# Bensons enemy system (initialize before use)
room_bensons = {}  # Dictionary mapping room number to list of benson data: [x, y, active, hit_cooldown]
benson_hit_by_lasso = set()  # Track which bensons have been hit (room, benson_index)
benson_speed = 0.2  # Very slow movement toward Woody
bensons_frozen = False  # When Jessie power is active, Bensons freeze

# Jessie special power system
jessie_power_active = False
jessie_animation_stage = 0  # 0=inactive, 1=descending, 2=landed, 3=disappearing
jessie_y_position = 0  # Y position during descent
jessie_power_cooldown = 0  # Frames until power can be used again
jessie_power_cooldown_max = 3600  # 1 minute at 60 FPS
jessie_animation_timer = 0

# Buzz Lightyear special power system
buzz_power_active = False
buzz_animation_stage = 0  # 0=inactive, 1=descending, 2=landed, 3=shooting_ray, 4=disappearing
buzz_y_position = 0  # Y position during descent
buzz_power_cooldown = 0  # Frames until power can be used again
buzz_power_cooldown_max = 7200  # 2 minutes at 60 FPS
buzz_animation_timer = 0
buzz_ray_alpha = 0.0  # Red ray transparency (0.0 to 1.0)

# Star and hat positions per room
room_star_positions = {}  # Dictionary mapping room number to (x, y) position
room_hat_positions = {}  # Dictionary mapping room number to (x, y) position

for room in range(total_rooms - 1):  # Not in boss room
    if random.random() < 0.8:  # 80% chance for star
        rooms_with_stars.add(room)
        # Generate random position for star
        star_x = random.uniform(-200, 200)
        star_y = random.uniform(-200, 200)
        room_star_positions[room] = (star_x, star_y)
    
    if random.random() < 0.55:  # 55% chance for hat
        rooms_with_hats.add(room)
        # Generate random position for hat
        hat_x = random.uniform(-200, 200)
        hat_y = random.uniform(-200, 200)
        room_hat_positions[room] = (hat_x, hat_y)

# Generate coins for each room (8-12 coins per room, very common)
for room in range(total_rooms - 1):  # Not in boss room
    num_coins = random.randint(8, 12)
    coin_positions = []
    for _ in range(num_coins):
        # Random positions spread throughout the room
        coin_x = random.uniform(-220, 220)
        coin_y = random.uniform(-220, 220)
        coin_positions.append((coin_x, coin_y))
    room_coins[room] = coin_positions

# Generate Bensons for each room (progressively increasing from 5 to 20)
for room in range(1, total_rooms - 1):  # Start from room 1, not in boss room or first room
    # Room 1 (index 1): 5 Bensons
    # Progressively increase to 20 by room 13 (index 13)
    if room == 1:
        num_bensons = 5
    else:
        # Linear scaling from 5 to 20 over rooms 2-13
        # room 2: ~6, room 3: ~8, ..., room 13: 20
        num_bensons = min(20, 5 + int((room - 1) * 1.25))
    
    benson_list = []
    for _ in range(num_bensons):
        # Random positions spread throughout the room
        benson_x = random.uniform(-220, 220)
        benson_y = random.uniform(-220, 220)
        benson_list.append([benson_x, benson_y, True, 0])  # x, y, active, hit_cooldown
    room_bensons[room] = benson_list

# Track collected items
collected_stars = set()
collected_hats = set()


def initialize_level(level):
    """Initialize game data for a specific level"""
    global total_rooms, current_room, room_bensons, room_coins, room_star_positions, room_hat_positions
    global collected_stars, collected_hats, collected_coins, benson_hit_by_lasso
    global woody_x, woody_y, woody_z, woody_angle, woody_health, woody_lives
    global boss_room_entered, gabby_visible, bo_peep_visible, gabby_hit
    global win_sequence_stage, show_level_text, level_text_timer, current_level
    global rooms_with_stars, rooms_with_hats
    
    current_level = level
    config = level_configs[level]
    total_rooms = config['total_rooms']
    current_room = 0
    
    # Reset Woody position to center, behind furniture
    woody_x = 0
    woody_y = 100  # Slightly back from center
    woody_z = 0
    woody_angle = 270
    woody_health = 100
    # Lives carry over between levels
    
    # Show level text
    show_level_text = True
    level_text_timer = 0
    
    # Reset boss room state
    boss_room_entered = False
    gabby_visible = False
    bo_peep_visible = False
    gabby_hit = False
    win_sequence_stage = 0
    
    # Clear collected items
    collected_stars = set()
    collected_hats = set()
    collected_coins = set()
    benson_hit_by_lasso = set()
    
    # Regenerate level-specific content
    room_coins = {}
    room_star_positions = {}
    room_hat_positions = {}
    room_bensons = {}
    rooms_with_stars = set()
    rooms_with_hats = set()
    
    random.seed(42 + level * 100)  # Different seed per level
    
    # Generate stars and hats
    for room in range(total_rooms - 1):  # Not in boss room
        if random.random() < 0.8:  # 80% chance for star
            star_x = random.uniform(-200, 200)
            star_y = random.uniform(-200, 200)
            room_star_positions[room] = (star_x, star_y)
            rooms_with_stars.add(room)
        
        if random.random() < 0.55:  # 55% chance for hat
            hat_x = random.uniform(-200, 200)
            hat_y = random.uniform(-200, 200)
            room_hat_positions[room] = (hat_x, hat_y)
            rooms_with_hats.add(room)
    
    # Generate coins
    for room in range(total_rooms - 1):
        num_coins = random.randint(8, 12)
        coin_positions = []
        for _ in range(num_coins):
            coin_x = random.uniform(-220, 220)
            coin_y = random.uniform(-220, 220)
            coin_positions.append((coin_x, coin_y))
        room_coins[room] = coin_positions
    
    # Generate enemies
    enemy_min = config['enemy_min']
    enemy_max = config['enemy_max']
    
    for room in range(1, total_rooms - 1):  # Start from room 1, not in boss room
        if level == 1:
            # Level 1: 5-10 enemies per room
            num_enemies = random.randint(enemy_min, enemy_max)
        else:
            # Level 2/3: Progressive scaling
            if room == 1:
                num_enemies = enemy_min
            else:
                num_enemies = min(enemy_max, enemy_min + int((room - 1) * 1.25))
        
        enemy_list = []
        for _ in range(num_enemies):
            enemy_x = random.uniform(-220, 220)
            # Don't spawn enemies too close to entry point (y > 150)
            enemy_y = random.uniform(-220, 150)
            enemy_list.append([enemy_x, enemy_y, True, 0])
        room_bensons[room] = enemy_list


# Track collected items
collected_stars = set()
collected_hats = set()

# Animation timer for floating items
item_animation_time = 0

# Boss room state
boss_room_entered = False
gabby_visible = False
bo_peep_visible = False
gabby_hit = False
bo_peep_approaching = False
bo_peep_x = 0
bo_peep_y = -200
game_won = False

# Gabby Gabby boss properties
gabby_x = 0
gabby_y = -150
gabby_health = 50  # Takes 50 lasso hits to defeat
gabby_move_speed = 0.15  # Slower movement
gabby_move_timer = 0
gabby_move_direction = 0  # Random movement direction

# Gabby's attack system
cup_projectiles = []  # List of active cups: [(x, y, dx, dy, lifetime), ...]
gabby_cup_attack_timer = 0
gabby_cup_attack_cooldown = 300  # 5 seconds at 60 FPS

gabby_stick_attack_timer = 0
gabby_stick_attack_cooldown = 240  # 4 seconds at 60 FPS
gabby_proximity_timer = 0  # Time Woody has been close
gabby_is_close = False
gabby_attacking_with_stick = False
stick_attack_duration = 20  # Frames for stick animation

# Attack ranges
gabby_close_range = 60  # Distance considered "close" for stick attack
gabby_far_range = 80  # Distance to start throwing cups

# Win sequence states
win_sequence_stage = 0  # 0=normal, 1=camera_turning, 2=cage_fading, 3=bo_approaching, 4=hugging, 5=mission_complete, 6=game_end
win_sequence_timer = 0
cage_alpha = 1.0  # For fade out
camera_target_angle = 0  # Camera rotation target
show_mission_complete = False
show_game_end = False

# Woody properties
woody_x = 0
woody_y = 100  # Start slightly behind center to avoid central furniture
woody_z = 0
woody_angle = 270  # Face towards front door (270 = facing -Y direction)
woody_jump_velocity = 0
woody_is_jumping = False
woody_on_ground = True

# Health and lives
woody_health = 100  # Health percentage (0-100)
woody_lives = 3  # Number of lives

# Health and lives
woody_health = 100  # Health percentage (0-100)
woody_lives = 3  # Number of lives

# Health and lives
woody_health = 100  # Health percentage (0-100)
woody_lives = 3  # Number of lives

# Lasso attack
lasso_attacking = False
lasso_attack_timer = 0
lasso_attack_duration = 20  # frames
lasso_damage_cooldown = 0  # Cooldown to prevent multiple hits per attack

# Camera
camera_distance = 100
camera_height = 50

# Movement
move_speed = 0.5  # Reduced from 0.8
rotation_speed = 0.3  # Reduced from 0.5
gravity = 0.5
jump_strength = 8

# Furniture collision boxes for each room layout (x, y, width, height)
# These represent rectangular collision areas for furniture
furniture_obstacles = {
    0: [],  # Will be populated based on room_pattern % 5
}

# Input states
keys_pressed = {
    'up': False,
    'down': False,
    'left': False,
    'right': False,
    'space': False,
    'a': False
}


def get_furniture_obstacles(room_pattern):
    """Get furniture collision boxes for a room layout"""
    obstacles = []
    
    if room_pattern == 0:  # Layout 1
        # Showcases on back wall
        for x_pos in [-200, -80, 80, 200]:
            obstacles.append((x_pos, 250, 40, 40))
        # Side tables
        for y_pos in [-150, 0, 150]:
            obstacles.append((-250, y_pos, 40, 40))
            obstacles.append((250, y_pos, 40, 40))
        # Central table with chairs
        obstacles.append((0, 0, 50, 50))
        for x, y in [(-40, -40), (40, -40), (-40, 40), (40, 40)]:
            obstacles.append((x, y, 25, 25))
    
    elif room_pattern == 1:  # Layout 2
        # Corner showcases
        for x, y in [(-240, -240), (240, -240), (-240, 240), (240, 240)]:
            obstacles.append((x, y, 40, 40))
        # Tables in center
        for x, y in [(-100, 100), (100, 100), (-100, -100), (100, -100)]:
            obstacles.append((x, y, 50, 50))
            obstacles.append((x - 30, y, 25, 25))
    
    elif room_pattern == 2:  # Layout 3
        # Tables along walls
        for y_pos in [-200, -80, 80, 200]:
            obstacles.append((-240, y_pos, 40, 40))
            obstacles.append((240, y_pos, 40, 40))
        # Central pedestal
        obstacles.append((0, 0, 60, 60))
    
    elif room_pattern == 3:  # Layout 4
        # Side tables
        for x_pos in [-200, 0, 200]:
            obstacles.append((x_pos, -230, 40, 40))
            obstacles.append((x_pos, 230, 40, 40))
        # Center tables
        for x, y in [(-100, 0), (100, 0)]:
            obstacles.append((x, y, 50, 50))
    
    elif room_pattern == 4:  # Layout 5
        # Diagonal showcases
        for x, y in [(-180, -180), (180, -180), (-180, 180), (180, 180)]:
            obstacles.append((x, y, 40, 40))
        # Center arrangement
        obstacles.append((0, 0, 50, 50))
        for x, y in [(-60, 0), (60, 0), (0, -60), (0, 60)]:
            obstacles.append((x, y, 30, 30))
    
    return obstacles


def check_collision_with_furniture(x, y, radius, obstacles):
    """Check if a circular entity collides with any rectangular obstacle"""
    for ox, oy, width, height in obstacles:
        # Find closest point on rectangle to circle center
        closest_x = max(ox - width/2, min(x, ox + width/2))
        closest_y = max(oy - height/2, min(y, oy + height/2))
        
        # Calculate distance
        dx = x - closest_x
        dy = y - closest_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < radius:
            return True
    return False


def draw_text(text, x, y, font=GLUT_BITMAP_HELVETICA_18):
    """Draw 2D text on screen"""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_star(x, y, animation_offset):
    """Draw an animated floating star"""
    glPushMatrix()
    
    # Floating animation - move up and down slowly
    float_height = 40 + 8 * math.sin(animation_offset * 0.5)  # Slower float
    glTranslatef(x, y, float_height)
    
    # Gentle rotation animation
    glRotatef(animation_offset * 15, 0, 0, 1)  # Slower rotation
    
    # Draw 5-pointed star using GL_TRIANGLES
    glColor3f(1.0, 0.85, 0.0)  # Gold color
    
    # Star parameters
    outer_radius = 8
    inner_radius = 3
    
    # Draw front face of star
    glBegin(GL_TRIANGLES)
    for i in range(5):
        # Outer point angle
        angle1 = i * 72 - 90  # Start from top
        angle2 = angle1 + 36   # Inner point
        angle3 = angle1 + 72   # Next outer point
        
        # Calculate vertices
        x1 = outer_radius * math.cos(math.radians(angle1))
        y1 = outer_radius * math.sin(math.radians(angle1))
        
        x2 = inner_radius * math.cos(math.radians(angle2))
        y2 = inner_radius * math.sin(math.radians(angle2))
        
        x3 = inner_radius * math.cos(math.radians(angle2 + 36))
        y3 = inner_radius * math.sin(math.radians(angle2 + 36))
        
        # Triangle from center to outer point
        glVertex3f(0, 0, 1)
        glVertex3f(x1, y1, 1)
        glVertex3f(x2, y2, 1)
        
        # Triangle connecting inner points
        glVertex3f(0, 0, 1)
        glVertex3f(x2, y2, 1)
        glVertex3f(x3, y3, 1)
    glEnd()
    
    # Draw back face
    glBegin(GL_TRIANGLES)
    for i in range(5):
        angle1 = i * 72 - 90
        angle2 = angle1 + 36
        angle3 = angle1 + 72
        
        x1 = outer_radius * math.cos(math.radians(angle1))
        y1 = outer_radius * math.sin(math.radians(angle1))
        
        x2 = inner_radius * math.cos(math.radians(angle2))
        y2 = inner_radius * math.sin(math.radians(angle2))
        
        x3 = inner_radius * math.cos(math.radians(angle2 + 36))
        y3 = inner_radius * math.sin(math.radians(angle2 + 36))
        
        glVertex3f(0, 0, -1)
        glVertex3f(x2, y2, -1)
        glVertex3f(x1, y1, -1)
        
        glVertex3f(0, 0, -1)
        glVertex3f(x3, y3, -1)
        glVertex3f(x2, y2, -1)
    glEnd()
    
    # Add thickness with sides
    glColor3f(0.9, 0.75, 0.0)  # Slightly darker for depth
    glBegin(GL_QUADS)
    for i in range(5):
        angle1 = i * 72 - 90
        angle2 = angle1 + 36
        
        x1 = outer_radius * math.cos(math.radians(angle1))
        y1 = outer_radius * math.sin(math.radians(angle1))
        
        x2 = inner_radius * math.cos(math.radians(angle2))
        y2 = inner_radius * math.sin(math.radians(angle2))
        
        # Outer edge
        glVertex3f(x1, y1, 1)
        glVertex3f(x1, y1, -1)
        glVertex3f(x2, y2, -1)
        glVertex3f(x2, y2, 1)
    glEnd()
    
    glPopMatrix()


def draw_hat_collectible(x, y, animation_offset):
    """Draw an animated floating hat (cowboy hat like Woody's)"""
    glPushMatrix()
    
    # Floating animation - move up and down slowly
    float_height = 35 + 8 * math.sin(animation_offset * 0.5 + 1)  # Slower float
    glTranslatef(x, y, float_height)
    
    # Gentle rotation
    glRotatef(animation_offset * 12, 0, 0, 1)  # Slower rotation
    
    # Draw miniature cowboy hat
    glColor3f(0.6, 0.4, 0.2)  # Brown
    
    # Hat base (brim)
    glPushMatrix()
    glScalef(2.5, 2.5, 0.3)
    glutSolidCube(4)
    glPopMatrix()
    
    # Hat top (crown)
    glPushMatrix()
    glTranslatef(0, 0, 3)
    glScalef(1.2, 1.2, 1.5)
    glutSolidCube(4)
    glPopMatrix()
    
    glPopMatrix()


def draw_coin(x, y, animation_offset):
    """Draw an animated floating coin"""
    glPushMatrix()
    
    # Floating animation - move up and down slowly
    float_height = 25 + 6 * math.sin(animation_offset * 0.5 + 2)  # Slower float, lower height
    glTranslatef(x, y, float_height)
    
    # Spinning rotation around Z axis for coin flip effect
    glRotatef(animation_offset * 20, 0, 0, 1)  # Spin animation
    
    # Tilt slightly for 3D effect
    glRotatef(15, 1, 0, 0)
    
    # Yellow/gold color
    glColor3f(1.0, 0.84, 0.0)  # Gold
    
    # Draw coin as a flat cylinder (torus looks like coin)
    glPushMatrix()
    glRotatef(90, 1, 0, 0)  # Rotate to make it horizontal
    glutSolidTorus(0.3, 4, 8, 20)  # Inner radius, outer radius, sides, rings
    glPopMatrix()
    
    # Add a center sphere for thickness
    glColor3f(0.9, 0.75, 0.0)  # Slightly darker center
    glutSolidSphere(3, 12, 12)
    
    glPopMatrix()


def draw_benson(x, y):
    """Draw a Benson enemy character"""
    glPushMatrix()
    glTranslatef(x, y, 0)
    
    # Get level-specific enemy color
    enemy_color = level_configs[current_level]['enemy_color']
    
    # Body (level-specific color)
    glColor3f(*enemy_color)
    glPushMatrix()
    glTranslatef(0, 0, 8)
    glScalef(0.8, 0.6, 1.0)
    glutSolidCube(8)
    glPopMatrix()
    
    # Head (slightly lighter)
    r, g, b = enemy_color
    glColor3f(min(r + 0.1, 1.0), min(g + 0.1, 1.0), min(b + 0.1, 1.0))
    glPushMatrix()
    glTranslatef(0, 0, 14)
    glutSolidSphere(3, 8, 8)
    glPopMatrix()
    
    # Arms
    glColor3f(*enemy_color)
    for x_offset in [-4, 4]:
        glPushMatrix()
        glTranslatef(x_offset, 0, 8)
        glScalef(0.3, 0.3, 0.8)
        glutSolidCube(5)
        glPopMatrix()
    
    # Legs (slightly darker)
    glColor3f(max(r - 0.05, 0.0), max(g - 0.05, 0.0), max(b - 0.05, 0.0))
    for x_offset in [-2, 2]:
        glPushMatrix()
        glTranslatef(x_offset, 0, 3)
        glScalef(0.3, 0.3, 0.8)
        glutSolidCube(5)
        glPopMatrix()
    
    glPopMatrix()


def draw_jessie(x, y, z):
    """Draw Jessie character for special power"""
    glPushMatrix()
    glTranslatef(x, y, z)
    
    # Body (red shirt with white)
    glColor3f(0.9, 0.1, 0.1)  # Red
    glPushMatrix()
    glTranslatef(0, 0, 10)
    glScalef(1.0, 0.7, 1.3)
    glutSolidCube(7)
    glPopMatrix()
    
    # Head (skin color)
    glColor3f(0.95, 0.8, 0.7)  # Skin tone
    glPushMatrix()
    glTranslatef(0, 0, 18)
    glutSolidSphere(4, 10, 10)
    glPopMatrix()
    
    # Red hair (ponytail)
    glColor3f(0.8, 0.15, 0.1)  # Dark red
    glPushMatrix()
    glTranslatef(0, 0, 20)
    glScalef(1, 1, 0.7)
    glutSolidSphere(4.2, 10, 10)
    glPopMatrix()
    
    # Cowgirl hat (yellow)
    glColor3f(0.9, 0.8, 0.2)  # Yellow
    glPushMatrix()
    glTranslatef(0, 0, 23)
    glScalef(1.2, 1.2, 0.4)
    glutSolidCube(5)
    glPopMatrix()
    
    # Arms
    glColor3f(0.9, 0.1, 0.1)
    for x_offset in [-5, 5]:
        glPushMatrix()
        glTranslatef(x_offset, 0, 10)
        glScalef(0.4, 0.4, 1.2)
        glutSolidCube(5)
        glPopMatrix()
    
    # Legs (blue jeans)
    glColor3f(0.2, 0.3, 0.6)  # Blue
    for x_offset in [-2.5, 2.5]:
        glPushMatrix()
        glTranslatef(x_offset, 0, 4)
        glScalef(0.4, 0.4, 1.2)
        glutSolidCube(6)
        glPopMatrix()
    
    glPopMatrix()


def draw_buzz(x, y, z):
    """Draw Buzz Lightyear character for special power"""
    glPushMatrix()
    glTranslatef(x, y, z)
    
    # Body (white and green space suit)
    # White chest
    glColor3f(0.95, 0.95, 0.95)  # White
    glPushMatrix()
    glTranslatef(0, 0, 10)
    glScalef(1.1, 0.8, 1.3)
    glutSolidCube(7)
    glPopMatrix()
    
    # Green accents on sides
    glColor3f(0.2, 0.8, 0.3)  # Bright green
    for x_offset in [-4, 4]:
        glPushMatrix()
        glTranslatef(x_offset, 0, 10)
        glScalef(0.3, 0.7, 1.2)
        glutSolidCube(7)
        glPopMatrix()
    
    # Purple accents
    glColor3f(0.5, 0.2, 0.7)  # Purple
    glPushMatrix()
    glTranslatef(0, 0, 7)
    glScalef(1.0, 0.6, 0.3)
    glutSolidCube(7)
    glPopMatrix()
    
    # Head (skin color with space helmet)
    glColor3f(0.95, 0.8, 0.7)  # Skin tone
    glPushMatrix()
    glTranslatef(0, 0, 18)
    glutSolidSphere(4, 10, 10)
    glPopMatrix()
    
    # Space helmet (transparent purple tint)
    glColor3f(0.7, 0.5, 0.8)  # Light purple
    glPushMatrix()
    glTranslatef(0, 0, 18)
    glutSolidSphere(4.5, 10, 10)
    glPopMatrix()
    
    # Purple hood/helmet top
    glColor3f(0.4, 0.2, 0.6)  # Dark purple
    glPushMatrix()
    glTranslatef(0, 0, 21)
    glScalef(1.1, 1.1, 0.5)
    glutSolidCube(5)
    glPopMatrix()
    
    # Arms (white with green)
    glColor3f(0.95, 0.95, 0.95)
    for x_offset in [-5, 5]:
        glPushMatrix()
        glTranslatef(x_offset, 0, 10)
        glScalef(0.4, 0.4, 1.2)
        glutSolidCube(5)
        glPopMatrix()
    
    # Legs (white with green)
    glColor3f(0.95, 0.95, 0.95)  # White
    for x_offset in [-2.5, 2.5]:
        glPushMatrix()
        glTranslatef(x_offset, 0, 4)
        glScalef(0.4, 0.4, 1.2)
        glutSolidCube(6)
        glPopMatrix()
    
    # Green leg accents
    glColor3f(0.2, 0.8, 0.3)
    for x_offset in [-2.5, 2.5]:
        glPushMatrix()
        glTranslatef(x_offset, 0, 2)
        glScalef(0.5, 0.5, 0.4)
        glutSolidCube(6)
        glPopMatrix()
    
    glPopMatrix()


def draw_red_ray(x, y, z, alpha):
    """Draw red ray shooting upward to roof"""
    if alpha <= 0:
        return
    
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Main red beam
    glColor4f(1.0, 0.0, 0.0, alpha)  # Red with transparency
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(90, 1, 0, 0)  # Point upward
    quad = gluNewQuadric()
    gluCylinder(quad, 5, 8, 200, 20, 20)  # Wide beam going up
    gluDeleteQuadric(quad)
    glPopMatrix()
    
    # Outer glow
    glColor4f(1.0, 0.3, 0.3, alpha * 0.3)  # Light red glow
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(90, 1, 0, 0)
    quad = gluNewQuadric()
    gluCylinder(quad, 8, 12, 200, 20, 20)
    gluDeleteQuadric(quad)
    glPopMatrix()
    
    glDisable(GL_BLEND)


def draw_health_and_lives():
    """Draw health meter and lives in top-left corner"""
    # Switch to 2D orthographic projection
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Draw lives text
    glColor3f(1, 1, 1)  # White
    glRasterPos2f(20, 760)
    life_text = f"Life = {woody_lives}"
    for ch in life_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
    # Health meter dimensions
    meter_x = 20
    meter_y = 680
    meter_width = 150  # Keep width same
    meter_height = 60  # Original height
    
    # Draw green container/border
    glColor3f(0, 0.6, 0)  # Dark green
    glLineWidth(3)
    glBegin(GL_LINE_LOOP)
    glVertex2f(meter_x, meter_y)
    glVertex2f(meter_x + meter_width, meter_y)
    glVertex2f(meter_x + meter_width, meter_y + meter_height)
    glVertex2f(meter_x, meter_y + meter_height)
    glEnd()
    
    # Calculate health fill height
    fill_height = (woody_health / 100.0) * meter_height
    
    # Draw health fill (gradient from yellow at bottom to red at top based on health)
    if woody_health > 0:
        # Bottom part is always yellow (healthy)
        # Top part transitions to red as health decreases
        health_ratio = woody_health / 100.0
        
        # Color changes from yellow (healthy) to red (low health)
        if health_ratio > 0.5:
            # Mostly healthy - yellow to orange
            r = 1.0
            g = 0.8
            b = 0.0
        elif health_ratio > 0.25:
            # Medium health - orange
            r = 1.0
            g = 0.5
            b = 0.0
        else:
            # Low health - red
            r = 1.0
            g = 0.0
            b = 0.0
        
        glColor3f(r, g, b)
        glBegin(GL_QUADS)
        glVertex2f(meter_x + 2, meter_y + 2)
        glVertex2f(meter_x + meter_width - 2, meter_y + 2)
        glVertex2f(meter_x + meter_width - 2, meter_y + fill_height - 2)
        glVertex2f(meter_x + 2, meter_y + fill_height - 2)
        glEnd()
    
    # Draw "HEALTH" label
    glColor3f(1, 1, 1)
    glRasterPos2f(meter_x + 50, meter_y + 25)
    health_label = "HEALTH"
    for ch in health_label:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_woody():
    """Draw Woody character"""
    global lasso_attacking, lasso_attack_timer, woody_fade_alpha
    
    glPushMatrix()
    
    # Position Woody
    glTranslatef(woody_x, woody_y, woody_z)
    glRotatef(woody_angle, 0, 0, 1)  # Rotate Woody
    
    # Body (brown/yellow cowboy vest)
    glColor4f(0.8, 0.6, 0.2, woody_fade_alpha)  # Yellow/tan color with alpha
    glPushMatrix()
    glTranslatef(0, 0, 10)
    glScalef(1.0, 0.7, 1.3)
    glutSolidCube(7)
    glPopMatrix()
    
    # Head (skin color)
    glColor4f(0.95, 0.8, 0.7, woody_fade_alpha)  # Skin tone with alpha
    glPushMatrix()
    glTranslatef(0, 0, 18)
    glutSolidSphere(4, 10, 10)
    glPopMatrix()
    
    # Brown hair
    glColor4f(0.3, 0.2, 0.1, woody_fade_alpha)  # Dark brown with alpha
    glPushMatrix()
    glTranslatef(0, 0, 20)
    glScalef(1, 1, 0.7)
    glutSolidSphere(4.2, 10, 10)
    glPopMatrix()
    
    # Cowboy hat (brown)
    glColor4f(0.4, 0.25, 0.15, woody_fade_alpha)  # Brown with alpha
    glPushMatrix()
    glTranslatef(0, 0, 22)
    # Hat crown (cube top)
    glutSolidCube(5)
    glPopMatrix()
    
    # Arms
    glColor4f(0.8, 0.6, 0.2, woody_fade_alpha)
    # Left arm
    glPushMatrix()
    glTranslatef(-5, 0, 8)
    glScalef(0.4, 0.4, 1.0)
    glutSolidCube(4)
    glPopMatrix()
    
    # Right arm (holding lasso)
    glPushMatrix()
    glTranslatef(5, 0, 8)
    glScalef(0.4, 0.4, 1.0)
    glutSolidCube(4)
    glPopMatrix()
    
    # Legs (blue jeans)
    glColor4f(0.2, 0.3, 0.6, woody_fade_alpha)  # Blue with alpha
    # Left leg
    glPushMatrix()
    glTranslatef(-2, 0, 2)
    glScalef(0.4, 0.4, 1.2)
    glutSolidCube(4)
    glPopMatrix()
    
    # Right leg
    glPushMatrix()
    glTranslatef(2, 0, 2)
    glScalef(0.4, 0.4, 1.2)
    glutSolidCube(4)
    glPopMatrix()
    
    # Lasso (coiled on right hand)
    glColor4f(0.7, 0.5, 0.2, woody_fade_alpha)  # Rope color with alpha
    
    if lasso_attacking and lasso_attack_timer < lasso_attack_duration:
        # Lasso extended forward during attack
        glPushMatrix()
        glTranslatef(5, 10 + lasso_attack_timer * 0.5, 8)
        glRotatef(90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), 0.6, 0.6, 15, 8, 8)
        # Lasso loop
        glTranslatef(0, 0, 15)
        glutSolidTorus(0.6, 2.5, 8, 10)
        glPopMatrix()
    else:
        # Coiled lasso on hand
        glPushMatrix()
        glTranslatef(5, 0, 8)
        glutSolidTorus(0.5, 1.5, 8, 10)
        glPopMatrix()
    
    glPopMatrix()


def draw_gabby_gabby(x, y):
    """Draw Gabby Gabby character"""
    glPushMatrix()
    glTranslatef(x, y, 0)
    
    # Body (orange dress) - larger
    glColor3f(1.0, 0.5, 0.0)  # Orange
    glPushMatrix()
    glTranslatef(0, 0, 15)
    glScalef(1.2, 1.0, 1.5)
    glutSolidCube(12)  # Increased from 8 to 12
    glPopMatrix()
    
    # Head (porcelain skin) - larger
    glColor3f(0.98, 0.9, 0.85)
    glPushMatrix()
    glTranslatef(0, 0, 28)  # Adjusted Z for larger body
    glutSolidSphere(6, 10, 10)  # Increased from 4.5 to 6
    glPopMatrix()
    
    # Hair covering head - brown female hairstyle
    glColor3f(0.35, 0.2, 0.1)  # Brown
    glPushMatrix()
    glTranslatef(0, 0, 30)  # On top of head
    glScalef(1.1, 1.1, 0.9)  # Slightly flattened on top
    glutSolidSphere(6.3, 10, 10)  # Covers the head
    glPopMatrix()
    
    # Brown ponytail - cylinder extending backward
    glColor3f(0.35, 0.2, 0.1)  # Brown
    glPushMatrix()
    glTranslatef(0, 5, 30)  # Position behind head
    glRotatef(90, 1, 0, 0)  # Rotate to point backward
    quad = gluNewQuadric()
    gluCylinder(quad, 1.5, 0.8, 8, 10, 10)  # Tapered ponytail
    gluDeleteQuadric(quad)
    glPopMatrix()
    
    # Hair base/bun at back of head
    glColor3f(0.35, 0.2, 0.1)
    glPushMatrix()
    glTranslatef(0, 3, 30)
    glutSolidSphere(2.5, 10, 10)
    glPopMatrix()
    
    # Arms - larger
    glColor3f(1.0, 0.5, 0.0)  # Orange dress color
    glPushMatrix()
    glTranslatef(-8, 0, 13)
    glScalef(0.4, 0.4, 1.2)
    glutSolidCube(7)  # Increased from 5 to 7
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(8, 0, 13)
    glScalef(0.4, 0.4, 1.2)
    glutSolidCube(7)
    glPopMatrix()
    
    # Legs - larger
    glColor3f(0.9, 0.4, 0.0)  # Slightly darker orange
    glPushMatrix()
    glTranslatef(-3.5, 0, 4)
    glScalef(0.4, 0.4, 1.3)
    glutSolidCube(7)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(3.5, 0, 4)
    glScalef(0.4, 0.4, 1.3)
    glutSolidCube(7)
    glPopMatrix()
    
    glPopMatrix()


def draw_lotso(x, y):
    """Draw Lotso bear character"""
    glPushMatrix()
    glTranslatef(x, y, 0)
    
    # Body (pink/magenta bear body) - larger
    glColor3f(0.9, 0.4, 0.6)  # Pink/magenta
    glPushMatrix()
    glTranslatef(0, 0, 15)
    glScalef(1.3, 1.1, 1.6)
    glutSolidSphere(8, 12, 12)  # Round bear body
    glPopMatrix()
    
    # Head (pink bear head) - larger
    glColor3f(0.95, 0.45, 0.65)  # Lighter pink
    glPushMatrix()
    glTranslatef(0, 0, 28)  # On top of body
    glutSolidSphere(6, 12, 12)
    glPopMatrix()
    
    # Ears (round)
    glColor3f(0.9, 0.4, 0.6)
    glPushMatrix()
    glTranslatef(-5, 0, 32)
    glutSolidSphere(2.5, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(5, 0, 32)
    glutSolidSphere(2.5, 10, 10)
    glPopMatrix()
    
    # Snout (lighter)
    glColor3f(0.98, 0.7, 0.8)
    glPushMatrix()
    glTranslatef(0, -5, 26)
    glutSolidSphere(3, 10, 10)
    glPopMatrix()
    
    # Nose (dark purple/brown)
    glColor3f(0.4, 0.2, 0.3)
    glPushMatrix()
    glTranslatef(0, -7, 26)
    glutSolidSphere(1.5, 8, 8)
    glPopMatrix()
    
    # Eyes (dark)
    glColor3f(0.2, 0.1, 0.1)
    glPushMatrix()
    glTranslatef(-3, -5, 29)
    glutSolidSphere(1, 8, 8)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(3, -5, 29)
    glutSolidSphere(1, 8, 8)
    glPopMatrix()
    
    # Arms (pink)
    glColor3f(0.9, 0.4, 0.6)
    glPushMatrix()
    glTranslatef(-10, 0, 16)
    glScalef(0.5, 0.5, 1.3)
    glutSolidCube(6)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(10, 0, 16)
    glScalef(0.5, 0.5, 1.3)
    glutSolidCube(6)
    glPopMatrix()
    
    # Legs (pink)
    glColor3f(0.85, 0.35, 0.55)
    glPushMatrix()
    glTranslatef(-4, 0, 5)
    glScalef(0.6, 0.6, 1.2)
    glutSolidCube(6)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(4, 0, 5)
    glScalef(0.6, 0.6, 1.2)
    glutSolidCube(6)
    glPopMatrix()
    
    glPopMatrix()


def draw_potato_head(x, y):
    """Draw Mr. Potato Head character"""
    glPushMatrix()
    glTranslatef(x, y, 0)
    
    # Body (brown potato oval)
    glColor3f(0.65, 0.45, 0.3)  # Brown potato color
    glPushMatrix()
    glTranslatef(0, 0, 18)
    glScalef(1.3, 1.0, 1.6)
    glutSolidSphere(10, 12, 12)  # Oval potato body
    glPopMatrix()
    
    # Eyes (white with black pupils)
    glColor3f(1.0, 1.0, 1.0)
    glPushMatrix()
    glTranslatef(-4, -7, 26)
    glutSolidSphere(2, 8, 8)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(4, -7, 26)
    glutSolidSphere(2, 8, 8)
    glPopMatrix()
    
    # Pupils
    glColor3f(0.0, 0.0, 0.0)
    glPushMatrix()
    glTranslatef(-4, -8, 26)
    glutSolidSphere(1, 8, 8)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(4, -8, 26)
    glutSolidSphere(1, 8, 8)
    glPopMatrix()
    
    # Red nose (big)
    glColor3f(0.9, 0.2, 0.2)
    glPushMatrix()
    glTranslatef(0, -9, 24)
    glutSolidSphere(2.5, 10, 10)
    glPopMatrix()
    
    # Mustache (brown)
    glColor3f(0.3, 0.2, 0.1)
    glPushMatrix()
    glTranslatef(-4, -10, 22)
    glScalef(2.5, 0.3, 0.3)
    glutSolidCube(3)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(4, -10, 22)
    glScalef(2.5, 0.3, 0.3)
    glutSolidCube(3)
    glPopMatrix()
    
    # Hat (brown derby)
    glColor3f(0.4, 0.25, 0.15)
    glPushMatrix()
    glTranslatef(0, 0, 32)
    glRotatef(90, 1, 0, 0)
    quad = gluNewQuadric()
    gluCylinder(quad, 6, 4, 5, 12, 12)
    gluDeleteQuadric(quad)
    glPopMatrix()
    
    # Hat brim
    glPushMatrix()
    glTranslatef(0, 0, 32)
    glRotatef(90, 1, 0, 0)
    quad = gluNewQuadric()
    gluDisk(quad, 4, 8, 16, 1)
    gluDeleteQuadric(quad)
    glPopMatrix()
    
    # Arms (detachable)
    glColor3f(0.65, 0.45, 0.3)
    glPushMatrix()
    glTranslatef(-12, 0, 16)
    glRotatef(45, 0, 1, 0)
    glScalef(0.5, 0.5, 1.5)
    glutSolidCube(5)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(12, 0, 16)
    glRotatef(-45, 0, 1, 0)
    glScalef(0.5, 0.5, 1.5)
    glutSolidCube(5)
    glPopMatrix()
    
    # Legs (shoes)
    glColor3f(0.2, 0.2, 0.8)  # Blue shoes
    glPushMatrix()
    glTranslatef(-5, 0, 4)
    glScalef(0.6, 1.2, 0.5)
    glutSolidCube(6)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(5, 0, 4)
    glScalef(0.6, 1.2, 0.5)
    glutSolidCube(6)
    glPopMatrix()
    
    glPopMatrix()


def draw_bo_peep(x, y):
    """Draw Bo Peep character"""
    glPushMatrix()
    glTranslatef(x, y, 0)
    
    # Body (pink dress)
    glColor3f(0.95, 0.6, 0.7)  # Pink
    glPushMatrix()
    glTranslatef(0, 0, 12)
    glScalef(1.3, 1.0, 1.5)
    glutSolidCube(8)
    glPopMatrix()
    
    # Head (porcelain)
    glColor3f(0.98, 0.9, 0.85)
    glPushMatrix()
    glTranslatef(0, 0, 22)
    glutSolidSphere(4, 10, 10)
    glPopMatrix()
    
    # Blonde hair
    glColor3f(0.9, 0.8, 0.5)  # Blonde
    glPushMatrix()
    glTranslatef(0, 0, 24)
    glScalef(1, 1, 0.7)
    glutSolidSphere(4.3, 10, 10)
    glPopMatrix()
    
    # Pink bonnet
    glColor3f(0.95, 0.7, 0.8)
    glPushMatrix()
    glTranslatef(0, 0, 26)
    glScalef(1.2, 0.8, 0.5)
    glutSolidCube(6)
    glPopMatrix()
    
    # Arms
    glColor3f(0.95, 0.6, 0.7)
    glPushMatrix()
    glTranslatef(-6, 0, 10)
    glScalef(0.4, 0.4, 1.2)
    glutSolidCube(5)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(6, 0, 10)
    glScalef(0.4, 0.4, 1.2)
    glutSolidCube(5)
    glPopMatrix()
    
    glPopMatrix()


def draw_buzz_caged(x, y):
    """Draw Buzz Lightyear character in cage"""
    glPushMatrix()
    glTranslatef(x, y, 0)
    
    # Body (green spacesuit)
    glColor3f(0.2, 0.7, 0.3)  # Green
    glPushMatrix()
    glTranslatef(0, 0, 12)
    glScalef(1.2, 0.9, 1.4)
    glutSolidCube(8)
    glPopMatrix()
    
    # Chest area (white/light)
    glColor3f(0.9, 0.9, 0.95)
    glPushMatrix()
    glTranslatef(0, -3, 14)
    glScalef(0.9, 0.4, 1.0)
    glutSolidCube(6)
    glPopMatrix()
    
    # Head (skin tone with helmet)
    glColor3f(0.95, 0.85, 0.75)
    glPushMatrix()
    glTranslatef(0, 0, 22)
    glutSolidSphere(3.5, 10, 10)
    glPopMatrix()
    
    # Purple helmet dome (transparent purple)
    glColor3f(0.5, 0.3, 0.7)  # Purple
    glPushMatrix()
    glTranslatef(0, 0, 23)
    glutSolidSphere(4, 10, 10)
    glPopMatrix()
    
    # Purple arms
    glColor3f(0.5, 0.3, 0.7)  # Purple
    glPushMatrix()
    glTranslatef(-6, 0, 11)
    glScalef(0.5, 0.5, 1.2)
    glutSolidCube(5)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(6, 0, 11)
    glScalef(0.5, 0.5, 1.2)
    glutSolidCube(5)
    glPopMatrix()
    
    # White/green legs
    glColor3f(0.9, 0.9, 0.95)  # White
    glPushMatrix()
    glTranslatef(-3, 0, 4)
    glScalef(0.6, 0.6, 1.3)
    glutSolidCube(6)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(3, 0, 4)
    glScalef(0.6, 0.6, 1.3)
    glutSolidCube(6)
    glPopMatrix()
    
    # Wings (red buttons on back - simplified)
    glColor3f(0.8, 0.1, 0.1)  # Red
    glPushMatrix()
    glTranslatef(-4, 2, 14)
    glutSolidSphere(1.5, 8, 8)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(4, 2, 14)
    glutSolidSphere(1.5, 8, 8)
    glPopMatrix()
    
    glPopMatrix()


def draw_jessie_caged(x, y):
    """Draw Jessie character in cage"""
    glPushMatrix()
    glTranslatef(x, y, 0)
    
    # Body (red shirt)
    glColor3f(0.9, 0.15, 0.15)  # Red
    glPushMatrix()
    glTranslatef(0, 0, 12)
    glScalef(1.0, 0.8, 1.3)
    glutSolidCube(8)
    glPopMatrix()
    
    # Head (skin tone)
    glColor3f(0.98, 0.8, 0.7)
    glPushMatrix()
    glTranslatef(0, 0, 22)
    glutSolidSphere(4, 10, 10)
    glPopMatrix()
    
    # Red hair (long braided)
    glColor3f(0.8, 0.2, 0.1)  # Red hair
    glPushMatrix()
    glTranslatef(0, 0, 24)
    glScalef(1.0, 1.0, 0.8)
    glutSolidSphere(4.3, 10, 10)
    glPopMatrix()
    
    # Braid hanging down
    glColor3f(0.8, 0.2, 0.1)
    glPushMatrix()
    glTranslatef(0, 4, 20)
    glRotatef(90, 1, 0, 0)
    quad = gluNewQuadric()
    gluCylinder(quad, 1.2, 0.8, 10, 8, 8)
    gluDeleteQuadric(quad)
    glPopMatrix()
    
    # Yellow cowboy hat
    glColor3f(0.95, 0.85, 0.3)  # Yellow
    glPushMatrix()
    glTranslatef(0, 0, 27)
    glRotatef(90, 1, 0, 0)
    quad = gluNewQuadric()
    gluCylinder(quad, 5, 3, 3, 12, 12)
    gluDeleteQuadric(quad)
    glPopMatrix()
    
    # Hat brim
    glPushMatrix()
    glTranslatef(0, 0, 27)
    glRotatef(90, 1, 0, 0)
    quad = gluNewQuadric()
    gluDisk(quad, 3, 7, 16, 1)
    gluDeleteQuadric(quad)
    glPopMatrix()
    
    # Blue jeans (legs)
    glColor3f(0.2, 0.3, 0.7)  # Blue jeans
    glPushMatrix()
    glTranslatef(-2.5, 0, 5)
    glScalef(0.5, 0.5, 1.2)
    glutSolidCube(6)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(2.5, 0, 5)
    glScalef(0.5, 0.5, 1.2)
    glutSolidCube(6)
    glPopMatrix()
    
    # Arms
    glColor3f(0.9, 0.15, 0.15)  # Red shirt
    glPushMatrix()
    glTranslatef(-5, 0, 10)
    glScalef(0.4, 0.4, 1.1)
    glutSolidCube(5)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(5, 0, 10)
    glScalef(0.4, 0.4, 1.1)
    glutSolidCube(5)
    glPopMatrix()
    
    glPopMatrix()


def draw_cup_projectile(x, y):
    """Draw a cup projectile"""
    glPushMatrix()
    glTranslatef(x, y, 15)  # Float at head height
    
    # Cup body (cylinder)
    glColor3f(0.9, 0.9, 0.95)  # White/light gray
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    quad = gluNewQuadric()
    gluCylinder(quad, 3, 2.5, 6, 10, 10)  # Cup shape
    gluDeleteQuadric(quad)
    glPopMatrix()
    
    # Cup bottom
    glPushMatrix()
    glTranslatef(0, 0, 0)
    glutSolidSphere(2.5, 8, 8)
    glPopMatrix()
    
    # Cup handle
    glColor3f(0.85, 0.85, 0.9)
    glPushMatrix()
    glTranslatef(3, 0, 3)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(0.5, 1.5, 8, 12)
    glPopMatrix()
    
    glPopMatrix()


def draw_blue_ball_projectile(x, y):
    """Draw a blue ball projectile for Mr. Potato Head"""
    glPushMatrix()
    glTranslatef(x, y, 15)  # Float at head height
    
    # Blue ball
    glColor3f(0.2, 0.4, 0.9)  # Blue
    glutSolidSphere(4, 12, 12)
    
    glPopMatrix()


def draw_red_ball_projectile(x, y):
    """Draw a red ball projectile for Lotso bear"""
    glPushMatrix()
    glTranslatef(x, y, 15)  # Float at head height
    
    # Red ball
    glColor3f(0.9, 0.2, 0.2)  # Red
    glutSolidSphere(4, 12, 12)
    
    glPopMatrix()


def draw_stick_attack(x, y, angle):
    """Draw Gabby's stick for melee attack"""
    glPushMatrix()
    glTranslatef(x, y, 15)
    glRotatef(angle, 0, 0, 1)  # Point toward Woody
    
    # Stick/rod
    glColor3f(0.4, 0.25, 0.1)  # Dark brown
    glPushMatrix()
    glTranslatef(15, 0, 0)  # Extend from Gabby
    glRotatef(90, 0, 1, 0)
    quad = gluNewQuadric()
    gluCylinder(quad, 0.8, 0.8, 25, 8, 8)  # Long stick
    gluDeleteQuadric(quad)
    glPopMatrix()
    
    glPopMatrix()


def draw_cage(x, y):
    """Draw cubic cage for Bo Peep"""
    cage_size = 35
    glColor3f(0.3, 0.3, 0.3)  # Dark gray
    
    glPushMatrix()
    glTranslatef(x, y, cage_size / 2)
    
    # Cage bars (vertical)
    for i in range(-1, 2):
        for j in range(-1, 2):
            if i != 0 or j != 0:
                glPushMatrix()
                glTranslatef(i * 12, j * 12, 0)
                glScalef(0.2, 0.2, 2)
                glutSolidCube(cage_size / 2)
                glPopMatrix()
    
    # Top and bottom frames
    for z in [0, cage_size]:
        glPushMatrix()
        glTranslatef(0, 0, z - cage_size / 2)
        glScalef(2, 2, 0.1)
        glutWireCube(cage_size / 2)
        glPopMatrix()
    
    glPopMatrix()


def draw_cage_with_alpha(x, y, alpha):
    """Draw cubic cage with transparency"""
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    cage_size = 35
    glColor4f(0.3, 0.3, 0.3, alpha)  # Dark gray with alpha
    
    glPushMatrix()
    glTranslatef(x, y, cage_size / 2)
    
    # Cage bars (vertical)
    for i in range(-1, 2):
        for j in range(-1, 2):
            if i != 0 or j != 0:
                glPushMatrix()
                glTranslatef(i * 12, j * 12, 0)
                glScalef(0.2, 0.2, 2)
                glutSolidCube(cage_size / 2)
                glPopMatrix()
    
    # Top and bottom frames
    for z in [0, cage_size]:
        glPushMatrix()
        glTranslatef(0, 0, z - cage_size / 2)
        glScalef(2, 2, 0.1)
        glutWireCube(cage_size / 2)
        glPopMatrix()
    
    glPopMatrix()
    glDisable(GL_BLEND)


def draw_museum_room():
    """Draw the current museum room with furniture"""
    # Get level-specific colors
    floor_color = level_configs[current_level]['floor_color']
    wall_color = level_configs[current_level]['wall_color']
    
    # Floor (level-specific color)
    glColor3f(*floor_color)
    glBegin(GL_QUADS)
    glVertex3f(-300, -300, 0)
    glVertex3f(300, -300, 0)
    glVertex3f(300, 300, 0)
    glVertex3f(-300, 300, 0)
    glEnd()
    
    # Walls (level-specific color)
    glColor3f(*wall_color)
    
    # Back wall
    glBegin(GL_QUADS)
    glVertex3f(-300, 300, 0)
    glVertex3f(300, 300, 0)
    glVertex3f(300, 300, 200)
    glVertex3f(-300, 300, 200)
    glEnd()
    
    # Left wall
    glBegin(GL_QUADS)
    glVertex3f(-300, -300, 0)
    glVertex3f(-300, 300, 0)
    glVertex3f(-300, 300, 200)
    glVertex3f(-300, -300, 200)
    glEnd()
    
    # Right wall
    glBegin(GL_QUADS)
    glVertex3f(300, -300, 0)
    glVertex3f(300, 300, 0)
    glVertex3f(300, 300, 200)
    glVertex3f(300, -300, 200)
    glEnd()
    
    # Doors - Create openings in walls
    door_width = 100  # Match the transition area width
    door_height = 50
    
    # Last room - no back door, door closes when entered
    if current_room == total_rooms - 1:
        # No doors in final boss room
        pass
    else:
        if current_room > 0:  # Not first room - door at back
            # Draw door frame at back wall
            glColor3f(0.4, 0.3, 0.2)
            # Left frame
            glBegin(GL_QUADS)
            glVertex3f(-door_width, 298, 0)
            glVertex3f(-door_width + 5, 298, 0)
            glVertex3f(-door_width + 5, 298, door_height)
            glVertex3f(-door_width, 298, door_height)
            glEnd()
            # Right frame
            glBegin(GL_QUADS)
            glVertex3f(door_width - 5, 298, 0)
            glVertex3f(door_width, 298, 0)
            glVertex3f(door_width, 298, door_height)
            glVertex3f(door_width - 5, 298, door_height)
            glEnd()
        
        if current_room < total_rooms - 1:  # Not last room - door at front
            # Draw door frame at front wall (player enters from here)
            glColor3f(0.4, 0.3, 0.2)
            # Left frame
            glBegin(GL_QUADS)
            glVertex3f(-door_width, -298, 0)
            glVertex3f(-door_width + 5, -298, 0)
            glVertex3f(-door_width + 5, -298, door_height)
            glVertex3f(-door_width, -298, door_height)
            glEnd()
            # Right frame
            glBegin(GL_QUADS)
            glVertex3f(door_width - 5, -298, 0)
            glVertex3f(door_width, -298, 0)
            glVertex3f(door_width, -298, door_height)
            glVertex3f(door_width - 5, -298, door_height)
            glEnd()
    
    # Draw furniture based on room layout patterns
    room_pattern = current_room % 5  # 5 different patterns
    
    # Boss room - special layout
    if current_room == total_rooms - 1:
        # Empty room for boss fight
        # Draw Boss and Rescued Character if boss encounter has started
        if boss_room_entered:
            if gabby_visible:
                # Draw level-specific boss
                boss_name = level_configs[current_level]['boss_name']
                if boss_name == 'potato_head':
                    draw_potato_head(gabby_x, gabby_y)
                elif boss_name == 'lotso':
                    draw_lotso(gabby_x, gabby_y)
                else:
                    draw_gabby_gabby(gabby_x, gabby_y)  # Gabby at her moving position
                
                # Draw stick attack if active
                if gabby_attacking_with_stick:
                    angle_to_woody = math.degrees(math.atan2(woody_y - gabby_y, woody_x - gabby_x))
                    draw_stick_attack(gabby_x, gabby_y, angle_to_woody)
            
            # Draw projectiles (level-specific)
            boss_name = level_configs[current_level]['boss_name']
            for cup in cup_projectiles:
                if boss_name == 'potato_head':
                    draw_blue_ball_projectile(cup[0], cup[1])
                elif boss_name == 'lotso':
                    draw_red_ball_projectile(cup[0], cup[1])
                else:
                    draw_cup_projectile(cup[0], cup[1])
            
            if bo_peep_visible:
                # Get level-specific rescued character
                rescue_character = level_configs[current_level]['rescue_character']
                
                # Draw cage with fade effect during win sequence
                if win_sequence_stage == 1 or (win_sequence_stage == 2 and cage_alpha > 0):
                    # Cage still visible during camera turn and fade
                    draw_cage_with_alpha(0, -200, cage_alpha)
                    if rescue_character == 'jessie':
                        draw_jessie_caged(0, -200)
                    elif rescue_character == 'buzz':
                        draw_buzz_caged(0, -200)
                    else:
                        draw_bo_peep(0, -200)  # Bo Peep inside cage
                elif win_sequence_stage == 0 and not gabby_hit:
                    # Normal state - cage fully visible
                    draw_cage(0, -200)
                    if rescue_character == 'jessie':
                        draw_jessie_caged(0, -200)
                    elif rescue_character == 'buzz':
                        draw_buzz_caged(0, -200)
                    else:
                        draw_bo_peep(0, -200)
                elif win_sequence_stage >= 3:
                    # Character is free - draw at animated position
                    if rescue_character == 'jessie':
                        draw_jessie(bo_peep_x, bo_peep_y, 0)  # Use draw_jessie without cage
                    elif rescue_character == 'buzz':
                        draw_buzz(bo_peep_x, bo_peep_y, 0)  # Use draw_buzz without cage
                    else:
                        draw_bo_peep(bo_peep_x, bo_peep_y)
    elif room_pattern == 0:
        draw_room_layout_1()
    elif room_pattern == 1:
        draw_room_layout_2()
    elif room_pattern == 2:
        draw_room_layout_3()
    elif room_pattern == 3:
        draw_room_layout_4()
    else:
        draw_room_layout_5()
    
    # Draw collectibles (stars and hats)
    if current_room < total_rooms - 1:  # Not in boss room
        # Draw star if this room has one and it hasn't been collected
        if current_room in rooms_with_stars and current_room not in collected_stars:
            star_x, star_y = room_star_positions[current_room]
            draw_star(star_x, star_y, item_animation_time)
        
        # Draw hat if this room has one and it hasn't been collected
        if current_room in rooms_with_hats and current_room not in collected_hats:
            hat_x, hat_y = room_hat_positions[current_room]
            draw_hat_collectible(hat_x, hat_y, item_animation_time)
        
        # Draw coins for this room
        if current_room in room_coins:
            for coin_index, (coin_x, coin_y) in enumerate(room_coins[current_room]):
                if (current_room, coin_index) not in collected_coins:
                    draw_coin(coin_x, coin_y, item_animation_time + coin_index * 0.5)
        
        # Draw Bensons for this room
        if current_room in room_bensons:
            for benson_index, benson in enumerate(room_bensons[current_room]):
                if benson[2]:  # If active (not defeated)
                    draw_benson(benson[0], benson[1])
        
        # Draw Jessie if power is active
        if jessie_power_active and jessie_animation_stage > 0:
            draw_jessie(woody_x, woody_y, jessie_y_position)
        
        # Draw Buzz if power is active
        if buzz_power_active and buzz_animation_stage > 0:
            draw_buzz(woody_x, woody_y, buzz_y_position)
            
            # Draw red ray when shooting
            if buzz_animation_stage >= 3 and buzz_ray_alpha > 0:
                draw_red_ray(woody_x, woody_y, buzz_y_position + 18, buzz_ray_alpha)
    
    # Room number display for debugging
    glColor3f(0.8, 0.8, 0.8)


def draw_room_layout_1():
    """Layout with showcases along walls"""
    # Showcases on back wall
    for x_pos in [-200, -80, 80, 200]:
        glColor3f(0.4, 0.3, 0.25)
        glPushMatrix()
        glTranslatef(x_pos, 250, 0)
        glScalef(0.8, 0.8, 2)
        glutSolidCube(20)
        glPopMatrix()
        glColor3f(0.6, 0.7, 0.8)
        glPushMatrix()
        glTranslatef(x_pos, 250, 25)
        glScalef(0.7, 0.7, 1.5)
        glutSolidCube(18)
        glPopMatrix()
    
    # Side tables on left and right
    for y_pos in [-150, 0, 150]:
        # Left side
        draw_table(-250, y_pos)
        # Right side
        draw_table(250, y_pos)
    
    # Central table with chairs
    draw_table(0, 0)
    for x, y in [(-40, -40), (40, -40), (-40, 40), (40, 40)]:
        draw_chair(x, y)
    
    # Wall pictures
    draw_wall_picture(-150, 295, 80)
    draw_wall_picture(150, 295, 80)
    draw_wall_picture(-295, 100, 80, True)
    draw_wall_picture(295, -100, 80, True)
    
    # Windows on left wall
    draw_window(-295, -200, 100)
    draw_window(-295, 0, 100)


def draw_room_layout_2():
    """Layout with corner showcases and center arrangement"""
    # Corner showcases
    positions = [(-240, -240), (240, -240), (-240, 240), (240, 240)]
    for x, y in positions:
        glColor3f(0.4, 0.3, 0.25)
        glPushMatrix()
        glTranslatef(x, y, 0)
        glScalef(0.8, 0.8, 2)
        glutSolidCube(20)
        glPopMatrix()
        glColor3f(0.6, 0.7, 0.8)
        glPushMatrix()
        glTranslatef(x, y, 25)
        glScalef(0.7, 0.7, 1.5)
        glutSolidCube(18)
        glPopMatrix()
    
    # Tables and chairs in center area
    for x, y in [(-100, 100), (100, 100), (-100, -100), (100, -100)]:
        draw_table(x, y)
        draw_chair(x - 30, y)
        draw_chair(x + 30, y)
    
    # Wall decorations
    draw_wall_picture(0, 295, 90)
    draw_wall_picture(-295, 0, 90, True)
    draw_wall_picture(295, 0, 90, True)
    
    # Windows
    draw_window(295, 150, 120)
    draw_window(-295, 150, 120)


def draw_room_layout_3():
    """Layout with pedestals and scattered furniture"""
    # Tall pedestals
    positions = [(-200, 200), (200, 200), (-200, -200), (200, -200), (0, 150)]
    for x, y in positions:
        glColor3f(0.35, 0.3, 0.3)
        glPushMatrix()
        glTranslatef(x, y, 0)
        glScalef(0.6, 0.6, 3)
        glutSolidCube(15)
        glPopMatrix()
    
    # Showcase line along back wall
    for x_pos in [-150, 0, 150]:
        glColor3f(0.4, 0.3, 0.25)
        glPushMatrix()
        glTranslatef(x_pos, 260, 0)
        glScalef(1, 0.8, 1.8)
        glutSolidCube(20)
        glPopMatrix()
        glColor3f(0.6, 0.7, 0.8)
        glPushMatrix()
        glTranslatef(x_pos, 260, 22)
        glScalef(0.9, 0.7, 1.4)
        glutSolidCube(18)
        glPopMatrix()
    
    # Tables
    draw_table(-120, 0)
    draw_table(120, 0)
    draw_table(0, -150)
    
    # Chairs scattered
    for x, y in [(-180, 80), (180, 80), (-80, -100), (80, -100), (0, 50)]:
        draw_chair(x, y)
    
    # Pictures
    for x in [-200, -80, 80, 200]:
        draw_wall_picture(x, 295, 70)
    
    # Windows
    draw_window(-295, -150, 100)
    draw_window(295, -150, 100)


def draw_room_layout_4():
    """Layout with symmetrical arrangement"""
    # Showcases in alcove style
    for x in [-220, -100, 100, 220]:
        glColor3f(0.4, 0.3, 0.25)
        glPushMatrix()
        glTranslatef(x, 270, 0)
        glScalef(0.7, 0.6, 2)
        glutSolidCube(20)
        glPopMatrix()
        glColor3f(0.6, 0.7, 0.8)
        glPushMatrix()
        glTranslatef(x, 270, 25)
        glScalef(0.6, 0.5, 1.5)
        glutSolidCube(18)
        glPopMatrix()
    
    # Tables in rows
    for y in [150, 50, -50, -150]:
        draw_table(-150, y)
        draw_table(150, y)
        if y != -150:
            draw_table(0, y + 25)
    
    # Chairs around tables
    for x, y in [(-180, 150), (-120, 150), (120, 50), (180, 50), (-150, -150), (150, -150)]:
        draw_chair(x, y)
    
    # Pictures
    draw_wall_picture(-100, 295, 85)
    draw_wall_picture(100, 295, 85)
    
    # Windows
    draw_window(-295, 100, 110)
    draw_window(295, -50, 110)


def draw_room_layout_5():
    """Layout with mixed furniture"""
    # Large showcases on sides
    for y in [-180, -60, 60, 180]:
        # Left wall
        glColor3f(0.4, 0.3, 0.25)
        glPushMatrix()
        glTranslatef(-260, y, 0)
        glScalef(0.7, 0.9, 2)
        glutSolidCube(20)
        glPopMatrix()
        glColor3f(0.6, 0.7, 0.8)
        glPushMatrix()
        glTranslatef(-260, y, 25)
        glScalef(0.6, 0.8, 1.5)
        glutSolidCube(18)
        glPopMatrix()
        
        # Right wall
        glColor3f(0.4, 0.3, 0.25)
        glPushMatrix()
        glTranslatef(260, y, 0)
        glScalef(0.7, 0.9, 2)
        glutSolidCube(20)
        glPopMatrix()
        glColor3f(0.6, 0.7, 0.8)
        glPushMatrix()
        glTranslatef(260, y, 25)
        glScalef(0.6, 0.8, 1.5)
        glutSolidCube(18)
        glPopMatrix()
    
    # Center arrangement
    draw_table(0, 120)
    draw_table(-100, 0)
    draw_table(100, 0)
    draw_table(0, -120)
    
    # Chairs
    for x, y in [(30, 120), (-30, 120), (-130, 0), (130, 0), (30, -120), (-30, -120)]:
        draw_chair(x, y)
    
    # Pedestals in corners
    for x, y in [(-230, -230), (230, -230), (-230, 230), (230, 230)]:
        glColor3f(0.35, 0.3, 0.3)
        glPushMatrix()
        glTranslatef(x, y, 0)
        glScalef(0.5, 0.5, 2.5)
        glutSolidCube(15)
        glPopMatrix()
    
    # Pictures
    draw_wall_picture(0, 295, 95)
    draw_wall_picture(-150, 295, 75)
    draw_wall_picture(150, 295, 75)
    
    # Windows
    draw_window(-295, 200, 105)
    draw_window(295, 200, 105)


def draw_table(x, y):
    """Helper function to draw a table"""
    glColor3f(0.3, 0.2, 0.15)
    # Table top
    glPushMatrix()
    glTranslatef(x, y, 15)
    glScalef(1.5, 1.5, 0.2)
    glutSolidCube(12)
    glPopMatrix()
    # Legs
    for dx, dy in [(-6, -6), (6, -6), (-6, 6), (6, 6)]:
        glPushMatrix()
        glTranslatef(x + dx, y + dy, 7)
        glScalef(0.2, 0.2, 1.2)
        glutSolidCube(6)
        glPopMatrix()


def draw_chair(x, y):
    """Helper function to draw a chair"""
    glColor3f(0.5, 0.3, 0.2)
    # Seat
    glPushMatrix()
    glTranslatef(x, y, 12)
    glScalef(1, 1, 0.3)
    glutSolidCube(10)
    glPopMatrix()
    # Backrest
    glPushMatrix()
    glTranslatef(x, y + 5, 20)
    glScalef(1, 0.3, 1.5)
    glutSolidCube(10)
    glPopMatrix()
    # Legs
    for dx, dy in [(-4, -4), (4, -4), (-4, 4), (4, 4)]:
        glPushMatrix()
        glTranslatef(x + dx, y + dy, 6)
        glScalef(0.2, 0.2, 1.2)
        glutSolidCube(5)
        glPopMatrix()


def draw_wall_picture(x, y, z, rotated=False):
    """Helper function to draw a wall picture"""
    glColor3f(0.6, 0.5, 0.3)
    glPushMatrix()
    glTranslatef(x, y, z)
    if rotated:
        glRotatef(90, 0, 0, 1)
    glScalef(1.5, 0.1, 1.2)
    glutSolidCube(15)
    glPopMatrix()


def draw_window(x, y, z):
    """Helper function to draw a window"""
    glColor3f(0.3, 0.4, 0.5)  # Dark window
    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(0.1, 1.5, 1.2)
    glutSolidCube(15)
    glPopMatrix()


def draw_start_screen():
    """Draw the start menu screen with Start text"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # Purple background
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Solid purple background
    glBegin(GL_QUADS)
    glColor3f(0.3, 0.15, 0.5)  # Purple
    glVertex2f(0, 0)
    glVertex2f(1000, 0)
    glVertex2f(1000, 800)
    glVertex2f(0, 800)
    glEnd()
    
    # Large "Start" text in center
    glColor3f(1, 1, 1)  # White
    # Using a large font for Start text
    glRasterPos2f(420, 400)
    start_text = "START"
    for char in start_text:
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(char))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glutSwapBuffers()


def draw_level_select_screen():
    """Draw the level selection screen with three colored boxes"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # Purple background
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Solid purple background
    glBegin(GL_QUADS)
    glColor3f(0.3, 0.15, 0.5)  # Purple
    glVertex2f(0, 0)
    glVertex2f(1000, 0)
    glVertex2f(1000, 800)
    glVertex2f(0, 800)
    glEnd()
    
    # "Which level you want?" text at top
    glColor3f(1, 1, 1)  # White
    glRasterPos2f(350, 650)
    level_text = "Which level you want?"
    for char in level_text:
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(char))
    
    # Three colored boxes for level selection
    # Box positions: x centers at 250, 500, 750; y from 300 to 500
    box_width = 150
    box_height = 200
    box_y_bottom = 300
    box_y_top = 500
    
    # Box 1 - Red
    glBegin(GL_QUADS)
    glColor3f(0.8, 0.2, 0.2)  # Red
    glVertex2f(175, box_y_bottom)
    glVertex2f(325, box_y_bottom)
    glVertex2f(325, box_y_top)
    glVertex2f(175, box_y_top)
    glEnd()
    
    # Box 1 border
    glLineWidth(3)
    glBegin(GL_LINE_LOOP)
    glColor3f(1, 1, 1)  # White border
    glVertex2f(175, box_y_bottom)
    glVertex2f(325, box_y_bottom)
    glVertex2f(325, box_y_top)
    glVertex2f(175, box_y_top)
    glEnd()
    
    # Number "1" in box 1
    glColor3f(1, 1, 1)
    glRasterPos2f(240, 390)
    glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord('1'))
    
    # Box 2 - Green
    glBegin(GL_QUADS)
    glColor3f(0.2, 0.8, 0.2)  # Green
    glVertex2f(425, box_y_bottom)
    glVertex2f(575, box_y_bottom)
    glVertex2f(575, box_y_top)
    glVertex2f(425, box_y_top)
    glEnd()
    
    # Box 2 border
    glBegin(GL_LINE_LOOP)
    glColor3f(1, 1, 1)
    glVertex2f(425, box_y_bottom)
    glVertex2f(575, box_y_bottom)
    glVertex2f(575, box_y_top)
    glVertex2f(425, box_y_top)
    glEnd()
    
    # Number "2" in box 2
    glColor3f(1, 1, 1)
    glRasterPos2f(490, 390)
    glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord('2'))
    
    # Box 3 - Blue
    glBegin(GL_QUADS)
    glColor3f(0.2, 0.2, 0.8)  # Blue
    glVertex2f(675, box_y_bottom)
    glVertex2f(825, box_y_bottom)
    glVertex2f(825, box_y_top)
    glVertex2f(675, box_y_top)
    glEnd()
    
    # Box 3 border
    glBegin(GL_LINE_LOOP)
    glColor3f(1, 1, 1)
    glVertex2f(675, box_y_bottom)
    glVertex2f(825, box_y_bottom)
    glVertex2f(825, box_y_top)
    glVertex2f(675, box_y_top)
    glEnd()
    
    # Number "3" in box 3
    glColor3f(1, 1, 1)
    glRasterPos2f(740, 390)
    glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord('3'))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glutSwapBuffers()


def update_game():
    """Update game logic"""
    global woody_x, woody_y, woody_z, woody_angle
    global woody_jump_velocity, woody_is_jumping, woody_on_ground
    global lasso_attacking, lasso_attack_timer, lasso_damage_cooldown
    global current_room, boss_room_entered, gabby_visible, bo_peep_visible
    global gabby_hit, bo_peep_approaching, bo_peep_x, bo_peep_y, game_won
    global win_sequence_stage, win_sequence_timer, cage_alpha, camera_target_angle
    global show_mission_complete, show_game_end
    global woody_health, woody_lives, woody_score
    global item_animation_time, collected_stars, collected_hats, collected_coins
    global gabby_x, gabby_y, gabby_health, gabby_move_timer, gabby_move_direction
    global cup_projectiles, gabby_cup_attack_timer, gabby_stick_attack_timer
    global gabby_proximity_timer, gabby_is_close, gabby_attacking_with_stick
    global jessie_power_active, jessie_animation_stage, jessie_y_position
    global jessie_power_cooldown, jessie_animation_timer, bensons_frozen
    global buzz_power_active, buzz_animation_stage, buzz_y_position
    global buzz_power_cooldown, buzz_animation_timer, buzz_ray_alpha
    global game_state, game_over_timer, woody_fade_alpha, show_game_over_text
    global show_level_text, level_text_timer
    
    # Update level text timer
    if show_level_text:
        level_text_timer += 1
        if level_text_timer >= level_text_duration:
            show_level_text = False
            level_text_timer = 0
    
    # Update animation timer (slower for gentler animations)
    item_animation_time += 0.02
    
    # Decrement lasso damage cooldown
    if lasso_damage_cooldown > 0:
        lasso_damage_cooldown -= 1
    
    # Decrement Jessie power cooldown
    if jessie_power_cooldown > 0:
        jessie_power_cooldown -= 1
    
    # Handle Jessie special power activation (works in all rooms including boss room)
    # Check if special powers are enabled for current level
    powers_enabled = level_configs[current_level]['special_powers_enabled']
    if powers_enabled == True or powers_enabled == 'jessie_only':
        if keys_pressed.get('j', False) and not jessie_power_active and jessie_power_cooldown == 0:
            # Activate Jessie power
            jessie_power_active = True
            jessie_animation_stage = 1  # Start descending
            jessie_y_position = 200  # Start from top
            jessie_animation_timer = 0
            keys_pressed['j'] = False  # Reset key
    
    # Decrement Buzz power cooldown
    if buzz_power_cooldown > 0:
        buzz_power_cooldown -= 1
    
    # Handle Buzz special power activation (only when fully enabled, not jessie_only)
    powers_enabled = level_configs[current_level]['special_powers_enabled']
    if powers_enabled == True:  # Not False and not 'jessie_only'
        if keys_pressed.get('b', False) and not buzz_power_active and buzz_power_cooldown == 0:
            # Activate Buzz power (works everywhere including boss room)
            buzz_power_active = True
            buzz_animation_stage = 1  # Start descending
            buzz_y_position = 200  # Start from top
            buzz_animation_timer = 0
            buzz_ray_alpha = 0.0
            keys_pressed['b'] = False  # Reset key
    
    # Update Jessie animation
    if jessie_power_active:
        jessie_animation_timer += 1
        
        if jessie_animation_stage == 1:  # Descending
            jessie_y_position -= 1.5  # Slower descend speed (was 3)
            if jessie_y_position <= 0:  # Landed
                jessie_y_position = 0
                jessie_animation_stage = 2
                jessie_animation_timer = 0
                # Freeze all Bensons in current room (doesn't affect Gabby)
                if current_room < total_rooms - 1:  # Only freeze Bensons in non-boss rooms
                    bensons_frozen = True
        
        elif jessie_animation_stage == 2:  # Landed - stay visible
            if jessie_animation_timer > 300:  # Stay for 5 seconds (300 frames at 60 FPS)
                jessie_animation_stage = 3
                jessie_animation_timer = 0
        
        elif jessie_animation_stage == 3:  # Disappearing
            if jessie_animation_timer > 30:  # Slower disappear (was 10)
                jessie_power_active = False
                jessie_animation_stage = 0
                jessie_power_cooldown = jessie_power_cooldown_max  # 1 minute cooldown
    
    # Update Buzz animation
    if buzz_power_active:
        buzz_animation_timer += 1
        
        if buzz_animation_stage == 1:  # Descending
            buzz_y_position -= 1.5  # Slower descend speed (was 3)
            if buzz_y_position <= 0:  # Landed
                buzz_y_position = 0
                buzz_animation_stage = 2
                buzz_animation_timer = 0
        
        elif buzz_animation_stage == 2:  # Landed briefly
            if buzz_animation_timer > 40:  # Longer pause before shooting (was 10)
                buzz_animation_stage = 3
                buzz_animation_timer = 0
        
        elif buzz_animation_stage == 3:  # Shooting ray
            # Fade in red ray slowly
            buzz_ray_alpha = min(1.0, buzz_animation_timer / 40.0)  # Slower fade in (was 20)
            
            if buzz_animation_timer == 30:  # Ray reaches full power (was 15)
                # Remove all Bensons in current room
                if current_room in room_bensons:
                    for benson in room_bensons[current_room]:
                        benson[2] = False  # Mark as inactive (disappeared)
                
                # Damage Gabby Gabby if in boss room
                if current_room == total_rooms - 1 and gabby_visible and not gabby_hit:
                    gabby_health -= 10  # 10 damage at once
                    if gabby_health <= 0:
                        gabby_health = 0
            
            if buzz_animation_timer > 180:  # Hold ray much longer (was 40) - about 3 seconds
                buzz_animation_stage = 4
                buzz_animation_timer = 0
        
        elif buzz_animation_stage == 4:  # Disappearing
            # Fade out ray slowly
            buzz_ray_alpha = max(0.0, 1.0 - (buzz_animation_timer / 60.0))  # Slower fade out (was 10)
            
            if buzz_animation_timer > 60:  # Slower disappear (was 15)
                buzz_power_active = False
                buzz_animation_stage = 0
                buzz_ray_alpha = 0.0
                buzz_power_cooldown = buzz_power_cooldown_max  # 2 minutes cooldown
    
    # Check for collectible pickup
    if current_room < total_rooms - 1:
        pickup_radius = 25  # Distance to collect items
        
        # Check star collection
        if current_room in rooms_with_stars and current_room not in collected_stars:
            star_x, star_y = room_star_positions[current_room]
            dx = woody_x - star_x
            dy = woody_y - star_y
            distance = math.sqrt(dx*dx + dy*dy)
            if distance < pickup_radius:
                collected_stars.add(current_room)
                # Fully restore health to 100%
                woody_health = 100
        
        # Check hat collection
        if current_room in rooms_with_hats and current_room not in collected_hats:
            hat_x, hat_y = room_hat_positions[current_room]
            dx = woody_x - hat_x
            dy = woody_y - hat_y
            distance = math.sqrt(dx*dx + dy*dy)
            if distance < pickup_radius:
                collected_hats.add(current_room)
                # Increase lives
                woody_lives += 1
        
        # Check coin collection
        if current_room in room_coins:
            for coin_index, (coin_x, coin_y) in enumerate(room_coins[current_room]):
                if (current_room, coin_index) not in collected_coins:
                    dx = woody_x - coin_x
                    dy = woody_y - coin_y
                    distance = math.sqrt(dx*dx + dy*dy)
                    if distance < pickup_radius:
                        collected_coins.add((current_room, coin_index))
                        # Increase score by 10
                        woody_score += 10
    
    # Update Bensons (enemies)
    if current_room in room_bensons and current_room < total_rooms - 1:
        for benson_index, benson in enumerate(room_bensons[current_room]):
            if benson[2]:  # If active
                benson_x, benson_y = benson[0], benson[1]
                
                # Bensons move toward Woody (very slow) - but not if frozen
                if not bensons_frozen:
                    dx = woody_x - benson_x
                    dy = woody_y - benson_y
                    distance_to_woody = math.sqrt(dx*dx + dy*dy)
                    
                    if distance_to_woody > 0:
                        # Normalize and move toward Woody
                        benson[0] += (dx / distance_to_woody) * benson_speed
                        benson[1] += (dy / distance_to_woody) * benson_speed
                else:
                    # Bensons are frozen, calculate distance but don't move
                    dx = woody_x - benson_x
                    dy = woody_y - benson_y
                    distance_to_woody = math.sqrt(dx*dx + dy*dy)
                
                # Decrement hit cooldown
                if benson[3] > 0:
                    benson[3] -= 1
                
                # Check collision with Woody (damage)
                if distance_to_woody < 15 and benson[3] == 0:
                    woody_health -= 5  # 5% damage
                    benson[3] = 60  # 1 second cooldown before next damage
                
                # Check if hit by lasso
                if lasso_attacking and (current_room, benson_index) not in benson_hit_by_lasso:
                    lasso_reach = 30
                    lasso_x = woody_x + lasso_reach * math.cos(math.radians(woody_angle))
                    lasso_y = woody_y + lasso_reach * math.sin(math.radians(woody_angle))
                    
                    lasso_dx = lasso_x - benson_x
                    lasso_dy = lasso_y - benson_y
                    lasso_distance = math.sqrt(lasso_dx*lasso_dx + lasso_dy*lasso_dy)
                    
                    if lasso_distance < 35:  # Hit range
                        benson[2] = False  # Deactivate (defeated)
                        benson_hit_by_lasso.add((current_room, benson_index))
                        woody_score += 50  # +50 score for defeating Benson
    
    # Check health and lives
    if woody_health <= 0:
        woody_lives -= 1
        if woody_lives > 0:
            # Reset health but lose a life
            woody_health = 100
        else:
            # Game over - trigger game over state
            woody_lives = 0
            woody_health = 0
            game_state = "game_over"
            game_over_timer = 0
            woody_fade_alpha = 1.0
            show_game_over_text = False
    
    # Game over animation logic
    if game_state == "game_over":
        game_over_timer += 1
        
        # VERY slow fade out of Woody (600 frames = 10 seconds at 60 FPS)
        if game_over_timer <= 600:
            woody_fade_alpha = 1.0 - (game_over_timer / 600.0)
        else:
            woody_fade_alpha = 0.0
            # Show "Game Over" text slowly after Woody disappears (after 10 seconds)
            if game_over_timer > 600:
                show_game_over_text = True
        
        return  # Don't process other game logic during game over
    
    # Boss fight logic (Gabby Gabby AI and attacks)
    if boss_room_entered and gabby_visible and not gabby_hit and win_sequence_stage == 0:
        # Calculate distance to Woody
        dx = woody_x - gabby_x
        dy = woody_y - gabby_y
        distance_to_woody = math.sqrt(dx*dx + dy*dy)
        
        # Gabby's movement AI - move randomly around the room
        gabby_move_timer += 1
        if gabby_move_timer > 200:  # Change direction every 3.3 seconds (slower)
            gabby_move_timer = 0
            gabby_move_direction = random.randint(0, 360)
        
        # Move Gabby
        move_x = gabby_move_speed * math.cos(math.radians(gabby_move_direction))
        move_y = gabby_move_speed * math.sin(math.radians(gabby_move_direction))
        
        # Keep Gabby in bounds (entire room)
        new_gabby_x = gabby_x + move_x
        new_gabby_y = gabby_y + move_y
        if -270 < new_gabby_x < 270:  # Expanded to almost full room width
            gabby_x = new_gabby_x
        else:
            gabby_move_direction = 180 - gabby_move_direction  # Bounce off wall
        if -270 < new_gabby_y < 270:  # Expanded to almost full room length
            gabby_y = new_gabby_y
        else:
            gabby_move_direction = -gabby_move_direction  # Bounce off wall
        
        # Check if Woody is close for stick attack
        if distance_to_woody < gabby_close_range:
            if not gabby_is_close:
                # Woody just got close, start proximity timer
                gabby_is_close = True
                gabby_proximity_timer = 0
            else:
                # Woody is staying close, increment timer
                gabby_proximity_timer += 1
                
                # After 4 seconds (240 frames), start attacking with stick
                if gabby_proximity_timer >= gabby_stick_attack_cooldown:
                    gabby_stick_attack_timer += 1
                    
                    if gabby_stick_attack_timer >= gabby_stick_attack_cooldown:
                        # Execute stick attack
                        gabby_attacking_with_stick = True
                        gabby_stick_attack_timer = 0
                        
                        # Deal damage to Woody
                        woody_health -= 10  # 10% damage
        else:
            # Woody moved away, reset proximity timer
            gabby_is_close = False
            gabby_proximity_timer = 0
            gabby_stick_attack_timer = 0
        
        # Stick attack animation countdown
        if gabby_attacking_with_stick:
            if gabby_proximity_timer < stick_attack_duration:
                pass  # Animation playing
            else:
                gabby_attacking_with_stick = False
        
        # Ranged cup attack when far away
        if distance_to_woody > gabby_far_range:
            gabby_cup_attack_timer += 1
            
            if gabby_cup_attack_timer >= gabby_cup_attack_cooldown:
                # Throw cup toward Woody
                angle_to_woody = math.atan2(dy, dx)
                cup_speed = 0.5  # Even slower projectile speed
                cup_dx = cup_speed * math.cos(angle_to_woody)
                cup_dy = cup_speed * math.sin(angle_to_woody)
                
                # Create new cup projectile
                cup_projectiles.append([gabby_x, gabby_y, cup_dx, cup_dy, 0])  # x, y, dx, dy, lifetime
                gabby_cup_attack_timer = 0
    
    # Update cup projectiles
    cups_to_remove = []
    for i, cup in enumerate(cup_projectiles):
        # Move cup
        cup[0] += cup[2]  # x += dx
        cup[1] += cup[3]  # y += dy
        cup[4] += 1  # increment lifetime
        
        # Check collision with Woody
        dx = woody_x - cup[0]
        dy = woody_y - cup[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 15:  # Hit Woody
            woody_health -= 5  # 5% damage
            cups_to_remove.append(i)
        elif abs(cup[0]) > 500 or abs(cup[1]) > 500:  # Only remove when very far out of room
            cups_to_remove.append(i)
    
    # Remove old cups
    for i in reversed(cups_to_remove):
        cup_projectiles.pop(i)
    
    # Handle win sequence stages
    if win_sequence_stage > 0:
        win_sequence_timer += 1
        
        if win_sequence_stage == 1:  # Camera turning toward cage
            # Calculate angle to look at cage from Woody's position
            cage_x, cage_y = 0, -200
            target_angle = math.degrees(math.atan2(cage_y - woody_y, cage_x - woody_x))
            
            # Smoothly rotate camera (very slow)
            angle_diff = target_angle - woody_angle
            # Normalize angle difference to -180 to 180
            while angle_diff > 180:
                angle_diff -= 360
            while angle_diff < -180:
                angle_diff += 360
            
            if abs(angle_diff) > 0.5:
                woody_angle += angle_diff * 0.015  # Very slow rotation
                if woody_angle < 0:
                    woody_angle += 360
                if woody_angle >= 360:
                    woody_angle -= 360
            else:
                # Camera focused on cage, move to next stage
                win_sequence_stage = 2
                win_sequence_timer = 0
        
        elif win_sequence_stage == 2:  # Cage fading
            # Fade out cage over 200 frames (~3.3 seconds)
            cage_alpha -= 0.005  # Slow fade
            if cage_alpha <= 0:
                cage_alpha = 0
                win_sequence_stage = 3
                win_sequence_timer = 0
                bo_peep_approaching = True
        
        elif win_sequence_stage == 3:  # Bo Peep approaching
            # Move Bo Peep toward Woody
            dx = woody_x - bo_peep_x
            dy = woody_y - bo_peep_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance > 5:  # Still approaching
                # Move toward Woody very slowly
                move_amount = 0.5  # Slow approach speed
                bo_peep_x += (dx / distance) * move_amount
                bo_peep_y += (dy / distance) * move_amount
            else:
                # Reached Woody - start hugging
                win_sequence_stage = 4
                win_sequence_timer = 0
                bo_peep_approaching = False
        
        elif win_sequence_stage == 4:  # Hugging
            # Wait 5 seconds (300 frames at 60fps)
            if win_sequence_timer >= 300:
                win_sequence_stage = 5
                win_sequence_timer = 0
                show_mission_complete = True
        
        elif win_sequence_stage == 5:  # Mission Complete displayed
            # Wait 3 seconds (180 frames)
            if win_sequence_timer >= 180:
                # Check if there's a next level
                if current_level < 3:
                    # Move to next level
                    win_sequence_stage = 6
                    win_sequence_timer = 0
                    show_level_text = True  # Show "Level Complete" message
                else:
                    # Final level completed - game end
                    win_sequence_stage = 6
                    win_sequence_timer = 0
                    show_game_end = True
        
        elif win_sequence_stage == 6:  # Level transition or Game End
            if current_level < 3:
                # Wait 2 seconds then move to next level
                if win_sequence_timer >= 120:
                    next_level = current_level + 1
                    initialize_level(next_level)
                    # Reset win sequence
                    win_sequence_stage = 0
                    show_mission_complete = False
                    show_level_text = True
                    level_text_timer = 0
            else:
                # Stay at this stage (final game end)
                pass
        
        return  # Don't process normal game logic during win sequence
    
    # If Gabby is hit, stop player movement (but not in win sequence yet)
    if gabby_hit:
        return
    
    # Constants for collision and doors
    collision_radius = 10  # Woody's collision radius
    door_width = 100  # Width of door area
    
    # Movement with wall collision only (furniture collision disabled)
    if keys_pressed['up']:
        # Calculate new position
        new_x = woody_x + move_speed * math.cos(math.radians(woody_angle))
        new_y = woody_y + move_speed * math.sin(math.radians(woody_angle))
        
        # Check X boundaries (left and right walls)
        if new_x >= -280 + collision_radius and new_x <= 280 - collision_radius:
            woody_x = new_x
        
        # Check Y boundaries - allow going beyond if in door area
        if abs(woody_x) < door_width:
            # In door area - allow movement beyond normal bounds for door transition
            if new_y >= -295 and new_y <= 295:
                woody_y = new_y
        else:
            # Not in door area - enforce wall collision
            if new_y >= -285 + collision_radius and new_y <= 285 - collision_radius:
                woody_y = new_y
    
    if keys_pressed['down']:
        # Calculate new position
        new_x = woody_x - move_speed * math.cos(math.radians(woody_angle))
        new_y = woody_y - move_speed * math.sin(math.radians(woody_angle))
        
        # Check X boundaries (left and right walls)
        if new_x >= -280 + collision_radius and new_x <= 280 - collision_radius:
            woody_x = new_x
        
        # Check Y boundaries - allow going beyond if in door area
        if abs(woody_x) < door_width:
            # In door area - allow movement beyond normal bounds for door transition
            if new_y >= -295 and new_y <= 295:
                woody_y = new_y
        else:
            # Not in door area - enforce wall collision
            if new_y >= -285 + collision_radius and new_y <= 285 - collision_radius:
                woody_y = new_y
    
    # Rotation
    if keys_pressed['left']:
        woody_angle += rotation_speed
        if woody_angle >= 360:
            woody_angle -= 360
    
    if keys_pressed['right']:
        woody_angle -= rotation_speed
        if woody_angle < 0:
            woody_angle += 360
    
    # Jumping
    if woody_is_jumping:
        woody_z += woody_jump_velocity
        woody_jump_velocity -= gravity
        
        if woody_z <= 0:
            woody_z = 0
            woody_is_jumping = False
            woody_on_ground = True
            woody_jump_velocity = 0
    
    # Lasso attack
    if lasso_attacking:
        lasso_attack_timer += 1
        if lasso_attack_timer >= lasso_attack_duration:
            lasso_attacking = False
            lasso_attack_timer = 0
        
        # Check collision with Gabby in boss room
        if boss_room_entered and gabby_visible and not gabby_hit:
            # Gabby is at position (0, -100)
            gabby_x = 0
            gabby_y = -100
            
            # Calculate lasso reach (in front of Woody)
            lasso_reach = 30  # Distance lasso extends
            lasso_x = woody_x + lasso_reach * math.cos(math.radians(woody_angle))
            lasso_y = woody_y + lasso_reach * math.sin(math.radians(woody_angle))
            
            # Check distance to Gabby
            dx = lasso_x - gabby_x
            dy = lasso_y - gabby_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < 40:  # Hit range
                # Gabby is hit! Reduce her health (only if cooldown expired)
                if lasso_damage_cooldown == 0:
                    gabby_health -= 1
                    lasso_damage_cooldown = 30  # 0.5 second cooldown to prevent multiple hits
                
                # Check if Gabby is defeated
                if gabby_health <= 0:
                    gabby_hit = True
                    gabby_visible = False
                    woody_score += 100  # +100 score for defeating Gabby
                    # Start win sequence - Woody stops moving and turns to Bo Peep
                    win_sequence_stage = 1
                    win_sequence_timer = 0
    
    # Check for room transitions through doors
    # Front door (at -Y) � Next room
    if woody_y <= -290 and abs(woody_x) < door_width and current_room < total_rooms - 1:
        current_room += 1
        woody_y = 280  # Enter from back of new room
        
        # Unfreeze Bensons when changing rooms
        bensons_frozen = False
        
        # Check if entering boss room
        if current_room == total_rooms - 1:
            boss_room_entered = True
            gabby_visible = True
            bo_peep_visible = True
            # Initialize boss position and health for boss fight
            gabby_x = 0
            gabby_y = -100
            # Set boss health based on level
            boss_name = level_configs[current_level]['boss_name']
            if boss_name == 'potato_head':
                gabby_health = 20  # Mr. Potato Head - 20 hits required
            elif boss_name == 'lotso':
                gabby_health = 30  # Lotso bear - 30 hits required
            else:
                gabby_health = 50  # Gabby Gabby - 50 hits required
            gabby_cup_attack_timer = 0
            gabby_stick_attack_timer = 0
            gabby_proximity_timer = 0
            gabby_is_close = False
            gabby_attacking_with_stick = False
            cup_projectiles.clear()
        return
    
    # Back door (at +Y) � Previous room (NOT allowed in boss room 15)
    # Woody can go back from any room except room 15 (boss room)
    if woody_y >= 290 and abs(woody_x) < door_width and current_room > 0 and current_room < total_rooms - 1:
        current_room -= 1
        woody_y = -280  # Enter from front of previous room
        
        # Unfreeze Bensons when changing rooms
        bensons_frozen = False
        return
    
    # Clamp Woody's position to room bounds (failsafe) - but allow extra space in door areas
    if abs(woody_x) < door_width:
        # In door area - wider Y bounds
        woody_y = max(-295, min(295, woody_y))
    else:
        # Not in door area - normal bounds
        woody_y = max(-285 + collision_radius, min(285 - collision_radius, woody_y))
    
    woody_x = max(-280 + collision_radius, min(280 - collision_radius, woody_x))


def showScreen():
    """Main display function"""
    global game_state, fade_alpha, fade_timer
    
    if game_state == "menu":
        draw_start_screen()
        return
    
    elif game_state == "level_select":
        draw_level_select_screen()
        return
    
    elif game_state == "fade":
        # Fade to black transition
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, 1000, 0, 800)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glColor3f(0, 0, 0)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(1000, 0)
        glVertex2f(1000, 800)
        glVertex2f(0, 800)
        glEnd()
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        
        glutSwapBuffers()
        
        fade_timer += 1
        if fade_timer > 30:  # Fade duration
            # Initialize the selected level
            initialize_level(selected_level)
            game_state = "playing"
            fade_timer = 0
        return
    
    elif game_state == "game_over":
        # Game over screen with fading Woody and message
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Camera setup same as playing state
        camera_x = woody_x - camera_distance * math.cos(math.radians(woody_angle))
        camera_y = woody_y - camera_distance * math.sin(math.radians(woody_angle))
        camera_z = woody_z + camera_height
        
        gluLookAt(camera_x, camera_y, camera_z,
                  woody_x, woody_y, woody_z + 10,
                  0, 0, 1)
        
        # Draw scene
        draw_museum_room()
        
        # Draw Woody with transparency (fading out)
        if woody_fade_alpha > 0:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            draw_woody()
            glDisable(GL_BLEND)
        
        # Display "Game Over" text after Woody disappears
        if show_game_over_text:
            glColor3f(1, 0, 0)  # Red color
            draw_text("GAME OVER", 400, 400, GLUT_BITMAP_TIMES_ROMAN_24)
        
        glutSwapBuffers()
        return
    
    # Playing state
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # Camera follows Woody from behind
    camera_x = woody_x - camera_distance * math.cos(math.radians(woody_angle))
    camera_y = woody_y - camera_distance * math.sin(math.radians(woody_angle))
    camera_z = woody_z + camera_height
    
    gluLookAt(camera_x, camera_y, camera_z,
              woody_x, woody_y, woody_z + 10,
              0, 0, 1)
    
    # Draw scene
    draw_museum_room()
    draw_woody()
    
    # Display health and lives
    draw_health_and_lives()
    
    # Display score at top right corner (gold color like coins)
    glColor3f(1.0, 0.84, 0.0)
    draw_text(f"SCORE: {woody_score}", 830, 760, GLUT_BITMAP_HELVETICA_18)
    
    # Display room number below score
    glColor3f(1, 1, 1)
    draw_text(f"ROOM {current_room + 1}/{total_rooms}", 830, 730, GLUT_BITMAP_HELVETICA_18)
    
    # Display level text at top center
    if show_level_text:
        if win_sequence_stage == 6 and current_level < 3:
            # Show "Level Complete" during level transition
            glColor3f(0, 1, 0)  # Green
            draw_text("LEVEL COMPLETE", 370, 760, GLUT_BITMAP_TIMES_ROMAN_24)
        else:
            # Show "Level N" at level start
            glColor3f(1, 1, 1)  # White
            draw_text(f"LEVEL {current_level}", 420, 760, GLUT_BITMAP_TIMES_ROMAN_24)
    
    # Display win sequence text
    if show_mission_complete:
        glColor3f(1, 1, 0)  # Yellow
        draw_text("MISSION COMPLETE", 350, 750, GLUT_BITMAP_TIMES_ROMAN_24)
    
    if show_game_end:
        glColor3f(1, 0.5, 0)  # Orange
        draw_text("THE GAME END", 380, 710, GLUT_BITMAP_TIMES_ROMAN_24)
    
    glutSwapBuffers()


def keyboardListener(key, x, y):
    """Handle keyboard press"""
    global lasso_attacking, lasso_attack_timer, woody_health, game_state, selected_level
    
    # Level selection with keyboard (1, 2, 3 keys)
    if game_state == "level_select":
        if key == b'1':
            selected_level = 1
            game_state = "fade"
            return
        elif key == b'2':
            selected_level = 2
            game_state = "fade"
            return
        elif key == b'3':
            selected_level = 3
            game_state = "fade"
            return
    
    # Game controls
    if key == b'a' or key == b'A':
        if not lasso_attacking:
            lasso_attacking = True
            lasso_attack_timer = 0
            keys_pressed['a'] = True
    
    # J key for Jessie special power
    if key == b'j' or key == b'J':
        keys_pressed['j'] = True
    
    # B key for Buzz special power
    if key == b'b' or key == b'B':
        keys_pressed['b'] = True
    
    # Test key to reduce health (H key)
    if key == b'h' or key == b'H':
        woody_health -= 5  # Simulate enemy hit


def keyboardUpListener(key, x, y):
    """Handle keyboard release"""
    if key == b'a' or key == b'A':
        keys_pressed['a'] = False


def specialKeyListener(key, x, y):
    """Handle special key press"""
    if key == GLUT_KEY_UP:
        keys_pressed['up'] = True
    elif key == GLUT_KEY_DOWN:
        keys_pressed['down'] = True
    elif key == GLUT_KEY_LEFT:
        keys_pressed['left'] = True
    elif key == GLUT_KEY_RIGHT:
        keys_pressed['right'] = True


def specialKeyUpListener(key, x, y):
    """Handle special key release"""
    if key == GLUT_KEY_UP:
        keys_pressed['up'] = False
    elif key == GLUT_KEY_DOWN:
        keys_pressed['down'] = False
    elif key == GLUT_KEY_LEFT:
        keys_pressed['left'] = False
    elif key == GLUT_KEY_RIGHT:
        keys_pressed['right'] = False


def mouseListener(button, state, x, y):
    """Handle mouse clicks"""
    global game_state, selected_level
    
    # Convert y coordinate (GLUT uses top-left origin, we need bottom-left)
    y = 800 - y
    
    if game_state == "menu" and button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        # Click anywhere on start screen to go to level select
        game_state = "level_select"
    
    elif game_state == "level_select" and button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        # Check if clicked on any of the three level boxes
        # Box 1 (Red): x 175-325, y 300-500
        if 175 <= x <= 325 and 300 <= y <= 500:
            selected_level = 1
            game_state = "fade"
        # Box 2 (Green): x 425-575, y 300-500
        elif 425 <= x <= 575 and 300 <= y <= 500:
            selected_level = 2
            game_state = "fade"
        # Box 3 (Blue): x 675-825, y 300-500
        elif 675 <= x <= 825 and 300 <= y <= 500:
            selected_level = 3
            game_state = "fade"


def idle():
    """Idle function for continuous updates"""
    if game_state == "playing":
        update_game()
    glutPostRedisplay()


def init():
    """Initialize OpenGL settings"""
    glClearColor(0, 0, 0, 1)
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, 1.25, 0.1, 2000)
    glMatrixMode(GL_MODELVIEW)


def main():
    """Main function"""
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Toy Story Adventure - Rescue Bo Peep")
    
    init()
    
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)
    glutSpecialFunc(specialKeyListener)
    glutSpecialUpFunc(specialKeyUpListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    
    glutMainLoop()


if __name__ == "__main__":
    main()
