import pygame
import sys
import random
import math
import array

# Initialize Pygame engine and mixer
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# --- Configuration & Geometry ---
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600  
FPS = 60

# Cyberpunk & Cosmic Neon Color Palette
BLACK = (3, 3, 8)
DARK_GRAY = (18, 20, 28)
CMD_BG = (5, 6, 10)
NEON_CYAN = (0, 255, 255)
NEON_LIME = (50, 255, 50)
NEON_RED = (255, 40, 80)
NEON_ORANGE = (255, 110, 0)
NEON_PURPLE = (180, 0, 255)
BULLET_BRASS = (225, 180, 60) 
WHITE = (240, 240, 255)

# Setup Display Context
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("SPACE DASH: AK-47 Overdrive")
clock = pygame.time.Clock()

# --- Typography (Fonts) ---
try:
    font_main = pygame.font.SysFont("Consolas", 24, bold=True)
    font_small = pygame.font.SysFont("Courier New", 15, bold=True)
except:
    font_main = pygame.font.Font(None, 28)
    font_small = pygame.font.Font(None, 16)

# --- Procedural Audio Generator ---
def generate_shoot_sound():
    duration = 0.1  
    sample_rate = 22050
    num_samples = int(duration * sample_rate)
    buf = array.array('h', [0] * num_samples)
    for i in range(num_samples):
        t = i / sample_rate
        freq = 800 - (t * 6000)
        freq = max(100, freq)
        val = math.sin(2 * math.pi * freq * t) * 0.7 + random.uniform(-0.3, 0.3)
        buf[i] = int(val * (1.0 - t / duration) * 16383)
    return pygame.mixer.Sound(buffer=buf)

def generate_missile_sound():
    duration = 0.3  
    sample_rate = 22050
    num_samples = int(duration * sample_rate)
    buf = array.array('h', [0] * num_samples)
    for i in range(num_samples):
        t = i / sample_rate
        freq = 200 + (t * 800) # Upward bass sweep
        val = math.sin(2 * math.pi * freq * t) * 0.5 + random.uniform(-0.4, 0.4)
        buf[i] = int(val * (1.0 - t / duration) * 20000)
    return pygame.mixer.Sound(buffer=buf)

def generate_explosion_sound():
    duration = 0.8  
    sample_rate = 22050
    num_samples = int(duration * sample_rate)
    buf = array.array('h', [0] * num_samples)
    for i in range(num_samples):
        t = i / sample_rate
        val = random.uniform(-1.0, 1.0)
        buf[i] = int(val * math.exp(-4.0 * t) * 24575)
    return pygame.mixer.Sound(buffer=buf)

snd_shoot = generate_shoot_sound()
snd_missile = generate_missile_sound()
snd_explosion = generate_explosion_sound()

# --- Procedural Graphic Vector Asset Generation ---
def generate_player_craft(color, width, height):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.polygon(surf, (0, 255, 255, 40), [(width//2, 0), (width, height-15), (0, height-15)], width=4)
    pygame.draw.polygon(surf, DARK_GRAY, [(10, 30), (25, 10), (35, height-10), (5, height-10)])
    pygame.draw.polygon(surf, DARK_GRAY, [(width-10, 30), (width-25, 10), (width-35, height-10), (width-5, height-10)])
    pygame.draw.polygon(surf, color, [(10, 30), (25, 10), (35, height-10), (5, height-10)], width=2)
    pygame.draw.polygon(surf, color, [(width-10, 30), (width-25, 10), (width-35, height-10), (width-5, height-10)], width=2)
    pygame.draw.polygon(surf, (40, 45, 55), [(width//2, 5), (width-30, height-20), (30, height-20)])
    pygame.draw.polygon(surf, WHITE, [(width//2, 5), (width-30, height-20), (30, height-20)], width=2)
    pygame.draw.circle(surf, NEON_PURPLE, (width//2, height//2 + 10), 8)
    pygame.draw.circle(surf, NEON_CYAN, (width//2, height//2 + 10), 4)
    return surf

def generate_hostile_drone(color, width, height):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.polygon(surf, color, [(width//2, height), (width, 0), (0, 0)])
    pygame.draw.polygon(surf, (15, 15, 22), [(width//2, height-12), (width-10, 4), (10, 4)])
    pygame.draw.circle(surf, NEON_ORANGE, (width//2, height//2 - 5), 6)
    return surf

# Dimensions
craft_width, craft_height = 80, 105
player_craft = generate_player_craft(NEON_CYAN, craft_width, craft_height)
hostile_drone_normal = generate_hostile_drone(NEON_RED, 65, 85)
hostile_drone_elite = generate_hostile_drone(NEON_PURPLE, 85, 105) # Stronger, bigger obstacle

# --- Initial Game Metrics & Telemetry ---
score = 0
gear = 1
current_speed = 20.0
target_speed = 20.0
missiles_left = 10

SPACE_LEFT = 500
SPACE_RIGHT = SCREEN_WIDTH - 40

player_x = (SPACE_LEFT + SPACE_RIGHT) // 2 - craft_width // 2
player_y = SCREEN_HEIGHT - craft_height - 40
player_velocity_x = 0
player_speed_side = 9

starfield = [{"x": random.randint(SPACE_LEFT, SCREEN_WIDTH), "y": random.randint(0, SCREEN_HEIGHT), "speed": random.uniform(1.5, 6.0)} for _ in range(80)]
thrust_particles = []
trail_ghosts = [] 
bullets = []
missiles = []
explosions = [] 
muzzle_flashes = []
obstacles = []
obstacle_spawn_timer = 0
obstacle_spawn_rate = 50

def draw_hud():
    hud_x = SCREEN_WIDTH - 220
    pygame.draw.rect(screen, DARK_GRAY, (hud_x - 10, 20, 215, 260), border_radius=12)
    pygame.draw.rect(screen, NEON_PURPLE, (hud_x - 10, 20, 215, 260), width=2, border_radius=12)
    pygame.draw.line(screen, NEON_CYAN, (hud_x - 10, 65), (hud_x + 205, 65), 1)
    
    header_txt = font_main.render("SPACE RADAR", True, NEON_CYAN)
    score_txt = font_main.render(f"SCORE: {int(score)}", True, WHITE)
    gear_txt = font_main.render(f"WARP:  {gear}/5", True, NEON_LIME if gear < 5 else NEON_RED)
    missile_txt = font_main.render(f"MSL:   {missiles_left}/10", True, NEON_CYAN if missiles_left > 0 else NEON_RED)
    speed_lbl = font_small.render("CHRONO VELOCITY:", True, WHITE)
    speed_val = font_main.render(f"{current_speed:.1f} KM/R", True, NEON_ORANGE)
    
    screen.blit(header_txt, (hud_x + 20, 30))
    screen.blit(score_txt, (hud_x, 80))
    screen.blit(gear_txt, (hud_x, 115))
    screen.blit(missile_txt, (hud_x, 150))
    screen.blit(speed_lbl, (hud_x, 195))
    screen.blit(speed_val, (hud_x, 220))

def draw_code_overlay():
    cmd_width = 460
    pygame.draw.rect(screen, CMD_BG, (0, 0, cmd_width, SCREEN_HEIGHT))
    pygame.draw.line(screen, NEON_PURPLE, (cmd_width, 0), (cmd_width, SCREEN_HEIGHT), 4)
    pygame.draw.rect(screen, DARK_GRAY, (0, 0, cmd_width, 35))
    pygame.draw.circle(screen, NEON_RED, (15, 17), 6)
    pygame.draw.circle(screen, NEON_ORANGE, (30, 17), 6)
    pygame.draw.circle(screen, NEON_LIME, (45, 17), 6)
    title_txt = font_small.render("Secure Terminal - ballistic_ak47.py", True, WHITE)
    screen.blit(title_txt, (65, 8))

    console_logs = [
        "SpaceDash CoreEngine v12.1 Operational.",
        "AK-47 Weapon Bay Systems: RUNNING.",
        "--------------------------------------------------",
        f"[TELEMETRY] score_points       == >> {int(score)}",
        f"[ENGINE]    warp_gear_ratio    == >> [ 0{gear} ]",
        f"[HYDRAULIC] warp_velocity_kmr  == >> {current_speed:.4f}",
        f"[MUNITION]  live_rounds_active == >> {len(bullets)} proj",
        f"[TACTICAL]  missiles_remaining == >> [ {missiles_left:02d} ]",
        f"[TRACKER]   detected_debris    == >> {len(obstacles)} objects",
        "",
        "[ONLINE] AK-47 Relay / Missile Pods: READY",
        "",
        ">> COCKPIT INTERFACE COMMANDS:",
        "   [*] STEER SHIP        -> [LEFT / RIGHT ARROW]",
        "   [*] INCREASE WARP     -> [UP / DOWN ARROW]",
        "   [!] FIRE AK-47 BULLET -> [ PRESS F KEY ]",
        "   [??] LAUNCH MISSILE    -> [ PRESS M KEY ]"
    ]
    
    start_x = 15
    start_y = 50
    line_spacing = 22
    for idx, log_line in enumerate(console_logs):
        if "[ONLINE]" in log_line or "COMMANDS" in log_line:
            text_color = NEON_LIME
        elif "==" in log_line or "[*]" in log_line or "[!]" in log_line or "[??]" in log_line:
            text_color = NEON_CYAN
        elif "v12.1" in log_line:
            text_color = NEON_PURPLE
        else:
            text_color = WHITE
        line_surface = font_small.render(log_line, True, text_color)
        screen.blit(line_surface, (start_x, start_y + idx * line_spacing))

def draw_environment():
    screen.fill(BLACK)
    for star in starfield:
        star["y"] += star["speed"] * (current_speed / 35.0)
        if star["y"] > SCREEN_HEIGHT:
            star["y"] = 0
            star["x"] = random.randint(SPACE_LEFT, SCREEN_WIDTH)
        color_val = min(255, int(150 + star["speed"] * 15))
        pygame.draw.circle(screen, (color_val, color_val, 255), (int(star["x"]), int(star["y"])), random.choice([1, 2, 3]))

# --- Core Mechanics Execution Loop ---
is_running = True
is_game_over = False

while is_running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False
        if not is_game_over:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    player_velocity_x = -player_speed_side
                if event.key == pygame.K_RIGHT:
                    player_velocity_x = player_speed_side
                if event.key == pygame.K_UP:
                    gear = min(5, gear + 1)
                if event.key == pygame.K_DOWN:
                    gear = max(1, gear - 1)
                
                # AK-47 Firing Triggers
                if event.key == pygame.K_f:
                    snd_shoot.stop() 
                    snd_shoot.play()
                    bullets.append(pygame.Rect(player_x + 12, player_y + 10, 3, 14))
                    bullets.append(pygame.Rect(player_x + craft_width - 15, player_y + 10, 3, 14))
                    muzzle_flashes.append({"x": player_x + 13, "y": player_y + 5, "timer": 3})
                    muzzle_flashes.append({"x": player_x + craft_width - 14, "y": player_y + 5, "timer": 3})

                # Tactical Missile Launch System
                if event.key == pygame.K_m and missiles_left > 0:
                    snd_missile.play()
                    missiles_left -= 1
                    # Center fired heavy rocket missile
                    missiles.append(pygame.Rect(player_x + craft_width//2 - 6, player_y - 10, 12, 24))

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT and player_velocity_x < 0:
                    player_velocity_x = 0
                if event.key == pygame.K_RIGHT and player_velocity_x > 0:
                    player_velocity_x = 0
        else:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                is_game_over = False
                score = 0
                gear = 1
                missiles_left = 10
                current_speed = 20.0
                player_x = (SPACE_LEFT + SPACE_RIGHT) // 2 - craft_width // 2
                obstacles.clear()
                bullets.clear()
                missiles.clear()
                explosions.clear()
                muzzle_flashes.clear()
                thrust_particles.clear()
                trail_ghosts.clear()

    if not is_game_over:
        gear_velocities_kmr = {1: 25.0, 2: 60.0, 3: 110.0, 4: 175.0, 5: 255.0}
        target_speed = gear_velocities_kmr[gear]
        current_speed += (target_speed - current_speed) * 0.04
        score += (current_speed / 40.0) * 0.15

        player_x += player_velocity_x
        if player_x < SPACE_LEFT + 15: player_x = SPACE_LEFT + 15
        if player_x > SPACE_RIGHT - craft_width - 15: player_x = SPACE_RIGHT - craft_width - 15

        trail_ghosts.append({"x": player_x, "y": player_y, "alpha": 100})
        if len(trail_ghosts) > 4:
            trail_ghosts.pop(0)

        if random.random() < 0.6:
            thrust_particles.append({"x": player_x + 20, "y": player_y + craft_height - 10, "r": random.randint(4, 8), "a": 255})
            thrust_particles.append({"x": player_x + craft_width - 20, "y": player_y + craft_height - 10, "r": random.randint(4, 8), "a": 255})
            
        for particle in thrust_particles[:]:
            particle["y"] += random.uniform(3, 6)
            particle["a"] -= 14
            if particle["a"] <= 0:
                thrust_particles.remove(particle)

        # Update Projectiles
        for bullet in bullets[:]:
            bullet.y -= 24  
            if bullet.y < 0: bullets.remove(bullet)

        for missile in missiles[:]:
            missile.y -= 14  # Missiles accelerate slightly slower but hit harder
            if missile.y < -30: missiles.remove(missile)

        for flash in muzzle_flashes[:]:
            flash["timer"] -= 1
            if flash["timer"] <= 0: muzzle_flashes.remove(flash)

        # Obstacle Generation Engine (Normal vs Powerful Elites)
        obstacle_spawn_timer += 1
        if obstacle_spawn_timer >= obstacle_spawn_rate:
            is_elite = random.random() < 0.20 # 20% spawn rate for ultra strong ships
            
            if is_elite:
                drone_w, drone_h = 85, 105
                max_hp = random.randint(8, 12) + gear # High HP armor tier
                points = 600
            else:
                drone_w, drone_h = 65, 85
                max_hp = random.randint(2, 3) + (gear // 2)
                points = 250

            spawn_x = random.randint(SPACE_LEFT + 30, SPACE_RIGHT - drone_w - 30)
            obstacles.append({
                "rect": pygame.Rect(spawn_x, -110, drone_w, drone_h),
                "hp": max_hp,
                "max_hp": max_hp,
                "is_elite": is_elite,
                "points": points
            })
            obstacle_spawn_timer = 0
            obstacle_spawn_rate = max(18, random.randint(30, 65) - (gear * 6))

        for drone_data in obstacles[:]:
            drone = drone_data["rect"]
            drone.y += (current_speed / 9.0) + (3.0 if not drone_data["is_elite"] else 2.0)
            if drone.y > SCREEN_HEIGHT:
                obstacles.remove(drone_data)
                score += 30  

        # --- Bullet Collisions Handling ---
        for bullet in bullets[:]:
            for drone_data in obstacles[:]:
                drone = drone_data["rect"]
                if bullet.colliderect(drone):
                    drone_data["hp"] -= 5 # Bullet Deal 5 units of damage
                    for _ in range(4):
                        explosions.append({
                            "x": bullet.x, "y": bullet.y, "r": random.randint(2, 4), "a": 255,
                            "vx": random.uniform(-3, 3), "vy": random.uniform(-4, 1)
                        })
                    if bullet in bullets: bullets.remove(bullet)
                    
                    if drone_data["hp"] <= 0:
                        snd_explosion.play()
                        for _ in range(25 if drone_data["is_elite"] else 15):
                            explosions.append({
                                "x": drone.centerx, "y": drone.centery, "r": random.randint(5, 10), "a": 255,
                                "vx": random.uniform(-7, 7), "vy": random.uniform(-8, 3)
                            })
                        score += drone_data["points"]
                        if drone_data in obstacles: obstacles.remove(drone_data)
                    break

        # --- Heavy Missile Collisions Handling ---
        for missile in missiles[:]:
            for drone_data in obstacles[:]:
                drone = drone_data["rect"]
                if missile.colliderect(drone):
                    drone_data["hp"] -= 35 # Missile Deal 35 units of massive kinetic damage payload!
                    snd_explosion.play()
                    
                    # Large missile cluster payload explosion
                    for _ in range(20):
                        explosions.append({
                            "x": missile.centerx, "y": missile.y, "r": random.randint(4, 9), "a": 255,
                            "vx": random.uniform(-6, 6), "vy": random.uniform(-6, 6)
                        })
                    if missile in missiles: missiles.remove(missile)
                    
                    if drone_data["hp"] <= 0:
                        for _ in range(35 if drone_data["is_elite"] else 15):
                            explosions.append({
                                "x": drone.centerx, "y": drone.centery, "r": random.randint(6, 12), "a": 255,
                                "vx": random.uniform(-9, 9), "vy": random.uniform(-9, 4)
                            })
                        score += drone_data["points"]
                        if drone_data in obstacles: obstacles.remove(drone_data)
                    break

        # Hull Breach Crash Detection Sequence
        player_hitbox = pygame.Rect(player_x + 12, player_y + 10, craft_width - 24, craft_height - 15)
        for drone_data in obstacles:
            drone = drone_data["rect"]
            if player_hitbox.colliderect(drone):
                is_game_over = True
                snd_explosion.play()  
                for _ in range(80):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(2, 13)
                    explosions.append({
                        "x": player_x + craft_width // 2, "y": player_y + craft_height // 2,
                        "r": random.randint(5, 13), "a": 255,
                        "vx": math.cos(angle) * speed, "vy": math.sin(angle) * speed
                    })

    # Particle physics
    for exp in explosions[:]:
        exp["x"] += exp["vx"]
        exp["y"] += exp["vy"]
        exp["a"] -= 8  
        if exp["a"] <= 0: explosions.remove(exp)

    # --- 4. Graphic Framework Render Layer Stack ---
    draw_environment()
    
    if not is_game_over:
        for idx, ghost in enumerate(trail_ghosts):
            alpha_surf = pygame.Surface((craft_width, craft_height), pygame.SRCALPHA)
            alpha_surf.blit(player_craft, (0, 0))
            alpha_surf.fill((255, 255, 255, int(ghost["alpha"] * (idx / len(trail_ghosts)))), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(alpha_surf, (ghost["x"], ghost["y"]))

        for particle in thrust_particles:
            p_layer = pygame.Surface((particle["r"]*2, particle["r"]*2), pygame.SRCALPHA)
            pygame.draw.circle(p_layer, (NEON_ORANGE[0], NEON_ORANGE[1], NEON_ORANGE[2], particle["a"]), (particle["r"], particle["r"]), particle["r"])
            screen.blit(p_layer, (particle["x"] - particle["r"], particle["y"] - particle["r"]))
        
    for bullet in bullets:
        pygame.draw.rect(screen, BULLET_BRASS, bullet, border_radius=1)
        pygame.draw.line(screen, WHITE, (bullet.centerx, bullet.y + 2), (bullet.centerx, bullet.bottom - 2), 1)

    for missile in missiles:
        # Draw dynamic tracking missile rocket
        pygame.draw.rect(screen, NEON_CYAN, missile, border_radius=4)
        pygame.draw.rect(screen, NEON_ORANGE, (missile.centerx - 3, missile.bottom, 6, 8)) # Missile Fire Exhaust Tail

    for flash in muzzle_flashes:
        pygame.draw.circle(screen, WHITE, (flash["x"], flash["y"]), random.randint(5, 10))
        pygame.draw.circle(screen, NEON_ORANGE, (flash["x"], flash["y"]), random.randint(2, 5))

    for drone_data in obstacles:
        drone = drone_data["rect"]
        if drone_data["is_elite"]:
            screen.blit(hostile_drone_elite, (drone.x, drone.y))
        else:
            screen.blit(hostile_drone_normal, (drone.x, drone.y))
            
        bar_w = drone.width
        bar_h = 6
        bar_x = drone.x
        bar_y = drone.y - 14
        health_ratio = max(0, drone_data["hp"] / drone_data["max_hp"])
        pygame.draw.rect(screen, (80, 10, 20), (bar_x, bar_y, bar_w, bar_h))
        # Color bar based on elite status
        bar_color = NEON_PURPLE if drone_data["is_elite"] else NEON_LIME
        pygame.draw.rect(screen, bar_color, (bar_x, bar_y, int(bar_w * health_ratio), bar_h))

    if not is_game_over:
        screen.blit(player_craft, (player_x, player_y))

    for exp in explosions:
        exp_surf = pygame.Surface((exp["r"]*2, exp["r"]*2), pygame.SRCALPHA)
        color_g = random.randint(100, 240) if exp["a"] > 150 else random.randint(30, 100)
        pygame.draw.circle(exp_surf, (255, color_g, 20, exp["a"]), (exp["r"], exp["r"]), exp["r"])
        screen.blit(exp_surf, (exp["x"] - exp["r"], exp["y"] - exp["r"]))

    draw_code_overlay()
    draw_hud()

    if is_game_over:
        dim_mask = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim_mask.fill((0, 0, 0, 180)) 
        screen.blit(dim_mask, (0, 0))
        
        fail_msg = font_main.render("CRITICAL HULL FAILURE: VESSEL DESTROYED", True, NEON_RED)
        retry_msg = font_small.render("Please press SPACE BAR to reboot console systems", True, WHITE)
        screen.blit(fail_msg, (SCREEN_WIDTH // 2 - fail_msg.get_width() // 2, SCREEN_HEIGHT // 2 - 25))
        screen.blit(retry_msg, (SCREEN_WIDTH // 2 - retry_msg.get_width() // 2, SCREEN_HEIGHT // 2 + 25))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()