#!/usr/bin/env python3
"""
PAC-MAN ULTIMATE - A Classic Pac-Man Game with AI Ghosts, Minigames & Intense Music!
Built by Toby with help from Copilot
"""

import pygame
import pygame.gfxdraw
import sys
import math
import random
import array

# ─── INITIALISE ──────────────────────────────────────────────────────────────
pygame.init()
SOUND_ENABLED = True
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
except pygame.error:
    SOUND_ENABLED = False
    print(">> Audio not available — running without sound")

TILE = 24
COLS, ROWS = 28, 31
WIDTH = TILE * COLS
HEIGHT = TILE * ROWS + 100  # extra space for HUD + rival scores
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PAC-MAN ULTIMATE")
clock = pygame.time.Clock()

# ─── COLOURS ─────────────────────────────────────────────────────────────────
BLACK   = (0, 0, 0)
YELLOW  = (255, 255, 0)
WHITE   = (255, 255, 255)
BLUE    = (33, 33, 222)
RED     = (255, 0, 0)
PINK    = (255, 184, 255)
CYAN    = (0, 255, 255)
ORANGE  = (255, 184, 82)
SCARED  = (33, 33, 222)
WALL_BG = (0, 0, 40)
DOT_COL = (255, 183, 174)
PURPLE  = (148, 0, 211)
GREEN   = (0, 200, 0)
GREY    = (128, 128, 128)
GOLD    = (255, 215, 0)

# ─── PARTICLE SYSTEM ────────────────────────────────────────────────────────
class Particle:
    """A single visual particle with physics and fade."""
    __slots__ = ['x', 'y', 'vx', 'vy', 'color', 'life', 'max_life', 'size', 'gravity', 'shape']

    def __init__(self, x, y, vx, vy, color, life, size=3, gravity=0, shape='circle'):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size
        self.gravity = gravity
        self.shape = shape

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.vx *= 0.98
        self.life -= dt
        return self.life > 0

    def draw(self, surface):
        alpha = max(0, min(255, int(255 * (self.life / self.max_life))))
        r = max(1, int(self.size * (self.life / self.max_life)))
        col = (*self.color[:3], alpha)
        if self.shape == 'circle':
            if r > 1:
                try:
                    pygame.gfxdraw.filled_circle(surface, int(self.x), int(self.y), r, col)
                    pygame.gfxdraw.aacircle(surface, int(self.x), int(self.y), r, col)
                except (ValueError, OverflowError):
                    pass
            else:
                try:
                    surface.set_at((int(self.x), int(self.y)), col[:3])
                except IndexError:
                    pass
        elif self.shape == 'spark':
            end_x = self.x + self.vx * 0.03
            end_y = self.y + self.vy * 0.03
            try:
                pygame.draw.aaline(surface, col[:3], (self.x, self.y), (end_x, end_y))
            except (ValueError, OverflowError):
                pass
        elif self.shape == 'star':
            for angle_off in range(0, 360, 72):
                rad = math.radians(angle_off + self.life * 200)
                ex = self.x + r * math.cos(rad)
                ey = self.y + r * math.sin(rad)
                try:
                    pygame.draw.aaline(surface, col[:3], (self.x, self.y), (ex, ey))
                except (ValueError, OverflowError):
                    pass


class ParticleSystem:
    """Manages all active particles."""
    def __init__(self):
        self.particles = []

    def emit_dot_eat(self, x, y, color):
        """Small sparkle burst when eating a dot."""
        for _ in range(6):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(30, 80)
            self.particles.append(Particle(
                x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                color, random.uniform(0.2, 0.4), size=2, shape='spark'
            ))

    def emit_power_pellet(self, x, y):
        """Big radial glow burst for power pellet."""
        for _ in range(20):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 180)
            colors = [YELLOW, WHITE, CYAN, (255, 100, 255)]
            self.particles.append(Particle(
                x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                random.choice(colors), random.uniform(0.4, 0.9),
                size=random.randint(2, 5), shape='circle'
            ))
        # Shockwave ring
        for i in range(24):
            angle = i * (2 * math.pi / 24)
            self.particles.append(Particle(
                x, y, math.cos(angle) * 150, math.sin(angle) * 150,
                WHITE, 0.3, size=2, shape='spark'
            ))

    def emit_ghost_eat(self, x, y, ghost_color):
        """Explosion when eating a ghost."""
        for _ in range(30):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(60, 200)
            self.particles.append(Particle(
                x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                ghost_color, random.uniform(0.3, 0.8),
                size=random.randint(2, 6), gravity=100, shape='circle'
            ))
        for _ in range(8):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(40, 120)
            self.particles.append(Particle(
                x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                WHITE, random.uniform(0.5, 1.0), size=4, shape='star'
            ))

    def emit_death(self, x, y):
        """Dramatic death burst."""
        for _ in range(50):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(30, 250)
            self.particles.append(Particle(
                x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                YELLOW, random.uniform(0.5, 1.5),
                size=random.randint(2, 7), gravity=150, shape='circle'
            ))
        for _ in range(15):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(80, 200)
            self.particles.append(Particle(
                x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                RED, random.uniform(0.3, 0.8), size=3, shape='spark'
            ))

    def emit_level_clear(self):
        """Fireworks across the whole screen."""
        for _ in range(8):
            cx = random.randint(50, WIDTH - 50)
            cy = random.randint(80, HEIGHT - 80)
            color = random.choice([YELLOW, CYAN, RED, PINK, GREEN, ORANGE, GOLD, WHITE])
            for _ in range(25):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(80, 250)
                self.particles.append(Particle(
                    cx, cy, math.cos(angle) * speed, math.sin(angle) * speed,
                    color, random.uniform(0.5, 1.5),
                    size=random.randint(2, 5), gravity=120, shape='circle'
                ))

    def emit_fruit(self, x, y):
        """Sparkle ring for fruit pickup."""
        for i in range(16):
            angle = i * (2 * math.pi / 16)
            self.particles.append(Particle(
                x, y, math.cos(angle) * 100, math.sin(angle) * 100,
                GOLD, 0.5, size=3, shape='star'
            ))

    def emit_trail(self, x, y, color):
        """Small trail particle behind moving entity."""
        self.particles.append(Particle(
            x + random.uniform(-3, 3), y + random.uniform(-3, 3),
            random.uniform(-10, 10), random.uniform(-10, 10),
            color, random.uniform(0.1, 0.25), size=2, shape='circle'
        ))

    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

    def clear(self):
        self.particles.clear()


# ─── SCORE POPUP SYSTEM ─────────────────────────────────────────────────────
class ScorePopup:
    """Floating score text that rises and fades."""
    def __init__(self, x, y, text, color, font):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.font = font
        self.life = 1.2
        self.max_life = 1.2

    def update(self, dt):
        self.y -= 40 * dt
        self.life -= dt
        return self.life > 0

    def draw(self, surface):
        alpha = max(0, min(255, int(255 * (self.life / self.max_life))))
        txt_surf = self.font.render(self.text, True, self.color)
        txt_surf.set_alpha(alpha)
        surface.blit(txt_surf, (int(self.x) - txt_surf.get_width() // 2, int(self.y)))


class ScorePopupSystem:
    """Manages floating score popups."""
    def __init__(self):
        self.popups = []

    def add(self, x, y, text, color, font):
        self.popups.append(ScorePopup(x, y, text, color, font))

    def update(self, dt):
        self.popups = [p for p in self.popups if p.update(dt)]

    def draw(self, surface):
        for p in self.popups:
            p.draw(surface)

    def clear(self):
        self.popups.clear()


# ─── SCREEN TRANSITION SYSTEM ───────────────────────────────────────────────
class ScreenTransition:
    """Handles fade, wipe, and pixelate screen transitions."""
    def __init__(self):
        self.active = False
        self.type = 'fade'  # fade, wipe, flash
        self.progress = 0.0
        self.duration = 0.5
        self.direction = 'in'  # in = going dark, out = coming back
        self.callback = None
        self.fade_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.flash_color = WHITE

    def start(self, trans_type='fade', duration=0.5, direction='in', callback=None, flash_color=WHITE):
        self.active = True
        self.type = trans_type
        self.duration = duration
        self.direction = direction
        self.progress = 0.0
        self.callback = callback
        self.flash_color = flash_color

    def update(self, dt):
        if not self.active:
            return
        self.progress += dt / self.duration
        if self.progress >= 1.0:
            self.active = False
            self.progress = 1.0
            if self.callback:
                self.callback()
                self.callback = None

    def draw(self, surface):
        if not self.active:
            return
        t = self.progress if self.direction == 'in' else (1.0 - self.progress)

        if self.type == 'fade':
            alpha = int(255 * t)
            self.fade_surface.fill((0, 0, 0, alpha))
            surface.blit(self.fade_surface, (0, 0))

        elif self.type == 'flash':
            alpha = int(200 * (1.0 - t))
            self.fade_surface.fill((*self.flash_color[:3], alpha))
            surface.blit(self.fade_surface, (0, 0))

        elif self.type == 'wipe':
            wipe_x = int(WIDTH * t)
            pygame.draw.rect(surface, BLACK, (0, 0, wipe_x, HEIGHT))


# ─── SCREEN SHAKE ────────────────────────────────────────────────────────────
class ScreenShake:
    """Camera shake effect."""
    def __init__(self):
        self.intensity = 0
        self.duration = 0
        self.offset_x = 0
        self.offset_y = 0

    def start(self, intensity=5, duration=0.3):
        self.intensity = intensity
        self.duration = duration

    def update(self, dt):
        if self.duration > 0:
            self.duration -= dt
            self.offset_x = random.randint(-int(self.intensity), int(self.intensity))
            self.offset_y = random.randint(-int(self.intensity), int(self.intensity))
            self.intensity = max(0, self.intensity - dt * 10)
        else:
            self.offset_x = 0
            self.offset_y = 0


# ─── SOUND GENERATOR ────────────────────────────────────────────────────────
def generate_tone(freq, duration_ms, volume=0.3, wave='square'):
    """Generate a retro chiptune tone."""
    sample_rate = 44100
    n_samples = int(sample_rate * duration_ms / 1000)
    buf = array.array('h', [0] * n_samples)
    max_amp = int(32767 * volume)
    for i in range(n_samples):
        t = i / sample_rate
        if wave == 'square':
            val = max_amp if math.sin(2 * math.pi * freq * t) >= 0 else -max_amp
        elif wave == 'sine':
            val = int(max_amp * math.sin(2 * math.pi * freq * t))
        elif wave == 'saw':
            val = int(max_amp * (2 * (freq * t % 1) - 1))
        else:
            val = max_amp if math.sin(2 * math.pi * freq * t) >= 0 else -max_amp
        # Fade out last 10%
        fade_start = int(n_samples * 0.9)
        if i > fade_start:
            val = int(val * (n_samples - i) / (n_samples - fade_start))
        buf[i] = max(-32768, min(32767, val))
    sound = pygame.mixer.Sound(buffer=buf)
    return sound

def generate_music_loop(tempo_bpm=140, bars=4):
    """Generate an intense chiptune music loop."""
    sample_rate = 44100
    beat = 60 / tempo_bpm
    total_beats = bars * 4
    total_samples = int(sample_rate * beat * total_beats)
    buf = array.array('h', [0] * total_samples)
    max_amp = 3500

    # Bass line (driving rhythm)
    bass_notes = [110, 110, 130.81, 130.81, 146.83, 146.83, 130.81, 130.81] * (bars // 2 + 1)
    # Melody (intense and catchy)
    melody_notes = [440, 523.25, 587.33, 523.25, 440, 392, 440, 523.25,
                    587.33, 659.25, 587.33, 523.25, 440, 523.25, 587.33, 440]
    # Arpeggios
    arp_notes = [220, 277.18, 329.63, 440, 329.63, 277.18] * 6

    for i in range(total_samples):
        t = i / sample_rate
        beat_pos = t / beat
        val = 0

        # Bass (square wave, plays every beat)
        bass_idx = int(beat_pos) % len(bass_notes)
        bass_freq = bass_notes[bass_idx]
        val += int(max_amp * 1.2) if math.sin(2 * math.pi * bass_freq * t) >= 0 else int(-max_amp * 1.2)

        # Melody (plays every half beat)
        mel_idx = int(beat_pos * 2) % len(melody_notes)
        mel_freq = melody_notes[mel_idx]
        val += int(max_amp * 0.7 * math.sin(2 * math.pi * mel_freq * t))

        # Arpeggio (fast, every quarter beat)
        arp_idx = int(beat_pos * 4) % len(arp_notes)
        arp_freq = arp_notes[arp_idx]
        arp_wave = 1 if math.sin(2 * math.pi * arp_freq * t) >= 0 else -1
        val += int(max_amp * 0.3 * arp_wave)

        # Hi-hat noise on every beat
        if (beat_pos * 4) % 1 < 0.05:
            val += random.randint(-max_amp // 3, max_amp // 3)

        buf[i] = max(-32768, min(32767, val))

    return pygame.mixer.Sound(buffer=buf)

def generate_chase_music():
    """Extra intense music for ghost chase / power mode."""
    sample_rate = 44100
    tempo = 170
    beat = 60 / tempo
    total_samples = int(sample_rate * beat * 16)
    buf = array.array('h', [0] * total_samples)
    max_amp = 3200
    notes = [196, 233.08, 261.63, 293.66, 349.23, 293.66, 261.63, 233.08]

    for i in range(total_samples):
        t = i / sample_rate
        beat_pos = t / beat
        idx = int(beat_pos * 3) % len(notes)
        freq = notes[idx]
        val = int(max_amp * 1.0) if math.sin(2 * math.pi * freq * t) >= 0 else int(-max_amp * 1.0)
        # Wobble effect
        val = int(val * (0.7 + 0.3 * math.sin(2 * math.pi * 6 * t)))
        buf[i] = max(-32768, min(32767, val))

    return pygame.mixer.Sound(buffer=buf)

# Pre-generate sounds
print(">>  Generating sounds...")
snd_chomp     = generate_tone(300, 60, 0.2, 'square')
snd_eat_ghost = generate_tone(600, 200, 0.3, 'saw')
snd_death     = generate_tone(200, 500, 0.4, 'sine')
snd_power     = generate_tone(150, 300, 0.3, 'square')
snd_menu      = generate_tone(440, 150, 0.2, 'sine')
snd_win       = generate_tone(880, 400, 0.3, 'sine')
snd_siren     = generate_tone(180, 800, 0.15, 'saw')
print(">>  Generating music loops...")
music_main    = generate_music_loop(140, 4)
music_chase   = generate_chase_music()
music_ghost_tag = generate_music_loop(160, 4)
print(">>  Audio ready!")

# ─── CLASSIC PAC-MAN MAZE ───────────────────────────────────────────────────
# 0=empty, 1=wall, 2=dot, 3=power pellet, 4=ghost house, 5=gate
MAZE_TEMPLATE = [
    "1111111111111111111111111111",
    "1222222222222112222222222221",
    "1211112111112112111121111121",
    "1311112111112112111121111131",
    "1211112111112112111121111121",
    "1222222222222222222222222221",
    "1211112112111111211211112121",
    "1211112112111111211211112121",
    "1222222112222112222112222221",
    "1111112111110110111121111121",
    "0000012111110110111121000000",
    "0000012110000000011212000000",
    "0000012110144441011212000000",
    "1111112110140041011211111111",
    "0000002000140041000200000000",
    "1111112110140041011211111111",
    "0000012110144441011212000000",
    "0000012110000000011212000000",
    "0000012110111111011212000000",
    "1111112110111111011211111111",
    "1222222222222112222222222221",
    "1211112111112112111121111121",
    "1211112111112112111121111121",
    "1322112222222002222222112231",
    "1112112112111111211211211121",
    "1112112112111111211211211121",
    "1222222212222112222122222221",
    "1211111111112112111111111121",
    "1211111111112112111111111121",
    "1222222222222222222222222221",
    "1111111111111111111111111111",
]

# Level 2: "The Arena" — open centre, tight corridors on edges
MAZE_LEVEL2 = [
    "1111111111111111111111111111",
    "1222222222222222222222222221",
    "1211112111112112111121111121",
    "1311110000002002000001111131",
    "1211110000002002000001111121",
    "1222221111112112111122222221",
    "1212222222222222222222221121",
    "1212111112110110112111121121",
    "1212222212210110122222121121",
    "1211112212111111122111121121",
    "0000002212000000022000000000",
    "0000002212000000022000000000",
    "0000002210144441022000000000",
    "1111112210140041022111111111",
    "0000002000140041000200000000",
    "1111112210140041022111111111",
    "0000002210144441022000000000",
    "0000002210000000022000000000",
    "0000002212111111122000000000",
    "1111112212111111122111111111",
    "1222222222222222222222222221",
    "1211222111200002111222111121",
    "1212222111202202111222121121",
    "1312002222202202222200213121",
    "1212002112202202211200121121",
    "1212222112200002211222121121",
    "1212222112222222211222121121",
    "1211111112211112211111111121",
    "1222222222211112222222222221",
    "1222222222222222222222222221",
    "1111111111111111111111111111",
]

# Level 3: "The Labyrinth" — winding paths, more power pellets
MAZE_LEVEL3 = [
    "1111111111111111111111111111",
    "1222222222221221222222222221",
    "1211212111121221211112121121",
    "1312212111121221211112121131",
    "1211212222221221222212121121",
    "1211212111100001111212121121",
    "1222212111102201111212222221",
    "1211212222202202222212121121",
    "1211111112202202211111121121",
    "1222222212200002212222222221",
    "0000012212211112212120000000",
    "0000012212200002212120000000",
    "0000012210144441012120000000",
    "1111112210140041012111111111",
    "0000002000140041000200000000",
    "1111112210140041012111111111",
    "0000012210144441012120000000",
    "0000012210000000012120000000",
    "0000012212111111212120000000",
    "1111112212111111212111111111",
    "1222222222222222222222222221",
    "1213211121222222112113121121",
    "1212211121222222112112121121",
    "1312211002222222001112121131",
    "1212211121211112112112121121",
    "1212211121211112112112121121",
    "1222222222211112222222222221",
    "1211111112222222211111111121",
    "1211111112211112211111111121",
    "1222222222211112222222222221",
    "1111111111111111111111111111",
]

# Level 4: "The Fortress" — thick walls, strategic corridors
MAZE_LEVEL4 = [
    "1111111111111111111111111111",
    "1222222222222222222222222221",
    "1211111211111111112111111121",
    "1312222211222222112222213121",
    "1211222211211112112222111121",
    "1222211111211112111112222221",
    "1222211111200002111112222221",
    "1211211112200002211112111121",
    "1211222222211112222222111121",
    "1211222112211112211222111121",
    "0000222112200002211222000000",
    "0000222112200002211222000000",
    "0000222110144441011222000000",
    "1111111110140041011111111111",
    "0000002000140041000200000000",
    "1111111110140041011111111111",
    "0000222110144441011222000000",
    "0000222112000000211222000000",
    "0000222112111111211222000000",
    "1111222112111111211222111111",
    "1222222222222222222222222221",
    "1312111121222222121111213121",
    "1212111121222222121111121121",
    "1212222222200002222222121121",
    "1212222121211112121222121121",
    "1211111121211112121111111121",
    "1222222222211112222222222221",
    "1211111111222222111111111121",
    "1211111111211112111111111121",
    "1232222222222222222222222321",
    "1111111111111111111111111111",
]

# Level 5: "The Gauntlet" — narrow corridors, many ghosts, lots of power pellets
MAZE_LEVEL5 = [
    "1111111111111111111111111111",
    "1322222221222221222222222321",
    "1212111121212121121111121121",
    "1212111121212121121111121121",
    "1212222222212121222222121121",
    "1211112112212121211111122221",
    "1222222112212121211222222221",
    "1211112112212121211211111121",
    "1222222112222222211222222221",
    "1211112112111111211211111121",
    "0000002112000000211200000000",
    "0000002112000000211200000000",
    "0000002110144441011200000000",
    "1111112110140041011211111111",
    "0000002000140041000200000000",
    "1111112110140041011211111111",
    "0000002110144441011200000000",
    "0000002112000000211200000000",
    "0000002112111111211200000000",
    "1111112112111111211211111111",
    "1222222222222222222222222221",
    "1212112121222222121211212121",
    "1212112121222222121211212121",
    "1312002020200002020200213121",
    "1212112121211112121211212121",
    "1212112121211112121211212121",
    "1222222222211112222222222221",
    "1211112111222222111211111121",
    "1211112111211112111211111121",
    "1322222222222222222222222321",
    "1111111111111111111111111111",
]

ALL_MAZES = [MAZE_TEMPLATE, MAZE_LEVEL2, MAZE_LEVEL3, MAZE_LEVEL4, MAZE_LEVEL5]

# ─── LEVEL COLOUR THEMES ────────────────────────────────────────────────────
LEVEL_THEMES = [
    {   # Level 1: Classic Blue
        'name': 'CLASSIC',
        'wall': (33, 33, 222),
        'dot': (255, 183, 174),
        'bg': (0, 0, 0),
        'pellet': (255, 183, 174),
        'gate': (255, 184, 255),
        'text_accent': (33, 33, 222),
    },
    {   # Level 2: Neon Green
        'name': 'NEON ARENA',
        'wall': (0, 255, 100),
        'dot': (200, 255, 200),
        'bg': (5, 15, 5),
        'pellet': (0, 255, 0),
        'gate': (255, 255, 0),
        'text_accent': (0, 255, 100),
    },
    {   # Level 3: Purple Labyrinth
        'name': 'SHADOW MAZE',
        'wall': (180, 0, 255),
        'dot': (220, 180, 255),
        'bg': (10, 0, 20),
        'pellet': (255, 100, 255),
        'gate': (255, 150, 255),
        'text_accent': (180, 0, 255),
    },
    {   # Level 4: Fire Fortress
        'name': 'FIRE FORTRESS',
        'wall': (255, 100, 0),
        'dot': (255, 220, 150),
        'bg': (20, 5, 0),
        'pellet': (255, 255, 0),
        'gate': (255, 50, 50),
        'text_accent': (255, 100, 0),
    },
    {   # Level 5: Ice Gauntlet
        'name': 'ICE GAUNTLET',
        'wall': (0, 200, 255),
        'dot': (200, 240, 255),
        'bg': (0, 5, 15),
        'pellet': (150, 255, 255),
        'gate': (100, 200, 255),
        'text_accent': (0, 200, 255),
    },
]

def parse_maze(template):
    maze = []
    for row_str in template:
        row = []
        for ch in row_str:
            row.append(int(ch))
        maze.append(row)
    return maze

# ─── SPRITE DRAWING (CLASSIC PIXEL ART) ─────────────────────────────────────
def draw_pacman(surface, x, y, direction, frame, size=TILE):
    """Draw classic Pac-Man with anti-aliased rendering."""
    cx, cy = x + size // 2, y + size // 2
    r = size // 2 - 2
    mouth_angle = abs(math.sin(frame * 0.3)) * 45

    if mouth_angle < 2:
        pygame.gfxdraw.filled_circle(surface, cx, cy, r, YELLOW)
        pygame.gfxdraw.aacircle(surface, cx, cy, r, YELLOW)
        pygame.gfxdraw.filled_circle(surface, cx - 2, cy - r // 2, 2, BLACK)
        return

    angles = {0: 0, 1: 180, 2: 270, 3: 90}  # right, left, down, up
    base = angles.get(direction, 0)

    start_rad = math.radians(base + mouth_angle)
    end_rad = math.radians(base + 360 - mouth_angle)

    points = [(cx, cy)]
    steps = 36
    for i in range(steps + 1):
        angle = start_rad + (end_rad - start_rad) * i / steps
        px = cx + r * math.cos(angle)
        py = cy - r * math.sin(angle)
        points.append((int(px), int(py)))
    if len(points) > 2:
        pygame.gfxdraw.filled_polygon(surface, points, YELLOW)
        pygame.gfxdraw.aapolygon(surface, points, YELLOW)

    # Eye
    if direction == 0:
        ex, ey = cx + 2, cy - r // 2
    elif direction == 1:
        ex, ey = cx - 2, cy - r // 2
    elif direction == 2:
        ex, ey = cx - r // 3, cy + 2
    else:
        ex, ey = cx - r // 3, cy - 2
    pygame.gfxdraw.filled_circle(surface, int(ex), int(ey), 2, BLACK)

def draw_ghost(surface, x, y, color, direction, frame, scared=False, size=TILE):
    """Draw a classic ghost sprite with anti-aliased rendering."""
    cx, cy = x + size // 2, y + size // 2
    r = size // 2 - 2

    body_color = SCARED if scared else color
    if scared and frame % 20 < 10:
        body_color = WHITE

    # Body (rounded top + rectangle bottom) — AA
    pygame.gfxdraw.filled_circle(surface, cx, cy - 2, r, body_color)
    pygame.gfxdraw.aacircle(surface, cx, cy - 2, r, body_color)
    pygame.draw.rect(surface, body_color, (x + 2, cy - 2, size - 4, r + 2))

    # Wavy bottom with smoother curves
    num_waves = 3
    wave_w = (size - 4) / num_waves
    for i in range(num_waves):
        wx = x + 2 + i * wave_w
        wy = cy + r
        peak = 5 if (i + int(frame / 5)) % 2 == 0 else 0
        points = [
            (int(wx), int(wy)),
            (int(wx + wave_w * 0.25), int(wy + peak * 0.5)),
            (int(wx + wave_w / 2), int(wy + peak)),
            (int(wx + wave_w * 0.75), int(wy + peak * 0.5)),
            (int(wx + wave_w), int(wy)),
        ]
        pygame.gfxdraw.filled_polygon(surface, points, body_color)

    # Eyes
    if scared:
        pygame.gfxdraw.filled_circle(surface, cx - 4, cy - 4, 3, WHITE)
        pygame.gfxdraw.aacircle(surface, cx - 4, cy - 4, 3, WHITE)
        pygame.gfxdraw.filled_circle(surface, cx + 4, cy - 4, 3, WHITE)
        pygame.gfxdraw.aacircle(surface, cx + 4, cy - 4, 3, WHITE)
        # Wavy mouth
        mouth_points = []
        for i in range(7):
            mx = cx - 5 + i * 2
            my = cy + 3 + (2 if i % 2 == 0 else -1)
            mouth_points.append((mx, my))
        if len(mouth_points) > 1:
            pygame.draw.aalines(surface, WHITE, False, mouth_points)
    else:
        for offset in [-4, 4]:
            pygame.gfxdraw.filled_circle(surface, cx + offset, cy - 4, 4, WHITE)
            pygame.gfxdraw.aacircle(surface, cx + offset, cy - 4, 4, WHITE)
            dx = {0: 2, 1: -2, 2: 0, 3: 0}.get(direction, 0)
            dy = {0: 0, 1: 0, 2: 2, 3: -2}.get(direction, 0)
            pygame.gfxdraw.filled_circle(surface, cx + offset + dx, cy - 4 + dy, 2, BLUE)

def draw_fruit(surface, x, y, fruit_type, size=TILE):
    """Draw bonus fruit with AA."""
    cx, cy = x + size // 2, y + size // 2
    if fruit_type == 'cherry':
        pygame.gfxdraw.filled_circle(surface, cx - 3, cy + 2, 4, RED)
        pygame.gfxdraw.aacircle(surface, cx - 3, cy + 2, 4, RED)
        pygame.gfxdraw.filled_circle(surface, cx + 3, cy + 2, 4, RED)
        pygame.gfxdraw.aacircle(surface, cx + 3, cy + 2, 4, RED)
        pygame.draw.aaline(surface, GREEN, (cx - 3, cy - 2), (cx, cy - 6))
        pygame.draw.aaline(surface, GREEN, (cx + 3, cy - 2), (cx, cy - 6))
    elif fruit_type == 'strawberry':
        points = [(cx, cy - 5), (cx - 5, cy + 2), (cx, cy + 6), (cx + 5, cy + 2)]
        pygame.gfxdraw.filled_polygon(surface, points, RED)
        pygame.gfxdraw.aapolygon(surface, points, RED)
        pygame.gfxdraw.filled_circle(surface, cx, cy - 5, 3, GREEN)
        pygame.gfxdraw.aacircle(surface, cx, cy - 5, 3, GREEN)

# ─── SAFE AUDIO CHANNEL (no-ops when audio unavailable) ─────────────────────
class SafeChannel:
    """Wraps pygame.mixer.Channel; silently no-ops when audio is disabled."""
    def __init__(self, channel_id):
        self._ch = pygame.mixer.Channel(channel_id) if SOUND_ENABLED else None
    def play(self, sound, loops=0):
        if self._ch:
            self._ch.play(sound, loops=loops)
    def stop(self):
        if self._ch:
            self._ch.stop()
    def get_busy(self):
        return self._ch.get_busy() if self._ch else False

# ─── GHOST AI ────────────────────────────────────────────────────────────────
class Ghost:
    """AI Ghost with classic Pac-Man behaviors."""
    SCATTER = 0
    CHASE = 1
    FRIGHTENED = 2

    def __init__(self, name, color, home_col, home_row, scatter_target):
        self.name = name
        self.color = color
        self.home_col = home_col
        self.home_row = home_row
        self.col = home_col
        self.row = home_row
        self.scatter_target = scatter_target
        self.direction = 3  # start going up
        self.mode = Ghost.SCATTER
        self.frightened_timer = 0
        self.speed = 1.0
        self.in_house = True
        self.release_timer = 0
        self.eaten = False
        self.x = home_col * TILE
        self.y = home_row * TILE
        self.move_progress = 0
        self.next_col = home_col
        self.next_row = home_row

    def reset(self):
        self.col = self.home_col
        self.row = self.home_row
        self.x = self.col * TILE
        self.y = self.row * TILE
        self.direction = 3
        self.mode = Ghost.SCATTER
        self.frightened_timer = 0
        self.in_house = True
        self.eaten = False
        self.move_progress = 0
        self.next_col = self.col
        self.next_row = self.row

    def get_target(self, pacman_col, pacman_row, pacman_dir, blinky_col, blinky_row):
        """Get target tile based on ghost personality."""
        if self.mode == Ghost.FRIGHTENED:
            return (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
        if self.mode == Ghost.SCATTER:
            return self.scatter_target

        # CHASE mode - each ghost has unique targeting
        if self.name == 'Blinky':
            # Directly targets Pac-Man
            return (pacman_col, pacman_row)
        elif self.name == 'Pinky':
            # Targets 4 tiles ahead of Pac-Man
            dx = {0: 4, 1: -4, 2: 0, 3: 0}[pacman_dir]
            dy = {0: 0, 1: 0, 2: 4, 3: -4}[pacman_dir]
            return (pacman_col + dx, pacman_row + dy)
        elif self.name == 'Inky':
            # Complex: uses Blinky's position to calculate target
            dx = {0: 2, 1: -2, 2: 0, 3: 0}[pacman_dir]
            dy = {0: 0, 1: 0, 2: 2, 3: -2}[pacman_dir]
            pivot_x = pacman_col + dx
            pivot_y = pacman_row + dy
            return (2 * pivot_x - blinky_col, 2 * pivot_y - blinky_row)
        elif self.name == 'Clyde':
            # Targets Pac-Man when far, scatter corner when close
            dist = abs(self.col - pacman_col) + abs(self.row - pacman_row)
            if dist > 8:
                return (pacman_col, pacman_row)
            else:
                return self.scatter_target
        return (pacman_col, pacman_row)

    def get_valid_moves(self, maze):
        """Get valid directions from current position."""
        moves = []
        opposites = {0: 1, 1: 0, 2: 3, 3: 2}
        for d, (dc, dr) in enumerate([(1, 0), (-1, 0), (0, 1), (0, -1)]):
            nc = self.col + dc
            nr = self.row + dr
            # Tunnel wrapping
            if nc < 0: nc = COLS - 1
            if nc >= COLS: nc = 0
            if 0 <= nr < ROWS and maze[nr][nc] != 1 and maze[nr][nc] != 5:
                # Ghosts can't reverse direction (unless frightened)
                if d != opposites.get(self.direction, -1) or self.mode == Ghost.FRIGHTENED:
                    moves.append((d, nc, nr))
        # If no moves without reversing, allow reverse
        if not moves:
            for d, (dc, dr) in enumerate([(1, 0), (-1, 0), (0, 1), (0, -1)]):
                nc = self.col + dc
                nr = self.row + dr
                if nc < 0: nc = COLS - 1
                if nc >= COLS: nc = 0
                if 0 <= nr < ROWS and maze[nr][nc] != 1:
                    moves.append((d, nc, nr))
        return moves

    def update(self, maze, pacman_col, pacman_row, pacman_dir, blinky_col, blinky_row, dt):
        """Move ghost toward its target."""
        if self.in_house:
            self.release_timer += dt
            if self.release_timer > 1.5:
                # Move out of ghost house
                self.row = 11
                self.col = 13
                self.x = self.col * TILE
                self.y = self.row * TILE
                self.in_house = False
            return

        if self.eaten:
            # Return to ghost house
            target = (13, 14)
            if abs(self.col - target[0]) <= 1 and abs(self.row - target[1]) <= 1:
                self.reset()
                self.in_house = True
                self.release_timer = 1.0
                return
        else:
            target = self.get_target(pacman_col, pacman_row, pacman_dir, blinky_col, blinky_row)

        if self.frightened_timer > 0:
            self.frightened_timer -= dt
            if self.frightened_timer <= 0:
                self.mode = Ghost.CHASE
                self.frightened_timer = 0

        # Move toward target
        self.move_progress += self.speed * dt * 8
        if self.move_progress >= 1.0:
            self.move_progress = 0
            self.col = self.next_col
            self.row = self.next_row
            self.x = self.col * TILE
            self.y = self.row * TILE

            # Choose next direction
            moves = self.get_valid_moves(maze)
            if moves:
                if self.mode == Ghost.FRIGHTENED and not self.eaten:
                    # Random movement when scared
                    d, nc, nr = random.choice(moves)
                else:
                    # Choose move closest to target
                    best = None
                    best_dist = float('inf')
                    for d, nc, nr in moves:
                        dist = (nc - target[0]) ** 2 + (nr - target[1]) ** 2
                        if dist < best_dist:
                            best_dist = dist
                            best = (d, nc, nr)
                    d, nc, nr = best
                self.direction = d
                self.next_col = nc
                self.next_row = nr
        else:
            # Interpolate position — snap on tunnel wrap
            dcol = self.next_col - self.col
            if abs(dcol) > 1:
                self.x = self.next_col * TILE
                self.y = self.next_row * TILE
            else:
                dx = dcol * TILE * self.move_progress
                dy = (self.next_row - self.row) * TILE * self.move_progress
                self.x = self.col * TILE + dx
                self.y = self.row * TILE + dy

    def frighten(self):
        if not self.eaten:
            self.mode = Ghost.FRIGHTENED
            self.frightened_timer = 7.0

    def draw(self, surface, frame, y_offset=0):
        scared = self.mode == Ghost.FRIGHTENED and not self.eaten
        if self.eaten:
            # Just draw eyes going back to house
            cx = int(self.x) + TILE // 2
            cy = int(self.y) + TILE // 2 + y_offset
            for offset in [-4, 4]:
                pygame.draw.circle(surface, WHITE, (cx + offset, cy - 2), 4)
                dx = {0: 2, 1: -2, 2: 0, 3: 0}.get(self.direction, 0)
                dy = {0: 0, 1: 0, 2: 2, 3: -2}.get(self.direction, 0)
                pygame.draw.circle(surface, BLUE, (cx + offset + dx, cy - 2 + dy), 2)
        else:
            draw_ghost(surface, int(self.x), int(self.y) + y_offset, self.color,
                       self.direction, frame, scared)

# ─── MAIN GAME CLASS ────────────────────────────────────────────────────────
class PacManGame:
    def __init__(self):
        self.state = 'menu'  # menu, classic, ghost_tag, pellet_frenzy, game_over, you_win
        self.font_big = pygame.font.SysFont('Consolas', 48, bold=True)
        self.font_med = pygame.font.SysFont('Consolas', 28, bold=True)
        self.font_sm  = pygame.font.SysFont('Consolas', 18)
        self.font_xs  = pygame.font.SysFont('Consolas', 14)
        self.font_popup = pygame.font.SysFont('Consolas', 22, bold=True)
        self.menu_sel = 0
        self.frame = 0
        self.high_score = 0
        self.music_channel = SafeChannel(0)
        self.sfx_channel = SafeChannel(1)
        self.gt_score = 0
        self.pf_score = 0
        self.last_mode = 'classic'
        # Visual effects systems
        self.particles = ParticleSystem()
        self.popups = ScorePopupSystem()
        self.transition = ScreenTransition()
        self.shake = ScreenShake()
        self.reset_classic()

    # ─── CLASSIC MODE ────────────────────────────────────────────────────
    def reset_classic(self, new_game=True):
        if new_game:
            self.score = 0
            self.lives = 3
            self.level = 1
            for rival in getattr(self, 'rivals', []):
                rival['score'] = 0

        maze_idx = (self.level - 1) % len(ALL_MAZES)
        self.maze = parse_maze(ALL_MAZES[maze_idx])
        self.theme = LEVEL_THEMES[maze_idx]
        self.pac_col = 13
        self.pac_row = 23
        self.pac_x = self.pac_col * TILE
        self.pac_y = self.pac_row * TILE
        self.pac_dir = 0
        self.pac_next_dir = 0
        self.pac_moving = False
        self.move_progress = 0.0
        self.pac_next_col = self.pac_col
        self.pac_next_row = self.pac_row
        self.dots_total = sum(row.count(2) + row.count(3) for row in self.maze)
        self.dots_eaten = 0
        self.combo = 0
        self.fruit_active = False
        self.fruit_timer = 0
        self.fruit_col = 13
        self.fruit_row = 17
        self.mode_timer = 0
        self.scatter_time = True
        self.death_anim = 0
        self.win_anim = 0
        self.ready_timer = 2.0
        self.paused = False

        # AI rival Pac-Men that compete for dots!
        if new_game or not hasattr(self, 'rivals') or not self.rivals:
            self.rivals = []
            rival_configs = [
                {'name': 'SPEEDY',  'color': CYAN,   'col': 1,  'row': 1,  'style': 'greedy'},
                {'name': 'MUNCHY',  'color': GREEN,   'col': 26, 'row': 1,  'style': 'explorer'},
                {'name': 'CHOMPER', 'color': ORANGE,  'col': 1,  'row': 29, 'style': 'aggressive'},
            ]
            for cfg in rival_configs:
                self.rivals.append({
                    'name': cfg['name'], 'color': cfg['color'],
                    'col': cfg['col'], 'row': cfg['row'],
                    'x': cfg['col'] * TILE, 'y': cfg['row'] * TILE,
                    'dir': 0, 'next_dir': 0,
                    'next_col': cfg['col'], 'next_row': cfg['row'],
                    'move_progress': 0.0,
                    'speed': 6.5 + random.random() * 1.5,
                    'score': 0, 'alive': True,
                    'style': cfg['style'],
                    'home_col': cfg['col'], 'home_row': cfg['row'],
                    'respawn_timer': 0,
                    'dot_target': None,
                })
        else:
            # Reset positions but keep scores
            for rival in self.rivals:
                rival['col'] = rival['home_col']
                rival['row'] = rival['home_row']
                rival['x'] = rival['col'] * TILE
                rival['y'] = rival['row'] * TILE
                rival['next_col'] = rival['col']
                rival['next_row'] = rival['row']
                rival['move_progress'] = 0
                rival['alive'] = True
                rival['respawn_timer'] = 0

        # Create ghosts with classic behaviors
        release_offsets = [0, 0.5, 1.0, 1.5]
        self.ghosts = [
            Ghost('Blinky', RED,    13, 11, (25, 0)),    # top-right
            Ghost('Pinky',  PINK,   13, 14, (2, 0)),     # top-left
            Ghost('Inky',   CYAN,   11, 14, (27, 30)),   # bottom-right
            Ghost('Clyde',  ORANGE, 15, 14, (0, 30)),    # bottom-left
        ]
        self.ghosts[0].in_house = False
        self.ghosts[0].x = 13 * TILE
        self.ghosts[0].y = 11 * TILE
        for i, g in enumerate(self.ghosts):
            g.release_timer = release_offsets[i]
            g.speed = 0.9 + self.level * 0.05

    def reset_positions(self):
        self.pac_col = 13
        self.pac_row = 23
        self.pac_x = self.pac_col * TILE
        self.pac_y = self.pac_row * TILE
        self.pac_dir = 0
        self.pac_next_dir = 0
        self.pac_moving = False
        self.move_progress = 0
        self.pac_next_col = self.pac_col
        self.pac_next_row = self.pac_row
        self.ready_timer = 2.0
        for g in self.ghosts:
            g.reset()
        self.ghosts[0].in_house = False
        self.ghosts[0].x = 13 * TILE
        self.ghosts[0].y = 11 * TILE
        release_offsets = [0, 0.5, 1.0, 1.5]
        for i, g in enumerate(self.ghosts):
            g.release_timer = release_offsets[i]
        for rival in self.rivals:
            rival['col'] = rival['home_col']
            rival['row'] = rival['home_row']
            rival['x'] = rival['col'] * TILE
            rival['y'] = rival['row'] * TILE
            rival['next_col'] = rival['col']
            rival['next_row'] = rival['row']
            rival['move_progress'] = 0
            rival['alive'] = True
            rival['respawn_timer'] = 0

    def can_move(self, col, row, direction):
        dc = {0: 1, 1: -1, 2: 0, 3: 0}[direction]
        dr = {0: 0, 1: 0, 2: 1, 3: -1}[direction]
        nc = col + dc
        nr = row + dr
        if nc < 0: nc = COLS - 1
        if nc >= COLS: nc = 0
        if 0 <= nr < ROWS and self.maze[nr][nc] not in (1, 4, 5):
            return True, nc, nr
        return False, col, row

    def update_classic(self, dt, keys_pressed):
        if self.paused:
            return

        # Ready countdown
        if self.ready_timer > 0:
            self.ready_timer -= dt
            return

        # Death animation
        if self.death_anim > 0:
            self.death_anim -= dt
            if self.death_anim <= 0:
                self.lives -= 1
                if self.lives <= 0:
                    self.state = 'game_over'
                    self.high_score = max(self.high_score, self.score)
                    self.music_channel.stop()
                    return
                self.reset_positions()
            return

        # Win animation
        if self.win_anim > 0:
            self.win_anim -= dt
            if self.win_anim <= 0:
                self.level += 1
                self.reset_classic(new_game=False)
                self.music_channel.stop()
            return

        # Music — track desired track and switch when state changes
        any_scared = any(g.mode == Ghost.FRIGHTENED and not g.eaten for g in self.ghosts)
        desired_track = 'chase' if any_scared else 'main'
        if not hasattr(self, '_current_track'):
            self._current_track = None
        if desired_track != self._current_track or not self.music_channel.get_busy():
            if desired_track == 'chase':
                self.music_channel.play(music_chase, loops=-1)
            else:
                self.music_channel.play(music_main, loops=-1)
            self._current_track = desired_track

        # Handle direction input
        if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]:
            self.pac_next_dir = 0
        elif keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]:
            self.pac_next_dir = 1
        elif keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]:
            self.pac_next_dir = 2
        elif keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_w]:
            self.pac_next_dir = 3

        # Move Pac-Man
        speed = 8.0
        self.move_progress += speed * dt
        if self.move_progress >= 1.0:
            self.move_progress = 0
            self.pac_col = self.pac_next_col
            self.pac_row = self.pac_next_row
            self.pac_x = self.pac_col * TILE
            self.pac_y = self.pac_row * TILE

            # Eat dot
            tile = self.maze[self.pac_row][self.pac_col]
            px = self.pac_col * TILE + TILE // 2
            py = self.pac_row * TILE + TILE // 2 + 50
            if tile == 2:
                self.maze[self.pac_row][self.pac_col] = 0
                self.score += 10
                self.dots_eaten += 1
                self.sfx_channel.play(snd_chomp)
                self.particles.emit_dot_eat(px, py, self.theme['dot'])
            elif tile == 3:
                self.maze[self.pac_row][self.pac_col] = 0
                self.score += 50
                self.dots_eaten += 1
                self.combo = 0
                for g in self.ghosts:
                    g.frighten()
                self.sfx_channel.play(snd_power)
                self.music_channel.play(music_chase, loops=-1)
                self.particles.emit_power_pellet(px, py)
                self.shake.start(3, 0.2)
                self.transition.start('flash', 0.15, 'out', flash_color=CYAN)

            # Check win
            if self.dots_eaten >= self.dots_total:
                self.win_anim = 3.0
                self.sfx_channel.play(snd_win)
                self.music_channel.stop()
                self.particles.emit_level_clear()
                return

            # Fruit spawn
            if self.dots_eaten in [70, 170] and not self.fruit_active:
                self.fruit_active = True
                self.fruit_timer = 10.0

            # Eat fruit
            if self.fruit_active and self.pac_col == self.fruit_col and self.pac_row == self.fruit_row:
                pts = 100 * self.level
                self.score += pts
                self.fruit_active = False
                self.sfx_channel.play(snd_eat_ghost)
                fx = self.fruit_col * TILE + TILE // 2
                fy = self.fruit_row * TILE + TILE // 2 + 50
                self.particles.emit_fruit(fx, fy)
                self.popups.add(fx, fy, f"+{pts}", GOLD, self.font_popup)

            # Try preferred direction first, then continue current
            can, nc, nr = self.can_move(self.pac_col, self.pac_row, self.pac_next_dir)
            if can:
                self.pac_dir = self.pac_next_dir
                self.pac_next_col = nc
                self.pac_next_row = nr
            else:
                can, nc, nr = self.can_move(self.pac_col, self.pac_row, self.pac_dir)
                if can:
                    self.pac_next_col = nc
                    self.pac_next_row = nr
                else:
                    self.pac_next_col = self.pac_col
                    self.pac_next_row = self.pac_row
        else:
            # Interpolate position — snap on tunnel wrap to avoid cross-screen sweep
            dcol = self.pac_next_col - self.pac_col
            if abs(dcol) > 1:
                # Tunnel wrap — snap to destination
                self.pac_x = self.pac_next_col * TILE
                self.pac_y = self.pac_next_row * TILE
            else:
                dx = dcol * TILE * self.move_progress
                dy = (self.pac_next_row - self.pac_row) * TILE * self.move_progress
                self.pac_x = self.pac_col * TILE + dx
                self.pac_y = self.pac_row * TILE + dy

        # Pac-Man trail effect
        if self.frame % 3 == 0 and self.death_anim <= 0:
            self.particles.emit_trail(
                int(self.pac_x) + TILE // 2,
                int(self.pac_y) + TILE // 2 + 50,
                YELLOW
            )

        # Scatter/chase mode switching
        self.mode_timer += dt
        if self.scatter_time and self.mode_timer > 7:
            self.scatter_time = False
            self.mode_timer = 0
            for g in self.ghosts:
                if g.mode != Ghost.FRIGHTENED:
                    g.mode = Ghost.CHASE
        elif not self.scatter_time and self.mode_timer > 20:
            self.scatter_time = True
            self.mode_timer = 0
            for g in self.ghosts:
                if g.mode != Ghost.FRIGHTENED:
                    g.mode = Ghost.SCATTER

        # Update ghosts
        blinky = self.ghosts[0]
        for g in self.ghosts:
            g.update(self.maze, self.pac_col, self.pac_row, self.pac_dir,
                     blinky.col, blinky.row, dt)

        # Collision detection
        for g in self.ghosts:
            if g.in_house or g.eaten:
                continue
            dist = math.sqrt((self.pac_x - g.x) ** 2 + (self.pac_y - g.y) ** 2)
            if dist < TILE * 0.8:
                if g.mode == Ghost.FRIGHTENED:
                    g.eaten = True
                    pts = 200 * (2 ** self.combo)
                    self.score += pts
                    self.combo += 1
                    self.sfx_channel.play(snd_eat_ghost)
                    gx = int(g.x) + TILE // 2
                    gy = int(g.y) + TILE // 2 + 50
                    self.particles.emit_ghost_eat(gx, gy, g.color)
                    self.popups.add(gx, gy, f"+{pts}", g.color, self.font_popup)
                    self.shake.start(4, 0.15)
                else:
                    self.death_anim = 1.5
                    self.sfx_channel.play(snd_death)
                    self.music_channel.stop()
                    self._current_track = None
                    dx = int(self.pac_x) + TILE // 2
                    dy = int(self.pac_y) + TILE // 2 + 50
                    self.particles.emit_death(dx, dy)
                    self.shake.start(8, 0.5)

        # Fruit timer
        if self.fruit_active:
            self.fruit_timer -= dt
            if self.fruit_timer <= 0:
                self.fruit_active = False

        # ─── UPDATE AI RIVAL PAC-MEN ────────────────────────────────────
        dc_map = {0: 1, 1: -1, 2: 0, 3: 0}
        dr_map = {0: 0, 1: 0, 2: 1, 3: -1}
        for rival in self.rivals:
            # Respawn timer if dead
            if not rival['alive']:
                rival['respawn_timer'] -= dt
                if rival['respawn_timer'] <= 0:
                    rival['alive'] = True
                    rival['col'] = rival['home_col']
                    rival['row'] = rival['home_row']
                    rival['x'] = rival['col'] * TILE
                    rival['y'] = rival['row'] * TILE
                    rival['next_col'] = rival['col']
                    rival['next_row'] = rival['row']
                    rival['move_progress'] = 0
                continue

            rival['move_progress'] += rival['speed'] * dt
            if rival['move_progress'] >= 1.0:
                rival['move_progress'] = 0
                rival['col'] = rival['next_col']
                rival['row'] = rival['next_row']
                rival['x'] = rival['col'] * TILE
                rival['y'] = rival['row'] * TILE

                # AI rival eats dots too!
                tile = self.maze[rival['row']][rival['col']]
                if tile == 2:
                    self.maze[rival['row']][rival['col']] = 0
                    rival['score'] += 10
                    self.dots_eaten += 1
                elif tile == 3:
                    self.maze[rival['row']][rival['col']] = 0
                    rival['score'] += 50
                    self.dots_eaten += 1
                    for g in self.ghosts:
                        g.frighten()
                    self.sfx_channel.play(snd_power)
                    self.music_channel.play(music_chase, loops=-1)

                # Check if all dots eaten (anyone can clear the level)
                if self.dots_eaten >= self.dots_total:
                    self.win_anim = 3.0
                    self.sfx_channel.play(snd_win)
                    self.music_channel.stop()
                    return

                # AI pathfinding — find nearest dot to chase
                best_dir = rival['dir']
                best_score = float('inf')

                if rival['style'] == 'greedy':
                    # Greedy: always go for nearest dot
                    target = self._find_nearest_dot(rival['col'], rival['row'])
                elif rival['style'] == 'explorer':
                    # Explorer: targets far-away clusters of dots
                    target = self._find_dot_cluster(rival['col'], rival['row'])
                elif rival['style'] == 'aggressive':
                    # Aggressive: tries to steal dots near the player
                    target = self._find_dot_near(self.pac_col, self.pac_row,
                                                 rival['col'], rival['row'])
                else:
                    target = self._find_nearest_dot(rival['col'], rival['row'])

                if target:
                    # Move toward target dot
                    dirs = [0, 1, 2, 3]
                    random.shuffle(dirs)
                    for d in dirs:
                        nc = rival['col'] + dc_map[d]
                        nr = rival['row'] + dr_map[d]
                        if nc < 0: nc = COLS - 1
                        if nc >= COLS: nc = 0
                        if 0 <= nr < ROWS and self.maze[nr][nc] not in [1, 5, 4]:
                            dist = (nc - target[0]) ** 2 + (nr - target[1]) ** 2
                            # Avoid ghosts that aren't scared
                            ghost_nearby = False
                            for g in self.ghosts:
                                if not g.in_house and not g.eaten and g.mode != Ghost.FRIGHTENED:
                                    gd = (nc - g.col) ** 2 + (nr - g.row) ** 2
                                    if gd < 9:
                                        ghost_nearby = True
                                        break
                            if ghost_nearby:
                                dist += 500  # penalise going near ghosts
                            if dist < best_score:
                                best_score = dist
                                best_dir = d
                                rival['next_col'] = nc
                                rival['next_row'] = nr
                else:
                    # No dots left or fallback — wander
                    dirs = [0, 1, 2, 3]
                    random.shuffle(dirs)
                    for d in dirs:
                        nc = rival['col'] + dc_map[d]
                        nr = rival['row'] + dr_map[d]
                        if nc < 0: nc = COLS - 1
                        if nc >= COLS: nc = 0
                        if 0 <= nr < ROWS and self.maze[nr][nc] not in [1, 5, 4]:
                            rival['next_col'] = nc
                            rival['next_row'] = nr
                            best_dir = d
                            break

                rival['dir'] = best_dir
            else:
                # Interpolate position — snap on tunnel wrap
                dcol = rival['next_col'] - rival['col']
                if abs(dcol) > 1:
                    rival['x'] = rival['next_col'] * TILE
                    rival['y'] = rival['next_row'] * TILE
                else:
                    dx = dcol * TILE * rival['move_progress']
                    dy = (rival['next_row'] - rival['row']) * TILE * rival['move_progress']
                    rival['x'] = rival['col'] * TILE + dx
                    rival['y'] = rival['row'] * TILE + dy

            # Rival gets caught by ghosts too!
            for g in self.ghosts:
                if g.in_house or g.eaten:
                    continue
                dist = math.sqrt((rival['x'] - g.x) ** 2 + (rival['y'] - g.y) ** 2)
                if dist < TILE * 0.8 and g.mode != Ghost.FRIGHTENED:
                    rival['alive'] = False
                    rival['respawn_timer'] = 5.0
                    break

    def _find_nearest_dot(self, col, row):
        """Find the closest dot to the given position."""
        best = None
        best_dist = float('inf')
        for r in range(ROWS):
            for c in range(COLS):
                if self.maze[r][c] in [2, 3]:
                    dist = abs(c - col) + abs(r - row)
                    if dist < best_dist:
                        best_dist = dist
                        best = (c, r)
        return best

    def _find_dot_cluster(self, col, row):
        """Find a cluster of dots (area with most dots) to target."""
        best = None
        best_count = -1
        # Check 5x5 regions across the maze
        for br in range(0, ROWS, 5):
            for bc in range(0, COLS, 5):
                count = 0
                center_c, center_r = bc + 2, br + 2
                for dr in range(-2, 3):
                    for dc in range(-2, 3):
                        cr = center_r + dr
                        cc = center_c + dc
                        if 0 <= cr < ROWS and 0 <= cc < COLS and self.maze[cr][cc] in [2, 3]:
                            count += 1
                if count > best_count:
                    # Prefer clusters not too close (explorer wants to roam)
                    dist = abs(center_c - col) + abs(center_r - row)
                    if dist > 3:
                        best_count = count
                        best = (min(max(center_c, 0), COLS - 1), min(max(center_r, 0), ROWS - 1))
        return best if best else self._find_nearest_dot(col, row)

    def _find_dot_near(self, target_col, target_row, my_col, my_row):
        """Find a dot near a target position (used by aggressive AI to steal dots near player)."""
        best = None
        best_dist = float('inf')
        for r in range(ROWS):
            for c in range(COLS):
                if self.maze[r][c] in [2, 3]:
                    # Prioritise dots near the target (player)
                    dist_to_target = abs(c - target_col) + abs(r - target_row)
                    dist_to_me = abs(c - my_col) + abs(r - my_row)
                    # Weighted score: prefer dots near player that we can reach
                    score = dist_to_target * 2 + dist_to_me
                    if score < best_dist:
                        best_dist = score
                        best = (c, r)
        return best

    def draw_maze(self, y_offset=0):
        theme = self.theme if hasattr(self, 'theme') else LEVEL_THEMES[0]
        wall_col = theme['wall']
        dot_col = theme['dot']
        pellet_col = theme['pellet']
        gate_col = theme['gate']
        # Dimmer wall fill for depth
        wall_fill = tuple(max(0, c // 4) for c in wall_col)
        for r in range(ROWS):
            for c in range(COLS):
                tile = self.maze[r][c]
                x = c * TILE
                y = r * TILE + y_offset
                cx = x + TILE // 2
                cy = y + TILE // 2
                if tile == 1:
                    # Filled wall with AA border
                    pygame.draw.rect(screen, wall_fill, (x + 2, y + 2, TILE - 4, TILE - 4),
                                     border_radius=3)
                    pygame.draw.rect(screen, wall_col, (x + 1, y + 1, TILE - 2, TILE - 2), 2,
                                     border_radius=4)
                elif tile == 2:
                    # AA dot
                    pygame.gfxdraw.filled_circle(screen, cx, cy, 2, dot_col)
                    pygame.gfxdraw.aacircle(screen, cx, cy, 2, dot_col)
                elif tile == 3:
                    # Power pellet with pulsing glow
                    if self.frame % 20 < 15:
                        pulse = abs(math.sin(self.frame * 0.15))
                        glow_r = int(8 + 3 * pulse)
                        # Outer glow
                        glow_col = (*pellet_col[:3], int(60 * pulse))
                        try:
                            pygame.gfxdraw.filled_circle(screen, cx, cy, glow_r, glow_col)
                        except (ValueError, OverflowError):
                            pass
                        # Core
                        pygame.gfxdraw.filled_circle(screen, cx, cy, 5, pellet_col)
                        pygame.gfxdraw.aacircle(screen, cx, cy, 5, pellet_col)
                elif tile == 5:
                    pygame.draw.rect(screen, gate_col, (x, y + TILE // 2 - 2, TILE, 4))

    def draw_classic(self):
        theme = self.theme if hasattr(self, 'theme') else LEVEL_THEMES[0]
        screen.fill(theme['bg'])
        y_off = 50

        # HUD top
        title = self.font_sm.render(f"YOU: {self.score}", True, YELLOW)
        screen.blit(title, (10, 5))
        hi = self.font_sm.render(f"HIGH: {self.high_score}", True, WHITE)
        screen.blit(hi, (WIDTH // 2 - hi.get_width() // 2, 5))
        lvl = self.font_sm.render(f"L{self.level}: {theme['name']}", True, theme['wall'])
        screen.blit(lvl, (WIDTH - lvl.get_width() - 10, 5))

        # Rival scores bar
        rx = 10
        for rival in self.rivals:
            status = "" if rival['alive'] else " X"
            rtxt = self.font_xs.render(f"{rival['name']}: {rival['score']}{status}",
                                        True, rival['color'])
            screen.blit(rtxt, (rx, 25))
            rx += rtxt.get_width() + 15

        # Draw maze
        self.draw_maze(y_off)

        # Draw fruit
        if self.fruit_active:
            draw_fruit(screen, self.fruit_col * TILE, self.fruit_row * TILE + y_off,
                        'cherry' if self.level % 2 == 1 else 'strawberry')

        # Draw ghosts
        for g in self.ghosts:
            if not g.in_house:
                g.draw(screen, self.frame, y_off)

        # Draw AI rival Pac-Men
        for rival in self.rivals:
            if rival['alive']:
                draw_pacman(screen, int(rival['x']), int(rival['y']) + y_off,
                            rival['dir'], self.frame)
                # Colour tint overlay to distinguish from player
                cx = int(rival['x']) + TILE // 2
                cy = int(rival['y']) + TILE // 2 + y_off
                r = TILE // 2 - 2
                tint = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                pygame.draw.circle(tint, (*rival['color'], 90), (TILE // 2, TILE // 2), r)
                screen.blit(tint, (int(rival['x']), int(rival['y']) + y_off))
                # Name tag
                tag = self.font_xs.render(rival['name'], True, rival['color'])
                screen.blit(tag, (int(rival['x']) - tag.get_width() // 2 + TILE // 2,
                                  int(rival['y']) + y_off - 12))

        # Draw Pac-Man
        if self.death_anim > 0:
            # Death spin animation
            spin_frame = int((1.5 - self.death_anim) * 20)
            draw_pacman(screen, int(self.pac_x), int(self.pac_y) + y_off,
                        spin_frame % 4, spin_frame)
        else:
            draw_pacman(screen, int(self.pac_x), int(self.pac_y) + y_off,
                        self.pac_dir, self.frame)

        # Ready text
        if self.ready_timer > 0:
            ready = self.font_big.render("READY!", True, YELLOW)
            screen.blit(ready, (WIDTH // 2 - ready.get_width() // 2,
                                 HEIGHT // 2 - ready.get_height() // 2))

        # Win animation
        if self.win_anim > 0:
            if int(self.win_anim * 4) % 2 == 0:
                win = self.font_big.render("LEVEL CLEAR!", True, YELLOW)
                screen.blit(win, (WIDTH // 2 - win.get_width() // 2, HEIGHT // 2 - 50))
                next_idx = self.level % len(ALL_MAZES)
                next_theme = LEVEL_THEMES[next_idx]
                nxt = self.font_med.render(f"Next: {next_theme['name']}", True, next_theme['wall'])
                screen.blit(nxt, (WIDTH // 2 - nxt.get_width() // 2, HEIGHT // 2 + 10))

        # Lives display
        for i in range(self.lives - 1):
            draw_pacman(screen, 10 + i * 28, HEIGHT - 35, 1, 5)

        # Paused
        if self.paused:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            pause_txt = self.font_big.render("PAUSED", True, YELLOW)
            screen.blit(pause_txt, (WIDTH // 2 - pause_txt.get_width() // 2,
                                    HEIGHT // 2 - pause_txt.get_height() // 2))

    # ─── GHOST TAG MINIGAME ─────────────────────────────────────────────
    def reset_ghost_tag(self):
        self.gt_maze = parse_maze(MAZE_TEMPLATE)
        # Remove dots from maze for cleaner look
        for r in range(ROWS):
            for c in range(COLS):
                if self.gt_maze[r][c] in [2, 3]:
                    self.gt_maze[r][c] = 0
        self.gt_score = 0
        self.gt_timer = 30.0
        self.gt_ghost_col = 1
        self.gt_ghost_row = 1
        self.gt_ghost_x = self.gt_ghost_col * TILE
        self.gt_ghost_y = self.gt_ghost_row * TILE
        self.gt_ghost_dir = 0
        self.gt_ghost_next_dir = 0
        self.gt_move_progress = 0
        self.gt_ghost_next_col = self.gt_ghost_col
        self.gt_ghost_next_row = self.gt_ghost_row
        # AI Pac-Men to chase
        self.gt_pacmen = []
        spawn_positions = [(13, 23), (6, 5), (21, 5), (6, 26), (21, 26)]
        for i, (sc, sr) in enumerate(spawn_positions[:3]):
            self.gt_pacmen.append({
                'col': sc, 'row': sr, 'x': sc * TILE, 'y': sr * TILE,
                'dir': random.randint(0, 3), 'speed': 0.7 + random.random() * 0.3,
                'move_progress': 0, 'next_col': sc, 'next_row': sr, 'alive': True,
                'color': [YELLOW, CYAN, ORANGE][i]
            })
        self.gt_ready = 2.0
        self.gt_won = False

    def update_ghost_tag(self, dt, keys_pressed):
        if self.gt_ready > 0:
            self.gt_ready -= dt
            return

        self.gt_timer -= dt
        all_caught = all(not p['alive'] for p in self.gt_pacmen)
        if self.gt_timer <= 0 or all_caught:
            self.gt_won = all_caught
            self.state = 'game_over'
            self.high_score = max(self.high_score, self.gt_score)
            self.music_channel.stop()
            return

        # Music
        if not self.music_channel.get_busy():
            self.music_channel.play(music_ghost_tag, loops=-1)

        # Player ghost movement
        if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]:
            self.gt_ghost_next_dir = 0
        elif keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]:
            self.gt_ghost_next_dir = 1
        elif keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]:
            self.gt_ghost_next_dir = 2
        elif keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_w]:
            self.gt_ghost_next_dir = 3

        speed = 9.0
        self.gt_move_progress += speed * dt
        if self.gt_move_progress >= 1.0:
            self.gt_move_progress = 0
            self.gt_ghost_col = self.gt_ghost_next_col
            self.gt_ghost_row = self.gt_ghost_next_row
            self.gt_ghost_x = self.gt_ghost_col * TILE
            self.gt_ghost_y = self.gt_ghost_row * TILE

            # Try directions
            dc = {0: 1, 1: -1, 2: 0, 3: 0}
            dr = {0: 0, 1: 0, 2: 1, 3: -1}
            # Try next direction first
            nc = self.gt_ghost_col + dc[self.gt_ghost_next_dir]
            nr = self.gt_ghost_row + dr[self.gt_ghost_next_dir]
            if nc < 0: nc = COLS - 1
            if nc >= COLS: nc = 0
            if 0 <= nr < ROWS and self.gt_maze[nr][nc] not in [1, 5]:
                self.gt_ghost_dir = self.gt_ghost_next_dir
                self.gt_ghost_next_col = nc
                self.gt_ghost_next_row = nr
            else:
                nc = self.gt_ghost_col + dc[self.gt_ghost_dir]
                nr = self.gt_ghost_row + dr[self.gt_ghost_dir]
                if nc < 0: nc = COLS - 1
                if nc >= COLS: nc = 0
                if 0 <= nr < ROWS and self.gt_maze[nr][nc] not in [1, 5]:
                    self.gt_ghost_next_col = nc
                    self.gt_ghost_next_row = nr
                else:
                    self.gt_ghost_next_col = self.gt_ghost_col
                    self.gt_ghost_next_row = self.gt_ghost_row
        else:
            dx = (self.gt_ghost_next_col - self.gt_ghost_col) * TILE * self.gt_move_progress
            dy = (self.gt_ghost_next_row - self.gt_ghost_row) * TILE * self.gt_move_progress
            self.gt_ghost_x = self.gt_ghost_col * TILE + dx
            self.gt_ghost_y = self.gt_ghost_row * TILE + dy

        # Update AI Pac-Men (run away from ghost)
        dc_map = {0: 1, 1: -1, 2: 0, 3: 0}
        dr_map = {0: 0, 1: 0, 2: 1, 3: -1}
        for p in self.gt_pacmen:
            if not p['alive']:
                continue
            p['move_progress'] += p['speed'] * dt * 7
            if p['move_progress'] >= 1.0:
                p['move_progress'] = 0
                p['col'] = p['next_col']
                p['row'] = p['next_row']
                p['x'] = p['col'] * TILE
                p['y'] = p['row'] * TILE

                # AI: run away from ghost
                best_dir = p['dir']
                best_dist = -1
                dirs = [0, 1, 2, 3]
                random.shuffle(dirs)
                for d in dirs:
                    nc = p['col'] + dc_map[d]
                    nr = p['row'] + dr_map[d]
                    if nc < 0: nc = COLS - 1
                    if nc >= COLS: nc = 0
                    if 0 <= nr < ROWS and self.gt_maze[nr][nc] not in [1, 5]:
                        dist = (nc - self.gt_ghost_col) ** 2 + (nr - self.gt_ghost_row) ** 2
                        # Add randomness so they're not too perfect
                        dist += random.randint(-5, 5)
                        if dist > best_dist:
                            best_dist = dist
                            best_dir = d
                            p['next_col'] = nc
                            p['next_row'] = nr
                p['dir'] = best_dir

            # Catch detection
            dist = math.sqrt((p['x'] - self.gt_ghost_x) ** 2 + (p['y'] - self.gt_ghost_y) ** 2)
            if dist < TILE * 0.8:
                p['alive'] = False
                self.gt_score += 500
                self.sfx_channel.play(snd_eat_ghost)
                self.particles.emit_ghost_eat(int(p['x']) + TILE // 2, int(p['y']) + TILE // 2 + 40, YELLOW)
                self.popups.add(int(p['x']) + TILE // 2, int(p['y']) + 40, '+500', CYAN, self.font_popup)
                self.shake.start(4, 0.2)

    def draw_ghost_tag(self):
        screen.fill(BLACK)
        y_off = 40

        # HUD
        title = self.font_sm.render(f"👻 GHOST TAG!  SCORE: {self.gt_score}", True, CYAN)
        screen.blit(title, (10, 5))
        timer = self.font_sm.render(f"TIME: {int(self.gt_timer)}s", True,
                                     RED if self.gt_timer < 10 else WHITE)
        screen.blit(timer, (WIDTH - timer.get_width() - 10, 5))

        # Draw maze walls only
        for r in range(ROWS):
            for c in range(COLS):
                if self.gt_maze[r][c] == 1:
                    x = c * TILE
                    y = r * TILE + y_off
                    pygame.draw.rect(screen, PURPLE, (x + 1, y + 1, TILE - 2, TILE - 2), 2,
                                     border_radius=4)

        # Draw AI Pac-Men
        for p in self.gt_pacmen:
            if p['alive']:
                draw_pacman(screen, int(p['x']), int(p['y']) + y_off,
                            p['dir'], self.frame, TILE)

        # Draw player ghost
        draw_ghost(screen, int(self.gt_ghost_x), int(self.gt_ghost_y) + y_off,
                   RED, self.gt_ghost_dir, self.frame)

        # Ready
        if self.gt_ready > 0:
            r_txt = self.font_big.render("TAG THEM!", True, CYAN)
            screen.blit(r_txt, (WIDTH // 2 - r_txt.get_width() // 2, HEIGHT // 2 - 30))

        # Remaining count
        alive = sum(1 for p in self.gt_pacmen if p['alive'])
        rem = self.font_sm.render(f"Pac-Men remaining: {alive}", True, YELLOW)
        screen.blit(rem, (WIDTH // 2 - rem.get_width() // 2, HEIGHT - 30))

    # ─── PELLET FRENZY MINIGAME ─────────────────────────────────────────
    def reset_pellet_frenzy(self):
        self.pf_maze = parse_maze(MAZE_TEMPLATE)
        # Replace all dots with power pellets!
        for r in range(ROWS):
            for c in range(COLS):
                if self.pf_maze[r][c] == 2:
                    self.pf_maze[r][c] = 3  # all power pellets!
        self.pf_score = 0
        self.pf_timer = 20.0
        self.pf_pac_col = 13
        self.pf_pac_row = 23
        self.pf_pac_x = self.pf_pac_col * TILE
        self.pf_pac_y = self.pf_pac_row * TILE
        self.pf_pac_dir = 0
        self.pf_pac_next_dir = 0
        self.pf_move_progress = 0
        self.pf_pac_next_col = self.pf_pac_col
        self.pf_pac_next_row = self.pf_pac_row
        self.pf_combo = 0
        self.pf_pellets_eaten = 0
        self.pf_ready = 2.0
        self.pf_ghosts = []
        for i in range(6):
            self.pf_ghosts.append({
                'col': random.choice([1, 26]),
                'row': random.choice([1, 29]),
                'x': 0, 'y': 0,
                'dir': random.randint(0, 3),
                'color': [RED, PINK, CYAN, ORANGE, PURPLE, GREEN][i],
                'speed': 0.6 + i * 0.08,
                'scared': False, 'scared_timer': 0,
                'move_progress': 0, 'next_col': 0, 'next_row': 0,
            })
            self.pf_ghosts[-1]['x'] = self.pf_ghosts[-1]['col'] * TILE
            self.pf_ghosts[-1]['y'] = self.pf_ghosts[-1]['row'] * TILE
            self.pf_ghosts[-1]['next_col'] = self.pf_ghosts[-1]['col']
            self.pf_ghosts[-1]['next_row'] = self.pf_ghosts[-1]['row']

    def update_pellet_frenzy(self, dt, keys_pressed):
        if self.pf_ready > 0:
            self.pf_ready -= dt
            return

        self.pf_timer -= dt
        if self.pf_timer <= 0:
            self.state = 'game_over'
            self.high_score = max(self.high_score, self.pf_score)
            self.music_channel.stop()
            return

        if not self.music_channel.get_busy():
            self.music_channel.play(music_chase, loops=-1)

        # Input
        if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]:
            self.pf_pac_next_dir = 0
        elif keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]:
            self.pf_pac_next_dir = 1
        elif keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]:
            self.pf_pac_next_dir = 2
        elif keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_w]:
            self.pf_pac_next_dir = 3

        # Move pac
        speed = 10.0
        self.pf_move_progress += speed * dt
        if self.pf_move_progress >= 1.0:
            self.pf_move_progress = 0
            self.pf_pac_col = self.pf_pac_next_col
            self.pf_pac_row = self.pf_pac_next_row
            self.pf_pac_x = self.pf_pac_col * TILE
            self.pf_pac_y = self.pf_pac_row * TILE

            # Eat pellet
            if self.pf_maze[self.pf_pac_row][self.pf_pac_col] == 3:
                self.pf_maze[self.pf_pac_row][self.pf_pac_col] = 0
                self.pf_pellets_eaten += 1
                self.pf_combo += 1
                self.pf_score += 50 * self.pf_combo
                self.sfx_channel.play(snd_power)
                px = self.pf_pac_col * TILE + TILE // 2
                py = self.pf_pac_row * TILE + TILE // 2 + 40
                self.particles.emit_power_pellet(px, py)
                self.popups.add(px, py, f'+{50 * self.pf_combo}', CYAN, self.font_popup)
                self.shake.start(3, 0.15)
                for g in self.pf_ghosts:
                    g['scared'] = True
                    g['scared_timer'] = 4.0

            dc = {0: 1, 1: -1, 2: 0, 3: 0}
            dr = {0: 0, 1: 0, 2: 1, 3: -1}
            nc = self.pf_pac_col + dc[self.pf_pac_next_dir]
            nr = self.pf_pac_row + dr[self.pf_pac_next_dir]
            if nc < 0: nc = COLS - 1
            if nc >= COLS: nc = 0
            if 0 <= nr < ROWS and self.pf_maze[nr][nc] not in [1, 5]:
                self.pf_pac_dir = self.pf_pac_next_dir
                self.pf_pac_next_col = nc
                self.pf_pac_next_row = nr
            else:
                nc = self.pf_pac_col + dc[self.pf_pac_dir]
                nr = self.pf_pac_row + dr[self.pf_pac_dir]
                if nc < 0: nc = COLS - 1
                if nc >= COLS: nc = 0
                if 0 <= nr < ROWS and self.pf_maze[nr][nc] not in [1, 5]:
                    self.pf_pac_next_col = nc
                    self.pf_pac_next_row = nr
                else:
                    self.pf_pac_next_col = self.pf_pac_col
                    self.pf_pac_next_row = self.pf_pac_row
        else:
            dx = (self.pf_pac_next_col - self.pf_pac_col) * TILE * self.pf_move_progress
            dy = (self.pf_pac_next_row - self.pf_pac_row) * TILE * self.pf_move_progress
            self.pf_pac_x = self.pf_pac_col * TILE + dx
            self.pf_pac_y = self.pf_pac_row * TILE + dy

        # Update ghosts
        dc_map = {0: 1, 1: -1, 2: 0, 3: 0}
        dr_map = {0: 0, 1: 0, 2: 1, 3: -1}
        for g in self.pf_ghosts:
            if g['scared']:
                g['scared_timer'] -= dt
                if g['scared_timer'] <= 0:
                    g['scared'] = False

            g['move_progress'] += g['speed'] * dt * 7
            if g['move_progress'] >= 1.0:
                g['move_progress'] = 0
                g['col'] = g['next_col']
                g['row'] = g['next_row']
                g['x'] = g['col'] * TILE
                g['y'] = g['row'] * TILE

                best_dir = g['dir']
                best_dist = float('inf') if not g['scared'] else -1
                dirs = [0, 1, 2, 3]
                random.shuffle(dirs)
                for d in dirs:
                    nc = g['col'] + dc_map[d]
                    nr = g['row'] + dr_map[d]
                    if nc < 0: nc = COLS - 1
                    if nc >= COLS: nc = 0
                    if 0 <= nr < ROWS and self.pf_maze[nr][nc] not in [1, 5]:
                        dist = (nc - self.pf_pac_col) ** 2 + (nr - self.pf_pac_row) ** 2
                        if g['scared']:
                            if dist > best_dist:
                                best_dist = dist
                                best_dir = d
                                g['next_col'] = nc
                                g['next_row'] = nr
                        else:
                            if dist < best_dist:
                                best_dist = dist
                                best_dir = d
                                g['next_col'] = nc
                                g['next_row'] = nr
                g['dir'] = best_dir

            # Collision
            dist = math.sqrt((g['x'] - self.pf_pac_x) ** 2 + (g['y'] - self.pf_pac_y) ** 2)
            if dist < TILE * 0.8:
                if g['scared']:
                    g['col'] = random.choice([1, 26])
                    g['row'] = random.choice([1, 29])
                    g['x'] = g['col'] * TILE
                    g['y'] = g['row'] * TILE
                    g['next_col'] = g['col']
                    g['next_row'] = g['row']
                    g['scared'] = False
                    self.pf_score += 200 * self.pf_combo
                    self.sfx_channel.play(snd_eat_ghost)
                    gx = int(g['x']) + TILE // 2
                    gy = int(g['y']) + TILE // 2 + 40
                    self.particles.emit_ghost_eat(gx, gy, g['color'])
                    self.popups.add(gx, gy, f'+{200 * self.pf_combo}', CYAN, self.font_popup)
                    self.shake.start(4, 0.2)
                else:
                    self.state = 'game_over'
                    self.high_score = max(self.high_score, self.pf_score)
                    self.sfx_channel.play(snd_death)
                    self.music_channel.stop()
                    self.particles.emit_death(int(self.pf_pac_x) + TILE // 2, int(self.pf_pac_y) + TILE // 2 + 40)
                    self.shake.start(8, 0.5)
                    return

    def draw_pellet_frenzy(self):
        screen.fill(BLACK)
        y_off = 40

        # HUD
        title = self.font_sm.render(f"⚡ PELLET FRENZY!  SCORE: {self.pf_score}", True, YELLOW)
        screen.blit(title, (10, 5))
        timer = self.font_sm.render(f"TIME: {int(self.pf_timer)}s  COMBO: x{self.pf_combo}",
                                     True, RED if self.pf_timer < 10 else WHITE)
        screen.blit(timer, (WIDTH - timer.get_width() - 10, 5))

        # Maze
        for r in range(ROWS):
            for c in range(COLS):
                tile = self.pf_maze[r][c]
                x = c * TILE
                y = r * TILE + y_off
                if tile == 1:
                    pygame.draw.rect(screen, GREEN, (x + 1, y + 1, TILE - 2, TILE - 2), 2,
                                     border_radius=4)
                elif tile == 3:
                    if self.frame % 15 < 12:
                        pygame.draw.circle(screen, YELLOW, (x + TILE // 2, y + TILE // 2), 6)

        # Ghosts
        for g in self.pf_ghosts:
            draw_ghost(screen, int(g['x']), int(g['y']) + y_off, g['color'],
                       g['dir'], self.frame, g['scared'])

        # Pac-Man
        draw_pacman(screen, int(self.pf_pac_x), int(self.pf_pac_y) + y_off,
                    self.pf_pac_dir, self.frame)

        if self.pf_ready > 0:
            txt = self.font_big.render("GO WILD!", True, YELLOW)
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 30))

    # ─── MENU ────────────────────────────────────────────────────────────
    def draw_menu(self):
        screen.fill(BLACK)

        # Animated title
        y_base = 60
        title_text = "PAC-MAN"
        for i, ch in enumerate(title_text):
            y = y_base + int(math.sin(self.frame * 0.08 + i * 0.5) * 8)
            col = YELLOW if ch != '-' else WHITE
            letter = self.font_big.render(ch, True, col)
            screen.blit(letter, (WIDTH // 2 - 130 + i * 38, y))

        sub = self.font_med.render("U L T I M A T E", True, CYAN)
        screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 130))

        # Animated Pac-Man & ghosts on menu
        menu_y = 180
        pac_x = int((self.frame * 2) % (WIDTH + 200)) - 100
        draw_pacman(screen, pac_x, menu_y, 0, self.frame, 32)
        for i, color in enumerate([RED, PINK, CYAN, ORANGE]):
            gx = pac_x - 40 - i * 36
            draw_ghost(screen, gx, menu_y, color, 0, self.frame, False, 32)

        # Menu options
        options = [
            ("🎮  CLASSIC PAC-MAN", "classic"),
            ("👻  GHOST TAG", "ghost_tag"),
            ("⚡  PELLET FRENZY", "pellet_frenzy"),
        ]
        for i, (label, _) in enumerate(options):
            y = 260 + i * 55
            color = YELLOW if i == self.menu_sel else WHITE
            if i == self.menu_sel:
                # Selection indicator
                ind = self.font_med.render("►", True, YELLOW)
                screen.blit(ind, (WIDTH // 2 - 175, y))
                # Glow effect
                pygame.draw.rect(screen, (50, 50, 0), (WIDTH // 2 - 160, y - 5,
                                320, 40), border_radius=8)
            txt = self.font_med.render(label, True, color)
            screen.blit(txt, (WIDTH // 2 - 140, y))

        # High score
        if self.high_score > 0:
            hs = self.font_sm.render(f"HIGH SCORE: {self.high_score}", True, YELLOW)
            screen.blit(hs, (WIDTH // 2 - hs.get_width() // 2, 440))

        # Controls
        ctrl = self.font_xs.render("Arrow Keys / WASD to move  •  ENTER to select  •  ESC for menu",
                                    True, GREY)
        screen.blit(ctrl, (WIDTH // 2 - ctrl.get_width() // 2, HEIGHT - 50))

        credit = self.font_xs.render("Built by Toby with Copilot 🎮", True, GREY)
        screen.blit(credit, (WIDTH // 2 - credit.get_width() // 2, HEIGHT - 25))

    def draw_game_over(self):
        screen.fill(BLACK)
        go = self.font_big.render("GAME OVER", True, RED)
        screen.blit(go, (WIDTH // 2 - go.get_width() // 2, 60))

        if self.last_mode == 'classic':
            # Build leaderboard for classic mode
            your_score = self.score
            entries = [("YOU", YELLOW, your_score)]
            if hasattr(self, 'rivals'):
                for rival in self.rivals:
                    entries.append((rival['name'], rival['color'], rival['score']))
            entries.sort(key=lambda e: e[2], reverse=True)

            board_y = 150
            header = self.font_med.render("LEADERBOARD", True, WHITE)
            screen.blit(header, (WIDTH // 2 - header.get_width() // 2, board_y))
            board_y += 45
            for i, (name, color, sc) in enumerate(entries):
                medal = ["1st", "2nd", "3rd", "4th"][i] if i < 4 else ""
                is_you = name == "YOU"
                prefix = f"{medal}  "
                line_color = YELLOW if is_you else color
                txt = self.font_med.render(f"{prefix}{name}: {sc}", True, line_color)
                screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, board_y))
                if is_you and i == 0:
                    win_txt = self.font_sm.render("YOU WIN!", True, YELLOW)
                    screen.blit(win_txt, (WIDTH // 2 - win_txt.get_width() // 2, board_y + 30))
                board_y += 38
        else:
            # Minigame score display
            if self.last_mode == 'ghost_tag':
                mode_name = "GHOST TAG"
                sc = self.gt_score
                won = getattr(self, 'gt_won', False)
                result_text = "ALL CAUGHT!" if won else "TIME'S UP!"
                result_color = GREEN if won else RED
            else:
                mode_name = "PELLET FRENZY"
                sc = self.pf_score
                result_text = "BUSTED!"
                result_color = RED
            mode_txt = self.font_med.render(mode_name, True, CYAN)
            screen.blit(mode_txt, (WIDTH // 2 - mode_txt.get_width() // 2, 140))
            res_txt = self.font_big.render(result_text, True, result_color)
            screen.blit(res_txt, (WIDTH // 2 - res_txt.get_width() // 2, 180))
            score_txt = self.font_big.render(f"{sc}", True, WHITE)
            screen.blit(score_txt, (WIDTH // 2 - score_txt.get_width() // 2, 240))
            pts = self.font_sm.render("points", True, GREY)
            screen.blit(pts, (WIDTH // 2 - pts.get_width() // 2, 300))

        if self.high_score > 0:
            hs = self.font_sm.render(f"Personal Best: {self.high_score}", True, GREY)
            screen.blit(hs, (WIDTH // 2 - hs.get_width() // 2, HEIGHT // 2 + 100))

        retry = self.font_sm.render("Press ENTER to continue  •  ESC for menu", True, GREY)
        screen.blit(retry, (WIDTH // 2 - retry.get_width() // 2, HEIGHT - 40))

    # ─── MAIN LOOP ───────────────────────────────────────────────────────
    def run(self):
        running = True
        while running:
            dt = clock.tick(FPS) / 1000.0
            self.frame += 1
            keys = pygame.key.get_pressed()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state in ['classic', 'ghost_tag', 'pellet_frenzy']:
                            if self.state == 'classic' and not self.paused:
                                self.paused = True
                            elif self.state == 'classic' and self.paused:
                                self.state = 'menu'
                                self.paused = False
                                self.music_channel.stop()
                                self._current_track = None
                            else:
                                self.state = 'menu'
                                self.music_channel.stop()
                        elif self.state == 'game_over':
                            self.state = 'menu'

                    if self.state == 'menu':
                        if event.key == pygame.K_UP or event.key == pygame.K_w:
                            self.menu_sel = (self.menu_sel - 1) % 3
                            self.sfx_channel.play(snd_menu)
                        elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                            self.menu_sel = (self.menu_sel + 1) % 3
                            self.sfx_channel.play(snd_menu)
                        elif event.key == pygame.K_RETURN:
                            modes = ['classic', 'ghost_tag', 'pellet_frenzy']
                            self.state = modes[self.menu_sel]
                            self.last_mode = self.state
                            self.particles.clear()
                            self.popups.clear()
                            if self.state == 'classic':
                                self.reset_classic()
                            elif self.state == 'ghost_tag':
                                self.reset_ghost_tag()
                            elif self.state == 'pellet_frenzy':
                                self.reset_pellet_frenzy()
                            self.sfx_channel.play(snd_win)

                    elif self.state == 'classic':
                        if event.key == pygame.K_p:
                            self.paused = not self.paused

                    elif self.state == 'game_over':
                        if event.key == pygame.K_RETURN:
                            self.state = 'menu'

            # Update
            if self.state == 'classic':
                self.update_classic(dt, keys)
            elif self.state == 'ghost_tag':
                self.update_ghost_tag(dt, keys)
            elif self.state == 'pellet_frenzy':
                self.update_pellet_frenzy(dt, keys)

            # Update visual effects (always, even during transitions)
            self.particles.update(dt)
            self.popups.update(dt)
            self.transition.update(dt)
            self.shake.update(dt)

            # Draw to offscreen then blit with shake offset
            screen.fill(BLACK)
            if self.state == 'menu':
                self.draw_menu()
            elif self.state == 'classic':
                self.draw_classic()
            elif self.state == 'ghost_tag':
                self.draw_ghost_tag()
            elif self.state == 'pellet_frenzy':
                self.draw_pellet_frenzy()
            elif self.state == 'game_over':
                self.draw_game_over()

            # Draw particles and popups on top
            self.particles.draw(screen)
            self.popups.draw(screen)
            self.transition.draw(screen)

            # Apply screen shake
            if self.shake.offset_x != 0 or self.shake.offset_y != 0:
                shake_surf = screen.copy()
                screen.fill(BLACK)
                screen.blit(shake_surf, (self.shake.offset_x, self.shake.offset_y))

            pygame.display.flip()

        pygame.quit()
        sys.exit()

# ─── LAUNCH! ─────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print(">>  PAC-MAN ULTIMATE")
    print("Loading...")
    game = PacManGame()
    game.run()

