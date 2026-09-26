
import sys
import random
import time
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# Game Constants
WIDTH, HEIGHT = 1000, 800
FPS = 60

# Game State
class GameState:
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    GAME_OVER = 4
    WIN_SCREEN = 5

current_state = GameState.LEVEL_1
score = 0
lives = 10
game_start_time = time.time()
level_start_time = time.time()

# Player (Woody) properties
class Player:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
        self.rotation = 0  # Camera/player rotation in degrees
        self.speed = 2.0
        self.rotation_speed = 3.0
        self.jump_height = 0
        self.is_jumping = False
        self.jump_velocity = 0
        self.lasso_attack = False
        self.lasso_timer = 0
        self.health = 100
        
player = Player()

# Enemy class
class Enemy:
    def __init__(self, x, z, enemy_type):
        self.x = x
        self.y = 0
        self.z = z
        self.type = enemy_type  # "monkey", "army", "benson"
        self.health = 50 if enemy_type == "monkey" else 70 if enemy_type == "army" else 90
        self.speed = random.uniform(0.5, 1.5)
        self.active = True
        self.hit_timer = 0
        
# Boss class
class Boss:
    def __init__(self, x, z, boss_type):
        self.x = x
        self.y = 0
        self.z = z
        self.type = boss_type  # "potato", "lotso", "gabby"
        self.health = 200 if boss_type == "potato" else 300 if boss_type == "lotso" else 400
        self.active = True
        
# Collectible items
class Collectible:
    def __init__(self, x, z, item_type):
        self.x = x
        self.y = 0
        self.z = z
        self.type = item_type  # "star" or "hat"
        self.active = True
        self.rotation = 0

# Game objects
enemies = []
bosses = []
collectibles = []
cages = []
special_effects = []

# Initialize game objects for level 1
def init_level_1():
    global enemies, collectibles, bosses, cages
    enemies.clear()
    collectibles.clear()
    bosses.clear()
    cages.clear()
    
    # Create red monkeys
    for i in range(8):
        x = random.uniform(-100, 100)
        z = random.uniform(50, 300)
        enemies.append(Enemy(x, z, "monkey"))
    
    # Create stars and hats
    for i in range(10):
        x = random.uniform(-150, 150)
        z = random.uniform(50, 400)
        collectibles.append(Collectible(x, z, "star"))
        
    for i in range(5):
        x = random.uniform(-150, 150)
        z = random.uniform(50, 400)
        collectibles.append(Collectible(x, z, "hat"))
    
    # Create Mr. Potato Head boss
    bosses.append(Boss(0, 500, "potato"))
    
    # Create Jessie's cage
    cages.append({"x": 0, "z": 550, "type": "jessie"})

# Initialize game objects for level 2
def init_level_2():
    global enemies, collectibles, bosses, cages
    enemies.clear()
    collectibles.clear()
    bosses.clear()
    cages.clear()
    
    # Create green army soldiers
    for i in range(12):
        x = random.uniform(-120, 120)
        z = random.uniform(50, 350)
        enemies.append(Enemy(x, z, "army"))
    
    # Create stars and hats
    for i in range(15):
        x = random.uniform(-200, 200)
        z = random.uniform(50, 500)
        collectibles.append(Collectible(x, z, "star"))
        
    for i in range(7):
        x = random.uniform(-200, 200)
        z = random.uniform(50, 500)
        collectibles.append(Collectible(x, z, "hat"))
    
    # Create Lotso boss
    bosses.append(Boss(0, 600, "lotso"))
    
    # Create Buzz's cage
    cages.append({"x": 0, "z": 650, "type": "buzz"})

# Initialize game objects for level 3
def init_level_3():
    global enemies, collectibles, bosses, cages
    enemies.clear()
    collectibles.clear()
    bosses.clear()
    cages.clear()
    
    # Create Benson enemies
    for i in range(15):
        x = random.uniform(-150, 150)
        z = random.uniform(50, 400)
        enemies.append(Enemy(x, z, "benson"))
    
    # Create stars and hats
    for i in range(20):
        x = random.uniform(-250, 250)
        z = random.uniform(50, 600)
        collectibles.append(Collectible(x, z, "star"))
        
    for i in range(10):
        x = random.uniform(-250, 250)
        z = random.uniform(50, 600)
        collectibles.append(Collectible(x, z, "hat"))
    
    # Create Gabby Gabby boss
    bosses.append(Boss(0, 700, "gabby"))
    
    # Create Bo Peep's cage
    cages.append({"x": 0, "z": 750, "type": "bopeep"})

# Initialize the game
def init():
    glClearColor(0.53, 0.81, 0.98, 1.0)  # Sky blue
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    
    # Simple light
    glLightfv(GL_LIGHT0, GL_POSITION, [1, 1, 1, 0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1, 1, 1, 1])
    
    init_level_1()

# Draw ground (desert, playground, museum)
def draw_ground():
    glPushMatrix()
    glTranslatef(0, -10, 0)
    
    if current_state == GameState.LEVEL_1:
        # Desert ground - sandy color
        glColor3f(0.96, 0.87, 0.7)
    elif current_state == GameState.LEVEL_2:
        # Playground ground - green
        glColor3f(0.4, 0.8, 0.4)
    elif current_state == GameState.LEVEL_3:
        # Museum floor - marble-like
        glColor3f(0.9, 0.9, 0.9)
    
    glBegin(GL_QUADS)
    glVertex3f(-500, 0, -100)
    glVertex3f(500, 0, -100)
    glVertex3f(500, 0, 800)
    glVertex3f(-500, 0, 800)
    glEnd()
    
    # Add grid lines for better depth perception
    glColor3f(0.7, 0.7, 0.7)
    glBegin(GL_LINES)
    for i in range(-400, 401, 50):
        glVertex3f(i, 0.1, -100)
        glVertex3f(i, 0.1, 800)
        glVertex3f(-400, 0.1, i)
        glVertex3f(400, 0.1, i)
    glEnd()
    
    glPopMatrix()

# Draw Woody (main character)
def draw_woody():
    glPushMatrix()
    glTranslatef(player.x, player.y + player.jump_height, player.z)
    glRotatef(player.rotation, 0, 1, 0)
    
    # Body (cowboy vest - brown)
    glColor3f(0.55, 0.27, 0.07)
    glPushMatrix()
    glTranslatef(0, 15, 0)
    glScalef(1.2, 2, 0.8)
    glutSolidCube(10)
    glPopMatrix()
    
    # Head (yellow)
    glColor3f(1, 1, 0)
    glPushMatrix()
    glTranslatef(0, 30, 0)
    glutSolidSphere(8, 10, 10)
    glPopMatrix()
    
    # Hat (brown)
    glColor3f(0.4, 0.2, 0.0)
    glPushMatrix()
    glTranslatef(0, 38, 0)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 10, 12, 5, 10, 10)
    glPopMatrix()
    
    # Arms
    glColor3f(1, 1, 0)
    # Left arm
    glPushMatrix()
    glTranslatef(-10, 20, 0)
    glScalef(0.5, 2, 0.5)
    glutSolidCube(10)
    glPopMatrix()
    
    # Right arm (with lasso)
    glPushMatrix()
    glTranslatef(10, 20, 0)
    glScalef(0.5, 2, 0.5)
    glutSolidCube(10)
    glPopMatrix()
    
    # Draw lasso when attacking
    if player.lasso_attack:
        glColor3f(1, 1, 1)
        glPushMatrix()
        glTranslatef(15, 25, 0)
        glRotatef(90, 0, 1, 0)
        glutSolidTorus(1, 15, 10, 10)
        glPopMatrix()
    
    # Legs
    glColor3f(0.2, 0.2, 0.6)  # Blue jeans
    # Left leg
    glPushMatrix()
    glTranslatef(-5, 5, 0)
    glScalef(0.7, 2, 0.7)
    glutSolidCube(10)
    glPopMatrix()
    
    # Right leg
    glPushMatrix()
    glTranslatef(5, 5, 0)
    glScalef(0.7, 2, 0.7)
    glutSolidCube(10)
    glPopMatrix()
    
    glPopMatrix()

# Draw enemies
def draw_enemy(enemy):
    if not enemy.active:
        return
        
    glPushMatrix()
    glTranslatef(enemy.x, enemy.y, enemy.z)
    
    if enemy.type == "monkey":
        # Red monkey
        glColor3f(1, 0, 0)
        glPushMatrix()
        glTranslatef(0, 10, 0)
        glutSolidSphere(8, 10, 10)  # Body
        glPopMatrix()
        
        # Head
        glPushMatrix()
        glTranslatef(0, 20, 0)
        glutSolidSphere(5, 10, 10)
        glPopMatrix()
        
        # Arms
        glPushMatrix()
        glTranslatef(-8, 15, 0)
        glScalef(0.5, 2, 0.5)
        glutSolidCube(5)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(8, 15, 0)
        glScalef(0.5, 2, 0.5)
        glutSolidCube(5)
        glPopMatrix()
        
    elif enemy.type == "army":
        # Green army soldier
        glColor3f(0, 0.6, 0)
        glPushMatrix()
        glTranslatef(0, 10, 0)
        glScalef(1, 2, 0.8)
        glutSolidCube(10)
        glPopMatrix()
        
        # Helmet
        glColor3f(0.8, 0.8, 0.8)
        glPushMatrix()
        glTranslatef(0, 20, 0)
        glutSolidSphere(6, 10, 10)
        glPopMatrix()
        
    elif enemy.type == "benson":
        # Benson (doll)
        glColor3f(0.8, 0.8, 1.0)
        glPushMatrix()
        glTranslatef(0, 15, 0)
        glutSolidSphere(10, 10, 10)  # Body
        glPopMatrix()
        
        # Head
        glPushMatrix()
        glTranslatef(0, 28, 0)
        glutSolidSphere(7, 10, 10)
        glPopMatrix()
    
    # Hit effect
    if enemy.hit_timer > 0:
        glColor3f(1, 1, 1)
        glPointSize(20)
        glBegin(GL_POINTS)
        glVertex3f(0, 30, 0)
        glEnd()
    
    glPopMatrix()

# Draw bosses
def draw_boss(boss):
    if not boss.active:
        return
        
    glPushMatrix()
    glTranslatef(boss.x, boss.y, boss.z)
    
    if boss.type == "potato":
        # Mr. Potato Head
        glColor3f(0.9, 0.7, 0.5)
        glPushMatrix()
        glScalef(2, 2, 2)
        glutSolidSphere(15, 15, 15)
        glPopMatrix()
        
        # Eyes
        glColor3f(1, 1, 1)
        glPushMatrix()
        glTranslatef(-8, 10, 12)
        glutSolidSphere(3, 10, 10)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(8, 10, 12)
        glutSolidSphere(3, 10, 10)
        glPopMatrix()
        
    elif boss.type == "lotso":
        # Lotso the bear (strawberry smell)
        glColor3f(0.8, 0.2, 0.3)
        glPushMatrix()
        glScalef(2.5, 2.5, 2.5)
        glutSolidSphere(15, 15, 15)
        glPopMatrix()
        
        # Strawberry stem
        glColor3f(0.3, 0.6, 0.2)
        glPushMatrix()
        glTranslatef(0, 40, 0)
        glRotatef(90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), 5, 2, 10, 10, 10)
        glPopMatrix()
        
    elif boss.type == "gabby":
        # Gabby Gabby
        glColor3f(0.9, 0.8, 0.9)  # Pink dress
        glPushMatrix()
        glScalef(3, 3, 3)
        glutSolidSphere(15, 15, 15)
        glPopMatrix()
        
        # Hair
        glColor3f(0.5, 0.3, 0.1)
        glPushMatrix()
        glTranslatef(0, 35, 0)
        glutSolidSphere(10, 10, 10)
        glPopMatrix()
    
    glPopMatrix()

# Draw collectibles
def draw_collectible(item):
    if not item.active:
        return
        
    glPushMatrix()
    glTranslatef(item.x, item.y + 5, item.z)
    glRotatef(item.rotation, 0, 1, 0)
    
    if item.type == "star":
        glColor3f(1, 1, 0)  # Yellow star
        glPushMatrix()
        glScalef(1.5, 1.5, 0.1)
        # Draw a simple star shape
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0, 0, 0)
        for i in range(11):
            angle = i * 36 * 3.14159 / 180
            radius = 5 if i % 2 == 0 else 3
            glVertex3f(radius * sin(angle), radius * cos(angle), 0)
        glEnd()
        glPopMatrix()
        
    elif item.type == "hat":
        glColor3f(0.1, 0.5, 0.9)  # Blue hat
        glPushMatrix()
        glRotatef(-90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), 4, 6, 4, 10, 10)
        glPopMatrix()
    
    glPopMatrix()

# Draw cages
def draw_cage(cage):
    glPushMatrix()
    glTranslatef(cage["x"], 0, cage["z"])
    
    # Cage bars
    glColor3f(0.5, 0.5, 0.5)
    for i in range(-15, 16, 5):
        glPushMatrix()
        glTranslatef(i, 0, 0)
        glScalef(0.5, 20, 0.5)
        glutSolidCube(5)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(0, 0, i)
        glScalef(0.5, 20, 0.5)
        glutSolidCube(5)
        glPopMatrix()
    
    # Character inside cage
    if cage["type"] == "jessie":
        glColor3f(0.8, 0.2, 0.2)  # Red for Jessie
        glPushMatrix()
        glTranslatef(0, 10, 0)
        glutSolidSphere(8, 10, 10)
        glPopMatrix()
    elif cage["type"] == "buzz":
        glColor3f(0.2, 0.2, 0.8)  # Blue for Buzz
        glPushMatrix()
        glTranslatef(0, 10, 0)
        glScalef(1, 1.5, 1)
        glutSolidCube(15)
        glPopMatrix()
    elif cage["type"] == "bopeep":
        glColor3f(1, 1, 1)  # White for Bo Peep
        glPushMatrix()
        glTranslatef(0, 10, 0)
        glutSolidSphere(10, 10, 10)
        glPopMatrix()
    
    glPopMatrix()

# Draw special effects
def draw_special_effects():
    for effect in special_effects[:]:
        glPushMatrix()
        glTranslatef(effect["x"], effect["y"], effect["z"])
        
        if effect["type"] == "jessie_freeze":
            glColor3f(0.2, 0.5, 1.0, 0.5)
            glutSolidSphere(effect["radius"], 10, 10)
            
        elif effect["type"] == "buzz_laser":
            glColor3f(1, 0, 0)
            glPushMatrix()
            glRotatef(90, 1, 0, 0)
            gluCylinder(gluNewQuadric(), 2, 2, effect["length"], 10, 10)
            glPopMatrix()
            
        glPopMatrix()

# Draw UI
def draw_ui():
    # Switch to 2D orthographic projection for UI
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIDTH, 0, HEIGHT)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Disable lighting for UI
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    
    # Draw score
    glColor3f(1, 1, 1)
    draw_text(10, HEIGHT - 30, f"Score: {score}")
    draw_text(10, HEIGHT - 60, f"Lives: {lives}")
    draw_text(10, HEIGHT - 90, f"Health: {player.health}%")
    
    # Draw level info
    if current_state == GameState.LEVEL_1:
        draw_text(WIDTH//2 - 50, HEIGHT - 30, "Level 1: Desert")
        draw_text(WIDTH//2 - 100, HEIGHT - 60, "Defeat Red Monkeys!")
    elif current_state == GameState.LEVEL_2:
        draw_text(WIDTH//2 - 50, HEIGHT - 30, "Level 2: Playground")
        draw_text(WIDTH//2 - 100, HEIGHT - 60, "Defeat Green Army!")
    elif current_state == GameState.LEVEL_3:
        draw_text(WIDTH//2 - 50, HEIGHT - 30, "Level 3: Museum")
        draw_text(WIDTH//2 - 100, HEIGHT - 60, "Defeat The Bensons!")
    
    # Draw controls help
    glColor3f(0.8, 0.8, 0.8)
    draw_text(10, 30, "Controls: Arrow Keys = Move, J = Jump, L = Lasso")
    if current_state >= GameState.LEVEL_2:
        draw_text(10, 60, "A = Jessie Freeze (Level 2-3)")
    if current_state == GameState.LEVEL_3:
        draw_text(10, 90, "S = Buzz Laser (Level 3)")
    
    # Draw timer
    elapsed = time.time() - level_start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    draw_text(WIDTH - 150, HEIGHT - 30, f"Time: {minutes:02d}:{seconds:02d}")
    
    # Draw game over or win screen
    if current_state == GameState.GAME_OVER:
        glColor3f(1, 0, 0)
        draw_text(WIDTH//2 - 100, HEIGHT//2, "GAME OVER")
        draw_text(WIDTH//2 - 120, HEIGHT//2 - 50, f"Final Score: {score}")
    elif current_state == GameState.WIN_SCREEN:
        glColor3f(0, 1, 0)
        draw_text(WIDTH//2 - 150, HEIGHT//2 + 100, "CONGRATULATIONS!")
        draw_text(WIDTH//2 - 100, HEIGHT//2 + 50, f"Total Score: {score}")
    
    # Re-enable 3D settings
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# Draw text using GLUT bitmap fonts (from allowed functions)
def draw_text(x, y, text):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

# Draw win screen picture
def draw_win_picture():
    glPushMatrix()
    glTranslatef(0, 0, -50)
    
    # Draw Bo Peep
    glColor3f(1, 1, 1)  # White dress
    glPushMatrix()
    glTranslatef(-20, 20, 0)
    glutSolidSphere(15, 15, 15)  # Body
    glPopMatrix()
    
    # Draw shepherd's hook
    glColor3f(0.8, 0.8, 0.8)
    glPushMatrix()
    glTranslatef(-5, 10, 0)
    glRotatef(45, 0, 0, 1)
    glScalef(0.5, 30, 0.5)
    glutSolidCube(2)
    glPopMatrix()
    
    # Draw Woody being held
    glColor3f(1, 1, 0)  # Yellow
    glPushMatrix()
    glTranslatef(10, 15, 0)
    glutSolidSphere(10, 10, 10)  # Woody's head
    glPopMatrix()
    
    # Draw Woody's hat
    glColor3f(0.4, 0.2, 0.0)
    glPushMatrix()
    glTranslatef(10, 23, 0)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 8, 10, 4, 10, 10)
    glPopMatrix()
    
    glPopMatrix()

# Main display function
def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    if current_state == GameState.WIN_SCREEN:
        # Win screen with 2D orthographic view
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, WIDTH, 0, HEIGHT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        draw_ui()
        
        # Draw the win picture
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, WIDTH/HEIGHT, 0.1, 1000)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0, 50, 100, 0, 0, 0, 0, 1, 0)
        
        draw_win_picture()
        
    elif current_state == GameState.GAME_OVER:
        # Game over screen
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, WIDTH, 0, HEIGHT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        draw_ui()
        
    else:
        # Regular 3D game view
        glViewport(0, 0, WIDTH, HEIGHT)
        
        # Set up perspective projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, WIDTH/HEIGHT, 0.1, 1000)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Camera follows Woody from behind
        cam_x = player.x - 50 * sin(player.rotation * 3.14159 / 180)
        cam_z = player.z - 50 * cos(player.rotation * 3.14159 / 180)
        cam_y = player.y + player.jump_height + 20
        
        look_x = player.x + 100 * sin(player.rotation * 3.14159 / 180)
        look_z = player.z + 100 * cos(player.rotation * 3.14159 / 180)
        look_y = player.y + player.jump_height + 10
        
        gluLookAt(cam_x, cam_y, cam_z,
                 look_x, look_y, look_z,
                 0, 1, 0)
        
        # Draw game world
        draw_ground()
        draw_woody()
        
        for enemy in enemies:
            draw_enemy(enemy)
            
        for boss in bosses:
            draw_boss(boss)
            
        for collectible in collectibles:
            draw_collectible(collectible)
            
        for cage in cages:
            draw_cage(cage)
            
        draw_special_effects()
    
    # Always draw UI last
    draw_ui()
    
    glutSwapBuffers()

# Update game logic
def update(value):
    global current_state, score, lives, level_start_time
    
    # Handle player jumping
    if player.is_jumping:
        player.jump_height += player.jump_velocity
        player.jump_velocity -= 0.5  # Gravity
        if player.jump_height <= 0:
            player.jump_height = 0
            player.is_jumping = False
            player.jump_velocity = 0
    
    # Handle lasso attack timer
    if player.lasso_attack:
        player.lasso_timer += 1
        if player.lasso_timer > 30:  # 0.5 seconds at 60 FPS
            player.lasso_attack = False
            player.lasso_timer = 0
    
    # Update collectible rotation
    for item in collectibles:
        if item.active:
            item.rotation = (item.rotation + 2) % 360
    
    # Update enemy movement
    for enemy in enemies[:]:
        if enemy.active:
            # Move toward player
            dx = player.x - enemy.x
            dz = player.z - enemy.z
            distance = (dx**2 + dz**2)**0.5
            
            if distance > 0:
                enemy.x += (dx / distance) * enemy.speed
                enemy.z += (dz / distance) * enemy.speed
            
            # Check collision with player
            if distance < 15:
                player.health -= 5
                enemy.active = False
                if player.health <= 0:
                    lives -= 1
                    player.health = 100
                    if lives <= 0:
                        current_state = GameState.GAME_OVER
            
            # Check if hit by lasso
            if player.lasso_attack and distance < 30:
                enemy.health -= 25
                enemy.hit_timer = 10
                if enemy.health <= 0:
                    enemy.active = False
                    score += 100
    
    # Update boss logic
    for boss in bosses:
        if boss.active:
            # Check if hit by lasso
            dx = player.x - boss.x
            dz = player.z - boss.z
            distance = (dx**2 + dz**2)**0.5
            
            if player.lasso_attack and distance < 40:
                boss.health -= 20
                if boss.health <= 0:
                    boss.active = False
                    score += 500
    
    # Update collectible collection
    for item in collectibles[:]:
        if item.active:
            dx = player.x - item.x
            dz = player.z - item.z
            distance = (dx**2 + dz**2)**0.5
            
            if distance < 15:
                item.active = False
                if item.type == "star":
                    score += 50
                elif item.type == "hat":
                    lives = min(lives + 1, 20)  # Cap at 20 lives
    
    # Update special effects
    for effect in special_effects[:]:
        effect["timer"] -= 1
        if effect["timer"] <= 0:
            special_effects.remove(effect)
    
    # Check level completion
    if current_state == GameState.LEVEL_1:
        if bosses and not bosses[0].active and cages:
            # Move to level 2
            current_state = GameState.LEVEL_2
            init_level_2()
            level_start_time = time.time()
            player.x = player.y = player.z = 0
            player.rotation = 0
            player.health = 100
    
    elif current_state == GameState.LEVEL_2:
        if bosses and not bosses[0].active and cages:
            # Move to level 3
            current_state = GameState.LEVEL_3
            init_level_3()
            level_start_time = time.time()
            player.x = player.y = player.z = 0
            player.rotation = 0
            player.health = 100
    
    elif current_state == GameState.LEVEL_3:
        if bosses and not bosses[0].active and cages:
            # Game completed
            current_state = GameState.WIN_SCREEN
    
    # Check time limits
    elapsed = time.time() - level_start_time
    if current_state == GameState.LEVEL_1 and elapsed > 300:  # 5 minutes
        current_state = GameState.GAME_OVER
    elif current_state == GameState.LEVEL_2 and elapsed > 420:  # 7 minutes
        current_state = GameState.GAME_OVER
    elif current_state == GameState.LEVEL_3 and elapsed > 600:  # 10 minutes
        current_state = GameState.GAME_OVER
    
    glutPostRedisplay()
    glutTimerFunc(1000//FPS, update, 0)

# Keyboard input handler
def keyboard(key, x, y):
    global current_state
    
    key = key.decode('utf-8')
    
    if current_state in [GameState.GAME_OVER, GameState.WIN_SCREEN]:
        if key == 'r' or key == 'R':
            # Restart game
            current_state = GameState.LEVEL_1
            init_level_1()
            global score, lives, player
            score = 0
            lives = 10
            player = Player()
            level_start_time = time.time()
        return
    
    if key == 'j' or key == 'J':
        if not player.is_jumping:
            player.is_jumping = True
            player.jump_velocity = 10
    
    elif key == 'l' or key == 'L':
        if not player.lasso_attack:
            player.lasso_attack = True
    
    elif key == 'a' or key == 'A':
        if current_state >= GameState.LEVEL_2:
            # Jessie freeze special move
            special_effects.append({
                "type": "jessie_freeze",
                "x": player.x,
                "y": player.y + 20,
                "z": player.z,
                "radius": 50,
                "timer": 180  # 3 seconds at 60 FPS
            })
            # Freeze enemies
            for enemy in enemies:
                enemy.speed = 0
    
    elif key == 's' or key == 'S':
        if current_state == GameState.LEVEL_3:
            # Buzz laser special move
            special_effects.append({
                "type": "buzz_laser",
                "x": player.x,
                "y": player.y + 15,
                "z": player.z,
                "length": 100,
                "timer": 60  # 1 second at 60 FPS
            })
            # Damage all enemies
            for enemy in enemies[:]:
                enemy.health = 0
                enemy.active = False
                score += 100
            # Damage boss
            for boss in bosses:
                if boss.active:
                    boss.health -= boss.health * 0.2  # 20% damage

# Special keys for movement
def special_keys(key, x, y):
    if current_state in [GameState.GAME_OVER, GameState.WIN_SCREEN]:
        return
    
    if key == GLUT_KEY_UP:
        # Move forward
        player.x += player.speed * sin(player.rotation * 3.14159 / 180)
        player.z += player.speed * cos(player.rotation * 3.14159 / 180)
    
    elif key == GLUT_KEY_DOWN:
        # Move backward
        player.x -= player.speed * sin(player.rotation * 3.14159 / 180)
        player.z -= player.speed * cos(player.rotation * 3.14159 / 180)
    
    elif key == GLUT_KEY_LEFT:
        # Turn left
        player.rotation += player.rotation_speed
    
    elif key == GLUT_KEY_RIGHT:
        # Turn right
        player.rotation -= player.rotation_speed

# Mouse handler (not used but required by GLUT)
def mouse(button, state, x, y):
    pass

# Main function
def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIDTH, HEIGHT)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Toy Story Adventure")
    
    init()
    
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutMouseFunc(mouse)
    glutIdleFunc(lambda: None)  # Using timer instead for better control
    glutTimerFunc(1000//FPS, update, 0)
    
    glutMainLoop()

if __name__ == "__main__":
    main()
