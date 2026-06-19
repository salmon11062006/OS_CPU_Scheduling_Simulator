import pygame
import sys
import copy
import math
from collections import namedtuple

# ── Import all schedulers ──────────────────────────────────────────────────────
from Helper import Task
from FCFS import fcfs
from SJF import sjf
from SRTF import srtf
from RR import round_robin
from MLQ import mlq
from nonPreEmptivePriority import nonPreEmptivePriority
from preEmptivePriority import preEmptivePriority

# ── Palette ────────────────────────────────────────────────────────────────────
BG          = (15,  17,  26)   # near-black navy
PANEL_BG    = (22,  26,  40)
CARD_BG     = (30,  35,  54)
BORDER      = (50,  58,  90)
TEXT_MAIN   = (220, 225, 245)
TEXT_DIM    = (110, 120, 160)
TEXT_ACCENT = (255, 255, 255)
ACCENT      = (99,  130, 255)  # indigo
ACCENT2     = (64,  200, 172)  # teal
WARN        = (255, 180,  60)
IDLE_COLOR  = (45,  50,  75)

TASK_PALETTE = [
    (99,  130, 255),  # indigo
    (64,  200, 172),  # teal
    (255, 120, 100),  # coral
    (200, 130, 255),  # lavender
    (255, 200,  60),  # amber
    (80,  200, 120),  # mint
    (255, 100, 180),  # pink
    (100, 180, 255),  # sky
]

# ── Timeline recorder ──────────────────────────────────────────────────────────
TimelineEvent = namedtuple("TimelineEvent", ["time", "task_name", "remaining"])

def build_timeline(tasks_cfg, algo_fn, **kwargs):
    """
    Run the scheduler on a fresh copy of tasks and record what ran at each tick.
    Returns (timeline_events, completed_tasks_info)
    """
    events = []

    class RecordingTask(Task):
        def execute(self):
            nonlocal events
            events.append(TimelineEvent(
                time=_clock[0],
                task_name=self.name,
                remaining=self.remaining_time - 1
            ))
            super().execute()
            _clock[0] += 1

    _clock = [0]

    # Rebuild tasks as RecordingTask instances
    rec_tasks = []
    for cfg in tasks_cfg:
        t = RecordingTask(
            name=cfg["name"],
            func=lambda: None,
            arrival_time=cfg["arrival_time"],
            burst_time=cfg["burst_time"],
            priority=cfg.get("priority", 0),
            queue=cfg.get("queue", 0),
        )
        rec_tasks.append(t)

    # Monkey-patch current_time tracking: schedulers manage their own clock,
    # so we intercept via execute() which is the atomic unit.
    # We store events indexed by call order; clock is incremented inside execute().
    _clock[0] = 0
    # Reset clock to 0 and let execute() drive it
    # But schedulers also have their own `current_time` — we only need the
    # *order* of execution, which execute() calls give us perfectly.

    algo_fn(rec_tasks, **kwargs)

    # Gather results
    results = {t.name: {"wt": t.waiting_time(), "tat": t.turnaround_time(),
                         "burst": t.burst_time, "arrival": t.arrival_time,
                         "completion": t.completion_time}
               for t in rec_tasks}
    return events, results


# ── Default task configurations ────────────────────────────────────────────────
DEFAULT_TASKS = [
    {"name": "P1", "arrival_time": 0, "burst_time": 6, "priority": 2, "queue": 0},
    {"name": "P2", "arrival_time": 2, "burst_time": 4, "priority": 1, "queue": 1},
    {"name": "P3", "arrival_time": 4, "burst_time": 2, "priority": 3, "queue": 0},
    {"name": "P4", "arrival_time": 6, "burst_time": 5, "priority": 2, "queue": 1},
    {"name": "P5", "arrival_time": 1, "burst_time": 3, "priority": 1, "queue": 0},
]

ALGORITHMS = [
    ("FCFS",              lambda t, **kw: fcfs(t)),
    ("SJF",               lambda t, **kw: sjf(t)),
    ("SRTF",              lambda t, **kw: srtf(t)),
    ("Round Robin",       lambda t, **kw: round_robin(t, quantum=kw.get("quantum", 2))),
    ("Non-Pre Priority",  lambda t, **kw: nonPreEmptivePriority(t)),
    ("Pre-Emp Priority",  lambda t, **kw: preEmptivePriority(t)),
    ("MLQ",               lambda t, **kw: mlq(t, quantum=kw.get("quantum", 2))),
]

# ── Pygame helpers ─────────────────────────────────────────────────────────────
def rounded_rect(surf, color, rect, radius=8):
    pygame.draw.rect(surf, color, rect, border_radius=radius)

def text(surf, msg, pos, font, color=TEXT_MAIN, anchor="topleft"):
    s = font.render(str(msg), True, color)
    r = s.get_rect(**{anchor: pos})
    surf.blit(s, r)
    return r

def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i]-a[i])*t) for i in range(3))

def make_font(size, bold=False):
    """
    pygame.font.SysFont('monospace', ...) only resolves on systems that
    actually have a font *named* 'monospace', and even when it resolves,
    that font often lacks glyphs for ▶ ⏸ ◀ ↺ ✎ ✕ ✓ × — which silently
    render as blank boxes. This tries a list of fonts with broad Unicode
    coverage and falls back to pygame's bundled default font (which is
    always present) instead of an unresolved system name.
    """
    candidates = [
        "DejaVu Sans Mono", "DejaVu Sans", "Noto Sans", "Segoe UI Symbol",
        "Arial Unicode MS", "Consolas", "Menlo", "Courier New", "monospace",
    ]
    available = pygame.font.get_fonts()
    for name in candidates:
        key = name.lower().replace(" ", "")
        if key in available:
            return pygame.font.SysFont(name, size, bold=bold)
    # Nothing matched -> bundled default font, guaranteed to exist
    return pygame.font.Font(None, size)

# ── Vector icons (no font glyph dependency) ────────────────────────────────────
def icon_play(surf, rect, color):
    cx, cy = rect.center
    s = min(rect.w, rect.h) * 0.32
    pygame.draw.polygon(surf, color, [
        (cx - s * 0.6, cy - s), (cx - s * 0.6, cy + s), (cx + s * 0.9, cy)
    ])

def icon_pause(surf, rect, color):
    cx, cy = rect.center
    s = min(rect.w, rect.h) * 0.30
    bar_w = s * 0.5
    pygame.draw.rect(surf, color, (cx - s, cy - s, bar_w, s * 2), border_radius=2)
    pygame.draw.rect(surf, color, (cx + s - bar_w, cy - s, bar_w, s * 2), border_radius=2)

def icon_step(surf, rect, color, direction=1):
    """Single-step arrow ( ▶| or |◀ ) used for prev/next."""
    cx, cy = rect.center
    s = min(rect.w, rect.h) * 0.28
    if direction > 0:
        pygame.draw.polygon(surf, color, [
            (cx - s * 0.7, cy - s), (cx - s * 0.7, cy + s), (cx + s * 0.3, cy)
        ])
        pygame.draw.rect(surf, color, (cx + s * 0.45, cy - s, s * 0.35, s * 2))
    else:
        pygame.draw.polygon(surf, color, [
            (cx + s * 0.7, cy - s), (cx + s * 0.7, cy + s), (cx - s * 0.3, cy)
        ])
        pygame.draw.rect(surf, color, (cx - s * 0.8, cy - s, s * 0.35, s * 2))

def icon_reset(surf, rect, color):
    """Counter-clockwise reset arrow drawn as an arc + arrowhead."""
    cx, cy = rect.center
    r = min(rect.w, rect.h) * 0.30
    arc_rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
    pygame.draw.arc(surf, color, arc_rect, math.radians(40), math.radians(310), width=2)
    head_x = cx + r * math.cos(math.radians(40))
    head_y = cy - r * math.sin(math.radians(40))
    pygame.draw.polygon(surf, color, [
        (head_x, head_y - 5), (head_x + 6, head_y + 2), (head_x - 5, head_y + 4)
    ])

def icon_pencil(surf, rect, color):
    cx, cy = rect.center
    s = min(rect.w, rect.h) * 0.28
    pygame.draw.line(surf, color, (cx - s, cy + s), (cx + s, cy - s), 3)
    pygame.draw.polygon(surf, color, [
        (cx - s - 3, cy + s + 3), (cx - s + 4, cy + s), (cx - s, cy + s + 6)
    ])

def icon_x(surf, rect, color, thickness=2):
    cx, cy = rect.center
    s = min(rect.w, rect.h) * 0.22
    pygame.draw.line(surf, color, (cx - s, cy - s), (cx + s, cy + s), thickness)
    pygame.draw.line(surf, color, (cx - s, cy + s), (cx + s, cy - s), thickness)

def icon_check(surf, rect, color, thickness=2):
    cx, cy = rect.center
    s = min(rect.w, rect.h) * 0.24
    pygame.draw.lines(surf, color, False, [
        (cx - s, cy), (cx - s * 0.2, cy + s * 0.8), (cx + s, cy - s * 0.8)
    ], thickness)

# ── Process Editor Overlay ─────────────────────────────────────────────────────
class ProcessEditor:
    """Modal overlay for adding/editing/deleting processes."""

    COL_X    = [20, 80, 145, 210, 270, 330]   # Name Arr Bst Pri Q  [Del]
    COL_HDRS = ["Name", "Arrival", "Burst", "Priority", "Queue"]
    ROW_H    = 30
    PANEL_W  = 430
    PANEL_H_BASE = 160   # header + footer; rows added on top

    def __init__(self, font_md, font_sm):
        self.font_md = font_md
        self.font_sm = font_sm
        self.visible = False
        self.rows    = []          # list of dict with string fields
        self.active  = None       # (row_idx, field_key) currently focused
        self._error  = ""
        self._del_rects  = []
        self._field_rects = {}    # (row, field) -> Rect
        self._apply_rect  = None
        self._cancel_rect = None
        self._add_rect    = None

    def open(self, tasks_cfg):
        """Clone current task list into editable rows."""
        self.rows = []
        for cfg in tasks_cfg:
            self.rows.append({
                "name":         str(cfg["name"]),
                "arrival_time": str(cfg["arrival_time"]),
                "burst_time":   str(cfg["burst_time"]),
                "priority":     str(cfg.get("priority", "0")),
                "queue":        str(cfg.get("queue", "0")),
            })
        self.active  = None
        self._error  = ""
        self.visible = True

    def close(self):
        self.visible = False
        self.active  = None

    def _panel_rect(self, W, H):
        n       = max(len(self.rows), 1)
        ph      = self.PANEL_H_BASE + n * self.ROW_H + 10
        ph      = min(ph, H - 60)
        px      = (W - self.PANEL_W) // 2
        py      = (H - ph) // 2
        return pygame.Rect(px, py, self.PANEL_W, ph)

    def draw(self, surf):
        if not self.visible:
            return
        W, H = surf.get_size()
        pr   = self._panel_rect(W, H)

        # Dim background
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 5, 180))
        surf.blit(dim, (0, 0))

        # Panel
        rounded_rect(surf, CARD_BG, pr, 12)
        pygame.draw.rect(surf, ACCENT, pr, 1, border_radius=12)

        # Title
        title_icon_r = pygame.Rect(pr.x + pr.w // 2 - 70, pr.y + 12, 16, 16)
        icon_pencil(surf, title_icon_r, ACCENT)
        text(surf, "Edit Processes", (pr.x + pr.w // 2 + 6, pr.y + 12),
             self.font_md, ACCENT, "midtop")

        # Column headers
        hy = pr.y + 36
        offsets = [self.COL_X[i] for i in range(len(self.COL_HDRS))]
        for i, h in enumerate(self.COL_HDRS):
            text(surf, h, (pr.x + offsets[i], hy), self.font_sm, TEXT_DIM)
        pygame.draw.line(surf, BORDER,
                         (pr.x + 10, hy + 16), (pr.x + pr.w - 10, hy + 16))

        # Rows
        self._del_rects   = []
        self._field_rects = {}
        FIELDS = ["name", "arrival_time", "burst_time", "priority", "queue"]
        ry = hy + 22
        max_ry = pr.y + pr.h - 55

        for ri, row in enumerate(self.rows):
            if ry + self.ROW_H > max_ry:
                break
            # Alternate row background
            if ri % 2 == 0:
                rounded_rect(surf, PANEL_BG,
                             pygame.Rect(pr.x + 8, ry - 3, pr.w - 16, self.ROW_H - 2), 4)

            for fi, field in enumerate(FIELDS):
                cx = pr.x + self.COL_X[fi]
                fw = self.COL_X[fi + 1] - self.COL_X[fi] - 4 if fi < len(self.COL_X) - 2 else 54
                fr = pygame.Rect(cx, ry, fw, 22)
                self._field_rects[(ri, field)] = fr

                is_active = (self.active == (ri, field))
                bg  = ACCENT if is_active else BORDER
                bdr = ACCENT if is_active else (60, 68, 100)
                rounded_rect(surf, (30, 35, 60) if not is_active else (40, 48, 90), fr, 3)
                pygame.draw.rect(surf, bg, fr, 1, border_radius=3)

                val = row[field]
                if is_active:
                    # Cursor blink
                    tick = (pygame.time.get_ticks() // 500) % 2
                    disp = val + ("|" if tick else " ")
                else:
                    disp = val
                text(surf, disp, (cx + 3, ry + 3), self.font_sm,
                     TEXT_ACCENT if is_active else TEXT_MAIN)

            # Delete button
            del_r = pygame.Rect(pr.x + pr.w - 36, ry, 28, 22)
            self._del_rects.append(del_r)
            rounded_rect(surf, (100, 40, 40), del_r, 4)
            pygame.draw.rect(surf, (180, 60, 60), del_r, 1, border_radius=4)
            icon_x(surf, del_r, (255, 100, 100))

            ry += self.ROW_H

        # Error message
        if self._error:
            text(surf, self._error,
                 (pr.x + pr.w // 2, max_ry + 4), self.font_sm, WARN, "midtop")

        # Buttons: [+ Add]  [Cancel]  [Apply]
        by = pr.y + pr.h - 36
        add_r    = pygame.Rect(pr.x + 10,             by, 90, 26)
        cancel_r = pygame.Rect(pr.x + pr.w - 210,     by, 90, 26)
        apply_r  = pygame.Rect(pr.x + pr.w - 110,     by, 100, 26)

        for r, lbl, bg, bdr in [
            (add_r,    "+ Add",  CARD_BG, ACCENT2),
            (cancel_r, "Cancel", CARD_BG, BORDER),
            (apply_r,  "Apply",  ACCENT,  ACCENT),
        ]:
            rounded_rect(surf, bg, r, 6)
            pygame.draw.rect(surf, bdr, r, 1, border_radius=6)
            if r is apply_r:
                icon_r = pygame.Rect(r.x + 8, r.y, 16, r.h)
                icon_check(surf, icon_r, TEXT_ACCENT)
                text(surf, lbl, (icon_r.right + 2, r.centery), self.font_sm,
                     TEXT_ACCENT, "midleft")
            else:
                text(surf, lbl, r.center, self.font_sm, TEXT_ACCENT, "center")

        self._add_rect    = add_r
        self._cancel_rect = cancel_r
        self._apply_rect  = apply_r

    def _next_name(self):
        existing = {r["name"] for r in self.rows}
        i = len(self.rows) + 1
        while f"P{i}" in existing:
            i += 1
        return f"P{i}"

    def handle_event(self, event):
        """Returns ('apply', tasks_cfg) | ('cancel',) | None"""
        if not self.visible:
            return None

        if event.type == pygame.KEYDOWN:
            if self.active:
                ri, field = self.active
                val = self.rows[ri][field]
                if event.key == pygame.K_BACKSPACE:
                    self.rows[ri][field] = val[:-1]
                elif event.key == pygame.K_RETURN or event.key == pygame.K_TAB:
                    # Move to next field
                    FIELDS = ["name", "arrival_time", "burst_time", "priority", "queue"]
                    fi = FIELDS.index(field)
                    if fi < len(FIELDS) - 1:
                        self.active = (ri, FIELDS[fi + 1])
                    elif ri < len(self.rows) - 1:
                        self.active = (ri + 1, FIELDS[0])
                    else:
                        self.active = None
                elif event.key == pygame.K_ESCAPE:
                    self.active = None
                elif event.unicode and len(val) < 6:
                    self.rows[ri][field] = val + event.unicode
                return None

            if event.key == pygame.K_ESCAPE:
                self.close()
                return ("cancel",)

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos

            # Delete buttons
            for i, dr in enumerate(self._del_rects):
                if dr.collidepoint(pos) and i < len(self.rows):
                    if len(self.rows) > 1:
                        self.rows.pop(i)
                        self.active = None
                        self._error = ""
                    else:
                        self._error = "Need at least one process."
                    return None

            # Field click
            for (ri, field), fr in self._field_rects.items():
                if fr.collidepoint(pos):
                    self.active = (ri, field)
                    return None

            if self._add_rect and self._add_rect.collidepoint(pos):
                self.rows.append({
                    "name": self._next_name(),
                    "arrival_time": "0",
                    "burst_time": "1",
                    "priority": "0",
                    "queue": "0",
                })
                self._error = ""
                return None

            if self._cancel_rect and self._cancel_rect.collidepoint(pos):
                self.close()
                return ("cancel",)

            if self._apply_rect and self._apply_rect.collidepoint(pos):
                return self._try_apply()

            # Click outside panel — close as cancel
            self.active = None

        return None

    def _try_apply(self):
        """Validate and return parsed task configs or set error."""
        seen_names = set()
        parsed = []
        for i, row in enumerate(self.rows):
            name = row["name"].strip()
            if not name:
                self._error = f"Row {i+1}: name cannot be empty."
                return None
            if name in seen_names:
                self._error = f"Duplicate name '{name}'."
                return None
            seen_names.add(name)
            try:
                arr  = int(row["arrival_time"])
                bst  = int(row["burst_time"])
                pri  = int(row["priority"])
                que  = int(row["queue"])
                if bst < 1:
                    raise ValueError("burst < 1")
                if arr < 0:
                    raise ValueError("arrival < 0")
            except ValueError as e:
                self._error = f"Row {i+1} ({name}): {e}"
                return None
            parsed.append({
                "name": name,
                "arrival_time": arr,
                "burst_time": bst,
                "priority": pri,
                "queue": que,
            })
        self.close()
        return ("apply", parsed)


# ── Main application ───────────────────────────────────────────────────────────
class App:
    W, H = 1280, 720

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.W, self.H), pygame.RESIZABLE)
        pygame.display.set_caption("CPU Scheduling Visualizer")
        self.clock_fps = pygame.time.Clock()

        self.font_lg  = make_font(22, bold=True)
        self.font_md  = make_font(15)
        self.font_sm  = make_font(12)
        self.font_xl  = make_font(28, bold=True)

        self.algo_idx   = 0
        self.quantum    = 2
        self.speed      = 8          # ticks animated per second
        self.playing    = False
        self.tick_ptr   = 0          # which timeline event we're up to
        self.anim_t     = 0.0        # fractional progress within current tick
        self.show_stats = False

        import copy
        self.tasks_cfg  = copy.deepcopy(DEFAULT_TASKS)
        self.editor     = ProcessEditor(self.font_md, self.font_sm)
        self._btn_rects = {}

        self._rebuild()

    # ── Build / rebuild timeline when algo changes ─────────────────────────────
    def _rebuild(self):
        self.playing  = False
        self.tick_ptr = 0
        self.anim_t   = 0.0

        name, fn = ALGORITHMS[self.algo_idx]
        kw = {"quantum": self.quantum}
        self.timeline, self.results = build_timeline(self.tasks_cfg, fn, **kw)

        # Assign colors to task names
        names = list(dict.fromkeys(e.task_name for e in self.timeline))
        self.task_color = {n: TASK_PALETTE[i % len(TASK_PALETTE)] for i, n in enumerate(names)}
        self.task_names = [c["name"] for c in self.tasks_cfg]

        self.total_ticks = len(self.timeline)
        self.algo_name   = name

    # ── Update ─────────────────────────────────────────────────────────────────
    def update(self, dt):
        if self.playing and self.tick_ptr < self.total_ticks:
            self.anim_t += dt * self.speed
            while self.anim_t >= 1.0 and self.tick_ptr < self.total_ticks:
                self.anim_t -= 1.0
                self.tick_ptr += 1
            if self.tick_ptr >= self.total_ticks:
                self.playing  = False
                self.anim_t   = 0.0
                self.show_stats = True

    # ── Draw ───────────────────────────────────────────────────────────────────
    def draw(self):
        W, H = self.screen.get_size()
        self.screen.fill(BG)

        self._draw_header(W)
        self._draw_sidebar(W, H)
        self._draw_gantt(W, H)
        self._draw_controls(W, H)
        if self.show_stats:
            self._draw_stats(W, H)
        self.editor.draw(self.screen)

        pygame.display.flip()

    def _draw_header(self, W):
        # Title bar
        rounded_rect(self.screen, PANEL_BG, (0, 0, W, 56))
        pygame.draw.line(self.screen, BORDER, (0, 56), (W, 56))
        text(self.screen, "CPU Scheduling Visualizer", (20, 14), self.font_lg, ACCENT)
        text(self.screen, f"Algorithm: {self.algo_name}", (W//2, 18), self.font_md, TEXT_MAIN, "midtop")
        # tick counter
        label = f"Tick {min(self.tick_ptr, self.total_ticks)} / {self.total_ticks}"
        text(self.screen, label, (W - 20, 18), self.font_md, TEXT_DIM, "topright")

    def _draw_sidebar(self, W, H):
        SB_W = 210
        rounded_rect(self.screen, PANEL_BG, (0, 56, SB_W, H - 56))
        pygame.draw.line(self.screen, BORDER, (SB_W, 56), (SB_W, H))

        text(self.screen, "Processes", (12, 70), self.font_md, TEXT_DIM)

        # Table header
        y = 95
        col_x = [14, 60, 100, 140, 175]
        headers = ["Name", "Arr", "Bst", "Pri", "Q"]
        for i, h in enumerate(headers):
            text(self.screen, h, (col_x[i], y), self.font_sm, TEXT_DIM)
        y += 18
        pygame.draw.line(self.screen, BORDER, (10, y), (SB_W - 10, y))
        y += 4

        for cfg in self.tasks_cfg:
            n = cfg["name"]
            color = self.task_color.get(n, TEXT_DIM)
            # Highlight if currently running
            running = (self.tick_ptr < self.total_ticks and
                       self.timeline[self.tick_ptr].task_name == n)
            if running:
                rounded_rect(self.screen, (*color[:3], 40),
                             pygame.Rect(10, y - 2, SB_W - 20, 18), 4)

            vals = [n, cfg["arrival_time"], cfg["burst_time"],
                    cfg.get("priority", "-"), cfg.get("queue", "-")]
            for i, v in enumerate(vals):
                c = color if i == 0 else (TEXT_MAIN if running else TEXT_DIM)
                text(self.screen, v, (col_x[i], y), self.font_sm, c)
            y += 20

        # Legend
        y += 10
        pygame.draw.line(self.screen, BORDER, (10, y), (SB_W - 10, y))
        y += 8
        text(self.screen, "Legend", (12, y), self.font_sm, TEXT_DIM)
        y += 16
        for name, color in self.task_color.items():
            rounded_rect(self.screen, color, (12, y + 2, 12, 12), 3)
            text(self.screen, name, (30, y), self.font_sm, TEXT_MAIN)
            y += 17

        # speed/quantum shown in footer panel

        # Edit processes button at bottom of sidebar
        edit_btn_r = pygame.Rect(10, H - 115, SB_W - 20, 28)
        rounded_rect(self.screen, CARD_BG, edit_btn_r, 6)
        pygame.draw.rect(self.screen, ACCENT2, edit_btn_r, 1, border_radius=6)
        icon_r = pygame.Rect(edit_btn_r.centerx - 62, edit_btn_r.y, 16, edit_btn_r.h)
        icon_pencil(self.screen, icon_r, ACCENT2)
        text(self.screen, "Edit Processes", (icon_r.right + 4, edit_btn_r.centery),
             self.font_sm, ACCENT2, "midleft")
        self._btn_rects["edit_processes"] = edit_btn_r

    def _draw_gantt(self, W, H):
        SB_W = 210
        gantt_x = SB_W + 16
        gantt_w = W - SB_W - 32
        gantt_top = 80
        gantt_h   = 52
        row_gap   = 64

        # Draw per-task Gantt rows
        task_rows = {n: i for i, n in enumerate(self.task_names)}
        n_rows = len(self.task_names)
        total_area_h = n_rows * row_gap + 20

        # Background lane
        for i, n in enumerate(self.task_names):
            ry = gantt_top + i * row_gap
            color = self.task_color.get(n, TEXT_DIM)
            # Lane label
            text(self.screen, n, (gantt_x - 4, ry + gantt_h//2), self.font_sm, color, "midright")
            rounded_rect(self.screen, CARD_BG, (gantt_x, ry, gantt_w, gantt_h), 6)

        if self.total_ticks == 0:
            return

        tick_w = gantt_w / self.total_ticks

        # Draw completed ticks
        for idx in range(min(self.tick_ptr, self.total_ticks)):
            ev = self.timeline[idx]
            row = task_rows.get(ev.task_name, 0)
            ry  = gantt_top + row * row_gap
            rx  = gantt_x + idx * tick_w
            rw  = tick_w + 1  # slight overlap to avoid gaps
            color = self.task_color.get(ev.task_name, ACCENT)
            rounded_rect(self.screen, color,
                         (int(rx), ry + 4, max(1, int(rw)), gantt_h - 8), 4)

        # Draw current tick (animated)
        if self.tick_ptr < self.total_ticks:
            ev = self.timeline[self.tick_ptr]
            row = task_rows.get(ev.task_name, 0)
            ry  = gantt_top + row * row_gap
            rx  = gantt_x + self.tick_ptr * tick_w
            rw  = tick_w * self.anim_t
            color = self.task_color.get(ev.task_name, ACCENT)
            # Pulsing bright leading edge
            bright = lerp_color(color, (255, 255, 255), 0.4)
            rounded_rect(self.screen, bright,
                         (int(rx), ry + 4, max(1, int(rw)), gantt_h - 8), 4)

            # Running indicator glow on lane
            glow_alpha = int(80 + 60 * math.sin(pygame.time.get_ticks() / 200))
            s = pygame.Surface((gantt_w, gantt_h), pygame.SRCALPHA)
            s.fill((*color, glow_alpha))
            self.screen.blit(s, (gantt_x, ry))

        # Time axis
        axis_y = gantt_top + n_rows * row_gap + 8
        pygame.draw.line(self.screen, BORDER, (gantt_x, axis_y), (gantt_x + gantt_w, axis_y))
        step = max(1, self.total_ticks // 20)
        for i in range(0, self.total_ticks + 1, step):
            x = int(gantt_x + i * tick_w)
            pygame.draw.line(self.screen, BORDER, (x, axis_y), (x, axis_y + 4))
            text(self.screen, str(i), (x, axis_y + 6), self.font_sm, TEXT_DIM, "midtop")

        # CPU utilisation bar
        util_y = axis_y + 28
        util_h = 14
        text(self.screen, "CPU", (gantt_x - 4, util_y + util_h//2), self.font_sm, TEXT_DIM, "midright")
        rounded_rect(self.screen, CARD_BG, (gantt_x, util_y, gantt_w, util_h), 4)
        for idx in range(min(self.tick_ptr, self.total_ticks)):
            ev = self.timeline[idx]
            color = self.task_color.get(ev.task_name, ACCENT)
            rx = gantt_x + idx * tick_w
            rounded_rect(self.screen, color,
                         (int(rx), util_y, max(1, int(tick_w + 1)), util_h), 2)

    def _draw_controls(self, W, H):
        # ── Footer panel ──────────────────────────────────────────────────────
        FOOTER_H = 80
        footer_y = H - FOOTER_H
        rounded_rect(self.screen, PANEL_BG, (0, footer_y, W, FOOTER_H))
        pygame.draw.line(self.screen, BORDER, (0, footer_y), (W, footer_y))

        # Only clear footer/control keys, not sidebar keys (e.g. edit_processes)
        for k in ("algo_left", "algo_right", "play", "prev", "next", "reset", "stats"):
            self._btn_rects.pop(k, None)

        btn_h   = 34
        btn_row = footer_y + 10        # vertical centre of button row
        hint_y  = footer_y + FOOTER_H - 18   # hint text baseline

        # ── LEFT GROUP: speed & quantum info ─────────────────────────────────
        SB_W = 210
        lx = SB_W + 16
        text(self.screen, f"Speed  {self.speed}×",      (lx, btn_row + 2),      self.font_sm, TEXT_DIM)
        text(self.screen, f"Quantum  {self.quantum}",   (lx, btn_row + 18),     self.font_sm, TEXT_DIM)

        # ── CENTER GROUP: algo switcher + playback buttons ────────────────────
        center = W // 2

        # Algo switcher row (above buttons, centred)
        arr_w   = 26
        algo_label_w = 180
        algo_total_w = arr_w * 2 + algo_label_w + 8   # arrows + label + gaps
        ax = center - algo_total_w // 2

        left_r  = pygame.Rect(ax,                   btn_row,      arr_w, btn_h)
        algo_r  = pygame.Rect(ax + arr_w + 4,       btn_row,      algo_label_w, btn_h)
        right_r = pygame.Rect(ax + arr_w + 4 + algo_label_w + 4, btn_row, arr_w, btn_h)

        for r, direction in ((left_r, -1), (right_r, 1)):
            rounded_rect(self.screen, CARD_BG, r, 6)
            pygame.draw.rect(self.screen, BORDER, r, 1, border_radius=6)
            icon_step(self.screen, r, TEXT_MAIN, direction)

        rounded_rect(self.screen, CARD_BG, algo_r, 6)
        pygame.draw.rect(self.screen, BORDER, algo_r, 1, border_radius=6)
        text(self.screen, self.algo_name, algo_r.center, self.font_sm, ACCENT, "center")

        self._btn_rects["algo_left"]  = left_r
        self._btn_rects["algo_right"] = right_r

        # Playback buttons (right of algo switcher, with a separator gap)
        pb_gap  = 18
        pb_x    = right_r.right + pb_gap
        pb_btns = [
            ("prev",  None,        ""),
            ("play",  "play_pause", "Pause" if self.playing else "Play"),
            ("next",  None,        ""),
            ("reset", "reset",     "Reset"),
        ]
        pb_widths = [44, 90, 44, 84]

        pygame.draw.line(self.screen, BORDER,
                         (pb_x - pb_gap//2, btn_row + 4),
                         (pb_x - pb_gap//2, btn_row + btn_h - 4))

        cx = pb_x
        for (key, icon_kind, lbl), w in zip(pb_btns, pb_widths):
            r = pygame.Rect(cx, btn_row, w, btn_h)
            is_play = (key == "play")
            bg  = ACCENT     if is_play else CARD_BG
            bdr = ACCENT     if is_play else BORDER
            rounded_rect(self.screen, bg, r, 7)
            pygame.draw.rect(self.screen, bdr, r, 1, border_radius=7)

            if key == "prev":
                icon_step(self.screen, r, TEXT_MAIN, -1)
            elif key == "next":
                icon_step(self.screen, r, TEXT_MAIN, 1)
            else:
                # Icon on the left third, label text on the right two-thirds
                icon_r = pygame.Rect(r.x, r.y, r.h, r.h)
                if key == "play":
                    (icon_pause if self.playing else icon_play)(self.screen, icon_r, TEXT_ACCENT)
                elif key == "reset":
                    icon_reset(self.screen, icon_r, TEXT_ACCENT)
                text(self.screen, lbl, (r.x + r.h - 2, r.centery), self.font_sm,
                     TEXT_ACCENT, "midleft")

            self._btn_rects[key] = r
            cx += w + 6

        # ── RIGHT GROUP: Stats button ─────────────────────────────────────────
        stats_w = 80
        stats_r = pygame.Rect(W - stats_w - 16, btn_row, stats_w, btn_h)
        rounded_rect(self.screen, ACCENT2 if self.show_stats else CARD_BG, stats_r, 7)
        pygame.draw.rect(self.screen, ACCENT2, stats_r, 1, border_radius=7)
        text(self.screen, "Stats", stats_r.center, self.font_sm, TEXT_ACCENT, "center")
        self._btn_rects["stats"] = stats_r

        # ── Hint bar ─────────────────────────────────────────────────────────
        hints = "Space: play/pause   ←→: step   R: reset   A/D: algo   [ ]: speed   , .: quantum"
        text(self.screen, hints, (W // 2, hint_y), self.font_sm, TEXT_DIM, "midtop")

    def _draw_stats(self, W, H):
        # Overlay card
        panel_w, panel_h = 560, 300
        px = (W - panel_w) // 2
        py = (H - panel_h) // 2
        s = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        s.fill((20, 24, 40, 230))
        self.screen.blit(s, (px, py))
        rounded_rect(self.screen, CARD_BG, (px, py, panel_w, panel_h), 12)
        pygame.draw.rect(self.screen, ACCENT, (px, py, panel_w, panel_h), 1, border_radius=12)

        text(self.screen, f"Results — {self.algo_name}", (px + panel_w//2, py + 16),
             self.font_md, ACCENT, "midtop")

        # Table
        headers = ["Process", "Arrival", "Burst", "Completion", "TAT", "WT"]
        col_xs   = [px + 20, px + 110, px + 180, px + 270, px + 370, px + 460]
        hy = py + 46
        for i, h in enumerate(headers):
            text(self.screen, h, (col_xs[i], hy), self.font_sm, TEXT_DIM)
        pygame.draw.line(self.screen, BORDER, (px + 10, hy + 16), (px + panel_w - 10, hy + 16))

        ry = hy + 22
        total_tat = total_wt = 0
        for n in self.task_names:
            if n not in self.results:
                continue
            r = self.results[n]
            color = self.task_color.get(n, TEXT_MAIN)
            vals = [n, r["arrival"], r["burst"], r["completion"], r["tat"], r["wt"]]
            for i, v in enumerate(vals):
                c = color if i == 0 else TEXT_MAIN
                text(self.screen, v, (col_xs[i], ry), self.font_sm, c)
            total_tat += r["tat"]
            total_wt  += r["wt"]
            ry += 20

        n_tasks = len(self.task_names)
        pygame.draw.line(self.screen, BORDER, (px + 10, ry + 2), (px + panel_w - 10, ry + 2))
        ry += 10
        text(self.screen, f"Avg Turnaround Time: {total_tat/n_tasks:.2f}",
             (px + 20, ry), self.font_sm, ACCENT2)
        text(self.screen, f"Avg Waiting Time: {total_wt/n_tasks:.2f}",
             (px + 300, ry), self.font_sm, WARN)
        ry += 22
        text(self.screen, "Click anywhere to close", (px + panel_w//2, ry),
             self.font_sm, TEXT_DIM, "midtop")
        self._stats_rect = pygame.Rect(px, py, panel_w, panel_h)

    # ── Event handling ─────────────────────────────────────────────────────────
    def handle(self, event):
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        # Let the editor consume events first when visible
        if self.editor.visible:
            result = self.editor.handle_event(event)
            if result and result[0] == "apply":
                self.tasks_cfg = result[1]
                self._rebuild()
            return   # swallow all events while editor is open

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if self.tick_ptr >= self.total_ticks:
                    self._do_reset()
                self.playing = not self.playing
            elif event.key == pygame.K_RIGHT:
                self.tick_ptr = min(self.tick_ptr + 1, self.total_ticks)
                self.anim_t = 0
            elif event.key == pygame.K_LEFT:
                self.tick_ptr = max(self.tick_ptr - 1, 0)
                self.anim_t = 0
            elif event.key == pygame.K_r:
                self._do_reset()
            elif event.key in (pygame.K_a,):
                self.algo_idx = (self.algo_idx - 1) % len(ALGORITHMS)
                self._rebuild()
            elif event.key in (pygame.K_d,):
                self.algo_idx = (self.algo_idx + 1) % len(ALGORITHMS)
                self._rebuild()
            elif event.key == pygame.K_RIGHTBRACKET:
                self.speed = min(self.speed + 1, 32)
            elif event.key == pygame.K_LEFTBRACKET:
                self.speed = max(self.speed - 1, 1)
            elif event.key == pygame.K_COMMA:
                self.quantum = max(1, self.quantum - 1)
                self._rebuild()
            elif event.key == pygame.K_PERIOD:
                self.quantum = min(self.quantum + 1, 10)
                self._rebuild()

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            rects = getattr(self, "_btn_rects", {})
            if self.show_stats and hasattr(self, "_stats_rect"):
                self.show_stats = False
                return
            if rects.get("play") and rects["play"].collidepoint(pos):
                if self.tick_ptr >= self.total_ticks:
                    self._do_reset()
                self.playing = not self.playing
            elif rects.get("reset") and rects["reset"].collidepoint(pos):
                self._do_reset()
            elif rects.get("prev") and rects["prev"].collidepoint(pos):
                self.tick_ptr = max(self.tick_ptr - 1, 0); self.anim_t = 0
            elif rects.get("next") and rects["next"].collidepoint(pos):
                self.tick_ptr = min(self.tick_ptr + 1, self.total_ticks); self.anim_t = 0
            elif rects.get("algo_left") and rects["algo_left"].collidepoint(pos):
                self.algo_idx = (self.algo_idx - 1) % len(ALGORITHMS); self._rebuild()
            elif rects.get("algo_right") and rects["algo_right"].collidepoint(pos):
                self.algo_idx = (self.algo_idx + 1) % len(ALGORITHMS); self._rebuild()
            elif rects.get("stats") and rects["stats"].collidepoint(pos):
                self.show_stats = not self.show_stats
            elif rects.get("edit_processes") and rects["edit_processes"].collidepoint(pos):
                self.editor.open(self.tasks_cfg)

    def _do_reset(self):
        self.playing   = False
        self.tick_ptr  = 0
        self.anim_t    = 0.0
        self.show_stats = False

    # ── Main loop ──────────────────────────────────────────────────────────────
    def run(self):
        while True:
            dt = self.clock_fps.tick(60) / 1000.0
            for event in pygame.event.get():
                self.handle(event)
            self.update(dt)
            self.draw()


if __name__ == "__main__":
    App().run()