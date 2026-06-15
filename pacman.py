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
    "1222222112222112222102222221",
    "1111112111110110111121111121",
    "0000012111110110111121000000",
    "0000012110000000011212000000",
    "0000012110144441011212000000",
    "1111112110140041011211111111",
    "0000002000140041000200000000",
    "1111112110140041011211111111",
    "0000012110144441011202000000",
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
    "1212222111202202111220121121",
    "1312002222202202222200203121",
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
    "0000012210000000012020000000",
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
    "1312222211222222112222203121",
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
    "1312111121222222121111203121",
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

# ─── BOSS BATTLE ARENA (wide open, no obstacles) ───────────────────────────
BOSS_ARENA = [
    "1111111111111111111111111111",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "0000000000000000000000000000",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1000000000000000000000000001",
    "1111111111111111111111111111",
]

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

# ─── PAC-MAN CUSTOMISATION OPTIONS ──────────────────────────────────────────
PAC_COLOURS = [
    ('Classic Yellow', YELLOW),
    ('Cool Blue',      (0, 180, 255)),
    ('Hot Pink',       (255, 80, 200)),
    ('Lime Green',     (80, 255, 80)),
    ('Fire Red',       (255, 60, 30)),
    ('Royal Purple',   (180, 60, 255)),
    ('Sunset Orange',  (255, 160, 40)),
    ('Ice White',      (220, 240, 255)),
    ('Mint',           (0, 255, 180)),
    ('Gold',           (255, 215, 0)),
]

PAC_SHAPES = ['classic', 'square', 'star', 'triangle', 'diamond']
PAC_HATS = ['none', 'crown', 'top_hat', 'cap', 'halo']

# Active customisation (global so draw_pacman can use it)
pac_custom = {'colour': YELLOW, 'shape': 'classic', 'hat': 'none'}

# ─── SPRITE DRAWING (CLASSIC PIXEL ART) ─────────────────────────────────────
def draw_pacman(surface, x, y, direction, frame, size=TILE, color=None, shape=None, hat=None):
    """Draw Pac-Man with customisable colour, shape and hat."""
    col = color if color else pac_custom['colour']
    shp = shape if shape else pac_custom['shape']
    ht = hat if hat else pac_custom['hat']
    cx, cy = x + size // 2, y + size // 2
    r = size // 2 - 2
    mouth_angle = abs(math.sin(frame * 0.3)) * 45

    angles = {0: 0, 1: 180, 2: 270, 3: 90}
    base = angles.get(direction, 0)

    if shp == 'classic':
        if mouth_angle < 2:
            pygame.gfxdraw.filled_circle(surface, cx, cy, r, col)
            pygame.gfxdraw.aacircle(surface, cx, cy, r, col)
            pygame.gfxdraw.filled_circle(surface, cx - 2, cy - r // 2, 2, BLACK)
            _draw_hat(surface, cx, cy, r, ht, size)
            return
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
            pygame.gfxdraw.filled_polygon(surface, points, col)
            pygame.gfxdraw.aapolygon(surface, points, col)

    elif shp == 'square':
        mouth_frac = mouth_angle / 45.0
        half = r
        if mouth_frac < 0.05:
            pygame.draw.rect(surface, col, (cx - half, cy - half, half * 2, half * 2), border_radius=3)
        else:
            gap = int(half * mouth_frac * 0.6)
            if direction == 0:
                pygame.draw.rect(surface, col, (cx - half, cy - half, half * 2, half - gap), border_radius=3)
                pygame.draw.rect(surface, col, (cx - half, cy + gap, half * 2, half - gap), border_radius=3)
            elif direction == 1:
                pygame.draw.rect(surface, col, (cx - half, cy - half, half * 2, half - gap), border_radius=3)
                pygame.draw.rect(surface, col, (cx - half, cy + gap, half * 2, half - gap), border_radius=3)
            elif direction == 2:
                pygame.draw.rect(surface, col, (cx - half, cy - half, half - gap, half * 2), border_radius=3)
                pygame.draw.rect(surface, col, (cx + gap, cy - half, half - gap, half * 2), border_radius=3)
            else:
                pygame.draw.rect(surface, col, (cx - half, cy - half, half - gap, half * 2), border_radius=3)
                pygame.draw.rect(surface, col, (cx + gap, cy - half, half - gap, half * 2), border_radius=3)

    elif shp == 'star':
        pts = []
        rot = math.radians(base - 90)
        for i in range(10):
            a = rot + math.radians(i * 36)
            rad = r if i % 2 == 0 else r * 0.45
            pts.append((int(cx + rad * math.cos(a)), int(cy + rad * math.sin(a))))
        if mouth_angle > 2 and len(pts) >= 3:
            pygame.gfxdraw.filled_polygon(surface, pts, col)
            pygame.gfxdraw.aapolygon(surface, pts, col)
        elif len(pts) >= 3:
            pygame.gfxdraw.filled_polygon(surface, pts, col)
            pygame.gfxdraw.aapolygon(surface, pts, col)

    elif shp == 'triangle':
        if mouth_angle < 2:
            pts = []
            for i in range(3):
                a = math.radians(base - 90 + i * 120)
                pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
            if len(pts) >= 3:
                pygame.gfxdraw.filled_polygon(surface, pts, col)
                pygame.gfxdraw.aapolygon(surface, pts, col)
        else:
            gap = mouth_angle * 0.4
            pts_top = []
            pts_bot = []
            for i in range(3):
                a = math.radians(base - 90 + i * 120)
                px, py = cx + r * math.cos(a), cy + r * math.sin(a)
                pts_top.append((int(px), int(py - gap)))
                pts_bot.append((int(px), int(py + gap)))
            mid = (cx, cy)
            top_tri = [mid, pts_top[0], pts_top[1]]
            bot_tri = [mid, pts_top[1], pts_top[2]]
            if len(top_tri) >= 3:
                pygame.gfxdraw.filled_polygon(surface, top_tri, col)
            if len(bot_tri) >= 3:
                pygame.gfxdraw.filled_polygon(surface, bot_tri, col)

    elif shp == 'diamond':
        stretch = 1.3
        pts = [
            (cx, int(cy - r * stretch)),
            (int(cx + r * 0.7), cy),
            (cx, int(cy + r * stretch)),
            (int(cx - r * 0.7), cy),
        ]
        if len(pts) >= 3:
            pygame.gfxdraw.filled_polygon(surface, pts, col)
            pygame.gfxdraw.aapolygon(surface, pts, col)

    # Eye
    if direction == 0:
        ex, ey = cx + 2, cy - r // 2
    elif direction == 1:
        ex, ey = cx - 2, cy - r // 2
    elif direction == 2:
        ex, ey = cx - r // 3, cy + 2
    else:
        ex, ey = cx - r // 3, cy - 2
    pygame.gfxdraw.filled_circle(surface, int(ex), int(ey), max(1, size // 12), BLACK)

    _draw_hat(surface, cx, cy, r, ht, size)


def _draw_hat(surface, cx, cy, r, hat, size):
    """Draw a hat/accessory on top of Pac-Man."""
    if hat == 'none':
        return
    top_y = cy - r
    if hat == 'crown':
        cw = int(r * 1.2)
        ch = int(r * 0.6)
        pts = [
            (cx - cw, top_y),
            (cx - cw, top_y - ch),
            (cx - cw // 2, top_y - ch // 3),
            (cx, top_y - ch),
            (cx + cw // 2, top_y - ch // 3),
            (cx + cw, top_y - ch),
            (cx + cw, top_y),
        ]
        pygame.draw.polygon(surface, GOLD, pts)
        pygame.draw.polygon(surface, (200, 170, 0), pts, 1)
        for dx in [-cw // 2, 0, cw // 2]:
            pygame.draw.circle(surface, RED, (cx + dx, top_y - ch + 3), max(1, size // 10))
    elif hat == 'top_hat':
        brim_w = int(r * 1.4)
        hat_w = int(r * 0.8)
        hat_h = int(r * 0.9)
        pygame.draw.rect(surface, (30, 30, 30), (cx - brim_w, top_y - 3, brim_w * 2, 6))
        pygame.draw.rect(surface, (40, 40, 40), (cx - hat_w, top_y - hat_h, hat_w * 2, hat_h))
        pygame.draw.rect(surface, (80, 0, 0), (cx - hat_w, top_y - int(hat_h * 0.3), hat_w * 2, 3))
    elif hat == 'cap':
        pygame.draw.arc(surface, RED, (cx - r, top_y - r // 2, r * 2, r), 0, math.pi, max(1, size // 6))
        pygame.draw.line(surface, RED, (cx, top_y - r // 2), (cx + int(r * 1.2), top_y), max(1, size // 8))
        pygame.draw.circle(surface, WHITE, (cx, top_y - r // 2), max(1, size // 10))
    elif hat == 'halo':
        halo_r = int(r * 0.8)
        halo_y = top_y - int(r * 0.4)
        glow = (255, 255, 150)
        pygame.draw.ellipse(surface, glow, (cx - halo_r, halo_y - 3, halo_r * 2, 8), 2)

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
        self.state = 'menu'  # menu, customise, level_select, classic, ghost_tag, pellet_frenzy, boss_battle, maze_runner, survival, invisible, game_over
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
        # Customisation state
        self.custom_section = 0  # 0=colour, 1=shape, 2=hat
        self.custom_colour_idx = 0
        self.custom_shape_idx = 0
        self.custom_hat_idx = 0
        # Level select state
        self.level_select_idx = 0
        # Visual effects systems
        self.particles = ParticleSystem()
        self.popups = ScorePopupSystem()
        self.transition = ScreenTransition()
        self.shake = ScreenShake()
        self.reset_classic()

    # ─── CLASSIC MODE ────────────────────────────────────────────────────
    def reset_classic(self, new_game=True, start_level=None):
        if new_game:
            self.score = 0
            self.lives = 3
            self.level = start_level if start_level else 1
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
                            rival['dir'], self.frame, color=YELLOW, shape='classic', hat='none')
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
                            p['dir'], self.frame, TILE, color=YELLOW, shape='classic', hat='none')

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

    # ─── BOSS BATTLE MODE ────────────────────────────────────────────────
    def reset_boss_battle(self, level=1, keep_score=False):
        self.bb_maze = parse_maze(BOSS_ARENA)
        self.bb_level = level
        if not keep_score:
            self.bb_score = 0
            self.bb_lives = 3
        # Scale difficulty with level
        base_hp = 20 + level * 10          # 30, 40, 50, …
        self.bb_boss_max_hp = base_hp
        self.bb_boss_hp = base_hp
        # Player — centre-bottom of open arena
        self.bb_pac_col = 14
        self.bb_pac_row = 25
        self.bb_pac_x = self.bb_pac_col * TILE
        self.bb_pac_y = self.bb_pac_row * TILE
        self.bb_pac_dir = 3
        self.bb_pac_next_dir = 3
        self.bb_move_progress = 0
        self.bb_pac_next_col = self.bb_pac_col
        self.bb_pac_next_row = self.bb_pac_row
        self.bb_invincible = 0
        self.bb_shoot_cooldown = 0
        # Projectiles (pellets shot by player and allies)
        self.bb_pellets = []
        # Ally Pac-Men
        self.bb_allies = []
        ally_spawns = [(4, 25), (22, 25), (14, 29)]
        ally_names = ['CHOMPY', 'ZIPPY', 'SPARKY']
        ally_colours = [CYAN, ORANGE, PINK]
        for i, (sc, sr) in enumerate(ally_spawns):
            self.bb_allies.append({
                'name': ally_names[i], 'color': ally_colours[i],
                'col': sc, 'row': sr, 'x': sc * TILE, 'y': sr * TILE,
                'dir': 3, 'next_dir': 3,
                'move_progress': 0, 'next_col': sc, 'next_row': sr,
                'alive': True, 'shoot_timer': random.uniform(0.5, 1.5),
                'respawn_timer': 0,
            })
        # Boss Ghost — big and mean, spawns at top-centre
        self.bb_boss_col = 13
        self.bb_boss_row = 4
        self.bb_boss_x = self.bb_boss_col * TILE
        self.bb_boss_y = self.bb_boss_row * TILE
        self.bb_boss_dir = 0
        self.bb_boss_next_col = self.bb_boss_col
        self.bb_boss_next_row = self.bb_boss_row
        self.bb_boss_move_progress = 0
        self.bb_boss_phase = 1  # gets harder at lower HP
        self.bb_boss_flash = 0
        self.bb_boss_charge_timer = 0
        self.bb_boss_charging = False
        self.bb_boss_charge_dir = 0
        self.bb_boss_spawn_timer = max(2.0, 5.0 - level * 0.5)  # spawns minions faster each level
        # Mini-ghosts spawned by boss
        self.bb_minions = []
        self.bb_ready = 2.5
        self.bb_won = False
        self.bb_win_timer = 0

    def _bb_can_move(self, maze, col, row, direction):
        dc = {0: 1, 1: -1, 2: 0, 3: 0}[direction]
        dr = {0: 0, 1: 0, 2: 1, 3: -1}[direction]
        nc = col + dc
        nr = row + dr
        if nc < 0: nc = COLS - 1
        if nc >= COLS: nc = 0
        if 0 <= nr < ROWS and maze[nr][nc] not in (1, 4, 5):
            return True, nc, nr
        return False, col, row

    def update_boss_battle(self, dt, keys_pressed):
        if self.bb_won:
            self.bb_win_timer -= dt
            if self.bb_win_timer <= 0:
                # Progress to next boss level!
                next_lvl = self.bb_level + 1
                saved_score = self.bb_score
                saved_lives = self.bb_lives
                self.reset_boss_battle(level=next_lvl, keep_score=True)
                self.bb_score = saved_score
                self.bb_lives = saved_lives
            return

        if self.bb_ready > 0:
            self.bb_ready -= dt
            return

        if not self.music_channel.get_busy():
            self.music_channel.play(music_chase, loops=-1)

        if self.bb_invincible > 0:
            self.bb_invincible -= dt
        if self.bb_shoot_cooldown > 0:
            self.bb_shoot_cooldown -= dt

        # ── Player input ──
        if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]:
            self.bb_pac_next_dir = 0
        elif keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]:
            self.bb_pac_next_dir = 1
        elif keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]:
            self.bb_pac_next_dir = 2
        elif keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_w]:
            self.bb_pac_next_dir = 3

        # Shoot pellet with SPACE or mouse click — aims toward mouse cursor
        mouse_shooting = pygame.mouse.get_pressed()[0]
        if (keys_pressed[pygame.K_SPACE] or mouse_shooting) and self.bb_shoot_cooldown <= 0:
            self.bb_shoot_cooldown = 0.25
            mx, my = pygame.mouse.get_pos()
            px = self.bb_pac_x + TILE // 2
            py = self.bb_pac_y + TILE // 2 + 40  # account for y_off in screen coords
            aim_dx = mx - px
            aim_dy = my - py
            aim_dist = max(1, math.sqrt(aim_dx * aim_dx + aim_dy * aim_dy))
            self.bb_pellets.append({
                'x': px,
                'y': py - 40,  # store in maze coords (without y_off)
                'dx': aim_dx / aim_dist * 350,
                'dy': aim_dy / aim_dist * 350,
                'life': 2.0, 'owner': 'player',
                'color': pac_custom['colour'],
            })
            self.sfx_channel.play(snd_chomp)

        # ── Move player ──
        speed = 9.0
        self.bb_move_progress += speed * dt
        if self.bb_move_progress >= 1.0:
            self.bb_move_progress = 0
            self.bb_pac_col = self.bb_pac_next_col
            self.bb_pac_row = self.bb_pac_next_row
            self.bb_pac_x = self.bb_pac_col * TILE
            self.bb_pac_y = self.bb_pac_row * TILE
            ok, nc, nr = self._bb_can_move(self.bb_maze, self.bb_pac_col, self.bb_pac_row, self.bb_pac_next_dir)
            if ok:
                self.bb_pac_dir = self.bb_pac_next_dir
                self.bb_pac_next_col = nc
                self.bb_pac_next_row = nr
            else:
                ok2, nc2, nr2 = self._bb_can_move(self.bb_maze, self.bb_pac_col, self.bb_pac_row, self.bb_pac_dir)
                if ok2:
                    self.bb_pac_next_col = nc2
                    self.bb_pac_next_row = nr2
                else:
                    self.bb_pac_next_col = self.bb_pac_col
                    self.bb_pac_next_row = self.bb_pac_row
        else:
            dcol = self.bb_pac_next_col - self.bb_pac_col
            if abs(dcol) > 1:
                self.bb_pac_x = self.bb_pac_next_col * TILE
            else:
                self.bb_pac_x = self.bb_pac_col * TILE + dcol * TILE * self.bb_move_progress
            self.bb_pac_y = self.bb_pac_row * TILE + (self.bb_pac_next_row - self.bb_pac_row) * TILE * self.bb_move_progress

        # ── Move & shoot allies ──
        dc_map = {0: 1, 1: -1, 2: 0, 3: 0}
        dr_map = {0: 0, 1: 0, 2: 1, 3: -1}
        for ally in self.bb_allies:
            if not ally['alive']:
                ally['respawn_timer'] -= dt
                if ally['respawn_timer'] <= 0:
                    ally['alive'] = True
                    ally['col'] = random.choice([1, 26])
                    ally['row'] = random.choice([23, 26, 29])
                    ally['x'] = ally['col'] * TILE
                    ally['y'] = ally['row'] * TILE
                    ally['next_col'] = ally['col']
                    ally['next_row'] = ally['row']
                continue

            # AI movement — move toward boss, avoid walls
            ally['move_progress'] += 7.0 * dt
            if ally['move_progress'] >= 1.0:
                ally['move_progress'] = 0
                ally['col'] = ally['next_col']
                ally['row'] = ally['next_row']
                ally['x'] = ally['col'] * TILE
                ally['y'] = ally['row'] * TILE
                best_dir = ally['dir']
                best_dist = float('inf')
                dirs = [0, 1, 2, 3]
                random.shuffle(dirs)
                for d in dirs:
                    nc = ally['col'] + dc_map[d]
                    nr = ally['row'] + dr_map[d]
                    if nc < 0: nc = COLS - 1
                    if nc >= COLS: nc = 0
                    if 0 <= nr < ROWS and self.bb_maze[nr][nc] not in (1, 4, 5):
                        dist = (nc - self.bb_boss_col) ** 2 + (nr - self.bb_boss_row) ** 2
                        if dist < best_dist:
                            best_dist = dist
                            best_dir = d
                            ally['next_col'] = nc
                            ally['next_row'] = nr
                ally['dir'] = best_dir
            else:
                ally['x'] = ally['col'] * TILE + (ally['next_col'] - ally['col']) * TILE * ally['move_progress']
                ally['y'] = ally['row'] * TILE + (ally['next_row'] - ally['row']) * TILE * ally['move_progress']

            # Ally auto-shoot
            ally['shoot_timer'] -= dt
            if ally['shoot_timer'] <= 0:
                ally['shoot_timer'] = random.uniform(0.8, 1.8)
                # Aim toward boss
                bx = self.bb_boss_x + TILE
                by = self.bb_boss_y + TILE
                ax = ally['x'] + TILE // 2
                ay = ally['y'] + TILE // 2
                dx = bx - ax
                dy = by - ay
                dist = max(1, math.sqrt(dx * dx + dy * dy))
                self.bb_pellets.append({
                    'x': ax, 'y': ay,
                    'dx': dx / dist * 300, 'dy': dy / dist * 300,
                    'life': 2.0, 'owner': 'ally',
                    'color': ally['color'],
                })

        # ── Update pellets ──
        boss_cx = self.bb_boss_x + TILE
        boss_cy = self.bb_boss_y + TILE
        boss_hit_r = TILE * 1.5
        for p in self.bb_pellets[:]:
            p['x'] += p['dx'] * dt
            p['y'] += p['dy'] * dt
            p['life'] -= dt
            # Off-screen or expired
            if p['life'] <= 0 or p['x'] < -20 or p['x'] > WIDTH + 20 or p['y'] < -20 or p['y'] > HEIGHT + 20:
                self.bb_pellets.remove(p)
                continue
            # Wall collision — remove pellet if it hits a wall
            pc = int(p['x']) // TILE
            pr = int(p['y']) // TILE
            if 0 <= pr < ROWS and 0 <= pc < COLS and self.bb_maze[pr][pc] == 1:
                self.particles.emit_dot_eat(int(p['x']), int(p['y']) + 40, p['color'])
                self.bb_pellets.remove(p)
                continue
            # Boss collision
            dist = math.sqrt((p['x'] - boss_cx) ** 2 + (p['y'] - boss_cy) ** 2)
            if dist < boss_hit_r:
                self.bb_boss_hp -= 1
                self.bb_boss_flash = 0.15
                pts = 100 if p['owner'] == 'player' else 50
                self.bb_score += pts
                self.particles.emit_ghost_eat(int(p['x']), int(p['y']) + 40, RED)
                self.popups.add(int(p['x']), int(p['y']) + 40, f'-1 HP!', RED, self.font_popup)
                self.shake.start(3, 0.15)
                self.sfx_channel.play(snd_eat_ghost)
                if p in self.bb_pellets:
                    self.bb_pellets.remove(p)
                # Check phase transitions
                if self.bb_boss_hp <= 0:
                    self.bb_won = True
                    self.bb_win_timer = 3.0
                    self.bb_score += 5000 * self.bb_level
                    self.particles.emit_level_clear()
                    self.shake.start(10, 1.0)
                    self.sfx_channel.play(snd_win)
                    self.music_channel.stop()
                    return
                elif self.bb_boss_hp <= self.bb_boss_max_hp // 3 and self.bb_boss_phase == 2:
                    self.bb_boss_phase = 3
                elif self.bb_boss_hp <= self.bb_boss_max_hp * 2 // 3 and self.bb_boss_phase == 1:
                    self.bb_boss_phase = 2

        # ── Boss AI ──
        self.bb_boss_flash = max(0, self.bb_boss_flash - dt)
        boss_speed = 3.0 + self.bb_boss_phase * 1.5 + (self.bb_level - 1) * 0.5

        # Boss charges toward player sometimes
        self.bb_boss_charge_timer -= dt
        if self.bb_boss_charge_timer <= 0 and not self.bb_boss_charging:
            if random.random() < 0.02 * self.bb_boss_phase:
                self.bb_boss_charging = True
                dx = self.bb_pac_x - self.bb_boss_x
                dy = self.bb_pac_y - self.bb_boss_y
                if abs(dx) > abs(dy):
                    self.bb_boss_charge_dir = 0 if dx > 0 else 1
                else:
                    self.bb_boss_charge_dir = 2 if dy > 0 else 3
                self.bb_boss_charge_timer = 2.0

        if self.bb_boss_charging:
            self.bb_boss_charge_timer -= dt
            if self.bb_boss_charge_timer <= 0:
                self.bb_boss_charging = False
                self.bb_boss_charge_timer = random.uniform(3.0 / self.bb_boss_phase, 6.0 / self.bb_boss_phase)

        # Boss movement
        self.bb_boss_move_progress += boss_speed * dt
        if self.bb_boss_move_progress >= 1.0:
            self.bb_boss_move_progress = 0
            self.bb_boss_col = self.bb_boss_next_col
            self.bb_boss_row = self.bb_boss_next_row
            self.bb_boss_x = self.bb_boss_col * TILE
            self.bb_boss_y = self.bb_boss_row * TILE

            if self.bb_boss_charging:
                ok, nc, nr = self._bb_can_move(self.bb_maze, self.bb_boss_col, self.bb_boss_row, self.bb_boss_charge_dir)
                if ok:
                    self.bb_boss_dir = self.bb_boss_charge_dir
                    self.bb_boss_next_col = nc
                    self.bb_boss_next_row = nr
                else:
                    self.bb_boss_charging = False
            else:
                best_dir = self.bb_boss_dir
                best_dist = float('inf')
                dirs = [0, 1, 2, 3]
                random.shuffle(dirs)
                for d in dirs:
                    nc = self.bb_boss_col + dc_map[d]
                    nr = self.bb_boss_row + dr_map[d]
                    if nc < 0: nc = COLS - 1
                    if nc >= COLS: nc = 0
                    if 0 <= nr < ROWS and self.bb_maze[nr][nc] not in (1, 4, 5):
                        dist = (nc - self.bb_pac_col) ** 2 + (nr - self.bb_pac_row) ** 2
                        if dist < best_dist:
                            best_dist = dist
                            best_dir = d
                            self.bb_boss_next_col = nc
                            self.bb_boss_next_row = nr
                self.bb_boss_dir = best_dir
        else:
            self.bb_boss_x = self.bb_boss_col * TILE + (self.bb_boss_next_col - self.bb_boss_col) * TILE * self.bb_boss_move_progress
            self.bb_boss_y = self.bb_boss_row * TILE + (self.bb_boss_next_row - self.bb_boss_row) * TILE * self.bb_boss_move_progress

        # Boss spawns minions
        self.bb_boss_spawn_timer -= dt
        if self.bb_boss_spawn_timer <= 0:
            self.bb_boss_spawn_timer = max(1.5, 6.0 - self.bb_boss_phase * 1.5 - self.bb_level * 0.3)
            if len(self.bb_minions) < 3 + self.bb_boss_phase + self.bb_level - 1:
                self.bb_minions.append({
                    'col': self.bb_boss_col, 'row': self.bb_boss_row,
                    'x': self.bb_boss_x, 'y': self.bb_boss_y,
                    'dir': random.randint(0, 3),
                    'next_col': self.bb_boss_col, 'next_row': self.bb_boss_row,
                    'move_progress': 0,
                    'color': [RED, PINK, ORANGE, PURPLE][random.randint(0, 3)],
                })

        # ── Update minions ──
        for m in self.bb_minions[:]:
            m['move_progress'] += (6.0 + (self.bb_level - 1) * 0.5) * dt
            if m['move_progress'] >= 1.0:
                m['move_progress'] = 0
                m['col'] = m['next_col']
                m['row'] = m['next_row']
                m['x'] = m['col'] * TILE
                m['y'] = m['row'] * TILE
                best_dir = m['dir']
                best_dist = float('inf')
                dirs = [0, 1, 2, 3]
                random.shuffle(dirs)
                target_col = self.bb_pac_col
                target_row = self.bb_pac_row
                # Sometimes target an ally instead
                if self.bb_allies and random.random() < 0.3:
                    alive_allies = [a for a in self.bb_allies if a['alive']]
                    if alive_allies:
                        t = random.choice(alive_allies)
                        target_col, target_row = t['col'], t['row']
                for d in dirs:
                    nc = m['col'] + dc_map[d]
                    nr = m['row'] + dr_map[d]
                    if nc < 0: nc = COLS - 1
                    if nc >= COLS: nc = 0
                    if 0 <= nr < ROWS and self.bb_maze[nr][nc] not in (1, 4, 5):
                        dist = (nc - target_col) ** 2 + (nr - target_row) ** 2
                        if dist < best_dist:
                            best_dist = dist
                            best_dir = d
                            m['next_col'] = nc
                            m['next_row'] = nr
                m['dir'] = best_dir
            else:
                m['x'] = m['col'] * TILE + (m['next_col'] - m['col']) * TILE * m['move_progress']
                m['y'] = m['row'] * TILE + (m['next_row'] - m['row']) * TILE * m['move_progress']

            # Minion vs pellet collision
            for p in self.bb_pellets[:]:
                dist = math.sqrt((p['x'] - m['x'] - TILE // 2) ** 2 + (p['y'] - m['y'] - TILE // 2) ** 2)
                if dist < TILE * 0.7:
                    self.particles.emit_ghost_eat(int(m['x']) + TILE // 2, int(m['y']) + TILE // 2 + 40, m['color'])
                    self.bb_score += 200
                    self.popups.add(int(m['x']) + TILE // 2, int(m['y']) + TILE // 2 + 40, '+200', CYAN, self.font_popup)
                    self.sfx_channel.play(snd_eat_ghost)
                    if p in self.bb_pellets:
                        self.bb_pellets.remove(p)
                    if m in self.bb_minions:
                        self.bb_minions.remove(m)
                    break

        # ── Collision: boss/minions vs player ──
        if self.bb_invincible <= 0:
            boss_dist = math.sqrt((self.bb_boss_x - self.bb_pac_x) ** 2 + (self.bb_boss_y - self.bb_pac_y) ** 2)
            if boss_dist < TILE * 1.8:
                self.bb_lives -= 1
                self.bb_invincible = 2.0
                self.shake.start(8, 0.5)
                self.sfx_channel.play(snd_death)
                self.particles.emit_death(int(self.bb_pac_x) + TILE // 2, int(self.bb_pac_y) + TILE // 2 + 40)
                if self.bb_lives <= 0:
                    self.state = 'game_over'
                    self.high_score = max(self.high_score, self.bb_score)
                    self.music_channel.stop()
                    return

            for m in self.bb_minions:
                dist = math.sqrt((m['x'] - self.bb_pac_x) ** 2 + (m['y'] - self.bb_pac_y) ** 2)
                if dist < TILE * 0.8:
                    self.bb_lives -= 1
                    self.bb_invincible = 2.0
                    self.shake.start(6, 0.3)
                    self.sfx_channel.play(snd_death)
                    self.particles.emit_death(int(self.bb_pac_x) + TILE // 2, int(self.bb_pac_y) + TILE // 2 + 40)
                    if self.bb_lives <= 0:
                        self.state = 'game_over'
                        self.high_score = max(self.high_score, self.bb_score)
                        self.music_channel.stop()
                        return
                    break

        # ── Collision: boss/minions vs allies ──
        for ally in self.bb_allies:
            if not ally['alive']:
                continue
            boss_dist = math.sqrt((self.bb_boss_x - ally['x']) ** 2 + (self.bb_boss_y - ally['y']) ** 2)
            if boss_dist < TILE * 1.5:
                ally['alive'] = False
                ally['respawn_timer'] = 5.0
                self.particles.emit_death(int(ally['x']) + TILE // 2, int(ally['y']) + TILE // 2 + 40)
                continue
            for m in self.bb_minions:
                dist = math.sqrt((m['x'] - ally['x']) ** 2 + (m['y'] - ally['y']) ** 2)
                if dist < TILE * 0.8:
                    ally['alive'] = False
                    ally['respawn_timer'] = 5.0
                    self.particles.emit_death(int(ally['x']) + TILE // 2, int(ally['y']) + TILE // 2 + 40)
                    break

    def _draw_boss_ghost(self, surface, x, y, frame, flash):
        """Draw a big 2x2 tile boss ghost — colour shifts with level."""
        size = TILE * 2
        cx, cy = x + size // 2, y + size // 2
        r = size // 2 - 2
        boss_body_colours = [(200, 0, 0), (180, 0, 180), (0, 160, 0), (200, 120, 0), (100, 0, 200)]
        base_col = boss_body_colours[(self.bb_level - 1) % len(boss_body_colours)]
        if flash > 0 and int(flash * 20) % 2 == 0:
            body_color = WHITE
        else:
            body_color = base_col

        # Body
        pygame.gfxdraw.filled_circle(surface, cx, cy - 4, r, body_color)
        pygame.gfxdraw.aacircle(surface, cx, cy - 4, r, body_color)
        pygame.draw.rect(surface, body_color, (x + 2, cy - 4, size - 4, r + 4))

        # Wavy bottom
        num_waves = 5
        wave_w = (size - 4) / num_waves
        for i in range(num_waves):
            wx = x + 2 + i * wave_w
            wy = cy + r
            peak = 8 if (i + int(frame / 5)) % 2 == 0 else 0
            pts = [
                (int(wx), int(wy)),
                (int(wx + wave_w * 0.25), int(wy + peak * 0.5)),
                (int(wx + wave_w / 2), int(wy + peak)),
                (int(wx + wave_w * 0.75), int(wy + peak * 0.5)),
                (int(wx + wave_w), int(wy)),
            ]
            pygame.gfxdraw.filled_polygon(surface, pts, body_color)

        # Angry eyes
        for offset in [-8, 8]:
            pygame.gfxdraw.filled_circle(surface, cx + offset, cy - 8, 6, WHITE)
            pygame.gfxdraw.aacircle(surface, cx + offset, cy - 8, 6, WHITE)
            pygame.gfxdraw.filled_circle(surface, cx + offset + 2, cy - 7, 3, RED)
        # Angry eyebrows
        pygame.draw.line(surface, (100, 0, 0), (cx - 16, cy - 18), (cx - 4, cy - 14), 2)
        pygame.draw.line(surface, (100, 0, 0), (cx + 16, cy - 18), (cx + 4, cy - 14), 2)

    def draw_boss_battle(self):
        screen.fill(BLACK)
        y_off = 40

        # HUD
        title = self.font_sm.render(f"⚔️ BOSS BATTLE!  SCORE: {self.bb_score}", True, YELLOW)
        screen.blit(title, (10, 5))

        # Boss HP bar
        bar_w = 200
        bar_h = 14
        bar_x = WIDTH // 2 - bar_w // 2
        bar_y = 22
        hp_frac = max(0, self.bb_boss_hp / self.bb_boss_max_hp)
        pygame.draw.rect(screen, (60, 0, 0), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        if hp_frac > 0:
            hp_col = GREEN if hp_frac > 0.5 else YELLOW if hp_frac > 0.25 else RED
            pygame.draw.rect(screen, hp_col, (bar_x, bar_y, int(bar_w * hp_frac), bar_h), border_radius=4)
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)
        hp_text = self.font_xs.render(f"BOSS LV.{self.bb_level}  HP: {max(0, self.bb_boss_hp)}/{self.bb_boss_max_hp}  Phase {self.bb_boss_phase}", True, WHITE)
        screen.blit(hp_text, (WIDTH // 2 - hp_text.get_width() // 2, bar_y - 14))

        # Lives
        lives_txt = self.font_sm.render(f"♥ x{self.bb_lives}", True, RED if self.bb_lives == 1 else YELLOW)
        screen.blit(lives_txt, (WIDTH - lives_txt.get_width() - 10, 5))

        # Maze (walls only) — colour shifts with boss level
        boss_wall_colours = [(33, 33, 222), (200, 0, 0), (0, 200, 80), (200, 0, 200), (255, 160, 0)]
        wall_col = boss_wall_colours[(self.bb_level - 1) % len(boss_wall_colours)]
        for r in range(ROWS):
            for c in range(COLS):
                if self.bb_maze[r][c] == 1:
                    x = c * TILE
                    y = r * TILE + y_off
                    pygame.draw.rect(screen, wall_col, (x + 1, y + 1, TILE - 2, TILE - 2), 2, border_radius=4)

        # Draw pellets in flight
        for p in self.bb_pellets:
            px, py = int(p['x']), int(p['y']) + y_off
            pygame.draw.circle(screen, p['color'], (px, py), 4)
            pygame.draw.circle(screen, WHITE, (px, py), 4, 1)

        # Draw minions
        for m in self.bb_minions:
            draw_ghost(screen, int(m['x']), int(m['y']) + y_off, m['color'],
                       m['dir'], self.frame, False)

        # Draw boss ghost (big!)
        self._draw_boss_ghost(screen, int(self.bb_boss_x), int(self.bb_boss_y) + y_off,
                              self.frame, self.bb_boss_flash)
        # Charging indicator
        if self.bb_boss_charging:
            charge_txt = self.font_xs.render("CHARGING!", True, RED)
            screen.blit(charge_txt, (int(self.bb_boss_x) + TILE - charge_txt.get_width() // 2,
                                     int(self.bb_boss_y) + y_off - 15))

        # Draw allies
        for ally in self.bb_allies:
            if ally['alive']:
                draw_pacman(screen, int(ally['x']), int(ally['y']) + y_off,
                            ally['dir'], self.frame, color=ally['color'], shape='classic', hat='none')
                tag = self.font_xs.render(ally['name'], True, ally['color'])
                screen.blit(tag, (int(ally['x']) - tag.get_width() // 2 + TILE // 2,
                                  int(ally['y']) + y_off - 12))

        # Draw player (blink when invincible)
        if self.bb_invincible <= 0 or int(self.bb_invincible * 10) % 2 == 0:
            draw_pacman(screen, int(self.bb_pac_x), int(self.bb_pac_y) + y_off,
                        self.bb_pac_dir, self.frame)

        # Draw crosshair at mouse position
        mx, my = pygame.mouse.get_pos()
        cross_col = pac_custom['colour']
        pygame.draw.line(screen, cross_col, (mx - 8, my), (mx + 8, my), 2)
        pygame.draw.line(screen, cross_col, (mx, my - 8), (mx, my + 8), 2)
        pygame.draw.circle(screen, cross_col, (mx, my), 6, 1)

        # Ready text
        if self.bb_ready > 0:
            lvl_txt = self.font_big.render(f"BOSS LEVEL {self.bb_level}!", True, RED)
            screen.blit(lvl_txt, (WIDTH // 2 - lvl_txt.get_width() // 2, HEIGHT // 2 - 70))
            txt = self.font_med.render("FIGHT!", True, YELLOW)
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 20))
            hint = self.font_sm.render("Aim with MOUSE, SPACE to shoot!", True, WHITE)
            screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT // 2 + 20))

        # Win text
        if self.bb_won:
            txt = self.font_big.render("BOSS DEFEATED!", True, GOLD)
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 40))
            bonus = self.font_med.render(f"+{5000 * self.bb_level} BONUS!  Next: Level {self.bb_level + 1}", True, YELLOW)
            screen.blit(bonus, (WIDTH // 2 - bonus.get_width() // 2, HEIGHT // 2 + 20))

    def _mode_random_dir(self, maze, col, row, current_dir):
        reverse = {0: 1, 1: 0, 2: 3, 3: 2}
        options = []
        for direction in range(4):
            ok, nc, nr = self._bb_can_move(maze, col, row, direction)
            if ok:
                options.append((direction, nc, nr))
        if not options:
            return current_dir, col, row
        non_reverse = [opt for opt in options if opt[0] != reverse.get(current_dir, -1)]
        direction, nc, nr = random.choice(non_reverse or options)
        return direction, nc, nr

    def _mode_random_open_tile(self, maze, edge_only=False):
        tiles = []
        if edge_only:
            for c in range(1, COLS - 1):
                for r in (1, ROWS - 2):
                    if maze[r][c] not in (1, 4, 5):
                        tiles.append((c, r))
            for r in range(1, ROWS - 1):
                for c in (1, COLS - 2):
                    if maze[r][c] not in (1, 4, 5):
                        tiles.append((c, r))
        else:
            for r in range(ROWS):
                for c in range(COLS):
                    if maze[r][c] not in (1, 4, 5):
                        tiles.append((c, r))
        return random.choice(tiles) if tiles else (13, 23)

    # ─── MAZE RUNNER MODE ────────────────────────────────────────────────
    def reset_maze_runner(self):
        self.mr_maze_idx = random.randrange(len(ALL_MAZES))
        self.mr_maze = parse_maze(ALL_MAZES[self.mr_maze_idx])
        self.mr_theme = LEVEL_THEMES[self.mr_maze_idx % len(LEVEL_THEMES)]
        start_positions = [(13, 23), (14, 23), (13, 14), (1, 1), (26, 29)]
        start_col, start_row = self._mode_random_open_tile(self.mr_maze)
        for sc, sr in start_positions:
            if self.mr_maze[sr][sc] not in (1, 4, 5):
                start_col, start_row = sc, sr
                break
        self.mr_pac_col = start_col
        self.mr_pac_row = start_row
        self.mr_pac_x = self.mr_pac_col * TILE
        self.mr_pac_y = self.mr_pac_row * TILE
        self.mr_pac_dir = 0
        self.mr_pac_next_dir = 0
        self.mr_move_progress = 0.0
        self.mr_pac_next_col = self.mr_pac_col
        self.mr_pac_next_row = self.mr_pac_row
        self.mr_timer = 60.0
        self.mr_elapsed = 0.0
        self.mr_ready = 2.0
        self.mr_score = 0
        self.mr_final_score = 0
        self.mr_bonus_points = 0
        self.mr_dots_total = sum(row.count(2) + row.count(3) for row in self.mr_maze)
        self.mr_dots_eaten = 0
        self.mr_completion_time = 0.0
        self.mr_end_timer = 0.0
        self.mr_won = False
        self.mr_result_text = ""

    def update_maze_runner(self, dt, keys_pressed):
        if self.mr_end_timer > 0:
            self.mr_end_timer -= dt
            if self.mr_end_timer <= 0:
                self.state = 'game_over'
                self.high_score = max(self.high_score, self.mr_final_score)
            return

        if self.mr_ready > 0:
            self.mr_ready -= dt
            return

        if not self.music_channel.get_busy():
            self.music_channel.play(music_chase, loops=-1)

        if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]:
            self.mr_pac_next_dir = 0
        elif keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]:
            self.mr_pac_next_dir = 1
        elif keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]:
            self.mr_pac_next_dir = 2
        elif keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_w]:
            self.mr_pac_next_dir = 3

        self.mr_elapsed += dt
        self.mr_timer = max(0.0, self.mr_timer - dt)
        self.mr_score = self.mr_dots_eaten * max(1, int(self.mr_timer) + 1)
        if self.mr_timer <= 0:
            self.mr_final_score = self.mr_score
            self.mr_result_text = "TIME'S UP!"
            self.mr_won = False
            self.state = 'game_over'
            self.high_score = max(self.high_score, self.mr_final_score)
            self.music_channel.stop()
            self.sfx_channel.play(snd_death)
            return

        speed = 9.6
        self.mr_move_progress += speed * dt
        if self.mr_move_progress >= 1.0:
            self.mr_move_progress = 0.0
            self.mr_pac_col = self.mr_pac_next_col
            self.mr_pac_row = self.mr_pac_next_row
            self.mr_pac_x = self.mr_pac_col * TILE
            self.mr_pac_y = self.mr_pac_row * TILE

            tile = self.mr_maze[self.mr_pac_row][self.mr_pac_col]
            px = self.mr_pac_col * TILE + TILE // 2
            py = self.mr_pac_row * TILE + TILE // 2 + 40
            if tile == 2:
                self.mr_maze[self.mr_pac_row][self.mr_pac_col] = 0
                self.mr_dots_eaten += 1
                self.mr_timer += 0.5
                self.sfx_channel.play(snd_chomp)
                self.particles.emit_dot_eat(px, py, self.mr_theme['dot'])
                self.popups.add(px, py, "+0.5s", CYAN, self.font_popup)
            elif tile == 3:
                self.mr_maze[self.mr_pac_row][self.mr_pac_col] = 0
                self.mr_dots_eaten += 1
                self.mr_timer += 3.0
                self.sfx_channel.play(snd_power)
                self.particles.emit_power_pellet(px, py)
                self.popups.add(px, py, "+3.0s", GOLD, self.font_popup)
                self.shake.start(3, 0.15)

            self.mr_score = self.mr_dots_eaten * max(1, int(self.mr_timer) + 1)
            if self.mr_dots_eaten >= self.mr_dots_total:
                self.mr_won = True
                self.mr_completion_time = self.mr_elapsed
                self.mr_bonus_points = int(self.mr_timer * 100)
                self.mr_final_score = self.mr_score + self.mr_bonus_points
                self.mr_score = self.mr_final_score
                self.mr_result_text = "MAZE CLEARED!"
                self.popups.add(px, py - 20, f"+{self.mr_bonus_points} BONUS!", YELLOW, self.font_popup)
                self.particles.emit_level_clear()
                self.sfx_channel.play(snd_win)
                self.music_channel.stop()
                self.mr_end_timer = 2.8
                return

            ok, nc, nr = self._bb_can_move(self.mr_maze, self.mr_pac_col, self.mr_pac_row, self.mr_pac_next_dir)
            if ok:
                self.mr_pac_dir = self.mr_pac_next_dir
                self.mr_pac_next_col = nc
                self.mr_pac_next_row = nr
            else:
                ok, nc, nr = self._bb_can_move(self.mr_maze, self.mr_pac_col, self.mr_pac_row, self.mr_pac_dir)
                if ok:
                    self.mr_pac_next_col = nc
                    self.mr_pac_next_row = nr
                else:
                    self.mr_pac_next_col = self.mr_pac_col
                    self.mr_pac_next_row = self.mr_pac_row
        else:
            dcol = self.mr_pac_next_col - self.mr_pac_col
            if abs(dcol) > 1:
                self.mr_pac_x = self.mr_pac_next_col * TILE
            else:
                self.mr_pac_x = self.mr_pac_col * TILE + dcol * TILE * self.mr_move_progress
            self.mr_pac_y = self.mr_pac_row * TILE + (self.mr_pac_next_row - self.mr_pac_row) * TILE * self.mr_move_progress

        if self.frame % 3 == 0:
            self.particles.emit_trail(self.mr_pac_x + TILE // 2, self.mr_pac_y + TILE // 2 + 40, pac_custom['colour'])

    def draw_maze_runner(self):
        screen.fill(self.mr_theme['bg'])
        y_off = 40

        score_txt = self.font_sm.render(f"🏁 SCORE: {self.mr_score}", True, YELLOW)
        screen.blit(score_txt, (10, 7))
        dots_left = self.mr_dots_total - self.mr_dots_eaten
        dots_txt = self.font_sm.render(f"DOTS: {self.mr_dots_eaten}/{self.mr_dots_total}  LEFT: {dots_left}", True, WHITE)
        screen.blit(dots_txt, (10, 28))
        timer_col = RED if self.mr_timer < 10 else CYAN
        timer_txt = self.font_big.render(f"{self.mr_timer:04.1f}", True, timer_col)
        screen.blit(timer_txt, (WIDTH // 2 - timer_txt.get_width() // 2, 2))
        mult_txt = self.font_sm.render(f"TIME BONUS x{max(1, int(self.mr_timer) + 1)}", True, GOLD)
        screen.blit(mult_txt, (WIDTH - mult_txt.get_width() - 10, 16))

        wall_fill = tuple(max(0, c // 4) for c in self.mr_theme['wall'])
        for r in range(ROWS):
            for c in range(COLS):
                tile = self.mr_maze[r][c]
                x = c * TILE
                y = r * TILE + y_off
                cx = x + TILE // 2
                cy = y + TILE // 2
                if tile == 1:
                    pygame.draw.rect(screen, wall_fill, (x + 2, y + 2, TILE - 4, TILE - 4), border_radius=3)
                    pygame.draw.rect(screen, self.mr_theme['wall'], (x + 1, y + 1, TILE - 2, TILE - 2), 2, border_radius=4)
                elif tile == 2:
                    pygame.gfxdraw.filled_circle(screen, cx, cy, 2, self.mr_theme['dot'])
                    pygame.gfxdraw.aacircle(screen, cx, cy, 2, self.mr_theme['dot'])
                elif tile == 3 and self.frame % 20 < 15:
                    pygame.gfxdraw.filled_circle(screen, cx, cy, 5, self.mr_theme['pellet'])
                    pygame.gfxdraw.aacircle(screen, cx, cy, 5, self.mr_theme['pellet'])

        draw_pacman(screen, int(self.mr_pac_x), int(self.mr_pac_y) + y_off, self.mr_pac_dir, self.frame)

        if self.mr_ready > 0:
            txt = self.font_big.render("MAZE RUN!", True, YELLOW)
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 40))
        elif self.mr_end_timer > 0:
            done = self.font_big.render(self.mr_result_text, True, GREEN)
            screen.blit(done, (WIDTH // 2 - done.get_width() // 2, HEIGHT // 2 - 45))
            time_txt = self.font_med.render(f"Finished in {self.mr_completion_time:.1f}s  •  Bonus +{self.mr_bonus_points}", True, WHITE)
            screen.blit(time_txt, (WIDTH // 2 - time_txt.get_width() // 2, HEIGHT // 2 + 10))

    # ─── SURVIVAL MODE ───────────────────────────────────────────────────
    def reset_survival(self):
        self.sv_maze = parse_maze(BOSS_ARENA)
        self.sv_pac_col = 14
        self.sv_pac_row = 15
        self.sv_pac_x = self.sv_pac_col * TILE
        self.sv_pac_y = self.sv_pac_row * TILE
        self.sv_pac_dir = 3
        self.sv_pac_next_dir = 3
        self.sv_move_progress = 0.0
        self.sv_pac_next_col = self.sv_pac_col
        self.sv_pac_next_row = self.sv_pac_row
        self.sv_score = 0
        self.sv_time = 0.0
        self.sv_score_tick = 0.0
        self.sv_spawn_timer = 3.0
        self.sv_spawn_interval = 3.0
        self.sv_ready = 2.0
        self.sv_lives = 3
        self.sv_invincible = 0.0
        self.sv_ghosts = []
        self.sv_power_pellet = None
        self.sv_power_spawn_timer = 15.0
        self.sv_power_mode = 0.0
        self.sv_ghosts_eaten = 0

    def update_survival(self, dt, keys_pressed):
        if self.sv_ready > 0:
            self.sv_ready -= dt
            return

        if not self.music_channel.get_busy():
            self.music_channel.play(music_chase, loops=-1)

        self.sv_time += dt
        self.sv_score_tick += dt
        while self.sv_score_tick >= 1.0:
            self.sv_score += 10
            self.sv_score_tick -= 1.0

        if self.sv_invincible > 0:
            self.sv_invincible -= dt
        if self.sv_power_mode > 0:
            self.sv_power_mode = max(0.0, self.sv_power_mode - dt)

        self.sv_power_spawn_timer -= dt
        if self.sv_power_spawn_timer <= 0:
            self.sv_power_spawn_timer += 15.0
            self.sv_power_pellet = self._mode_random_open_tile(self.sv_maze)
            px = self.sv_power_pellet[0] * TILE + TILE // 2
            py = self.sv_power_pellet[1] * TILE + TILE // 2 + 40
            self.popups.add(px, py, "POWER!", CYAN, self.font_popup)

        self.sv_spawn_interval = max(0.5, 3.0 - self.sv_time * 0.05)
        self.sv_spawn_timer -= dt
        if self.sv_spawn_timer <= 0 and len(self.sv_ghosts) < 15:
            self.sv_spawn_timer = self.sv_spawn_interval
            gc, gr = self._mode_random_open_tile(self.sv_maze, edge_only=True)
            ghost_speed = min(9.0, 5.2 + self.sv_time * 0.04)
            direction, nc, nr = self._mode_random_dir(self.sv_maze, gc, gr, random.randint(0, 3))
            self.sv_ghosts.append({
                'col': gc, 'row': gr, 'x': gc * TILE, 'y': gr * TILE,
                'dir': direction, 'next_col': nc, 'next_row': nr,
                'move_progress': 0.0, 'speed': ghost_speed,
                'color': random.choice([RED, PINK, CYAN, ORANGE, PURPLE, GREEN]),
            })

        if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]:
            self.sv_pac_next_dir = 0
        elif keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]:
            self.sv_pac_next_dir = 1
        elif keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]:
            self.sv_pac_next_dir = 2
        elif keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_w]:
            self.sv_pac_next_dir = 3

        self.sv_move_progress += 8.8 * dt
        if self.sv_move_progress >= 1.0:
            self.sv_move_progress = 0.0
            self.sv_pac_col = self.sv_pac_next_col
            self.sv_pac_row = self.sv_pac_next_row
            self.sv_pac_x = self.sv_pac_col * TILE
            self.sv_pac_y = self.sv_pac_row * TILE
            if self.sv_power_pellet and (self.sv_pac_col, self.sv_pac_row) == self.sv_power_pellet:
                self.sv_power_pellet = None
                self.sv_power_mode = 5.0
                self.sfx_channel.play(snd_power)
                self.particles.emit_power_pellet(int(self.sv_pac_x) + TILE // 2, int(self.sv_pac_y) + TILE // 2 + 40)
                self.popups.add(int(self.sv_pac_x) + TILE // 2, int(self.sv_pac_y) + 20, "SCARED!", CYAN, self.font_popup)
                self.shake.start(3, 0.2)

            ok, nc, nr = self._bb_can_move(self.sv_maze, self.sv_pac_col, self.sv_pac_row, self.sv_pac_next_dir)
            if ok:
                self.sv_pac_dir = self.sv_pac_next_dir
                self.sv_pac_next_col = nc
                self.sv_pac_next_row = nr
            else:
                ok, nc, nr = self._bb_can_move(self.sv_maze, self.sv_pac_col, self.sv_pac_row, self.sv_pac_dir)
                if ok:
                    self.sv_pac_next_col = nc
                    self.sv_pac_next_row = nr
                else:
                    self.sv_pac_next_col = self.sv_pac_col
                    self.sv_pac_next_row = self.sv_pac_row
        else:
            dcol = self.sv_pac_next_col - self.sv_pac_col
            if abs(dcol) > 1:
                self.sv_pac_x = self.sv_pac_next_col * TILE
            else:
                self.sv_pac_x = self.sv_pac_col * TILE + dcol * TILE * self.sv_move_progress
            self.sv_pac_y = self.sv_pac_row * TILE + (self.sv_pac_next_row - self.sv_pac_row) * TILE * self.sv_move_progress

        if self.frame % 3 == 0:
            self.particles.emit_trail(self.sv_pac_x + TILE // 2, self.sv_pac_y + TILE // 2 + 40, pac_custom['colour'])

        for ghost in self.sv_ghosts:
            ghost['speed'] = min(9.5, ghost['speed'] + dt * 0.03)
            ghost['move_progress'] += ghost['speed'] * dt * (0.75 if self.sv_power_mode > 0 else 1.0)
            if ghost['move_progress'] >= 1.0:
                ghost['move_progress'] = 0.0
                ghost['col'] = ghost['next_col']
                ghost['row'] = ghost['next_row']
                ghost['x'] = ghost['col'] * TILE
                ghost['y'] = ghost['row'] * TILE
                direction, nc, nr = self._mode_random_dir(self.sv_maze, ghost['col'], ghost['row'], ghost['dir'])
                ghost['dir'] = direction
                ghost['next_col'] = nc
                ghost['next_row'] = nr
            else:
                dcol = ghost['next_col'] - ghost['col']
                if abs(dcol) > 1:
                    ghost['x'] = ghost['next_col'] * TILE
                else:
                    ghost['x'] = ghost['col'] * TILE + dcol * TILE * ghost['move_progress']
                ghost['y'] = ghost['row'] * TILE + (ghost['next_row'] - ghost['row']) * TILE * ghost['move_progress']

            dist = math.sqrt((ghost['x'] - self.sv_pac_x) ** 2 + (ghost['y'] - self.sv_pac_y) ** 2)
            if dist < TILE * 0.8:
                if self.sv_power_mode > 0:
                    gc, gr = self._mode_random_open_tile(self.sv_maze, edge_only=True)
                    ghost['col'] = gc
                    ghost['row'] = gr
                    ghost['x'] = gc * TILE
                    ghost['y'] = gr * TILE
                    ghost['move_progress'] = 0.0
                    direction, nc, nr = self._mode_random_dir(self.sv_maze, gc, gr, ghost['dir'])
                    ghost['dir'] = direction
                    ghost['next_col'] = nc
                    ghost['next_row'] = nr
                    self.sv_score += 500
                    self.sv_ghosts_eaten += 1
                    gx = int(ghost['x']) + TILE // 2
                    gy = int(ghost['y']) + TILE // 2 + 40
                    self.sfx_channel.play(snd_eat_ghost)
                    self.particles.emit_ghost_eat(gx, gy, ghost['color'])
                    self.popups.add(gx, gy, "+500", GOLD, self.font_popup)
                    self.shake.start(4, 0.2)
                elif self.sv_invincible <= 0:
                    self.sv_lives -= 1
                    self.sv_invincible = 2.0
                    self.sv_pac_col = 14
                    self.sv_pac_row = 15
                    self.sv_pac_x = self.sv_pac_col * TILE
                    self.sv_pac_y = self.sv_pac_row * TILE
                    self.sv_pac_next_col = self.sv_pac_col
                    self.sv_pac_next_row = self.sv_pac_row
                    self.sv_move_progress = 0.0
                    self.sv_ready = 1.0
                    self.sfx_channel.play(snd_death)
                    self.particles.emit_death(int(self.sv_pac_x) + TILE // 2, int(self.sv_pac_y) + TILE // 2 + 40)
                    self.shake.start(8, 0.4)
                    for push_ghost in self.sv_ghosts:
                        gc, gr = self._mode_random_open_tile(self.sv_maze, edge_only=True)
                        push_ghost['col'] = gc
                        push_ghost['row'] = gr
                        push_ghost['x'] = gc * TILE
                        push_ghost['y'] = gr * TILE
                        push_ghost['move_progress'] = 0.0
                        direction, nc, nr = self._mode_random_dir(self.sv_maze, gc, gr, push_ghost['dir'])
                        push_ghost['dir'] = direction
                        push_ghost['next_col'] = nc
                        push_ghost['next_row'] = nr
                    if self.sv_lives <= 0:
                        self.state = 'game_over'
                        self.high_score = max(self.high_score, self.sv_score)
                        self.music_channel.stop()
                    return

    def draw_survival(self):
        screen.fill((8, 0, 0))
        y_off = 40

        title = self.font_sm.render(f"🛡️ SURVIVAL  SCORE: {self.sv_score}", True, YELLOW)
        screen.blit(title, (10, 7))
        timer_txt = self.font_big.render(f"{self.sv_time:05.1f}s", True, WHITE if self.sv_lives > 1 else RED)
        screen.blit(timer_txt, (WIDTH // 2 - timer_txt.get_width() // 2, 2))
        info_txt = self.font_sm.render(f"GHOSTS: {len(self.sv_ghosts)}/15  ♥ {self.sv_lives}", True, CYAN)
        screen.blit(info_txt, (WIDTH - info_txt.get_width() - 10, 16))

        for r in range(ROWS):
            for c in range(COLS):
                if self.sv_maze[r][c] == 1:
                    x = c * TILE
                    y = r * TILE + y_off
                    pygame.draw.rect(screen, (120, 0, 0), (x + 1, y + 1, TILE - 2, TILE - 2), 2, border_radius=4)

        if self.sv_power_pellet and self.frame % 20 < 15:
            px = self.sv_power_pellet[0] * TILE + TILE // 2
            py = self.sv_power_pellet[1] * TILE + TILE // 2 + y_off
            pygame.gfxdraw.filled_circle(screen, px, py, 6, CYAN)
            pygame.gfxdraw.aacircle(screen, px, py, 6, WHITE)

        for ghost in self.sv_ghosts:
            draw_ghost(screen, int(ghost['x']), int(ghost['y']) + y_off, ghost['color'],
                       ghost['dir'], self.frame, self.sv_power_mode > 0)

        if self.sv_invincible <= 0 or int(self.sv_invincible * 12) % 2 == 0:
            draw_pacman(screen, int(self.sv_pac_x), int(self.sv_pac_y) + y_off, self.sv_pac_dir, self.frame)

        if self.sv_ready > 0:
            txt = self.font_big.render("SURVIVE!", True, YELLOW)
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 40))

        hint = self.font_sm.render("Power pellet every 15 seconds  •  +500 for scared ghosts", True, GREY)
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 30))

    # ─── INVISIBLE MAZE MODE ─────────────────────────────────────────────
    def _iv_reveal_walls(self, hit_col, hit_row):
        for r in range(max(0, hit_row - 3), min(ROWS, hit_row + 4)):
            for c in range(max(0, hit_col - 3), min(COLS, hit_col + 4)):
                if (c - hit_col) ** 2 + (r - hit_row) ** 2 <= 10 and self.iv_maze[r][c] in (1, 5):
                    self.iv_reveals[(c, r)] = 1.5
                    if self.iv_maze[r][c] == 1:
                        self.iv_seen_walls.add((c, r))

    def reset_invisible(self):
        self.iv_maze = parse_maze(MAZE_TEMPLATE)
        self.iv_pac_col = 13
        self.iv_pac_row = 23
        self.iv_pac_x = self.iv_pac_col * TILE
        self.iv_pac_y = self.iv_pac_row * TILE
        self.iv_pac_dir = 0
        self.iv_pac_next_dir = 0
        self.iv_move_progress = 0.0
        self.iv_pac_next_col = self.iv_pac_col
        self.iv_pac_next_row = self.iv_pac_row
        self.iv_score = 0
        self.iv_lives = 3
        self.iv_ready = 2.0
        self.iv_invincible = 0.0
        self.iv_combo = 0
        self.iv_dots_total = sum(row.count(2) + row.count(3) for row in self.iv_maze)
        self.iv_dots_eaten = 0
        self.iv_reveals = {}
        self.iv_seen_walls = set()
        self.iv_wall_total = sum(row.count(1) for row in self.iv_maze)
        self.iv_won = False
        self.iv_end_timer = 0.0
        self.iv_ghosts = []
        ghost_specs = [
            (13, 11, RED),
            (13, 14, PINK),
            (11, 14, CYAN),
            (15, 14, ORANGE),
        ]
        for i, (gc, gr, color) in enumerate(ghost_specs):
            direction, nc, nr = self._mode_random_dir(self.iv_maze, gc, gr, random.randint(0, 3))
            self.iv_ghosts.append({
                'home_col': gc, 'home_row': gr,
                'col': gc, 'row': gr, 'x': gc * TILE, 'y': gr * TILE,
                'dir': direction, 'next_col': nc, 'next_row': nr,
                'move_progress': 0.0, 'speed': 5.6 + i * 0.25,
                'color': color, 'scared_timer': 0.0,
            })

    def update_invisible(self, dt, keys_pressed):
        if self.iv_end_timer > 0:
            self.iv_end_timer -= dt
            if self.iv_end_timer <= 0:
                self.state = 'game_over'
                self.high_score = max(self.high_score, self.iv_score)
            return

        if self.iv_ready > 0:
            self.iv_ready -= dt
            return

        if not self.music_channel.get_busy():
            self.music_channel.play(music_ghost_tag, loops=-1)

        if self.iv_invincible > 0:
            self.iv_invincible -= dt

        for key in list(self.iv_reveals.keys()):
            self.iv_reveals[key] -= dt
            if self.iv_reveals[key] <= 0:
                del self.iv_reveals[key]

        if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]:
            self.iv_pac_next_dir = 0
        elif keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]:
            self.iv_pac_next_dir = 1
        elif keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]:
            self.iv_pac_next_dir = 2
        elif keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_w]:
            self.iv_pac_next_dir = 3

        self.iv_move_progress += 8.0 * dt
        if self.iv_move_progress >= 1.0:
            self.iv_move_progress = 0.0
            self.iv_pac_col = self.iv_pac_next_col
            self.iv_pac_row = self.iv_pac_next_row
            self.iv_pac_x = self.iv_pac_col * TILE
            self.iv_pac_y = self.iv_pac_row * TILE

            tile = self.iv_maze[self.iv_pac_row][self.iv_pac_col]
            px = self.iv_pac_col * TILE + TILE // 2
            py = self.iv_pac_row * TILE + TILE // 2 + 40
            if tile == 2:
                self.iv_maze[self.iv_pac_row][self.iv_pac_col] = 0
                self.iv_dots_eaten += 1
                self.iv_score += 10
                self.sfx_channel.play(snd_chomp)
                self.particles.emit_dot_eat(px, py, PURPLE)
            elif tile == 3:
                self.iv_maze[self.iv_pac_row][self.iv_pac_col] = 0
                self.iv_dots_eaten += 1
                self.iv_score += 50
                self.iv_combo = 0
                self.sfx_channel.play(snd_power)
                self.particles.emit_power_pellet(px, py)
                self.shake.start(3, 0.2)
                for ghost in self.iv_ghosts:
                    ghost['scared_timer'] = 5.0

            if self.iv_dots_eaten >= self.iv_dots_total:
                self.iv_won = True
                self.iv_end_timer = 2.8
                self.sfx_channel.play(snd_win)
                self.particles.emit_level_clear()
                self.music_channel.stop()
                return

            ok, nc, nr = self._bb_can_move(self.iv_maze, self.iv_pac_col, self.iv_pac_row, self.iv_pac_next_dir)
            if ok:
                self.iv_pac_dir = self.iv_pac_next_dir
                self.iv_pac_next_col = nc
                self.iv_pac_next_row = nr
            else:
                dc = {0: 1, 1: -1, 2: 0, 3: 0}
                dr = {0: 0, 1: 0, 2: 1, 3: -1}
                hit_col = self.iv_pac_col + dc[self.iv_pac_next_dir]
                hit_row = self.iv_pac_row + dr[self.iv_pac_next_dir]
                if hit_col < 0:
                    hit_col = COLS - 1
                if hit_col >= COLS:
                    hit_col = 0
                if 0 <= hit_row < ROWS and self.iv_maze[hit_row][hit_col] in (1, 4, 5):
                    self._iv_reveal_walls(hit_col, hit_row)
                ok, nc, nr = self._bb_can_move(self.iv_maze, self.iv_pac_col, self.iv_pac_row, self.iv_pac_dir)
                if ok:
                    self.iv_pac_next_col = nc
                    self.iv_pac_next_row = nr
                else:
                    hit_col = self.iv_pac_col + dc[self.iv_pac_dir]
                    hit_row = self.iv_pac_row + dr[self.iv_pac_dir]
                    if hit_col < 0:
                        hit_col = COLS - 1
                    if hit_col >= COLS:
                        hit_col = 0
                    if 0 <= hit_row < ROWS and self.iv_maze[hit_row][hit_col] in (1, 4, 5):
                        self._iv_reveal_walls(hit_col, hit_row)
                    self.iv_pac_next_col = self.iv_pac_col
                    self.iv_pac_next_row = self.iv_pac_row
        else:
            dcol = self.iv_pac_next_col - self.iv_pac_col
            if abs(dcol) > 1:
                self.iv_pac_x = self.iv_pac_next_col * TILE
            else:
                self.iv_pac_x = self.iv_pac_col * TILE + dcol * TILE * self.iv_move_progress
            self.iv_pac_y = self.iv_pac_row * TILE + (self.iv_pac_next_row - self.iv_pac_row) * TILE * self.iv_move_progress

        if self.frame % 3 == 0:
            self.particles.emit_trail(self.iv_pac_x + TILE // 2, self.iv_pac_y + TILE // 2 + 40, PURPLE)

        for ghost in self.iv_ghosts:
            if ghost['scared_timer'] > 0:
                ghost['scared_timer'] = max(0.0, ghost['scared_timer'] - dt)
            ghost['move_progress'] += ghost['speed'] * dt * (0.8 if ghost['scared_timer'] > 0 else 1.0)
            if ghost['move_progress'] >= 1.0:
                ghost['move_progress'] = 0.0
                ghost['col'] = ghost['next_col']
                ghost['row'] = ghost['next_row']
                ghost['x'] = ghost['col'] * TILE
                ghost['y'] = ghost['row'] * TILE
                direction, nc, nr = self._mode_random_dir(self.iv_maze, ghost['col'], ghost['row'], ghost['dir'])
                ghost['dir'] = direction
                ghost['next_col'] = nc
                ghost['next_row'] = nr
            else:
                dcol = ghost['next_col'] - ghost['col']
                if abs(dcol) > 1:
                    ghost['x'] = ghost['next_col'] * TILE
                else:
                    ghost['x'] = ghost['col'] * TILE + dcol * TILE * ghost['move_progress']
                ghost['y'] = ghost['row'] * TILE + (ghost['next_row'] - ghost['row']) * TILE * ghost['move_progress']

            dist = math.sqrt((ghost['x'] - self.iv_pac_x) ** 2 + (ghost['y'] - self.iv_pac_y) ** 2)
            if dist < TILE * 0.8:
                if ghost['scared_timer'] > 0:
                    self.iv_combo += 1
                    pts = 200 * self.iv_combo
                    self.iv_score += pts
                    ghost['col'] = ghost['home_col']
                    ghost['row'] = ghost['home_row']
                    ghost['x'] = ghost['col'] * TILE
                    ghost['y'] = ghost['row'] * TILE
                    ghost['move_progress'] = 0.0
                    ghost['scared_timer'] = 0.0
                    direction, nc, nr = self._mode_random_dir(self.iv_maze, ghost['col'], ghost['row'], ghost['dir'])
                    ghost['dir'] = direction
                    ghost['next_col'] = nc
                    ghost['next_row'] = nr
                    gx = int(ghost['x']) + TILE // 2
                    gy = int(ghost['y']) + TILE // 2 + 40
                    self.sfx_channel.play(snd_eat_ghost)
                    self.particles.emit_ghost_eat(gx, gy, ghost['color'])
                    self.popups.add(gx, gy, f"+{pts}", CYAN, self.font_popup)
                    self.shake.start(4, 0.2)
                elif self.iv_invincible <= 0:
                    self.iv_lives -= 1
                    self.iv_combo = 0
                    self.iv_invincible = 2.0
                    self.iv_ready = 1.0
                    self.iv_pac_col = 13
                    self.iv_pac_row = 23
                    self.iv_pac_x = self.iv_pac_col * TILE
                    self.iv_pac_y = self.iv_pac_row * TILE
                    self.iv_pac_next_col = self.iv_pac_col
                    self.iv_pac_next_row = self.iv_pac_row
                    self.iv_move_progress = 0.0
                    self.sfx_channel.play(snd_death)
                    self.particles.emit_death(int(self.iv_pac_x) + TILE // 2, int(self.iv_pac_y) + TILE // 2 + 40)
                    self.shake.start(8, 0.4)
                    for reset_ghost in self.iv_ghosts:
                        reset_ghost['col'] = reset_ghost['home_col']
                        reset_ghost['row'] = reset_ghost['home_row']
                        reset_ghost['x'] = reset_ghost['col'] * TILE
                        reset_ghost['y'] = reset_ghost['row'] * TILE
                        reset_ghost['move_progress'] = 0.0
                        reset_ghost['scared_timer'] = 0.0
                        direction, nc, nr = self._mode_random_dir(self.iv_maze, reset_ghost['col'], reset_ghost['row'], reset_ghost['dir'])
                        reset_ghost['dir'] = direction
                        reset_ghost['next_col'] = nc
                        reset_ghost['next_row'] = nr
                    if self.iv_lives <= 0:
                        self.state = 'game_over'
                        self.high_score = max(self.high_score, self.iv_score)
                        self.music_channel.stop()
                    return

    def draw_invisible(self):
        screen.fill((6, 0, 14))
        y_off = 40

        title = self.font_sm.render(f"🌫️ INVISIBLE MAZE  SCORE: {self.iv_score}", True, YELLOW)
        screen.blit(title, (10, 7))
        reveal_pct = int(len(self.iv_seen_walls) * 100 / max(1, self.iv_wall_total))
        info = self.font_sm.render(f"WALLS FOUND: {reveal_pct}%  •  DOTS: {self.iv_dots_eaten}/{self.iv_dots_total}", True, CYAN)
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, 28))
        lives = self.font_sm.render(f"♥ x{self.iv_lives}", True, WHITE if self.iv_lives > 1 else RED)
        screen.blit(lives, (WIDTH - lives.get_width() - 10, 16))

        for r in range(ROWS):
            for c in range(COLS):
                tile = self.iv_maze[r][c]
                x = c * TILE
                y = r * TILE + y_off
                cx = x + TILE // 2
                cy = y + TILE // 2
                if tile == 2:
                    pygame.gfxdraw.filled_circle(screen, cx, cy, 2, WHITE)
                    pygame.gfxdraw.aacircle(screen, cx, cy, 2, WHITE)
                elif tile == 3 and self.frame % 20 < 15:
                    pygame.gfxdraw.filled_circle(screen, cx, cy, 5, GOLD)
                    pygame.gfxdraw.aacircle(screen, cx, cy, 5, WHITE)

                reveal = self.iv_reveals.get((c, r), 0.0)
                if tile in (1, 5) and reveal > 0:
                    alpha = max(30, int(220 * (reveal / 1.5)))
                    tile_surf = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                    pygame.draw.rect(tile_surf, (70, 0, 100, alpha // 3), (2, 2, TILE - 4, TILE - 4), border_radius=3)
                    pygame.draw.rect(tile_surf, (180, 80, 255, alpha), (1, 1, TILE - 2, TILE - 2), 2, border_radius=4)
                    screen.blit(tile_surf, (x, y))

        for ghost in self.iv_ghosts:
            draw_ghost(screen, int(ghost['x']), int(ghost['y']) + y_off, ghost['color'],
                       ghost['dir'], self.frame, ghost['scared_timer'] > 0)

        if self.iv_invincible <= 0 or int(self.iv_invincible * 12) % 2 == 0:
            draw_pacman(screen, int(self.iv_pac_x), int(self.iv_pac_y) + y_off, self.iv_pac_dir, self.frame)

        if self.iv_ready > 0:
            txt = self.font_big.render("LISTEN TO THE WALLS...", True, PURPLE)
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 40))
        elif self.iv_end_timer > 0:
            txt = self.font_big.render("MAZE MASTER!", True, GREEN)
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 40))

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
            ("⚔️  BOSS BATTLE", "boss_battle"),
            ("🏁  MAZE RUNNER", "maze_runner"),
            ("🛡️  SURVIVAL", "survival"),
            ("🌫️  INVISIBLE MAZE", "invisible"),
            ("🗺️  CHOOSE LEVEL", "level_select"),
            ("🎨  CUSTOMISE PAC-MAN", "customise"),
        ]
        for i, (label, _) in enumerate(options):
            y = 240 + i * 36
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
            hs_y = 240 + len(options) * 36 + 16
            screen.blit(hs, (WIDTH // 2 - hs.get_width() // 2, hs_y))

        # Controls
        ctrl = self.font_xs.render("Arrow Keys / WASD to move  •  ENTER to select  •  ESC for menu",
                                    True, GREY)
        screen.blit(ctrl, (WIDTH // 2 - ctrl.get_width() // 2, HEIGHT - 50))

        credit = self.font_xs.render("Built by Toby with Copilot 🎮", True, GREY)
        screen.blit(credit, (WIDTH // 2 - credit.get_width() // 2, HEIGHT - 25))

    def draw_customise(self):
        screen.fill(BLACK)

        # Title
        title = self.font_big.render("CUSTOMISE", True, YELLOW)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 30))

        # Live preview - big animated Pac-Man
        preview_size = 80
        preview_x = WIDTH // 2 - preview_size // 2
        preview_y = 100
        # Rotating preview
        d = (self.frame // 30) % 4
        draw_pacman(screen, preview_x, preview_y, d, self.frame, preview_size)

        # Shadow under preview
        pygame.draw.ellipse(screen, (30, 30, 30),
                            (preview_x + 10, preview_y + preview_size + 5, preview_size - 20, 10))

        sections = ['COLOUR', 'SHAPE', 'HAT']
        values = [
            PAC_COLOURS[self.custom_colour_idx][0],
            PAC_SHAPES[self.custom_shape_idx].upper(),
            PAC_HATS[self.custom_hat_idx].upper().replace('_', ' '),
        ]

        y_start = 210
        for i, (section, value) in enumerate(zip(sections, values)):
            y = y_start + i * 80
            is_sel = (i == self.custom_section)

            # Section label
            label_col = YELLOW if is_sel else GREY
            label = self.font_sm.render(section, True, label_col)
            screen.blit(label, (WIDTH // 2 - label.get_width() // 2, y))

            # Value with arrows
            val_col = WHITE if is_sel else (150, 150, 150)
            val_text = self.font_med.render(value, True, val_col)
            val_x = WIDTH // 2 - val_text.get_width() // 2
            screen.blit(val_text, (val_x, y + 22))

            if is_sel:
                # Draw selection arrows
                arrow_bounce = int(math.sin(self.frame * 0.15) * 3)
                left_arrow = self.font_med.render("<", True, YELLOW)
                right_arrow = self.font_med.render(">", True, YELLOW)
                screen.blit(left_arrow, (val_x - 35 + arrow_bounce, y + 22))
                screen.blit(right_arrow, (val_x + val_text.get_width() + 15 - arrow_bounce, y + 22))

                # Glow behind selected section
                glow_rect = (WIDTH // 2 - 160, y - 5, 320, 65)
                pygame.draw.rect(screen, (40, 40, 10), glow_rect, border_radius=8)

            # Colour swatches for colour section
            if i == 0:
                swatch_y = y + 55
                swatch_size = 14
                total_w = len(PAC_COLOURS) * (swatch_size + 4)
                sx = WIDTH // 2 - total_w // 2
                for ci, (_, c) in enumerate(PAC_COLOURS):
                    rect = (sx + ci * (swatch_size + 4), swatch_y, swatch_size, swatch_size)
                    pygame.draw.rect(screen, c, rect, border_radius=3)
                    if ci == self.custom_colour_idx:
                        pygame.draw.rect(screen, WHITE, (rect[0] - 2, rect[1] - 2,
                                         swatch_size + 4, swatch_size + 4), 2, border_radius=4)

        # Controls hint
        hint = self.font_xs.render("UP/DOWN to pick section  •  LEFT/RIGHT to change  •  ENTER or ESC to save",
                                   True, GREY)
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 50))

        credit = self.font_xs.render("Make it YOUR Pac-Man! 🎨", True, GREY)
        screen.blit(credit, (WIDTH // 2 - credit.get_width() // 2, HEIGHT - 25))

    def draw_level_select(self):
        screen.fill(BLACK)

        # Title
        title = self.font_big.render("CHOOSE LEVEL", True, YELLOW)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 30))

        level_names = [
            ("1 — CLASSIC",       "The original maze"),
            ("2 — NEON ARENA",    "Open centre, tight edges"),
            ("3 — SHADOW MAZE",   "Winding labyrinth paths"),
            ("4 — FIRE FORTRESS", "Thick walls, tight corridors"),
            ("5 — ICE GAUNTLET",  "Narrow paths, lots of ghosts"),
        ]

        # Draw mini maze preview of selected level
        sel = self.level_select_idx
        theme = LEVEL_THEMES[sel]
        maze_data = ALL_MAZES[sel]
        mini_tile = 5
        maze_w = COLS * mini_tile
        maze_h = ROWS * mini_tile
        mx = WIDTH // 2 - maze_w // 2
        my = 100

        # Background for preview
        bg_col = theme.get('bg', BLACK)
        pygame.draw.rect(screen, bg_col, (mx - 4, my - 4, maze_w + 8, maze_h + 8), border_radius=4)
        pygame.draw.rect(screen, theme['wall'], (mx - 4, my - 4, maze_w + 8, maze_h + 8), 2, border_radius=4)

        for r_idx, row_str in enumerate(maze_data):
            for c_idx, ch in enumerate(row_str):
                px = mx + c_idx * mini_tile
                py = my + r_idx * mini_tile
                v = int(ch)
                if v == 1:
                    pygame.draw.rect(screen, theme['wall'], (px, py, mini_tile, mini_tile))
                elif v == 2:
                    cx_d = px + mini_tile // 2
                    cy_d = py + mini_tile // 2
                    pygame.draw.circle(screen, theme['dot'], (cx_d, cy_d), 1)
                elif v == 3:
                    cx_d = px + mini_tile // 2
                    cy_d = py + mini_tile // 2
                    pygame.draw.circle(screen, theme['pellet'], (cx_d, cy_d), 2)
                elif v == 5:
                    pygame.draw.rect(screen, theme['gate'], (px, py + mini_tile // 2, mini_tile, 1))

        # Level list below preview
        list_y = my + maze_h + 20
        for i, (name, desc) in enumerate(level_names):
            y = list_y + i * 42
            is_sel = (i == self.level_select_idx)
            lv_theme = LEVEL_THEMES[i]

            if is_sel:
                # Glow background
                pygame.draw.rect(screen, (40, 40, 10), (WIDTH // 2 - 180, y - 4, 360, 38), border_radius=6)
                # Arrow indicator
                bounce = int(math.sin(self.frame * 0.15) * 3)
                arrow = self.font_med.render("►", True, lv_theme['wall'])
                screen.blit(arrow, (WIDTH // 2 - 195 + bounce, y))

            name_col = lv_theme['wall'] if is_sel else GREY
            name_txt = self.font_med.render(name, True, name_col)
            screen.blit(name_txt, (WIDTH // 2 - 160, y))

            if is_sel:
                desc_txt = self.font_xs.render(desc, True, WHITE)
                screen.blit(desc_txt, (WIDTH // 2 - 160, y + 24))

        # Controls
        hint = self.font_xs.render("UP/DOWN or LEFT/RIGHT to browse  •  ENTER to play  •  ESC to go back",
                                   True, GREY)
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 50))

        credit = self.font_xs.render("Pick your battlefield! ⚔️", True, GREY)
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
            detail_text = None
            if self.last_mode == 'ghost_tag':
                mode_name = "GHOST TAG"
                sc = self.gt_score
                won = getattr(self, 'gt_won', False)
                result_text = "ALL CAUGHT!" if won else "TIME'S UP!"
                result_color = GREEN if won else RED
            elif self.last_mode == 'pellet_frenzy':
                mode_name = "PELLET FRENZY"
                sc = self.pf_score
                result_text = "BUSTED!"
                result_color = RED
            elif self.last_mode == 'boss_battle':
                mode_name = "BOSS BATTLE"
                sc = self.bb_score
                result_text = "THE BOSS WON!"
                result_color = RED
            elif self.last_mode == 'maze_runner':
                mode_name = "MAZE RUNNER"
                sc = self.mr_final_score
                won = getattr(self, 'mr_won', False)
                result_text = f"CLEARED IN {self.mr_completion_time:.1f}s!" if won else "TIME'S UP!"
                result_color = GREEN if won else RED
                detail_text = f"Bonus: +{self.mr_bonus_points}" if won else f"Dots grabbed: {self.mr_dots_eaten}/{self.mr_dots_total}"
            elif self.last_mode == 'survival':
                mode_name = "SURVIVAL"
                sc = self.sv_score
                result_text = f"SURVIVED {self.sv_time:.1f}s"
                result_color = YELLOW
                detail_text = f"Ghosts tagged: {self.sv_ghosts_eaten}"
            else:
                mode_name = "INVISIBLE MAZE"
                sc = self.iv_score
                won = getattr(self, 'iv_won', False)
                result_text = "MAZE MASTER!" if won else "LOST IN THE DARK!"
                result_color = GREEN if won else RED
                reveal_pct = int(len(self.iv_seen_walls) * 100 / max(1, self.iv_wall_total))
                detail_text = f"Walls found: {reveal_pct}%"
            mode_txt = self.font_med.render(mode_name, True, CYAN)
            screen.blit(mode_txt, (WIDTH // 2 - mode_txt.get_width() // 2, 140))
            res_txt = self.font_big.render(result_text, True, result_color)
            screen.blit(res_txt, (WIDTH // 2 - res_txt.get_width() // 2, 180))
            score_txt = self.font_big.render(f"{sc}", True, WHITE)
            screen.blit(score_txt, (WIDTH // 2 - score_txt.get_width() // 2, 240))
            pts = self.font_sm.render("points", True, GREY)
            screen.blit(pts, (WIDTH // 2 - pts.get_width() // 2, 300))
            if detail_text:
                detail = self.font_sm.render(detail_text, True, GREY)
                screen.blit(detail, (WIDTH // 2 - detail.get_width() // 2, 330))

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
                        if self.state in ['classic', 'ghost_tag', 'pellet_frenzy', 'boss_battle', 'maze_runner', 'survival', 'invisible']:
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
                            self.menu_sel = (self.menu_sel - 1) % 9
                            self.sfx_channel.play(snd_menu)
                        elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                            self.menu_sel = (self.menu_sel + 1) % 9
                            self.sfx_channel.play(snd_menu)
                        elif event.key == pygame.K_RETURN:
                            modes = ['classic', 'ghost_tag', 'pellet_frenzy', 'boss_battle', 'maze_runner', 'survival', 'invisible', 'level_select', 'customise']
                            self.state = modes[self.menu_sel]
                            if self.state in ('customise', 'level_select'):
                                self.sfx_channel.play(snd_menu)
                            else:
                                self.last_mode = self.state
                                self.particles.clear()
                                self.popups.clear()
                                if self.state == 'classic':
                                    self.reset_classic()
                                elif self.state == 'ghost_tag':
                                    self.reset_ghost_tag()
                                elif self.state == 'pellet_frenzy':
                                    self.reset_pellet_frenzy()
                                elif self.state == 'boss_battle':
                                    self.reset_boss_battle()
                                elif self.state == 'maze_runner':
                                    self.reset_maze_runner()
                                elif self.state == 'survival':
                                    self.reset_survival()
                                elif self.state == 'invisible':
                                    self.reset_invisible()
                                self.sfx_channel.play(snd_win)

                    elif self.state == 'customise':
                        if event.key == pygame.K_ESCAPE:
                            # Apply customisation and go back
                            pac_custom['colour'] = PAC_COLOURS[self.custom_colour_idx][1]
                            pac_custom['shape'] = PAC_SHAPES[self.custom_shape_idx]
                            pac_custom['hat'] = PAC_HATS[self.custom_hat_idx]
                            self.state = 'menu'
                            self.sfx_channel.play(snd_menu)
                        elif event.key == pygame.K_UP or event.key == pygame.K_w:
                            self.custom_section = (self.custom_section - 1) % 3
                            self.sfx_channel.play(snd_menu)
                        elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                            self.custom_section = (self.custom_section + 1) % 3
                            self.sfx_channel.play(snd_menu)
                        elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                            if self.custom_section == 0:
                                self.custom_colour_idx = (self.custom_colour_idx - 1) % len(PAC_COLOURS)
                            elif self.custom_section == 1:
                                self.custom_shape_idx = (self.custom_shape_idx - 1) % len(PAC_SHAPES)
                            else:
                                self.custom_hat_idx = (self.custom_hat_idx - 1) % len(PAC_HATS)
                            pac_custom['colour'] = PAC_COLOURS[self.custom_colour_idx][1]
                            pac_custom['shape'] = PAC_SHAPES[self.custom_shape_idx]
                            pac_custom['hat'] = PAC_HATS[self.custom_hat_idx]
                            self.sfx_channel.play(snd_menu)
                        elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                            if self.custom_section == 0:
                                self.custom_colour_idx = (self.custom_colour_idx + 1) % len(PAC_COLOURS)
                            elif self.custom_section == 1:
                                self.custom_shape_idx = (self.custom_shape_idx + 1) % len(PAC_SHAPES)
                            else:
                                self.custom_hat_idx = (self.custom_hat_idx + 1) % len(PAC_HATS)
                            pac_custom['colour'] = PAC_COLOURS[self.custom_colour_idx][1]
                            pac_custom['shape'] = PAC_SHAPES[self.custom_shape_idx]
                            pac_custom['hat'] = PAC_HATS[self.custom_hat_idx]
                            self.sfx_channel.play(snd_menu)
                        elif event.key == pygame.K_RETURN:
                            pac_custom['colour'] = PAC_COLOURS[self.custom_colour_idx][1]
                            pac_custom['shape'] = PAC_SHAPES[self.custom_shape_idx]
                            pac_custom['hat'] = PAC_HATS[self.custom_hat_idx]
                            self.state = 'menu'
                            self.sfx_channel.play(snd_win)

                    elif self.state == 'level_select':
                        if event.key == pygame.K_ESCAPE:
                            self.state = 'menu'
                            self.sfx_channel.play(snd_menu)
                        elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                            self.level_select_idx = (self.level_select_idx - 1) % len(ALL_MAZES)
                            self.sfx_channel.play(snd_menu)
                        elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                            self.level_select_idx = (self.level_select_idx + 1) % len(ALL_MAZES)
                            self.sfx_channel.play(snd_menu)
                        elif event.key == pygame.K_UP or event.key == pygame.K_w:
                            self.level_select_idx = (self.level_select_idx - 1) % len(ALL_MAZES)
                            self.sfx_channel.play(snd_menu)
                        elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                            self.level_select_idx = (self.level_select_idx + 1) % len(ALL_MAZES)
                            self.sfx_channel.play(snd_menu)
                        elif event.key == pygame.K_RETURN:
                            chosen_level = self.level_select_idx + 1
                            self.state = 'classic'
                            self.last_mode = 'classic'
                            self.particles.clear()
                            self.popups.clear()
                            self.reset_classic(new_game=True, start_level=chosen_level)
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
            elif self.state == 'boss_battle':
                self.update_boss_battle(dt, keys)
            elif self.state == 'maze_runner':
                self.update_maze_runner(dt, keys)
            elif self.state == 'survival':
                self.update_survival(dt, keys)
            elif self.state == 'invisible':
                self.update_invisible(dt, keys)

            # Update visual effects (always, even during transitions)
            self.particles.update(dt)
            self.popups.update(dt)
            self.transition.update(dt)
            self.shake.update(dt)

            # Draw to offscreen then blit with shake offset
            screen.fill(BLACK)
            if self.state == 'menu':
                self.draw_menu()
            elif self.state == 'customise':
                self.draw_customise()
            elif self.state == 'level_select':
                self.draw_level_select()
            elif self.state == 'classic':
                self.draw_classic()
            elif self.state == 'ghost_tag':
                self.draw_ghost_tag()
            elif self.state == 'pellet_frenzy':
                self.draw_pellet_frenzy()
            elif self.state == 'boss_battle':
                self.draw_boss_battle()
            elif self.state == 'maze_runner':
                self.draw_maze_runner()
            elif self.state == 'survival':
                self.draw_survival()
            elif self.state == 'invisible':
                self.draw_invisible()
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
