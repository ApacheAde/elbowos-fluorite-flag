#!/usr/bin/env python3
"""Fluorite Flag — neon minesweeper arcade for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/workspace/artifacts/FLUORITE_FLAG_ElbowOS.mp4")
TITLE, HANDLE = "FLUORITE FLAG", "x.com/ElbowOS"

INDIGO = (8, 6, 28)
PURPLE = (40, 20, 80)
CYAN = (0, 255, 240)
MAGENTA = (255, 40, 180)
GOLD = (255, 220, 60)
MINT = (80, 255, 160)
WHITE = (240, 250, 255)
DARK = (20, 12, 40)

COLS, ROWS = 6, 10
TILE = 140
OX = (W - COLS * TILE) // 2
OY = 420

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.quit()
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 48, bold=True)
        self.big = pygame.font.SysFont("consolas", 72, bold=True)
        self.tiny = pygame.font.SysFont("consolas", 28, bold=True)
        self.reset()

    def reset(self):
        self.bombs = set()
        while len(self.bombs) < 12:
            self.bombs.add((random.randrange(COLS), random.randrange(ROWS)))
        self.revealed = [[False]*COLS for _ in range(ROWS)]
        self.flagged = [[False]*COLS for _ in range(ROWS)]
        self.score = 0
        self.tick = 0
        self.particles = []
        self.flash = 0
        self.seq = [(r, c) for r in range(ROWS) for c in range(COLS) if (c, r) not in self.bombs]
        random.shuffle(self.seq)
        self.reveal_i = 0

    def neighbors(self, c, r):
        return [(c+dc, r+dr) for dc in (-1,0,1) for dr in (-1,0,1)
                if (dc or dr) and 0 <= c+dc < COLS and 0 <= r+dr < ROWS]

    def count(self, c, r):
        return sum(1 for nc, nr in self.neighbors(c, r) if (nc, nr) in self.bombs)

    def reveal(self, c, r):
        if self.revealed[r][c] or self.flagged[r][c]:
            return
        self.revealed[r][c] = True
        if (c, r) in self.bombs:
            self.flash = 12
            self.score = max(0, self.score - 40)
            for _ in range(20):
                self.particles.append([OX+c*TILE+TILE//2, OY+r*TILE+TILE//2,
                                       random.uniform(-4,4), random.uniform(-6,2), MAGENTA, 20])
            return
        n = self.count(c, r)
        self.score += 10 + n * 5
        for _ in range(6):
            self.particles.append([OX+c*TILE+TILE//2, OY+r*TILE+TILE//2,
                                   random.uniform(-2,2), random.uniform(-3,1), CYAN, 15])

    def update(self, auto=False):
        self.tick += 1
        self.flash = max(0, self.flash - 1)
        for p in self.particles[:]:
            p[0] += p[2]; p[1] += p[3]; p[5] -= 1
            if p[5] <= 0:
                self.particles.remove(p)
        if auto and self.tick % 4 == 0 and self.reveal_i < len(self.seq):
            r, c = self.seq[self.reveal_i]
            self.reveal_i += 1
            self.reveal(c, r)
            if random.random() < 0.08:
                for nc, nr in self.neighbors(c, r):
                    if (nc, nr) in self.bombs and not self.flagged[nr][nc]:
                        self.flagged[nr][nc] = True
                        self.score += 25
                        break

    def draw(self):
        self.screen.fill(INDIGO)
        for y in range(0, H, 6):
            pygame.draw.line(self.screen, (12, 8, 36), (0, y), (W, y))
        t = self.big.render(TITLE, True, CYAN)
        self.screen.blit(t, (W//2 - t.get_width()//2, 80))
        sub = self.font.render(HANDLE, True, MAGENTA)
        self.screen.blit(sub, (W//2 - sub.get_width()//2, 160))
        sc = self.font.render(f"SCORE {self.score:04d}", True, GOLD)
        self.screen.blit(sc, (W//2 - sc.get_width()//2, 280))
        for r in range(ROWS):
            for c in range(COLS):
                x, y = OX + c*TILE, OY + r*TILE
                rect = pygame.Rect(x+4, y+4, TILE-8, TILE-8)
                if self.revealed[r][c]:
                    if (c, r) in self.bombs:
                        col = MAGENTA if self.flash else (180, 20, 120)
                        pygame.draw.rect(self.screen, col, rect, border_radius=12)
                        pygame.draw.circle(self.screen, GOLD, rect.center, 28)
                    else:
                        pygame.draw.rect(self.screen, (16, 28, 60), rect, border_radius=12)
                        n = self.count(c, r)
                        if n:
                            col = [CYAN, MINT, GOLD, MAGENTA][min(n-1, 3)]
                            num = self.font.render(str(n), True, col)
                            self.screen.blit(num, (rect.centerx - num.get_width()//2,
                                                   rect.centery - num.get_height()//2))
                else:
                    glow = 30 + int(20 * math.sin(self.tick*0.1 + c + r))
                    pygame.draw.rect(self.screen, (glow//2, glow//4, glow), rect, border_radius=12)
                    pygame.draw.rect(self.screen, CYAN, rect, 3, border_radius=12)
                    if self.flagged[r][c]:
                        pygame.draw.polygon(self.screen, MAGENTA,
                                            [(rect.centerx, rect.y+20),
                                             (rect.centerx+22, rect.centery),
                                             (rect.centerx, rect.bottom-20)])
        for p in self.particles:
            pygame.draw.circle(self.screen, p[4], (int(p[0]), int(p[1])), max(1, p[5]//3))
        ft = self.tiny.render("CLEAR THE GRID  •  FLAG THE BOMBS", True, WHITE)
        self.screen.blit(ft, (W//2 - ft.get_width()//2, H - 120))

    def play_interactive(self):
        running = True
        while running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = e.pos
                    c = (mx - OX) // TILE
                    r = (my - OY) // TILE
                    if 0 <= c < COLS and 0 <= r < ROWS:
                        if e.button == 1:
                            self.reveal(c, r)
                        elif e.button == 3:
                            if not self.revealed[r][c]:
                                self.flagged[r][c] = not self.flagged[r][c]
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                    self.reset()
            self.update(False)
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

    def record(self):
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
            "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
            "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-movflags", "+faststart", "-an", OUT
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        total = FPS * SECS
        for i in range(total):
            self.update(True)
            self.draw()
            frame = pygame.surfarray.array3d(self.screen).transpose(1, 0, 2)
            try:
                proc.stdin.write(frame.tobytes())
            except BrokenPipeError:
                break
            if i % 30 == 0:
                print(f"frame {i}/{total}")
        proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "ignore")
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1200:]}")
        print("wrote", OUT)
        pygame.quit()

def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()

if __name__ == "__main__":
    main()
