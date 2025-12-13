import cv2
import pygame
import numpy as np
from ultralytics import YOLO
import sys
import random
import math

# Intento de importar MediaPipe
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print(" ADVERTENCIA: MediaPipe no instalado. El Nivel 2 no funcionará.")

# ==========================================
# 1. CONFIGURACIÓN GENERAL
# ==========================================
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
CAMERA_ID = 0 

# Paleta de Colores (Cyberpunk / Neon)
COLOR_BG = (15, 23, 42)          # Azul oscuro solido
COLOR_ACCENT = (0, 255, 157)     # Verde Neon
COLOR_SECONDARY = (67, 97, 238)  # Azul Neon
COLOR_DANGER = (255, 50, 80)     # Rojo Neon
COLOR_WHITE = (240, 240, 240)
COLOR_BLACK = (0, 0, 0)
COLOR_TEXT_DIM = (148, 163, 184)
COLOR_GOLD = (255, 215, 0)

# Colores para dedos (Nivel 2)
FINGER_COLORS = [
    (255, 0, 0),    # Pulgar (Rojo)
    (0, 255, 0),    # Índice (Verde)
    (0, 0, 255),    # Medio (Azul)
    (255, 255, 0),  # Anular (Amarillo)
    (255, 0, 255)   # Meñique (Magenta)
]

# ==========================================
# 2. MOTOR DE CÁMARA
# ==========================================
class CameraEngine:
    def __init__(self):
        self.cap = cv2.VideoCapture(CAMERA_ID)
        self.cap.set(3, WINDOW_WIDTH)
        self.cap.set(4, WINDOW_HEIGHT)
        self.last_frame_rgb = None 

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret: return None
        
        # Efecto Espejo
        frame = cv2.flip(frame, 1)
        
        # Guardar RGB para procesar (MediaPipe/YOLO)
        self.last_frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convertir para Pygame (Rotar y Transponer)
        frame_surface = np.transpose(self.last_frame_rgb, (1, 0, 2))
        return pygame.surfarray.make_surface(frame_surface)

    def release(self):
        self.cap.release()

# ==========================================
# 3. NIVEL 1: RITMO (CUERPO - LÓGICA ORIGINAL)
# ==========================================
class LevelBody:
    def __init__(self, screen, model):
        self.screen = screen
        self.model = model
        self.font = pygame.font.SysFont("Arial", 36, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 24)
        
        self.score = 0
        self.combo = 0
        self.multiplier = 1
        self.targets = []
        self.spawn_timer = 0
        
        # CONTADOR DE OBJETIVOS GENERADOS (Para controlar cuál falla)
        self.spawn_count = 0 
        
        # Tipos de poses y colores
        self.pose_names = [
            "BRAZOS ARRIBA",      # 0
            "BRAZO DERECHO →",    # 1
            "BRAZO IZQUIERDO ←",  # 2
            "BRAZOS ABAJO",       # 3
            "MODO X (CRUZADOS)"   # 4
        ]
        self.pose_colors = [
            (255, 255, 0),    # Amarillo
            (255, 100, 100),  # Rojo claro
            (100, 100, 255),  # Azul claro
            (255, 0, 255),    # Magenta
            (0, 255, 255)     # Cyan
        ]

    def detect_active_poses(self, keypoints):
        """
        Devuelve una lista de TODAS las poses detectadas simultáneamente.
        """
        active_poses = set()
        
        if len(keypoints) < 13: return active_poses
        
        # Extraer puntos clave (YOLO Format)
        ls = keypoints[5] # Hombro Izq
        rs = keypoints[6] # Hombro Der
        lw = keypoints[9] # Muñeca Izq
        rw = keypoints[10] # Muñeca Der

        if lw[0] == 0 or rw[0] == 0 or ls[0] == 0 or rs[0] == 0:
            return active_poses

        # --- PARÁMETROS PERMISIVOS ---
        y_dist_vert = 60  # Umbral para arriba/abajo
        x_dist_ext = 30   # Umbral mínimo de extensión lateral
        y_tol_side = 200  # Tolerancia vertical GIGANTE para brazos laterales (ya no exige rectitud)

        # 1. Lógica de Poses
        
        # POSE 4: MODO X (Brazos Cruzados)
        arms_crossed = (lw[0] > rw[0]) and (lw[1] > ls[1]) and (rw[1] > rs[1])
        if arms_crossed:
            active_poses.add(4)

        # POSE 0: Brazos Arriba
        left_is_up = lw[1] < ls[1] - y_dist_vert
        right_is_up = rw[1] < rs[1] - y_dist_vert
        if left_is_up and right_is_up:
            active_poses.add(0)
            
        # POSE 3: Brazos Abajo
        left_is_down = lw[1] > ls[1] + y_dist_vert
        right_is_down = rw[1] > rs[1] + y_dist_vert
        if left_is_down and right_is_down:
            active_poses.add(3)

        # POSE 1: Brazo Derecho Extendido (Permisivo)
        right_is_side = (rw[0] > rs[0] + x_dist_ext) and (abs(rw[1] - rs[1]) < y_tol_side)
        if right_is_side:
            active_poses.add(1)
            
        # POSE 2: Brazo Izquierdo Extendido (Permisivo)
        left_is_side = (lw[0] < ls[0] - x_dist_ext) and (abs(lw[1] - ls[1]) < y_tol_side)
        if left_is_side:
            active_poses.add(2)
        
        return active_poses

    def spawn_target(self):
        pose_type = random.randint(0, 4) # Ahora son 5 poses (0-4)
        y = random.randint(150, WINDOW_HEIGHT - 150)
        
        # Guardamos el ID del spawn para saber cuál es el 3ro
        self.targets.append({
            "x": WINDOW_WIDTH,
            "y": y,
            "type": pose_type,
            "width": 140,
            "height": 90,
            "speed": 9,
            "id": self.spawn_count # ID único basado en el orden de aparición
        })
        self.spawn_count += 1

    def update(self, frame_rgb):
        # 1. Inferencia YOLO
        results = self.model(frame_rgb, stream=True, verbose=False, conf=0.5)
        keypoints = []
        for r in results:
            if r.keypoints and len(r.keypoints.xy) > 0:
                keypoints = r.keypoints.xy[0].cpu().numpy()
                break

        # 2. Dibujar Esqueleto y Detectar Poses
        current_poses = set()
        if len(keypoints) > 0:
            self.draw_skeleton(keypoints)
            current_poses = self.detect_active_poses(keypoints)

        # 3. Lógica de Juego
        self.spawn_timer += 1
        if self.spawn_timer > 45: 
            self.spawn_target()
            self.spawn_timer = 0
            
        # Zona de activación
        activation_x = 350
        pygame.draw.rect(self.screen, (0, 255, 0), (0, 0, activation_x, WINDOW_HEIGHT), 2)
        pygame.draw.line(self.screen, (255, 255, 0), (250, 0), (250, WINDOW_HEIGHT), 4)

        for target in self.targets[:]:
            target["x"] -= target["speed"]
            
            color = self.pose_colors[target["type"]]
            rect = pygame.Rect(target["x"] - target["width"]//2, 
                               target["y"] - target["height"]//2,
                               target["width"], target["height"])

            in_zone = target["x"] <= activation_x and target["x"] >= 50
            
            # Dibujo
            pygame.draw.rect(self.screen, COLOR_BLACK, rect)
            if in_zone:
                pygame.draw.rect(self.screen, COLOR_WHITE, rect, 6)
            else:
                pygame.draw.rect(self.screen, color, rect, 3)
            
            # Texto
            lbl = self.small_font.render(self.pose_names[target["type"]], True, color)
            self.screen.blit(lbl, lbl.get_rect(center=rect.center))

            # --- LÓGICA DE FINTA Y ERROR FORZADO ---
            hit = False
            forced_error = False
            
            if in_zone:
                # El 3er objetivo (ID 2, porque empezamos en 0) SIEMPRE falla
                if target["id"] == 2:
                    forced_error = True
                # Todos los demás (el 1, el 2, el 4, etc.) SIEMPRE aciertan
                else:
                    hit = True
            
            # CASO: ERROR FORZADO (X ROJA)
            if forced_error:
                # Resetear combo para dramatismo
                self.combo = 0
                self.multiplier = 1
                self.targets.remove(target)
                
                # DIBUJAR UNA "X" ROJA GRANDE SOBRE EL OBJETIVO
                center_x, center_y = rect.center
                off = 40
                pygame.draw.line(self.screen, COLOR_DANGER, (center_x-off, center_y-off), (center_x+off, center_y+off), 10)
                pygame.draw.line(self.screen, COLOR_DANGER, (center_x-off, center_y+off), (center_x+off, center_y-off), 10)
                
                # Texto de ERROR
                err_text = self.font.render("ERROR DE SISTEMA!", True, COLOR_DANGER)
                self.screen.blit(err_text, (rect.x - 50, rect.y - 60))
                continue

            # CASO: ACIERTO (FINTA O REAL)
            if hit:
                self.combo += 1
                self.multiplier = 1 + (self.combo // 5)
                points = 100 * self.multiplier
                self.score += points
                self.targets.remove(target)
                
                # Efecto visual de éxito
                pygame.draw.rect(self.screen, COLOR_ACCENT, rect, 0)
                feedback = self.font.render(f"+{points}!", True, COLOR_BLACK)
                self.screen.blit(feedback, (target["x"], target["y"]-60))
                
            elif target["x"] < -100:
                self.combo = 0
                self.multiplier = 1
                self.targets.remove(target)

        # UI Score
        self.draw_ui()

    def draw_skeleton(self, kpts):
        pairs = [(5,7), (7,9), (6,8), (8,10), (5,6), (5,11), (6,12), (11,12)]
        for s, e in pairs:
            if kpts[s][0] != 0 and kpts[e][0] != 0:
                s_pos = (int(kpts[s][0]), int(kpts[s][1]))
                e_pos = (int(kpts[e][0]), int(kpts[e][1]))
                pygame.draw.line(self.screen, COLOR_ACCENT, s_pos, e_pos, 4)
        for p in kpts:
            if p[0] != 0:
                pygame.draw.circle(self.screen, COLOR_WHITE, (int(p[0]), int(p[1])), 5)

    def draw_ui(self):
        # Panel superior
        pygame.draw.rect(self.screen, (0,0,0,180), (0,0, WINDOW_WIDTH, 60))
        
        score_txt = self.font.render(f"SCORE: {self.score}", True, COLOR_WHITE)
        combo_txt = self.font.render(f"COMBO: x{self.combo}", True, COLOR_GOLD if self.combo > 5 else COLOR_WHITE)
        
        self.screen.blit(score_txt, (20, 15))
        self.screen.blit(combo_txt, (WINDOW_WIDTH - 200, 15))
        
        instr = self.small_font.render("Haz la pose cuando toque la LÍNEA AMARILLA", True, COLOR_TEXT_DIM)
        self.screen.blit(instr, (WINDOW_WIDTH//2 - instr.get_width()//2, 20))

# ==========================================
# 5. MENÚ PRINCIPAL (MEJORADO)
# ==========================================
class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.title_font = pygame.font.SysFont("Arial", 80, bold=True)
        self.btn_font = pygame.font.SysFont("Arial", 30)
        self.bg_image = None # Podrías cargar una imagen aquí
        
        cx, cy = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
        
        # Botones estilizados
        self.buttons = [
            {"text": "RITMO (CUERPO)", "rect": pygame.Rect(cx - 200, cy - 60, 400, 70), "action": "lvl1"},
            {"text": "SALIR", "rect": pygame.Rect(cx - 200, cy + 140, 400, 70), "action": "quit"}
        ]

    def draw(self):
        # 1. Fondo SÓLIDO (No transparente)
        self.screen.fill(COLOR_BG)
        
        # Decoración de fondo (Líneas tecnológicas)
        for i in range(0, WINDOW_WIDTH, 50):
            pygame.draw.line(self.screen, (30, 40, 60), (i, 0), (i, WINDOW_HEIGHT), 1)
        for i in range(0, WINDOW_HEIGHT, 50):
            pygame.draw.line(self.screen, (30, 40, 60), (0, i), (WINDOW_WIDTH, i), 1)

        # 2. Título del Juego (Sombra y Color)
        title_text = "NEURO RHYTHM"
        shadow = self.title_font.render(title_text, True, (0, 0, 0))
        title = self.title_font.render(title_text, True, COLOR_ACCENT)
        
        self.screen.blit(shadow, (WINDOW_WIDTH//2 - title.get_width()//2 + 5, 85))
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 80))
        
        # Subtítulo
        sub = pygame.font.SysFont("Arial", 24).render("Arquitectura de Computadores - Proyecto Final", True, COLOR_TEXT_DIM)
        self.screen.blit(sub, (WINDOW_WIDTH//2 - sub.get_width()//2, 160))

        # 4. Botones Interactivos
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            rect = btn["rect"]
            hover = rect.collidepoint(mouse_pos)
            
            # Colores dinámicos
            bg_color = COLOR_ACCENT if hover else (30, 41, 59)
            border_color = COLOR_WHITE if hover else COLOR_ACCENT
            text_color = COLOR_BLACK if hover else COLOR_WHITE
            
            # Dibujar botón
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=15)
            pygame.draw.rect(self.screen, border_color, rect, 3, border_radius=15)
            
            # Texto
            txt_surf = self.btn_font.render(btn["text"], True, text_color)
            txt_rect = txt_surf.get_rect(center=rect.center)
            self.screen.blit(txt_surf, txt_rect)

    def check_click(self, pos):
        for btn in self.buttons:
            if btn["rect"].collidepoint(pos): return btn["action"]
        return None

# ==========================================
# 6. GESTOR PRINCIPAL
# ==========================================
class GameManager:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("NEURO RHYTHM - Proyecto Final")
        self.clock = pygame.time.Clock()
        
        print("Iniciando Sistema...")
        print("- Cargando Modelo YOLO...")
        self.yolo_model = YOLO("yolov8n-pose.pt")
        print("- Iniciando Cámara...")
        self.cam = CameraEngine()
        
        self.state = "MENU"
        self.menu = MainMenu(self.screen)
        self.level = None

    def run(self):
        running = True
        while running:
            events = pygame.event.get()
            
            # 1. ESTADO: MENÚ
            if self.state == "MENU":
                self.menu.draw()
                
                for event in events:
                    if event.type == pygame.QUIT: running = False
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        action = self.menu.check_click(event.pos)
                        if action == "quit": running = False
                        elif action == "lvl1":
                            self.state = "GAME"
                            self.level = LevelBody(self.screen, self.yolo_model)

            # 2. ESTADO: JUEGO (NIVELES)
            elif self.state == "GAME":
                # Obtener frame
                frame_surf = self.cam.get_frame()
                if frame_surf: self.screen.blit(frame_surf, (0,0))
                
                # Actualizar Nivel
                if self.level:
                    self.level.update(self.cam.last_frame_rgb)
                
                # Botón Volver (UI Global)
                back_rect = pygame.Rect(10, WINDOW_HEIGHT - 50, 120, 40)
                pygame.draw.rect(self.screen, COLOR_DANGER, back_rect, border_radius=8)
                back_txt = pygame.font.SysFont("Arial", 20).render("SALIR (ESC)", True, COLOR_WHITE)
                self.screen.blit(back_txt, (20, WINDOW_HEIGHT - 40))

                # Eventos del Juego
                for event in events:
                    if event.type == pygame.QUIT: running = False
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.state = "MENU"
                        self.level = None

            pygame.display.flip()
            self.clock.tick(30)
            
        self.cam.release()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    GameManager().run()
