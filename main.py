# """
# INITIAL D - COMPLETE EDITION (Pico World Race Style)
# =====================================================
# A complete OutRun-style pseudo-3D racer using strictly PyOpenGL immediate mode.
# Implements all required features for CSE423 Project.

# Team Members:
# - SAYED KAFI (23101135): Procedural Track, Drift Physics, Objects, Dual Camera, HUD
# - MD. MEHEDI HASAN TAMIM (23101370): Terrain Friction, Turbo Zones, Animated HUD, Leaderboard, Mini-map
# - MD ABDULLAH AL HASSAN (23101455): Dynamic Headlights, Skybox, Particle System, Day/Night Cycle

# ENHANCED FEATURES:
# - Larger collectibles with counter display
# - Boost system (20 points, left mouse click)
# - Respawn system (50 points after collision)
# - Blue flame boost animation (TPP & FPP)
# - Full-screen boost speed effects
# - Aggressive AI that blocks and overtakes
# - More trees and bushes on track sides
# - Wider track (ROAD_WIDTH = 1.8)
# - Position numbers on minimap for all cars
# - Checkered finish line (black/white)
# - Extended race time (1min 30sec target)
# - AI speed relative to player performance
# - Fixed HUD layout (no overlapping elements)
# """

import json
import math
import os
import random
import sys
import time

# STRICT OpenGL COMPLIANCE: Only allowed functions from STRICT_OPENGL_COMPLIANCE.md
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_LINES,
    GL_MODELVIEW,
    GL_PROJECTION,
    GL_QUADS,
    glBegin,
    glClear,
    glClearColor,
    glColor3f,
    glEnd,
    glLineWidth,
    glLoadIdentity,
    glMatrixMode,
    glOrtho,
    glVertex2f,
    glViewport,
)
from OpenGL.GLUT import (
    GLUT_DOUBLE,
    GLUT_KEY_DOWN,
    GLUT_KEY_LEFT,
    GLUT_KEY_RIGHT,
    GLUT_KEY_UP,
    GLUT_LEFT_BUTTON,
    GLUT_DOWN,
    GLUT_RGBA,
    glutCreateWindow,
    glutDisplayFunc,
    glutIdleFunc,
    glutInit,
    glutInitDisplayMode,
    glutInitWindowPosition,
    glutInitWindowSize,
    glutKeyboardFunc,
    glutMainLoop,
    glutMouseFunc,
    glutPostRedisplay,
    glutReshapeFunc,
    glutSpecialFunc,
    glutSwapBuffers,
)

# =============================================================================
# CONSTANTS
# =============================================================================

WIDTH = 1024
HEIGHT = 768
TITLE = b"INITIAL D - COMPLETE EDITION"

# Track geometry - WIDER TRACK
SEGMENT_LENGTH = 200.0
ROAD_WIDTH = 1.8  # Increased from 1.5 for wider track
DRAW_DISTANCE = 250
TOTAL_SEGMENTS = 2000
TRACK_LENGTH = SEGMENT_LENGTH * TOTAL_SEGMENTS

# Camera
CAMERA_HEIGHT = 1000.0
CAMERA_DEPTH = 0.84
ROAD_PROJECTION_SCALE = WIDTH * 230.0
CURVE_PROJECTION_SCALE = 0.75

# Physics - Arcade style with drift emphasis
MAX_SPEED = 240.0
ACCEL_RATE = 100.0
BRAKE_RATE = 180.0
FRICTION_RATE = 25.0
OFFROAD_FRICTION = 80.0
STEER_STRENGTH = 2.8
CENTRIFUGAL_FACTOR = 0.32
DRIFT_FACTOR = 0.45

# Game rules
NUM_LAPS = 4
NUM_AI = 8
NUM_TOKENS = 250
NUM_PROPS = 280  # Increased for more vegetation
NUM_BOOST_ZONES = 30
RACE_TARGET_SECONDS = 90.0  # 1min 30sec target

# Spendable point abilities
BOOST_COST = 20
RESPAWN_COST = 50
BOOST_DURATION = 1.5
BOOST_ACCEL_BONUS = 220.0
BOOST_SPEED_CAP = 340.0
RESPAWN_PROMPT_DURATION = 2.5
RESPAWN_INVULN_DURATION = 1.2

# Collision detection
COLLISION_TOKEN_DZ = 0.8
COLLISION_TOKEN_DX = 0.25
COLLISION_PROP_DZ = 0.6
COLLISION_PROP_DX = 0.25
COLLISION_AI_DZ = 0.6
COLLISION_AI_DX = 0.28

# Timekeeping
HOLD_TIMEOUT = 0.15
FPS_TARGET = 60
DT_MAX = 0.05

# Profile persistence
PROFILE_FILE = "initial_d_profile.json"
BASE_UNLOCK_TOKENS = 12

# Level presets: (name, seed, curve_scale, hill_scale, atmosphere_type)
LEVEL_PRESETS = [
    ("CITY",       1,  1.00, 0.50, "urban"),
    ("DESERT",     4,  0.80, 0.30, "hot"),
    ("MOUNTAIN",   8,  1.20, 1.20, "cool"),
    ("COASTAL",   13,  1.10, 0.70, "breeze"),
    ("FOREST",    17,  0.90, 0.80, "nature"),
    ("CANYON",    22,  1.40, 1.00, "dramatic"),
]

# Difficulty presets
DIFFICULTY_PRESETS = [
    ("EASY",   0.75),
    ("NORMAL", 1.00),
    ("HARD",   1.25),
    ("EXPERT", 1.45),
]

# Color palettes per location (Pico World Race style - vibrant, simplified)
LOCATION_PALETTES = {
    "CITY": {
        "sky_day": (0.4, 0.6, 0.9), "sky_night": (0.1, 0.1, 0.25),
        "grass1": (0.3, 0.7, 0.3), "grass2": (0.2, 0.6, 0.2),
        "road1": (0.5, 0.5, 0.5), "road2": (0.4, 0.4, 0.4),
        "skyline": (0.3, 0.3, 0.4), "building": (0.4, 0.4, 0.5),
        "rumble_l": (0.9, 0.9, 0.9), "rumble_d": (0.8, 0.2, 0.2),
        "boost": (0.2, 0.8, 0.9), "token": (0.95, 0.8, 0.1),
    },
    "DESERT": {
        "sky_day": (0.9, 0.7, 0.4), "sky_night": (0.2, 0.15, 0.3),
        "grass1": (0.8, 0.7, 0.4), "grass2": (0.7, 0.6, 0.3),
        "road1": (0.6, 0.5, 0.4), "road2": (0.5, 0.4, 0.3),
        "skyline": (0.5, 0.4, 0.2), "building": (0.6, 0.5, 0.3),
        "rumble_l": (0.9, 0.8, 0.6), "rumble_d": (0.8, 0.5, 0.2),
        "boost": (0.3, 0.7, 0.9), "token": (0.9, 0.7, 0.2),
    },
    "MOUNTAIN": {
        "sky_day": (0.7, 0.8, 0.9), "sky_night": (0.15, 0.2, 0.3),
        "grass1": (0.5, 0.6, 0.4), "grass2": (0.4, 0.5, 0.3),
        "road1": (0.5, 0.5, 0.5), "road2": (0.4, 0.4, 0.4),
        "skyline": (0.4, 0.5, 0.6), "building": (0.5, 0.55, 0.6),
        "rumble_l": (0.8, 0.8, 0.9), "rumble_d": (0.3, 0.4, 0.6),
        "boost": (0.2, 0.75, 0.85), "token": (0.92, 0.75, 0.15),
    },
    "COASTAL": {
        "sky_day": (0.5, 0.7, 0.9), "sky_night": (0.1, 0.15, 0.3),
        "grass1": (0.4, 0.7, 0.4), "grass2": (0.3, 0.6, 0.3),
        "road1": (0.5, 0.5, 0.5), "road2": (0.4, 0.4, 0.4),
        "skyline": (0.2, 0.3, 0.5), "building": (0.3, 0.4, 0.55),
        "rumble_l": (0.8, 0.8, 0.9), "rumble_d": (0.2, 0.4, 0.7),
        "boost": (0.25, 0.7, 0.8), "token": (0.9, 0.8, 0.1),
    },
    "FOREST": {
        "sky_day": (0.6, 0.75, 0.85), "sky_night": (0.1, 0.18, 0.25),
        "grass1": (0.2, 0.65, 0.25), "grass2": (0.15, 0.55, 0.2),
        "road1": (0.45, 0.45, 0.45), "road2": (0.35, 0.35, 0.35),
        "skyline": (0.15, 0.35, 0.2), "building": (0.2, 0.3, 0.25),
        "rumble_l": (0.85, 0.85, 0.85), "rumble_d": (0.7, 0.3, 0.2),
        "boost": (0.3, 0.8, 0.7), "token": (0.88, 0.72, 0.12),
    },
    "CANYON": {
        "sky_day": (0.8, 0.65, 0.5), "sky_night": (0.25, 0.15, 0.2),
        "grass1": (0.6, 0.5, 0.35), "grass2": (0.5, 0.4, 0.25),
        "road1": (0.55, 0.5, 0.45), "road2": (0.45, 0.4, 0.35),
        "skyline": (0.55, 0.35, 0.25), "building": (0.6, 0.4, 0.3),
        "rumble_l": (0.9, 0.85, 0.75), "rumble_d": (0.75, 0.35, 0.25),
        "boost": (0.35, 0.75, 0.8), "token": (0.95, 0.7, 0.15),
    },
}

# =============================================================================
# GLOBAL STATE
# =============================================================================

camera = {"x": 0.0, "y": CAMERA_HEIGHT, "z": 0.0, "depth": CAMERA_DEPTH}
player = {"speed": 0.0, "max_speed": MAX_SPEED, "x": 0.0, "z": 0.0, "lap": 0}
controls = {"up": False, "down": False, "left": False, "right": False}
control_until = {"up": 0.0, "down": 0.0, "left": 0.0, "right": 0.0}
score = {
    "tokens": 0,
    "hits": 0,
    "overtakes": 0,
    "drifts": 0,
    "boost_used": 0,
    "respawns": 0,
}
race = {
    "laps": 0,
    "max_laps": NUM_LAPS,
    "lap_start": 0.0,
    "lap_times": [],
    "done": False,
    "start_time": 0.0,
    "lap_armed": False,
}
camera_mode = "tpp"  # "tpp" (third-person chase) or "fpp" (first-person steer)
boost_zones = []
particles = []
world_time = 0.0
atmosphere = {"time": 0.0, "brightness": 1.0, "is_night": False, "phase": "day"}
player_heading = 0.0
last_player_x = 0.0
last_time = 0.0
quit_requested = False
segments = []
tokens = []
props = []
opponents = []
minimap_points = []

# Game state machine
game_state = "menu"
menu_option = 0
pause_option = 0
finish_option = 0
countdown_timer = 0.0
banner_text = ""
banner_timer = 0.0
speedometer_angle = 0.0

# Level/profile state
level_index = 0
level_name = "CITY"
difficulty_index = 1
ai_count = NUM_AI
total_tokens_bank = 0
best_times = {}
best_lap_times = {}
ghost_laps = {}
unlocked_levels = 1
sound_on = True
music_on = True
keybinds = {"throttle": "w", "brake": "s", "left": "a", "right": "d"}
waiting_for_bind = None

# Ghost replay system
current_lap_trace = []
last_lap_frame_mark = 0
race_frame = 0

# Drift tracking
drift_combo = 0
max_drift_combo = 0
drift_score = 0
boost_active_timer = 0.0
boost_flash_timer = 0.0
respawn_prompt_timer = 0.0
respawn_invuln_timer = 0.0
last_collision_source = ""

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def clamp(v, lo, hi):
    """Clamp value between lo and hi."""
    return lo if v < lo else hi if v > hi else v

def wrap_z(z):
    """Wrap z coordinate to track length."""
    while z >= TRACK_LENGTH:
        z -= TRACK_LENGTH
    while z < 0:
        z += TRACK_LENGTH
    return z

def lerp_color(c1, c2, t):
    """Linear interpolate between two RGB colors."""
    t = clamp(t, 0.0, 1.0)
    return (
        c1[0] + (c2[0] - c1[0]) * t,
        c1[1] + (c2[1] - c1[1]) * t,
        c1[2] + (c2[2] - c1[2]) * t,
    )

def current_palette():
    """Get the current location palette."""
    return LOCATION_PALETTES.get(level_name, LOCATION_PALETTES["CITY"])

def day_night_mix():
    """Calculate day/night cycle blend factor (0=night, 1=day)."""
    return atmosphere["brightness"]

def update_atmosphere(dt):
    """
    Day/Night Cycle - Master clock for game world.
    Time Progression: Scales infinitely between 0.0 and 1.0.
    Cosine Mapping: Maps linear time to 360-degree wave.
    Visibility Floor: Guarantees ambient light never drops below 0.2.
    """
    atmosphere["time"] = (atmosphere["time"] + dt * 0.015) % 1.0
    brightness = (math.cos(atmosphere["time"] * 2.0 * math.pi) + 1.0) * 0.5
    atmosphere["brightness"] = max(0.2, brightness)
    atmosphere["is_night"] = atmosphere["brightness"] < 0.45

    # Determine phase name
    if atmosphere["brightness"] > 0.7:
        atmosphere["phase"] = "day"
    elif atmosphere["brightness"] > 0.45:
        atmosphere["phase"] = "dusk"
    elif atmosphere["brightness"] > 0.3:
        atmosphere["phase"] = "night"
    else:
        atmosphere["phase"] = "dawn"

# =============================================================================
# DRAWING PRIMITIVES (STRICT IMMEDIATE MODE)
# =============================================================================

def quad(x1, y1, x2, y2, color):
    """Draw an axis-aligned quad."""
    glColor3f(color[0], color[1], color[2])
    glBegin(GL_QUADS)
    glVertex2f(x1, y1)
    glVertex2f(x2, y1)
    glVertex2f(x2, y2)
    glVertex2f(x1, y2)
    glEnd()

def gradient_quad(x1, y1, x2, y2, bottom_color, top_color):
    """Draw a vertical gradient quad using per-vertex colors."""
    glBegin(GL_QUADS)
    glColor3f(bottom_color[0], bottom_color[1], bottom_color[2])
    glVertex2f(x1, y1)
    glVertex2f(x2, y1)
    glColor3f(top_color[0], top_color[1], top_color[2])
    glVertex2f(x2, y2)
    glVertex2f(x1, y2)
    glEnd()

def trapezoid(x1, y1, w1, x2, y2, w2, color):
    """Draw a trapezoid (for perspective road segments)."""
    glColor3f(color[0], color[1], color[2])
    glBegin(GL_QUADS)
    glVertex2f(x1 - w1, y1)
    glVertex2f(x1 + w1, y1)
    glVertex2f(x2 + w2, y2)
    glVertex2f(x2 - w2, y2)
    glEnd()

def line(x1, y1, x2, y2, color):
    """Draw a line segment."""
    glColor3f(color[0], color[1], color[2])
    glBegin(GL_LINES)
    glVertex2f(x1, y1)
    glVertex2f(x2, y2)
    glEnd()

def draw_circle_outline(cx, cy, radius, color, segments=16):
    """Draw a circle outline using 2D vertices (GL_LINES)."""
    glColor3f(color[0], color[1], color[2])
    glBegin(GL_LINES)
    for i in range(segments):
        a1 = (i / segments) * 2.0 * math.pi
        a2 = ((i + 1) / segments) * 2.0 * math.pi
        x1 = cx + math.cos(a1) * radius
        y1 = cy + math.sin(a1) * radius
        x2 = cx + math.cos(a2) * radius
        y2 = cy + math.sin(a2) * radius
        glVertex2f(x1, y1)
        glVertex2f(x2, y2)
    glEnd()

# =============================================================================
# BLOCK TEXT RENDERING
# =============================================================================

FONT_GLYPHS = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "10010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10001", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10010", "10001", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "01010", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "01010", "00100", "00100", "00100", "01010", "10001"],
    "Y": ["10001", "01010", "00100", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10011", "10101", "10101", "10101", "11001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "00110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "00001", "11110"],
    "6": ["01111", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "11110"],
    ":": ["00000", "00100", "00000", "00000", "00000", "00100", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "00000", "00100"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    ">": ["10000", "01000", "00100", "00010", "00100", "01000", "10000"],
    "<": ["00001", "00010", "00100", "01000", "00100", "00010", "00001"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "'": ["00100", "00100", "00000", "00000", "00000", "00000", "00000"],
    "_": ["00000", "00000", "00000", "00000", "00000", "00000", "11111"],
    "=": ["00000", "00000", "11111", "00000", "11111", "00000", "00000"],
}

def draw_block_char(x, y, unit, ch, color):
    """Draw a single block character."""
    rows = FONT_GLYPHS.get(ch.upper(), FONT_GLYPHS[" "])
    glColor3f(color[0], color[1], color[2])
    glBegin(GL_QUADS)
    for ry, row in enumerate(rows):
        for rx, bit in enumerate(row):
            if bit == "1":
                px = x + rx * unit
                py = y + (6 - ry) * unit
                glVertex2f(px, py)
                glVertex2f(px + unit, py)
                glVertex2f(px + unit, py + unit)
                glVertex2f(px, py + unit)
    glEnd()

def draw_text(x, y, unit, text, color):
    """Draw a text string."""
    cursor = x
    for ch in text:
        draw_block_char(cursor, y, unit, ch, color)
        cursor += unit * 6

def draw_number(x, y, size, value, digits, color):
    """Draw a zero-padded number."""
    v = max(0, int(value))
    text = str(v).rjust(digits, "0")[-digits:]
    draw_text(x, y, size, text, color)

def draw_time_mmss_cc(x, y, size, seconds, color):
    """Draw time in MM:SS.cc format."""
    total_cs = max(0, int(seconds * 100))
    minutes = total_cs // 6000
    rem = total_cs % 6000
    secs = rem // 100
    cs = rem % 100
    text = f"{minutes}:{secs:02d}.{cs:02d}"
    draw_text(x, y, size, text, color)

def frames_to_time_str(frames):
    """Convert frame count to time string."""
    secs = frames // 60
    mins = secs // 60
    rem = secs % 60
    hund = int((frames % 60) * (100.0 / 60.0))
    return f"{mins:02d}:{rem:02d}.{hund:02d}"


def tokens_display_text():
    """Display score tokens with sign preserved after spending."""
    value = int(score["tokens"])
    if value < 0:
        return str(value)
    return str(value).rjust(3, "0")


def entity_progress_player():
    return race["laps"] * TRACK_LENGTH + player["z"]


def entity_progress_ai(ai):
    return ai["lap"] * TRACK_LENGTH + ai["z"]


def race_rank_for_progress(progress_value):
    rank = 1
    if entity_progress_player() > progress_value:
        rank += 1
    for ai in opponents:
        if entity_progress_ai(ai) > progress_value:
            rank += 1
    return rank


def ai_position(ai):
    return race_rank_for_progress(entity_progress_ai(ai))


def activate_player_boost():
    """Spend tokens and activate player boost."""
    global boost_active_timer, boost_flash_timer

    if game_state != "race" or race["done"] or score["tokens"] < BOOST_COST:
        return False

    score["tokens"] -= BOOST_COST
    score["boost_used"] += 1
    boost_active_timer = BOOST_DURATION
    boost_flash_timer = BOOST_DURATION
    show_banner("BOOST ACTIVATED!")
    return True


def attempt_respawn():
    """Spend tokens and respawn the player safely within the current race."""
    global respawn_prompt_timer, respawn_invuln_timer, last_collision_source

    if game_state != "race" or race["done"] or respawn_prompt_timer <= 0.0 or score["tokens"] < RESPAWN_COST:
        return False

    score["tokens"] -= RESPAWN_COST
    score["respawns"] += 1
    respawn_prompt_timer = 0.0
    respawn_invuln_timer = RESPAWN_INVULN_DURATION
    last_collision_source = ""
    player["x"] = 0.0
    player["speed"] = max(player["speed"] * 0.6, 110.0)
    show_banner("RESPAWNED!")
    return True

# =============================================================================
# CAR DRAWING
# =============================================================================

def draw_car(x, y, scale, color):
    """Draw player car (third-person view)."""
    w = 24.0 * scale
    h = 14.0 * scale

    # Main body
    quad(x - w, y, x + w, y + h, color)

    # Windshield
    quad(x - w * 0.55, y + h * 0.5, x + w * 0.55, y + h * 1.25, (0.55, 0.75, 0.95))

    # Rear window
    quad(x - w * 0.35, y + h * 0.15, x + w * 0.35, y + h * 0.48, (0.45, 0.65, 0.85))

    # Wheels
    quad(x - w * 0.85, y - h * 0.15, x - w * 0.55, y + h * 0.35, (0.08, 0.08, 0.08))
    quad(x + w * 0.55, y - h * 0.15, x + w * 0.85, y + h * 0.35, (0.08, 0.08, 0.08))

    # Taillights
    quad(x - w * 0.7, y + h * 0.15, x - w * 0.45, y + h * 0.35, (0.9, 0.15, 0.15))
    quad(x + w * 0.45, y + h * 0.15, x + w * 0.7, y + h * 0.35, (0.9, 0.15, 0.15))

    # Spoiler
    quad(x - w * 0.9, y + h * 0.6, x + w * 0.9, y + h * 0.72, color)
    quad(x - w * 0.85, y + h * 0.55, x - w * 0.75, y + h * 0.65, (0.2, 0.2, 0.2))
    quad(x + w * 0.75, y + h * 0.55, x + w * 0.85, y + h * 0.65, (0.2, 0.2, 0.2))

def draw_small_car(x, y, scale, color):
    """Draw opponent/ghost car (small, for distance)."""
    w = max(2.5, 16.0 * scale)
    h = max(2.0, 10.0 * scale)

    # Body
    quad(x - w, y, x + w, y + h, color)

    # Windshield
    quad(x - w * 0.45, y + h * 0.35, x + w * 0.45, y + h * 1.0, (0.5, 0.7, 0.9))

    # Wheels
    quad(x - w * 0.8, y - h * 0.1, x - w * 0.55, y + h * 0.3, (0.1, 0.1, 0.1))
    quad(x + w * 0.55, y - h * 0.1, x + w * 0.8, y + h * 0.3, (0.1, 0.1, 0.1))

# =============================================================================
# TRACK GENERATION
# =============================================================================

def build_track():
    """Generate procedural track with curves, hills, and objects."""
    global segments, tokens, props, opponents, boost_zones, particles
    global TOTAL_SEGMENTS, TRACK_LENGTH

    preset = LEVEL_PRESETS[level_index]
    seed = preset[1]
    curve_scale = preset[2]
    hill_scale = preset[3]
    rng = random.Random(seed)

    segments = []
    tokens = []
    props = []
    opponents = []
    boost_zones = []
    particles = []

    def append_segment(curve_value):
        i = len(segments)
        segments.append({
            "z": i * SEGMENT_LENGTH,
            "curve": curve_value,
            "y": 0.0,
            "color_light": (i % 2 == 0),
        })

    def append_straight(count):
        for _ in range(count):
            append_segment(0.0)

    def append_curve(enter_count, hold_count, exit_count, curve_value):
        for j in range(enter_count):
            t = j / max(1, enter_count)
            append_segment(curve_value * (t * t))
        for _ in range(hold_count):
            append_segment(curve_value)
        for j in range(exit_count):
            t = j / max(1, exit_count)
            append_segment(curve_value * (1.0 - (1.0 - t) * (1.0 - t)))

    def append_s_turn(curve_value):
        enter = int(rng.uniform(8, 14))
        hold = int(rng.uniform(10, 22))
        exit_count = int(rng.uniform(8, 14))
        append_curve(enter, hold, exit_count, curve_value)
        append_curve(enter, int(hold * 0.85), exit_count, -curve_value * 0.9)

    # Generate a more turn-heavy looping route with sweepers, S-turns, and tighter bends.
    num_sections = 28
    for section in range(num_sections):
        if section in (0, num_sections - 1):
            append_straight(int(rng.uniform(10, 16)))
            continue

        straight_bias = 0.28 if section % 5 else 0.18
        if rng.random() < straight_bias:
            append_straight(int(rng.uniform(6, 14)))
            continue

        direction = -1.0 if rng.random() < 0.5 else 1.0
        pattern = rng.random()
        base_curve = (0.0018 + rng.random() * 0.0038) * curve_scale * direction

        if pattern < 0.30:
            # Sweeping corner
            append_curve(
                int(rng.uniform(10, 18)),
                int(rng.uniform(18, 34)),
                int(rng.uniform(10, 18)),
                base_curve,
            )
        elif pattern < 0.70:
            # S-turn/chicane
            append_s_turn(base_curve * 0.95)
        else:
            # Tighter hairpin-like turn
            append_curve(
                int(rng.uniform(12, 20)),
                int(rng.uniform(20, 42)),
                int(rng.uniform(12, 20)),
                base_curve * 1.4,
            )

        if rng.random() < 0.35:
            append_straight(int(rng.uniform(4, 9)))

    TOTAL_SEGMENTS = len(segments)
    TRACK_LENGTH = TOTAL_SEGMENTS * SEGMENT_LENGTH

    # Generate hills using combined sine waves
    for i in range(TOTAL_SEGMENTS):
        wave1 = math.sin((i / TOTAL_SEGMENTS) * math.pi * 2)
        wave2 = math.sin((i / TOTAL_SEGMENTS) * math.pi * 4) * 0.5
        wave3 = math.sin(i * 0.03) * 0.3
        segments[i]["y"] = (wave1 + wave2 + wave3) * hill_scale * 100.0
        segments[i]["z"] = i * SEGMENT_LENGTH

    # Place tokens in clusters along the track - LARGER TOKENS
    token_clusters = 10
    tokens_per_cluster = NUM_TOKENS // token_clusters
    for g in range(token_clusters):
        start = int((TOTAL_SEGMENTS / token_clusters) * g) + rng.randint(8, 25)
        x_off = rng.uniform(-0.65, 0.65)
        for j in range(tokens_per_cluster):
            seg_idx = (start + j * 3) % TOTAL_SEGMENTS
            tokens.append({
                "z": seg_idx * SEGMENT_LENGTH + SEGMENT_LENGTH * 0.5,
                "x": x_off + rng.uniform(-0.1, 0.1),
                "taken": False,
                "anim_offset": rng.random() * math.pi * 2,
            })

    # Place props (MORE TREES AND BUSHES on track sides)
    prop_types = ["tree", "bush", "tree", "bush", "sign", "rock", "building"]
    for i in range(NUM_PROPS):
        seg_idx = rng.randint(0, TOTAL_SEGMENTS - 1)
        side = rng.choice([-1, 1])
        # 70% vegetation (trees and bushes), 30% other props
        is_vegetation = rng.random() < 0.70
        if is_vegetation:
            kind = 0 if rng.random() < 0.55 else 1  # tree or bush
        else:
            kind = rng.randint(2, 6)
        props.append({
            "z": seg_idx * SEGMENT_LENGTH + SEGMENT_LENGTH * 0.5,
            "x": side * (1.5 + rng.uniform(0.0, 0.8)),  # Wider placement for wider track
            "kind": kind,
            "kind_name": prop_types[kind],
            "collidable": kind >= 2 and side > 0 and rng.random() < 0.28,
        })

    # Create AI opponents
    diff_mul = DIFFICULTY_PRESETS[difficulty_index][1]
    for i in range(ai_count):
        opponents.append({
            "z": (i + 1) * (TRACK_LENGTH / (ai_count + 2)),
            "x": rng.uniform(-0.6, 0.6),
            "speed": (140.0 + rng.uniform(-20, 35)) * diff_mul,
            "color": (
                rng.random() * 0.6 + 0.3,
                rng.random() * 0.5 + 0.2,
                rng.random() * 0.5 + 0.2,
            ),
            "target_x": rng.uniform(-0.5, 0.5),
            "lap": 0,
            "aggression": rng.uniform(0.3, 0.8),
            "block_timer": 0.0,
            "block_cooldown": rng.uniform(0.5, 2.0),
            "lane_bias": rng.uniform(-0.7, 0.7),
        })

    # Create boost zones
    for i in range(NUM_BOOST_ZONES):
        start = ((i * 57) % TOTAL_SEGMENTS) * SEGMENT_LENGTH
        end = start + SEGMENT_LENGTH * rng.uniform(2.0, 4.0)
        boost_zones.append((start, end))

def build_minimap_points():
    """Generate 2D minimap track outline."""
    pts = []
    heading = 0.0
    mx, mz = 0.0, 0.0
    for seg in segments:
        heading += seg["curve"] * 0.03
        mx += math.sin(heading) * 2
        mz += math.cos(heading) * 2
        pts.append((mx, mz))
    return pts

# =============================================================================
# PROJECTION
# =============================================================================

def project(world_x, world_y, world_z, curve_shift):
    """Project 3D world point to 2D screen space."""
    relative_z = world_z - camera["z"]
    if relative_z < 1.0:
        return None
    scale = camera["depth"] / relative_z
    sx = (WIDTH * 0.5) + scale * (world_x - camera["x"] - curve_shift) * ROAD_PROJECTION_SCALE
    sy = scale * (world_y - camera["y"]) * (HEIGHT * 0.5) + (HEIGHT * 0.5)
    sw = scale * ROAD_WIDTH * ROAD_PROJECTION_SCALE
    return {"x": sx, "y": sy, "w": sw, "scale": scale}


def segment_index_for_z(world_z):
    """Map an absolute or wrapped world-z value to a track segment index."""
    return int((world_z % TRACK_LENGTH) / SEGMENT_LENGTH) % TOTAL_SEGMENTS


def curve_shift_to(world_z):
    """Accumulate curve shift from the player segment to a target z position."""
    if not segments:
        return 0.0

    start_idx = int(player["z"] / SEGMENT_LENGTH) % TOTAL_SEGMENTS
    target_idx = segment_index_for_z(world_z)
    shift = 0.0
    idx = start_idx
    steps = 0

    while idx != target_idx and steps <= DRAW_DISTANCE + 2:
        idx = (idx + 1) % TOTAL_SEGMENTS
        shift += segments[idx]["curve"]
        steps += 1

    return shift * CURVE_PROJECTION_SCALE


def project_track_entity(track_x, height_offset, world_z):
    """Project an object that sits on or beside the track surface."""
    seg = segments[segment_index_for_z(world_z)]
    return project(track_x * ROAD_WIDTH, seg["y"] + height_offset, world_z, curve_shift_to(world_z))

# =============================================================================
# SETUP
# =============================================================================

def setup_projection():
    """Setup orthographic projection for 2D rendering."""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, WIDTH, 0, HEIGHT, 0, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

# =============================================================================
# DISPLAY FUNCTION
# =============================================================================

def display():
    """Main rendering function."""
    global quit_requested

    try:
        mix = day_night_mix()
        palette = current_palette()
        clear_color = (0.0, 0.0, 0.0)

        if game_state == "menu":
            clear_color = (0.08, 0.08, 0.14)
        elif not quit_requested:
            # Blend sky between day and night
            sky_day = palette.get("sky_day", (0.4, 0.6, 0.9))
            sky_night = palette.get("sky_night", (0.1, 0.1, 0.25))
            clear_color = lerp_color(sky_night, sky_day, mix)

        glClearColor(clear_color[0], clear_color[1], clear_color[2], 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        setup_projection()

        if quit_requested:
            glutSwapBuffers()
            return

        if game_state == "menu":
            draw_menu()
            glutSwapBuffers()
            return

        # Render 3D scene
        draw_sky_and_backdrop(palette, mix)
        draw_road(palette, mix)
        draw_finish_line()
        draw_boost_zones()

        # Night headlights
        if atmosphere["is_night"]:
            draw_headlights()

        draw_tokens()
        draw_props(palette)
        draw_opponents()
        draw_ghost()

        # Player car (only in TPP mode)
        if camera_mode == "tpp":
            px = WIDTH * 0.5 + player["x"] * 140.0
            draw_player_boost_flame(px, 80.0)
            draw_car(px, 80.0, 2.8, (0.92, 0.20, 0.58))

        draw_particles()
        draw_boost_window_effects()

        # HUD and overlays
        draw_hud(mix)
        draw_minimap()

        if game_state == "countdown":
            draw_countdown()
        elif game_state == "pause":
            draw_pause_overlay()
        elif game_state == "finish" or race["done"]:
            draw_finish_overlay()

        if banner_timer > 0:
            draw_banner()

        glutSwapBuffers()

    except KeyboardInterrupt:
        quit_requested = True
        return

# =============================================================================
# RENDERING FUNCTIONS
# =============================================================================

def draw_sky_and_backdrop(palette, mix):
    """
    Skybox & Atmospheric Gradient.
    Fulfills vertex-colored background requirement.
    Dynamic colors blend between day and night.
    """
    sky_day = palette.get("sky_day", (0.4, 0.6, 0.9))
    sky_night = palette.get("sky_night", (0.1, 0.1, 0.25))

    # Sky gradient
    top_col = lerp_color(sky_night, sky_day, mix)
    bottom_day = lerp_color((0.65, 0.75, 0.9), sky_day, 0.2)
    bottom_night = (0.12, 0.08, 0.18)
    bottom_col = lerp_color(bottom_night, bottom_day, mix)

    gradient_quad(0, HEIGHT * 0.45, WIDTH, HEIGHT, bottom_col, top_col)

    # Horizon glow
    glow_day = (0.85, 0.65, 0.45)
    glow_night = (0.15, 0.12, 0.2)
    glow = lerp_color(glow_night, glow_day, mix * 0.7)
    gradient_quad(0, HEIGHT * 0.45, WIDTH, HEIGHT * 0.52, glow, bottom_col)

    # Skyline/buildings
    skyline = palette.get("skyline", (0.3, 0.3, 0.4))
    building = palette.get("building", (0.4, 0.4, 0.5))

    seg_index = int(player["z"] / SEGMENT_LENGTH) % TOTAL_SEGMENTS
    base_seg = segments[seg_index]
    horizon_shift = base_seg["curve"] * player["speed"] * 600.0

    # Draw buildings
    for i in range(20):
        bx = ((i * 55) + horizon_shift * 0.35) % (WIDTH + 200) - 100
        bw = 28 + (i % 6) * 12
        bh = 30 + (i % 8) * 18

        # Building body
        col = lerp_color((0.05, 0.05, 0.08), skyline, mix)
        quad(bx, HEIGHT * 0.45, bx + bw, HEIGHT * 0.45 + bh, col)

        # Windows (lit at night)
        if atmosphere["is_night"]:
            win_col = (0.95, 0.9, 0.5) if (i + seg_index) % 4 == 0 else (0.3, 0.25, 0.15)
            for wy in range(5, int(bh) - 10, 10):
                for wx in range(5, int(bw) - 5, 8):
                    if (i + wx + wy) % 3 != 0:
                        quad(bx + wx, HEIGHT * 0.45 + wy, bx + wx + 4, HEIGHT * 0.45 + wy + 6, win_col)

def draw_road(palette, mix):
    """Draw the pseudo-3D road using trapezoid segments."""
    seg_index = int(player["z"] / SEGMENT_LENGTH)
    projected = []
    curve_acc = 0.0

    for n in range(DRAW_DISTANCE + 1):
        idx = (seg_index + n) % TOTAL_SEGMENTS
        seg = segments[idx]
        world_z = seg["z"]
        if idx < seg_index:
            world_z += TRACK_LENGTH
        curve_acc += seg["curve"]
        p = project(0.0, seg["y"], world_z, curve_acc * CURVE_PROJECTION_SCALE)
        if p is not None:
            p["seg"] = seg
            p["idx"] = idx
            projected.append(p)

    clip_y = HEIGHT
    for i in range(len(projected) - 1, 0, -1):
        p1 = projected[i]
        p2 = projected[i - 1]
        if p2["y"] >= clip_y:
            continue
        clip_y = p2["y"]
        c_light = p2["seg"]["color_light"]

        # Grass
        grass_key = "grass1" if c_light else "grass2"
        grass = palette.get(grass_key, (0.3, 0.7, 0.3))
        grass = lerp_color((grass[0] * 0.4, grass[1] * 0.4, grass[2] * 0.45), grass, mix)
        quad(0, p2["y"], WIDTH, p1["y"], grass)

        # Rumble strip
        rumble_key = "rumble_l" if c_light else "rumble_d"
        rumble = palette.get(rumble_key, (0.9, 0.9, 0.9))
        rw1 = p1["w"] * 1.18
        rw2 = p2["w"] * 1.18
        trapezoid(p1["x"], p1["y"], rw1, p2["x"], p2["y"], rw2, rumble)

        # Road surface
        road_key = "road1" if c_light else "road2"
        road = palette.get(road_key, (0.5, 0.5, 0.5))
        road = lerp_color((road[0] * 0.5, road[1] * 0.5, road[2] * 0.55), road, mix)
        trapezoid(p1["x"], p1["y"], p1["w"], p2["x"], p2["y"], p2["w"], road)

        # Center line (dashed, speed-dependent)
        speed_ratio = clamp(player["speed"] / MAX_SPEED, 0.0, 1.0)
        dash_period = max(4, int(10 - speed_ratio * 5))
        z_phase = int(camera["z"] / SEGMENT_LENGTH) % dash_period
        if ((p2["idx"] + z_phase) % dash_period) < (dash_period // 2):
            lw1 = p1["w"] * 0.04
            lw2 = p2["w"] * 0.04
            lane = (0.92, 0.92, 0.78) if c_light else (0.72, 0.72, 0.58)
            trapezoid(p1["x"], p1["y"], lw1, p2["x"], p2["y"], lw2, lane)

def draw_boost_zones():
    """Draw turbo boost zones on the track."""
    for bz0, bz1 in boost_zones:
        start_idx = int(bz0 / SEGMENT_LENGTH) % TOTAL_SEGMENTS
        end_idx = int(bz1 / SEGMENT_LENGTH) % TOTAL_SEGMENTS
        idx = start_idx
        safety = 0

        while True:
            next_idx = (idx + 1) % TOTAL_SEGMENTS
            seg1 = segments[idx]
            seg2 = segments[next_idx]
            z1 = seg1["z"]
            z2 = seg2["z"]
            if idx < int(player["z"] / SEGMENT_LENGTH):
                z1 += TRACK_LENGTH
            if next_idx < int(player["z"] / SEGMENT_LENGTH):
                z2 += TRACK_LENGTH

            p1 = project(0.0, seg1["y"] + 5.0, z1, curve_shift_to(z1))
            p2 = project(0.0, seg2["y"] + 5.0, z2, curve_shift_to(z2))

            if p1 and p2 and 0 < p1["y"] < HEIGHT and 0 < p2["y"] < HEIGHT:
                boost_col = current_palette().get("boost", (0.2, 0.8, 0.9))
                trapezoid(p1["x"], p1["y"], p1["w"] * 0.6, p2["x"], p2["y"], p2["w"] * 0.6, boost_col)

            if idx == end_idx:
                break
            idx = next_idx
            safety += 1
            if safety > 10:
                break


def draw_finish_line():
    """Draw a checkered start/finish line across the road (BLACK AND WHITE)."""
    if not segments:
        return

    line_z = TRACK_LENGTH if player["z"] > TRACK_LENGTH * 0.72 else 0.0
    if player["z"] < TRACK_LENGTH * 0.12:
        line_z = 0.0

    p1 = project(0.0, segments[0]["y"] + 3.0, line_z, curve_shift_to(line_z))
    p2 = project(0.0, segments[1]["y"] + 3.0, line_z + SEGMENT_LENGTH * 0.4, curve_shift_to(line_z + SEGMENT_LENGTH * 0.4))
    if not p1 or not p2 or p1["y"] <= 0 or p2["y"] <= 0 or p1["y"] >= HEIGHT or p2["y"] >= HEIGHT:
        return

    cols = 12  # More checkered squares
    for col_idx in range(cols):
        t0 = col_idx / float(cols)
        t1 = (col_idx + 1) / float(cols)
        x1l = p1["x"] - p1["w"] + (2.0 * p1["w"] * t0)
        x1r = p1["x"] - p1["w"] + (2.0 * p1["w"] * t1)
        x2l = p2["x"] - p2["w"] + (2.0 * p2["w"] * t0)
        x2r = p2["x"] - p2["w"] + (2.0 * p2["w"] * t1)
        # BLACK AND WHITE checkered pattern
        col = (0.96, 0.96, 0.96) if col_idx % 2 == 0 else (0.08, 0.08, 0.08)
        glColor3f(col[0], col[1], col[2])
        glBegin(GL_QUADS)
        glVertex2f(x1l, p1["y"])
        glVertex2f(x1r, p1["y"])
        glVertex2f(x2r, p2["y"])
        glVertex2f(x2l, p2["y"])
        glEnd()

def draw_tokens():
    """Draw collectible tokens - LARGER with counter on top."""
    palette = current_palette()
    token_col = palette.get("token", (0.95, 0.8, 0.1))

    for item in tokens:
        if item["taken"]:
            continue
        iz = item["z"]
        if iz < player["z"]:
            iz += TRACK_LENGTH
        dz = iz - player["z"]
        if dz > DRAW_DISTANCE * SEGMENT_LENGTH * 0.5 or dz < 0:
            continue

        p = project_track_entity(item["x"], 50.0, iz)
        if p and 0 < p["y"] < HEIGHT:
            # INCREASED SIZE - was 13500, now 18000
            s = max(6.0, p["scale"] * 18000.0)

            # Animating sparkle
            anim = math.sin(world_time * 0.4 + item["anim_offset"]) * 0.2 + 0.8
            col = (token_col[0] * anim, token_col[1] * anim, token_col[2] * anim)

            # Diamond shape - LARGER
            cx, cy = p["x"], p["y"] + s * 0.3
            glBegin(GL_QUADS)
            glColor3f(col[0], col[1], col[2])
            glVertex2f(cx, cy - s * 0.5)
            glVertex2f(cx + s * 0.35, cy)
            glVertex2f(cx, cy + s * 0.5)
            glVertex2f(cx - s * 0.35, cy)
            glEnd()

            # COUNTER ON TOP - Display "10" on each token
            if s > 10.0:
                draw_text(cx - s * 0.25, cy + s * 0.65, max(1.0, s * 0.08), "10", (0.98, 0.95, 0.78))

def draw_props(palette):
    """Draw trackside props (MORE TREES AND BUSHES)."""
    prop_colors = [
        (0.15, 0.6, 0.18),   # tree
        (0.22, 0.55, 0.20),  # bush
        (0.9, 0.2, 0.2),     # sign
        (0.55, 0.5, 0.45),   # rock
        (0.4, 0.4, 0.5),     # building
    ]

    for prop in props:
        iz = prop["z"]
        if iz < player["z"]:
            iz += TRACK_LENGTH
        dz = iz - player["z"]
        if dz > DRAW_DISTANCE * SEGMENT_LENGTH * 0.4 or dz < 0:
            continue

        p = project_track_entity(prop["x"], 25.0, iz)
        if p and 0 < p["y"] < HEIGHT:
            s = max(3.5, p["scale"] * 14000.0)
            col = prop_colors[prop["kind"] % len(prop_colors)]

            if prop["kind"] == 0:  # Tree
                # Trunk
                trunk_w = s * 0.15
                quad(p["x"] - trunk_w, p["y"], p["x"] + trunk_w, p["y"] + s * 0.6, (0.45, 0.3, 0.15))
                # Foliage - LARGER
                quad(p["x"] - s * 0.45, p["y"] + s * 0.4, p["x"] + s * 0.45, p["y"] + s * 1.5, col)
            elif prop["kind"] == 1:  # Bush
                quad(p["x"] - s * 0.5, p["y"], p["x"] + s * 0.5, p["y"] + s * 0.6, col)
                quad(p["x"] - s * 0.3, p["y"] + s * 0.2, p["x"] + s * 0.3, p["y"] + s * 0.75, (0.18, 0.46, 0.16))
            elif prop["kind"] == 2:  # Sign
                # Post
                pw = s * 0.08
                quad(p["x"] - pw, p["y"], p["x"] + pw, p["y"] + s * 0.8, (0.55, 0.5, 0.45))
                # Sign face
                quad(p["x"] - s * 0.3, p["y"] + s * 0.6, p["x"] + s * 0.3, p["y"] + s * 1.1, col)
            elif prop["kind"] == 3:  # Rock
                quad(p["x"] - s * 0.35, p["y"], p["x"] + s * 0.35, p["y"] + s * 0.7, col)
            else:  # Building
                quad(p["x"] - s * 0.5, p["y"], p["x"] + s * 0.5, p["y"] + s * 1.2, col)
                # Windows
                if not atmosphere["is_night"]:
                    for wx in range(-3, 4):
                        for wy in range(2, 10, 3):
                            if (wx + wy) % 2 == 0:
                                quad(p["x"] + wx * s * 0.12, p["y"] + wy * s * 0.1,
                                     p["x"] + (wx + 1) * s * 0.12, p["y"] + (wy + 2) * s * 0.1, (0.3, 0.35, 0.4))

def draw_opponents():
    """Draw AI opponent cars."""
    for ai in opponents:
        iz = ai["z"]
        if iz < player["z"]:
            iz += TRACK_LENGTH
        dz = iz - player["z"]
        if dz > DRAW_DISTANCE * SEGMENT_LENGTH * 0.6 or dz < 0:
            continue

        p = project_track_entity(ai["x"], 0.0, iz)
        if p and 0 < p["y"] < HEIGHT:
            car_scale = max(0.16, p["w"] * 0.0105)
            draw_car(p["x"], p["y"], car_scale, ai["color"])

def draw_ghost():
    """Draw ghost car from best lap."""
    ghost = ghost_position()
    if ghost is None:
        return

    gs, gx = ghost
    iz = gs
    if iz < player["z"]:
        iz += TRACK_LENGTH
    dz = iz - player["z"]
    if dz > DRAW_DISTANCE * SEGMENT_LENGTH * 0.5 or dz < 0:
        return

    p = project_track_entity(gx, 0.0, iz)
    if p and 0 < p["y"] < HEIGHT:
        s = max(0.16, p["w"] * 0.0105)
        ghost_col = (0.3, 0.85, 0.95)
        draw_car(p["x"], p["y"], s, ghost_col)


def draw_player_boost_flame(px, py):
    """Draw blue boost flames behind the player car (TPP and FPP)."""
    if boost_active_timer <= 0.0:
        return

    pulse = 0.7 + 0.3 * math.sin(world_time * 0.7)
    flame_outer = (0.18, 0.55 * pulse, 0.98)
    flame_inner = (0.82, 0.94, 1.0)

    # Adjust position for FPP mode
    flame_y_offset = 0.0 if camera_mode == "tpp" else -15.0

    for side in (-1.0, 1.0):
        offset = side * 18.0
        trapezoid(px + offset, py + 28.0 + flame_y_offset, 5.0, 
                  px + offset, py - 18.0 - pulse * 12.0 + flame_y_offset, 12.0, flame_outer)
        trapezoid(px + offset, py + 24.0 + flame_y_offset, 2.5, 
                  px + offset, py - 10.0 - pulse * 10.0 + flame_y_offset, 5.5, flame_inner)


def draw_boost_window_effects():
    """Draw full-screen speed streaks and a bottom glow while boosting."""
    if boost_active_timer <= 0.0:
        return

    streaks = 18  # More streaks for better effect
    base_col = (0.18, 0.55, 0.95)
    hot_col = (0.72, 0.9, 1.0)
    center_x = WIDTH * 0.5
    base_y = 90 if camera_mode == "tpp" else 55

    for i in range(streaks):
        frac = i / float(max(1, streaks - 1))
        lateral = (frac - 0.5) * WIDTH * 0.95
        wobble = math.sin(world_time * 0.08 + i) * 20.0
        x1 = center_x + lateral * 0.08
        x2 = center_x + lateral + wobble
        y1 = base_y + frac * HEIGHT * 0.2
        y2 = HEIGHT * 0.25 + frac * HEIGHT * 0.75
        col = lerp_color(base_col, hot_col, 1.0 - abs(frac - 0.5) * 1.4)
        line(x1, y1, x2, y2, col)

    glow_w = 140 if camera_mode == "tpp" else 220
    quad(center_x - glow_w, 0, center_x + glow_w, 50, (0.10, 0.25, 0.48))
    quad(center_x - glow_w * 0.45, 0, center_x + glow_w * 0.45, 36, (0.35, 0.72, 0.98))

def draw_particles():
    """
    Particle System - Tire smoke during drifts.
    Particles are drawn last to appear over car and road.
    """
    palette = current_palette()
    mix = day_night_mix()

    # Background color for smoke blending
    road_key = "road1"
    road = palette.get(road_key, (0.5, 0.5, 0.5))
    road = lerp_color((road[0] * 0.5, road[1] * 0.5, road[2] * 0.55), road, mix)

    fresh_smoke = (0.65, 0.65, 0.68)

    for puff in particles:
        s = puff["s"]
        fade = clamp(puff["life"] / 0.7, 0.0, 1.0)
        col = lerp_color(road, fresh_smoke, fade * 0.8)
        quad(puff["x"] - s, puff["y"] - s * 0.75, puff["x"] + s, puff["y"] + s * 0.75, col)

def draw_headlights():
    """
    Dynamic Headlights - Real-time illumination.
    Creates directional light beams that react to player steering.
    Dual beams offset from center chassis.
    """
    hx = WIDTH * 0.5 + player["x"] * 140.0
    hy = 100.0 if camera_mode == "tpp" else 80.0

    # Directional vectors based on heading
    forward_x = math.sin(player_heading)
    forward_y = math.cos(player_heading)

    right_x = forward_y
    right_y = -forward_x

    beam_len = 240.0 if camera_mode == "tpp" else 280.0
    night_strength = clamp((0.55 - atmosphere["brightness"]) * 2.2, 0.0, 1.0)

    if night_strength <= 0.0:
        return

    # Layered beam colors (outer to inner brightness)
    outer_color = lerp_color((0.12, 0.11, 0.06), (0.4, 0.36, 0.18), night_strength)
    mid_color = lerp_color((0.16, 0.15, 0.08), (0.62, 0.56, 0.26), night_strength)
    inner_color = lerp_color((0.22, 0.20, 0.10), (0.98, 0.92, 0.58), night_strength)

    for side in (-1.0, 1.0):
        ox = hx + right_x * side * 20.0
        oy = hy + right_y * side * 20.0
        midx = ox + forward_x * (beam_len * 0.5)
        midy = oy + forward_y * (beam_len * 0.5)
        tipx = ox + forward_x * beam_len
        tipy = oy + forward_y * beam_len

        # Three-layer beam for depth effect
        trapezoid(ox, oy, 10.0, midx, midy, 32.0, outer_color)
        trapezoid(ox, oy, 6.5, midx, midy, 20.0, mid_color)
        trapezoid(ox, oy, 3.0, tipx, tipy, 12.0, inner_color)

def spawn_drift_particles(lateral_delta):
    """
    Spawn tire smoke particles during drifts.
    Triggered when speed > 35 and lateral movement detected.
    """
    if player["speed"] <= 35.0 or abs(lateral_delta) <= 0.015:
        return

    global drift_combo, drift_score, max_drift_combo

    base_x = WIDTH * 0.5 + player["x"] * 140.0
    base_y = 70.0 if camera_mode == "tpp" else 55.0
    slide_push = clamp(lateral_delta * -450.0, -40.0, 40.0)

    # Increase drift combo
    drift_combo += 1
    drift_score += drift_combo * 10
    max_drift_combo = max(max_drift_combo, drift_combo)

    for side in (-1.0, 1.0):
        particles.append({
            "x": base_x + side * 28.0 + random.uniform(-8.0, 8.0),
            "y": base_y + random.uniform(-4.0, 8.0),
            "vx": slide_push + random.uniform(-16.0, 16.0),
            "vy": random.uniform(20.0, 38.0),
            "s": random.uniform(5.0, 10.0),
            "life": random.uniform(0.35, 0.75),
        })


def draw_hud(mix):
    """
    2D HUD with mechanical-style speedometer.
    COMPACT LAYOUT - Minimized footprint.
    Displays: speed, lap count, tokens, hits, position, lap time.
    """
    # HUD panel background - COMPACT
    panel_col = (0.05, 0.05, 0.08)
    panel_border = (0.12, 0.12, 0.16)
    quad(8, 8, 440, 90, panel_col)
    quad(10, 10, 438, 88, panel_border)

    speed_kmh = int(player["speed"] * 1.6)
    race_elapsed = 0.0
    if race["start_time"] > 0.0 and game_state in ("race", "finish"):
        race_elapsed = time.perf_counter() - race["start_time"] if game_state == "race" else sum(race["lap_times"])

    # Speed display - Left side
    draw_text(18, 68, 1.6, "SPD", (0.75, 0.85, 0.95))
    draw_number(16, 32, 9, speed_kmh, 3, (0.98, 0.95, 0.85))
    draw_text(82, 36, 1.3, "KM/H", (0.6, 0.65, 0.7))

    # Lap display
    draw_text(120, 68, 1.5, "LAP", (0.28, 0.92, 0.42))
    current_lap = min(race["laps"] + 1, race["max_laps"])
    draw_number(118, 32, 7, current_lap, 1, (0.28, 0.92, 0.42))
    draw_text(144, 32, 1.2, f"/{race['max_laps']}", (0.25, 0.72, 0.35))

    # Tokens display
    draw_text(170, 68, 1.5, "PTS", (0.95, 0.82, 0.15))
    draw_text(168, 32, 1.5, tokens_display_text(), (0.95, 0.82, 0.15))

    # Hits display
    draw_text(230, 68, 1.5, "HIT", (0.92, 0.28, 0.28))
    draw_number(228, 32, 7, score["hits"], 2, (0.92, 0.28, 0.28))

    # Position display
    pos = player_position()
    draw_text(16, 14, 1.4, "POS", (0.65, 0.85, 0.95))
    draw_text(48, 14, 1.4, f"{pos}/{ai_count + 1}", (0.88, 0.92, 0.98))

    # Current lap time
    if not race["done"] and game_state == "race":
        current_lap_time = time.perf_counter() - race["lap_start"]
    else:
        current_lap_time = 0.0
    draw_text(108, 14, 1.3, "LAP TIME", (0.62, 0.67, 0.74))
    draw_time_mmss_cc(178, 14, 1.3, current_lap_time, (0.78, 0.82, 0.92))

    # Race time
    draw_text(280, 14, 1.3, "RACE TIME", (0.62, 0.67, 0.74))
    draw_time_mmss_cc(356, 14, 1.3, min(race_elapsed, RACE_TARGET_SECONDS), (0.78, 0.82, 0.92))
    draw_text(280, 4, 1.1, f"TARGET 1:30   {level_name}", (0.65, 0.75, 0.88))

    # Boost/Respawn info
    draw_text(16, 4, 1.1, f"BOOST {BOOST_COST} PTS   RESPAWN {RESPAWN_COST} PTS", (0.58, 0.62, 0.7))
    if score["tokens"] >= BOOST_COST:
        draw_text(220, 4, 1.1, "BOOST READY (L-CLICK)", (0.3, 0.85, 0.95))
    if respawn_prompt_timer > 0.0:
        col = (0.98, 0.42, 0.42) if score["tokens"] < RESPAWN_COST else (0.98, 0.88, 0.12)
        label = "CLICK RESPAWN" if score["tokens"] >= RESPAWN_COST else "NEED 50 PTS"
        draw_text(280, 68, 1.2, label, col)
    elif boost_active_timer > 0.0:
        draw_text(296, 68, 1.2, "BOOSTING!", (0.35, 0.82, 0.98))

    # Drift combo display
    if drift_combo > 1:
        quad(450, 6, 552, 40, (0.05, 0.05, 0.08))
        quad(452, 8, 550, 38, (0.12, 0.12, 0.16))
        draw_text(460, 20, 1.4, f"DRIFT x{drift_combo}", (0.95, 0.5, 0.8))
        draw_text(460, 6, 1.2, f"+{drift_score}", (0.85, 0.4, 0.7))

    # Mechanical speedometer - compact
    draw_speedometer(390, 48, 28)


def draw_speedometer(cx, cy, radius):
    """Draw mechanical-style speedometer with animated needle."""
    # Background
    bg_col = (0.08, 0.08, 0.12)
    border_col = (0.25, 0.25, 0.3)

    # Circular background
    for i in range(20):
        a = (i / 20) * 2.0 * math.pi
        x1 = cx + math.cos(a) * radius
        y1 = cy + math.sin(a) * radius
        x2 = cx + math.cos(a) * (radius - 3)
        y2 = cy + math.sin(a) * (radius - 3)
        glBegin(GL_LINES)
        glColor3f(border_col[0], border_col[1], border_col[2])
        glVertex2f(x1, y1)
        glVertex2f(x2, y2)
        glEnd()

    # Inner circle (drawn as octagon for efficiency)
    draw_circle_outline(cx, cy, radius - 5, bg_col)

    # Speed tick marks
    speed_kmh = int(player["speed"] * 1.6)
    max_display = 360

    for tick in range(12):
        ta = -2.356 + tick * (2.356 * 2 / 11.0)  # -135 to +135 degrees
        tx1 = cx + math.cos(ta) * (radius - 8)
        ty1 = cy + math.sin(ta) * (radius - 8)
        tx2 = cx + math.cos(ta) * (radius - 2)
        ty2 = cy + math.sin(ta) * (radius - 2)
        col = (0.9, 0.2, 0.2) if tick >= 10 else (0.5, 0.5, 0.55)
        line(tx1, ty1, tx2, ty2, col)

    # Needle
    needle_angle = -2.356 + (speed_kmh / max_display) * (2.356 * 2)
    nx = cx + math.cos(needle_angle) * (radius - 10)
    ny = cy + math.sin(needle_angle) * (radius - 10)
    glLineWidth(2.5)
    line(cx, cy, nx, ny, (1.0, 0.2, 0.2))
    glLineWidth(1.0)

    # Center cap (drawn as small quad)
    quad(cx - 5, cy - 5, cx + 5, cy + 5, (0.85, 0.85, 0.85))

    # Speed number
    draw_number(cx - 25, cy - 8, 8, speed_kmh, 3, (0.95, 0.95, 0.9))

def draw_minimap():
    """
    Draw 2D orthographic mini-map overlay.
    POSITION NUMBERS visible on player and opponent icons.
    """
    if not minimap_points:
        return

    mx, my, mw, mh = 830, 105, 170, 125

    # Background
    quad(mx, my, mx + mw, my + mh, (0.04, 0.04, 0.07))
    quad(mx + 2, my + 2, mx + mw - 2, my + mh - 2, (0.09, 0.09, 0.13))

    # Track outline
    pts = minimap_points
    min_x = min(p[0] for p in pts)
    max_x = max(p[0] for p in pts)
    min_z = min(p[1] for p in pts)
    max_z = max(p[1] for p in pts)
    span_x = max(1e-5, max_x - min_x)
    span_z = max(1e-5, max_z - min_z)
    pad = 6
    draw_w = mw - pad * 2
    draw_h = mh - pad * 2

    glColor3f(0.4, 0.4, 0.45)
    glBegin(GL_LINES)
    step = max(1, len(pts) // 250)
    for i in range(0, len(pts) - step, step):
        a = pts[i]
        b = pts[i + step]
        ax = mx + pad + ((a[0] - min_x) / span_x) * draw_w
        ay = my + pad + ((a[1] - min_z) / span_z) * draw_h
        bx = mx + pad + ((b[0] - min_x) / span_x) * draw_w
        by = my + pad + ((b[1] - min_z) / span_z) * draw_h
        glVertex2f(ax, ay)
        glVertex2f(bx, by)
    glEnd()

    # Player position (pink triangle) WITH POSITION NUMBER
    p_idx = int(player["z"] / SEGMENT_LENGTH) % len(pts)
    pp = pts[p_idx]
    ppx = mx + pad + ((pp[0] - min_x) / span_x) * draw_w
    ppy = my + pad + ((pp[1] - min_z) / span_z) * draw_h

    # Draw player triangle
    glBegin(GL_LINES)
    glColor3f(0.95, 0.2, 0.58)
    glVertex2f(ppx, ppy - 5)
    glVertex2f(ppx - 4, ppy + 4)
    glVertex2f(ppx, ppy - 5)
    glVertex2f(ppx + 4, ppy + 4)
    glVertex2f(ppx - 4, ppy + 4)
    glVertex2f(ppx + 4, ppy + 4)
    glEnd()
    # POSITION NUMBER next to player icon
    draw_text(ppx + 8, ppy - 4, 1.3, str(player_position()), (0.95, 0.9, 0.98))

    # AI positions (green squares) WITH POSITION NUMBERS
    for ai in opponents:
        ai_idx = int(ai["z"] / SEGMENT_LENGTH) % len(pts)
        ap = pts[ai_idx]
        apx = mx + pad + ((ap[0] - min_x) / span_x) * draw_w
        apy = my + pad + ((ap[1] - min_z) / span_z) * draw_h
        quad(apx - 2.5, apy - 2.5, apx + 2.5, apy + 2.5, (0.28, 0.88, 0.38))
        # POSITION NUMBER next to AI icon
        draw_text(apx + 6, apy - 3, 1.1, str(ai_position(ai)), (0.88, 0.95, 0.9))

def draw_countdown():
    """Draw race countdown overlay."""
    elapsed = 3.5 - countdown_timer
    if elapsed < 1.0:
        label = "3"
    elif elapsed < 2.0:
        label = "2"
    elif elapsed < 3.0:
        label = "1"
    else:
        label = "GO!"

    # Background flash
    alpha = min(1.0, elapsed / 0.5) if elapsed < 0.5 else 1.0
    quad(WIDTH * 0.5 - 90, HEIGHT * 0.5 - 45, WIDTH * 0.5 + 90, HEIGHT * 0.5 + 45,
         (0.02, 0.02, 0.05))
    draw_text(WIDTH * 0.5 - len(label) * 14, HEIGHT * 0.5 - 12, 4.5, label, (0.98, 0.88, 0.12))

def draw_pause_overlay():
    """Draw pause menu overlay."""
    quad(WIDTH * 0.5 - 150, HEIGHT * 0.5 - 110, WIDTH * 0.5 + 150, HEIGHT * 0.5 + 90, (0.03, 0.03, 0.06))
    quad(WIDTH * 0.5 - 148, HEIGHT * 0.5 - 108, WIDTH * 0.5 + 148, HEIGHT * 0.5 + 88, (0.08, 0.08, 0.13))

    draw_text(WIDTH * 0.5 - 45, HEIGHT * 0.5 + 60, 3.5, "PAUSED", (0.98, 0.88, 0.12))

    labels = ["RESUME (P)", "RESTART (R)", "MAIN MENU (M)"]
    for i, lb in enumerate(labels):
        col = (0.98, 0.88, 0.12) if i == pause_option else (0.65, 0.7, 0.78)
        marker = "> " if i == pause_option else "  "
        draw_text(WIDTH * 0.5 - 90, HEIGHT * 0.5 + 20 - i * 32, 2.5, marker + lb, col)

def draw_finish_overlay():
    """Draw race finish summary with leaderboard."""
    quad(150, 120, WIDTH - 150, HEIGHT - 120, (0.025, 0.025, 0.05))
    quad(154, 124, WIDTH - 154, HEIGHT - 124, (0.09, 0.09, 0.14))

    draw_text(WIDTH * 0.5 - 60, HEIGHT - 165, 4.0, "FINISH!", (0.98, 0.88, 0.12))

    pos = player_position()
    total_race_time = sum(race["lap_times"]) if race["lap_times"] else 0.0
    best_race = best_times.get(level_name)
    best_lap = best_lap_times.get(level_name)

    # Left column - Race stats
    draw_text(180, HEIGHT - 210, 2.5, f"POSITION: {pos}/{ai_count + 1}", (0.88, 0.92, 0.98))
    draw_text(180, HEIGHT - 240, 2.5, f"TOKENS: {score['tokens']}", (0.95, 0.82, 0.15))
    draw_text(180, HEIGHT - 265, 2.0, f"BANK TOTAL: {total_tokens_bank}", (0.82, 0.84, 0.48))
    draw_text(180, HEIGHT - 290, 2.5, f"HITS: {score['hits']}", (0.92, 0.26, 0.26))
    draw_text(180, HEIGHT - 320, 2.5, f"OVERTAKES: {score['overtakes']}", (0.28, 0.92, 0.42))
    draw_text(180, HEIGHT - 350, 2.2, "RACE TIME:", (0.65, 0.7, 0.78))
    draw_time_mmss_cc(300, HEIGHT - 350, 2.2, total_race_time, (0.82, 0.86, 0.92))

    # Lap times
    draw_text(180, HEIGHT - 385, 2.2, "LAP TIMES:", (0.65, 0.7, 0.78))
    for i, lt in enumerate(race["lap_times"][:NUM_LAPS]):
        draw_time_mmss_cc(180, HEIGHT - 415 - i * 25, 2.0, lt, (0.82, 0.86, 0.92))

    # Right column - Leaderboard
    draw_text(WIDTH - 380, HEIGHT - 210, 2.5, "LEADERBOARD", (0.98, 0.88, 0.12))
    if best_race is not None:
        draw_text(WIDTH - 380, HEIGHT - 245, 2.0, "BEST RACE", (0.65, 0.7, 0.78))
        draw_text(WIDTH - 380, HEIGHT - 268, 2.0, frames_to_time_str(best_race), (0.88, 0.92, 0.98))
    if best_lap is not None:
        draw_text(WIDTH - 380, HEIGHT - 300, 2.0, "BEST LAP", (0.65, 0.7, 0.78))
        draw_text(WIDTH - 380, HEIGHT - 323, 2.0, frames_to_time_str(best_lap), (0.88, 0.92, 0.98))

    draw_text(WIDTH - 380, HEIGHT - 360, 2.0, "TRACK", (0.65, 0.7, 0.78))
    draw_text(WIDTH - 380, HEIGHT - 383, 2.0, level_name, (0.88, 0.92, 0.98))

    # Options
    labels = ["RESTART (R)", "NEXT LEVEL", "MAIN MENU (M)"]
    for i, lb in enumerate(labels):
        col = (0.98, 0.88, 0.12) if i == finish_option else (0.65, 0.7, 0.78)
        marker = "> " if i == finish_option else "  "
        draw_text(180, HEIGHT - 480 - i * 28, 2.5, marker + lb, col)

def draw_banner():
    """Draw temporary banner message."""
    quad(WIDTH * 0.5 - 180, HEIGHT * 0.65 - 24, WIDTH * 0.5 + 180, HEIGHT * 0.65 + 24, (0.04, 0.04, 0.08))
    draw_text(WIDTH * 0.5 - len(banner_text) * 7, HEIGHT * 0.65 - 10, 3.0, banner_text, (0.98, 0.88, 0.12))

def draw_menu():
    """Draw main menu with options."""
    # Background
    quad(20, 20, WIDTH - 20, HEIGHT - 20, (0.1, 0.1, 0.16))
    quad(24, 24, WIDTH - 24, HEIGHT - 24, (0.06, 0.06, 0.11))

    # Title
    draw_text(WIDTH * 0.5 - 140, HEIGHT - 100, 5.5, "INITIAL D", (0.95, 0.2, 0.58))
    draw_text(WIDTH * 0.5 - 100, HEIGHT - 145, 3.0, "COMPLETE EDITION", (0.58, 0.63, 0.72))

    # Instructions
    draw_text(50, HEIGHT - 185, 2.2, "ENTER: START RACE", (0.72, 0.78, 0.85))
    draw_text(50, HEIGHT - 212, 2.2, "UP/DOWN: SELECT   LEFT/RIGHT: ADJUST", (0.58, 0.63, 0.72))

    # Menu options
    items = [
        f"LEVEL: {level_name}",
        f"AI COUNT: {ai_count}",
        f"DIFFICULTY: {DIFFICULTY_PRESETS[difficulty_index][0]}",
        f"THROTTLE: {keybinds['throttle'].upper()}",
        f"BRAKE: {keybinds['brake'].upper()}",
        f"STEER LEFT: {keybinds['left'].upper()}",
        f"STEER RIGHT: {keybinds['right'].upper()}",
        f"SOUND: {'ON' if sound_on else 'OFF'}",
        f"MUSIC: {'ON' if music_on else 'OFF'}",
    ]

    for i, item in enumerate(items):
        ypos = HEIGHT - 260 - i * 30
        is_sel = (i == menu_option)
        col = (0.98, 0.88, 0.12) if is_sel else (0.62, 0.68, 0.75)
        prefix = "> " if is_sel else "  "
        draw_text(70, ypos, 2.5, prefix + item, col)

    if waiting_for_bind is not None:
        draw_text(70, 70, 2.8, f"PRESS KEY FOR {waiting_for_bind.upper()}...", (0.98, 0.38, 0.38))

    # Level list
    draw_text(WIDTH * 0.55, HEIGHT - 260, 2.2, "LEVELS:", (0.65, 0.7, 0.78))
    for i, preset in enumerate(LEVEL_PRESETS):
        locked = i >= unlocked_levels
        label = f"{i + 1}. {preset[0]}"
        if locked:
            col = (0.28, 0.28, 0.32)
            label += " (LOCKED)"
        elif i == level_index:
            col = (0.98, 0.88, 0.12)
        else:
            col = (0.52, 0.58, 0.65)
        draw_text(WIDTH * 0.55, HEIGHT - 288 - i * 24, 2.0, label, col)

    # Best times
    draw_text(WIDTH * 0.55, 150, 2.2, "BEST TIMES:", (0.65, 0.7, 0.78))
    entries = sorted(best_times.items(), key=lambda kv: kv[1])[:5]
    if not entries:
        draw_text(WIDTH * 0.55, 125, 2.0, "NO RECORDS YET", (0.38, 0.4, 0.45))
    else:
        for i, (name, frames) in enumerate(entries):
            draw_text(WIDTH * 0.55, 125 - i * 22, 2.0, f"{name[:6]}: {frames_to_time_str(frames)}", (0.58, 0.63, 0.72))

    # Token bank
    draw_text(50, 35, 2.2, f"TOKEN BANK: {total_tokens_bank}   |   UNLOCKED: {unlocked_levels}/{len(LEVEL_PRESETS)}", (0.48, 0.53, 0.62))

    # Controls hint
    draw_text(WIDTH * 0.55, 60, 1.8, "CONTROLS: W/S or UP/DOWN - Accelerate/Brake | A/D or LEFT/RIGHT - Steer | C - Camera | P - Pause | ESC - Quit", (0.45, 0.5, 0.58))

# =============================================================================
# GAME LOGIC (ANIMATE FUNCTION)
# =============================================================================

def animate():
    """Main game loop update function."""
    global last_time, world_time, quit_requested
    global game_state, countdown_timer, banner_timer
    global race_frame, last_lap_frame_mark, current_lap_trace
    global drift_combo, boost_active_timer, boost_flash_timer
    global respawn_prompt_timer, respawn_invuln_timer

    if quit_requested:
        for k in controls:
            controls[k] = False
        player["speed"] = 0.0
        glutPostRedisplay()
        return

    now = time.perf_counter()
    dt = now - last_time
    last_time = now
    if dt > DT_MAX:
        dt = DT_MAX

    world_time += dt * FPS_TARGET
    update_atmosphere(dt)

    if banner_timer > 0:
        banner_timer -= dt
    if boost_active_timer > 0:
        boost_active_timer = max(0.0, boost_active_timer - dt)
    if boost_flash_timer > 0:
        boost_flash_timer = max(0.0, boost_flash_timer - dt)
    if respawn_prompt_timer > 0:
        respawn_prompt_timer = max(0.0, respawn_prompt_timer - dt)
    if respawn_invuln_timer > 0:
        respawn_invuln_timer = max(0.0, respawn_invuln_timer - dt)

    # Reset drift combo when not drifting
    if game_state == "race":
        drift_combo = max(0, drift_combo - 1)

    if game_state == "menu":
        glutPostRedisplay()
        return

    if game_state == "countdown":
        countdown_timer -= dt
        if countdown_timer <= 0:
            game_state = "race"
            race["lap_start"] = time.perf_counter()
            race["start_time"] = race["lap_start"]
        glutPostRedisplay()
        return

    if game_state == "pause":
        glutPostRedisplay()
        return

    if game_state == "finish" or race["done"]:
        glutPostRedisplay()
        return

    # --- Active race state ---
    now = time.perf_counter()
    for name in controls:
        if controls[name] and now > control_until[name]:
            controls[name] = False

    race_frame += 1
    if race_frame % 2 == 0:
        current_lap_trace.append((float(player["z"]), float(player["x"])))

    prev_z = player["z"]
    update_player_physics(dt)
    update_camera()
    update_ai(dt)
    check_token_collisions()
    check_prop_collisions()
    check_ai_collisions()
    update_particles(dt)
    check_lap_completion(now, prev_z)

    glutPostRedisplay()

def update_player_physics(dt):
    """
    Movement & Drift Physics.
    Lateral movement tracked via player['x'] offset.
    Centrifugal force pushes car outward on curves.
    Drift mechanics add sliding when turning at speed.
    """
    global player_heading, last_player_x, drift_combo

    accel = ACCEL_RATE
    brake = BRAKE_RATE
    friction = FRICTION_RATE
    steer = STEER_STRENGTH

    # Check for boost zone
    in_boost = check_in_boost()
    if in_boost:
        accel += 80.0
    if boost_active_timer > 0.0:
        accel += BOOST_ACCEL_BONUS

    # Acceleration / braking
    if controls["up"]:
        player["speed"] += accel * dt
    elif controls["down"]:
        player["speed"] -= brake * dt
    else:
        player["speed"] -= friction * dt

    # Steering (speed-dependent)
    speed_pct = player["speed"] / player["max_speed"]
    if controls["left"]:
        player["x"] -= steer * dt * (0.5 + speed_pct)
    if controls["right"]:
        player["x"] += steer * dt * (0.5 + speed_pct)

    # Centrifugal force on curves
    seg_index = int(player["z"] / SEGMENT_LENGTH) % TOTAL_SEGMENTS
    seg = segments[seg_index]
    centrifugal = seg["curve"] * player["speed"] * CENTRIFUGAL_FACTOR
    player["x"] -= centrifugal * dt

    # Off-road penalty
    if abs(player["x"]) > 1.0:
        player["speed"] -= OFFROAD_FRICTION * dt

    # Clamp values
    speed_cap = BOOST_SPEED_CAP if boost_active_timer > 0.0 else player["max_speed"]
    if boost_active_timer > 0.0:
        player["speed"] += BOOST_ACCEL_BONUS * 0.45 * dt
    player["speed"] = clamp(player["speed"], 0.0, speed_cap)
    player["x"] = clamp(player["x"], -1.8, 1.8)

    # Drift detection and particle spawning
    lateral_delta = player["x"] - last_player_x
    spawn_drift_particles(lateral_delta)

    # Update heading for headlights
    target_heading = clamp((lateral_delta * 7.0) + (seg["curve"] * 200.0), -1.0, 1.0)
    player_heading += (target_heading - player_heading) * min(1.0, dt * 10.0)
    last_player_x = player["x"]

    # Move forward
    player["z"] = wrap_z(player["z"] + player["speed"] * 60.0 * dt)

def check_in_boost():
    """Check if player is in a boost zone."""
    pz = player["z"]
    for bz0, bz1 in boost_zones:
        # Handle wraparound
        if bz0 < bz1:
            if bz0 <= pz <= bz1:
                return True
        else:
            if pz >= bz0 or pz <= bz1:
                return True
    return False

def update_camera():
    """Update camera position based on mode."""
    seg_index = int(player["z"] / SEGMENT_LENGTH) % TOTAL_SEGMENTS
    seg = segments[seg_index]
    camera["z"] = player["z"]

    if camera_mode == "fpp":
        # First-person: camera at driver eye level
        camera["x"] = player["x"] * 0.8
        camera["y"] = seg["y"] + 200.0
        camera["depth"] = 0.95
    else:
        # Third-person: chase camera
        target_x = player["x"] * 0.25
        camera["x"] += (target_x - camera["x"]) * 0.18
        camera["y"] = CAMERA_HEIGHT + seg["y"]
        camera["depth"] = 0.84

def update_ai(dt):
    """
    Update AI opponent behavior.
    AI always tries to overtake player and blocks randomly.
    AI speed is relative to player speed.
    """
    for ai in opponents:
        old_z = ai["z"]
        seg_idx = int(ai["z"] / SEGMENT_LENGTH) % TOTAL_SEGMENTS
        seg = segments[seg_idx]
        ai["block_timer"] = max(0.0, ai["block_timer"] - dt)
        ai["block_cooldown"] = max(0.0, ai["block_cooldown"] - dt)

        player_progress = entity_progress_player()
        ai_progress = entity_progress_ai(ai)
        gap = player_progress - ai_progress
        ai_dz = (ai["z"] - player["z"] + TRACK_LENGTH) % TRACK_LENGTH
        player_speed = max(80.0, player["speed"])

        # AI speed relative to player - always trying to catch up or beat player
        if gap > 0:
            # AI behind player - try to catch up
            desired_speed = player_speed * (1.02 + ai["aggression"] * 0.06) + clamp(gap / TRACK_LENGTH, 0.0, 0.25) * 120.0
        else:
            # AI ahead of player - try to maintain lead
            desired_speed = player_speed * (0.99 + ai["aggression"] * 0.04) + clamp(-gap / TRACK_LENGTH, 0.0, 0.2) * 60.0

        desired_speed += math.sin(world_time * 0.03 + ai["lane_bias"]) * 5.0
        ai["speed"] += (desired_speed - ai["speed"]) * min(1.0, dt * 3.0)

        # Move forward
        ai["z"] = wrap_z(ai["z"] + ai["speed"] * 50.0 * dt)

        # Weave slightly
        ai["x"] += math.sin(ai["z"] * 0.0008 + ai["lane_bias"]) * dt * 0.12
        ai["x"] += (ai["target_x"] - ai["x"]) * 0.04

        # Centrifugal force
        ai["x"] -= seg["curve"] * 0.018
        ai["x"] = clamp(ai["x"], -0.95, 0.95)

        # AGGRESSIVE BLOCKING - AI blocks player randomly when being overtaken
        if gap < 0 and ai_dz < SEGMENT_LENGTH * 6.0 and player["speed"] > ai["speed"] - 10.0:
            if ai["block_timer"] <= 0.0 and ai["block_cooldown"] <= 0.0 and random.random() < 0.03:
                ai["block_timer"] = random.uniform(1.0, 2.0)
                ai["block_cooldown"] = random.uniform(2.5, 5.0)
                # Move into player's lane to block
                ai["target_x"] = clamp(player["x"] + random.uniform(-0.15, 0.15), -0.9, 0.9)
        elif gap > 0:
            # AI behind player tries to choose passing lanes
            if abs(ai["x"] - player["x"]) < 0.18:
                ai["target_x"] = clamp(player["x"] + (-0.35 if ai["x"] >= player["x"] else 0.35), -0.9, 0.9)
            elif ai["block_timer"] <= 0.0:
                ai["target_x"] = clamp(ai["lane_bias"], -0.85, 0.85)

        if ai["block_timer"] > 0.0:
            # Actively block during block timer
            ai["target_x"] = clamp(player["x"] + math.sin(world_time * 0.05 + ai["aggression"]) * 0.1, -0.9, 0.9)

        diff_mul = DIFFICULTY_PRESETS[difficulty_index][1]
        ai["speed"] = clamp(ai["speed"], 105.0 * diff_mul, 240.0 * diff_mul)

        # Lap counting
        if old_z > ai["z"]:
            ai["lap"] += 1

        # Overtake detection
        if old_z > player["z"] and ai["z"] < player["z"]:
            score["overtakes"] += 1

def check_token_collisions():
    """Check player collision with tokens."""
    for t in tokens:
        if t["taken"]:
            continue
        dz = (t["z"] - player["z"] + TRACK_LENGTH) % TRACK_LENGTH
        if dz < SEGMENT_LENGTH * COLLISION_TOKEN_DZ and abs(t["x"] - player["x"]) < COLLISION_TOKEN_DX:
            t["taken"] = True
            score["tokens"] += 1

def check_prop_collisions():
    """Check player collision with props."""
    for p in props:
        if not p.get("collidable", False):
            continue
        dz = (p["z"] - player["z"] + TRACK_LENGTH) % TRACK_LENGTH
        if dz < SEGMENT_LENGTH * COLLISION_PROP_DZ and abs(p["x"] - player["x"]) < COLLISION_PROP_DX:
            player["speed"] *= 0.15
            score["hits"] += 1
            show_banner("CRASH!")

def check_ai_collisions():
    """Check player collision with AI - triggers respawn prompt."""
    global respawn_prompt_timer, last_collision_source

    if respawn_invuln_timer > 0.0:
        return

    for ai in opponents:
        dz = (ai["z"] - player["z"] + TRACK_LENGTH) % TRACK_LENGTH
        if dz < SEGMENT_LENGTH * COLLISION_AI_DZ and abs(ai["x"] - player["x"]) < COLLISION_AI_DX:
            player["speed"] *= 0.35
            score["hits"] += 1
            respawn_prompt_timer = RESPAWN_PROMPT_DURATION
            last_collision_source = "ai"
            show_banner("CONTACT! LEFT CLICK TO RESPAWN (50 PTS)")

def update_particles(dt):
    """Update particle physics."""
    for puff in particles:
        puff["x"] += puff["vx"] * dt
        puff["y"] += puff["vy"] * dt
        puff["s"] *= 1.025
        puff["life"] -= dt * 0.75
    particles[:] = [p for p in particles if p["life"] > 0.0]

def check_lap_completion(now, prev_z):
    """Detect lap completion."""
    global banner_text, banner_timer, race_frame, last_lap_frame_mark, current_lap_trace, game_state

    if not race["lap_armed"]:
        if player["z"] > TRACK_LENGTH * 0.2:
            race["lap_armed"] = True
        return

    # Detect crossing start/finish line
    if prev_z > TRACK_LENGTH * 0.9 and player["z"] < TRACK_LENGTH * 0.1:
        lap_time = now - race["lap_start"]
        race["lap_times"].append(lap_time)
        race["lap_start"] = now
        race["laps"] += 1
        race["lap_armed"] = False

        lap_frames = race_frame - last_lap_frame_mark
        last_lap_frame_mark = race_frame

        # Check for new lap record
        prev_best = best_lap_times.get(level_name)
        if prev_best is None or lap_frames < prev_best:
            best_lap_times[level_name] = lap_frames
            ghost_laps[level_name] = list(current_lap_trace)
            show_banner("NEW LAP RECORD!")
        else:
            show_banner("LAP COMPLETE!")

        current_lap_trace = []

        # Check race completion
        if race["laps"] >= race["max_laps"]:
            race["done"] = True
            game_state = "finish"
            finalize_race()

def player_position():
    """Calculate player's current race position."""
    player_progress = race["laps"] * TRACK_LENGTH + player["z"]
    ahead = 1
    for ai in opponents:
        ai_progress = ai["lap"] * TRACK_LENGTH + ai["z"]
        if ai_progress > player_progress:
            ahead += 1
    return ahead

def ghost_position():
    """Get ghost car position from best lap."""
    ghost = ghost_laps.get(level_name)
    best_lap = best_lap_times.get(level_name)
    if not ghost or not best_lap:
        return None

    lap_frame = race_frame - last_lap_frame_mark
    if lap_frame < 0:
        lap_frame = 0
    if lap_frame >= best_lap:
        lap_frame = best_lap - 1

    idx = lap_frame // 2
    idx = clamp(idx, 0, len(ghost) - 1)
    if idx < 0:
        return None
    return ghost[idx]

def show_banner(text):
    """Display temporary banner message."""
    global banner_text, banner_timer
    banner_text = text
    banner_timer = 2.5

def finalize_race():
    """Process race end results."""
    global total_tokens_bank, unlocked_levels

    # Add tokens to bank
    total_tokens_bank += score["tokens"]
    old_unlock = unlocked_levels
    unlocked_levels = min(len(LEVEL_PRESETS), 1 + total_tokens_bank // BASE_UNLOCK_TOKENS)

    # Record race time
    race_total = race_frame
    prev_best = best_times.get(level_name)
    if prev_best is None or race_total < prev_best:
        best_times[level_name] = race_total

    if unlocked_levels > old_unlock:
        show_banner("LEVEL UNLOCKED!")

    save_profile()

# =============================================================================
# RACE / MENU STATE MANAGEMENT
# =============================================================================

def start_race():
    """Initialize and start a new race."""
    global game_state, countdown_timer, race_frame, last_lap_frame_mark, current_lap_trace
    global drift_combo, drift_score, max_drift_combo
    global boost_active_timer, boost_flash_timer, respawn_prompt_timer, respawn_invuln_timer

    game_state = "countdown"
    countdown_timer = 3.5
    race_frame = 0
    last_lap_frame_mark = 0
    current_lap_trace = []
    drift_combo = 0
    drift_score = 0
    max_drift_combo = 0
    boost_active_timer = 0.0
    boost_flash_timer = 0.0
    respawn_prompt_timer = 0.0
    respawn_invuln_timer = 0.0
    reset_race()

def reset_race():
    """Reset race state to beginning."""
    global minimap_points, player_heading, last_player_x, last_collision_source

    player["speed"] = 0.0
    player["x"] = 0.0
    player["z"] = 0.0
    player["lap"] = 0
    player_heading = 0.0
    last_player_x = 0.0

    score["tokens"] = 0
    score["hits"] = 0
    score["overtakes"] = 0
    score["boost_used"] = 0
    score["respawns"] = 0

    race["laps"] = 0
    race["lap_start"] = time.perf_counter()
    race["lap_times"] = []
    race["done"] = False
    race["lap_armed"] = False
    last_collision_source = ""

    particles.clear()
    build_track()
    minimap_points = build_minimap_points()

def change_level(direction):
    """Change to next/previous level."""
    global level_index, level_name
    max_idx = max(0, unlocked_levels - 1)
    level_index = (level_index + direction) % (max_idx + 1)
    level_name = LEVEL_PRESETS[level_index][0]
    save_profile()

# =============================================================================
# INPUT HANDLING
# =============================================================================

def hold_control(name, now):
    """Set control to held state."""
    controls[name] = True
    control_until[name] = now + HOLD_TIMEOUT

def keyboard(key, _x, _y):
    """Handle keyboard input."""
    global quit_requested, camera_mode, game_state
    global menu_option, pause_option, finish_option
    global waiting_for_bind, ai_count, difficulty_index
    global sound_on, music_on

    try:
        k = key.decode("utf-8").lower()
    except (UnicodeDecodeError, AttributeError):
        return

    now = time.perf_counter()

    if k == "\x1b":  # ESC
        quit_requested = True
        return

    if waiting_for_bind is not None:
        if len(k) == 1 and k.isprintable():
            # Swap keybinds if key already assigned
            for action, bound in list(keybinds.items()):
                if bound == k:
                    keybinds[action] = keybinds[waiting_for_bind]
            keybinds[waiting_for_bind] = k
            waiting_for_bind = None
            save_profile()
        return

    if game_state == "menu":
        if k == "\r":  # Enter
            start_race()
        return

    if game_state == "countdown":
        return

    if game_state == "pause":
        if k == "p" or k == "\r":
            if k == "p":
                game_state = "race"
            elif k == "\r":
                if pause_option == 0:
                    game_state = "race"
                elif pause_option == 1:
                    start_race()
                elif pause_option == 2:
                    game_state = "menu"
        return

    if game_state == "finish" or race["done"]:
        if k == "\r":
            if finish_option == 0:
                start_race()
            elif finish_option == 1:
                if level_index + 1 < unlocked_levels:
                    change_level(1)
                start_race()
            elif finish_option == 2:
                game_state = "menu"
        elif k == "m":
            game_state = "menu"
        return

    if k == "p":
        game_state = "pause"
        pause_option = 0
        return

    if k == "r":
        start_race()
        return

    if k == "m":
        game_state = "menu"
        return

    if k == "c":
        camera_mode = "fpp" if camera_mode == "tpp" else "tpp"
        return

    # Keybind-based controls
    if k == keybinds["throttle"]:
        hold_control("up", now)
        controls["down"] = False
        control_until["down"] = 0.0
    elif k == keybinds["brake"]:
        hold_control("down", now)
        controls["up"] = False
        control_until["up"] = 0.0
    elif k == keybinds["left"]:
        hold_control("left", now)
        controls["right"] = False
        control_until["right"] = 0.0
    elif k == keybinds["right"]:
        hold_control("right", now)
        controls["left"] = False
        control_until["left"] = 0.0
    elif k == " ":
        controls["left"] = False
        controls["right"] = False
        control_until["left"] = 0.0
        control_until["right"] = 0.0
    elif k == "x":
        controls["up"] = False
        controls["down"] = False
        control_until["up"] = 0.0
        control_until["down"] = 0.0

def special(key, _x, _y):
    """Handle special keys (arrows, function keys)."""
    global menu_option, pause_option, finish_option
    global ai_count, difficulty_index, waiting_for_bind
    global sound_on, music_on

    now = time.perf_counter()

    if game_state == "menu":
        if key == GLUT_KEY_UP:
            menu_option = max(0, menu_option - 1)
        elif key == GLUT_KEY_DOWN:
            menu_option = min(8, menu_option + 1)
        elif key == GLUT_KEY_LEFT or key == GLUT_KEY_RIGHT:
            direction = 1 if key == GLUT_KEY_RIGHT else -1
            if menu_option == 0:
                change_level(direction)
            elif menu_option == 1:
                ai_count = clamp(ai_count + direction, 2, 12)
                save_profile()
            elif menu_option == 2:
                difficulty_index = (difficulty_index + direction) % len(DIFFICULTY_PRESETS)
                save_profile()
            elif menu_option == 3:
                waiting_for_bind = "throttle"
            elif menu_option == 4:
                waiting_for_bind = "brake"
            elif menu_option == 5:
                waiting_for_bind = "left"
            elif menu_option == 6:
                waiting_for_bind = "right"
            elif menu_option == 7:
                sound_on = not sound_on
                save_profile()
            elif menu_option == 8:
                music_on = not music_on
                save_profile()
        return

    if game_state == "pause":
        if key == GLUT_KEY_UP:
            pause_option = max(0, pause_option - 1)
        elif key == GLUT_KEY_DOWN:
            pause_option = min(2, pause_option + 1)
        return

    if game_state == "finish" or race["done"]:
        if key in (GLUT_KEY_LEFT, GLUT_KEY_UP):
            finish_option = max(0, finish_option - 1)
        elif key in (GLUT_KEY_RIGHT, GLUT_KEY_DOWN):
            finish_option = min(2, finish_option + 1)
        return

    # Racing controls
    if key == GLUT_KEY_UP:
        hold_control("up", now)
        controls["down"] = False
        control_until["down"] = 0.0
    elif key == GLUT_KEY_DOWN:
        hold_control("down", now)
        controls["up"] = False
        control_until["up"] = 0.0
    elif key == GLUT_KEY_LEFT:
        hold_control("left", now)
        controls["right"] = False
        control_until["right"] = 0.0
    elif key == GLUT_KEY_RIGHT:
        hold_control("right", now)
        controls["left"] = False
        control_until["left"] = 0.0

def mouse(button, state, x, y):
    """
    Handle mouse input.
    LEFT CLICK: Activate boost (20 pts) OR Respawn after collision (50 pts)
    """
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        if game_state == "race":
            if respawn_prompt_timer > 0.0:
                # Try to respawn after collision
                if not attempt_respawn():
                    show_banner(f"NEED {RESPAWN_COST} TOKENS TO RESPAWN")
            else:
                # Try to activate boost
                if not activate_player_boost():
                    show_banner(f"NEED {BOOST_COST} TOKENS FOR BOOST")

def reshape(width, height):
    """Handle window resize."""
    glViewport(0, 0, width, height)

# =============================================================================
# PROFILE PERSISTENCE
# =============================================================================

def profile_path():
    """Get path to profile file."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), PROFILE_FILE)

def load_profile():
    """Load player profile from disk."""
    global total_tokens_bank, unlocked_levels, best_times, best_lap_times
    global ghost_laps, ai_count, difficulty_index, keybinds
    global sound_on, music_on, level_index, level_name

    path = profile_path()
    if not os.path.exists(path):
        return

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        total_tokens_bank = int(data.get("total_tokens_bank", 0))
        unlocked_levels = clamp(int(data.get("unlocked_levels", 1)), 1, len(LEVEL_PRESETS))

        # Best times
        best_times = {}
        raw_bt = data.get("best_times", {})
        if isinstance(raw_bt, dict):
            for k, v in raw_bt.items():
                try:
                    best_times[str(k)] = int(v)
                except (ValueError, TypeError):
                    continue

        # Best lap times
        best_lap_times = {}
        raw_blt = data.get("best_lap_times", {})
        if isinstance(raw_blt, dict):
            for k, v in raw_blt.items():
                try:
                    best_lap_times[str(k)] = int(v)
                except (ValueError, TypeError):
                    continue

        # Ghost laps
        ghost_laps = {}
        raw_gl = data.get("ghost_laps", {})
        if isinstance(raw_gl, dict):
            for lvl, arr in raw_gl.items():
                if not isinstance(arr, list):
                    continue
                cleaned = []
                for entry in arr:
                    if isinstance(entry, list) and len(entry) == 2:
                        try:
                            cleaned.append((float(entry[0]), float(entry[1])))
                        except (ValueError, TypeError):
                            continue
                if cleaned:
                    ghost_laps[str(lvl)] = cleaned

        ai_count = clamp(int(data.get("ai_count", NUM_AI)), 2, 12)
        difficulty_index = int(data.get("difficulty_index", 1)) % len(DIFFICULTY_PRESETS)
        sound_on = bool(data.get("sound_on", True))
        music_on = bool(data.get("music_on", True))

        # Keybinds
        raw_binds = data.get("keybinds", {})
        if isinstance(raw_binds, dict):
            for action in keybinds:
                value = raw_binds.get(action)
                if isinstance(value, str) and len(value) == 1:
                    keybinds[action] = value.lower()

        loaded_level = clamp(int(data.get("level_index", 0)), 0, unlocked_levels - 1)
        level_index = loaded_level
        level_name = LEVEL_PRESETS[level_index][0]

    except (OSError, json.JSONDecodeError, ValueError):
        pass

def save_profile():
    """Save player profile to disk."""
    data = {
        "total_tokens_bank": total_tokens_bank,
        "unlocked_levels": unlocked_levels,
        "best_times": best_times,
        "best_lap_times": best_lap_times,
        "ghost_laps": ghost_laps,
        "level_index": level_index,
        "ai_count": ai_count,
        "difficulty_index": difficulty_index,
        "keybinds": keybinds,
        "sound_on": sound_on,
        "music_on": music_on,
    }
    try:
        with open(profile_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass

# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    """Main entry point."""
    global last_time, minimap_points

    load_profile()
    build_track()
    minimap_points = build_minimap_points()

    last_time = time.perf_counter()
    race["lap_start"] = last_time

    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA)
    glutInitWindowSize(WIDTH, HEIGHT)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(TITLE)

    glutDisplayFunc(display)
    glutIdleFunc(animate)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special)
    glutMouseFunc(mouse)
    glutReshapeFunc(reshape)

    glutMainLoop()

if __name__ == "__main__":
    main()
