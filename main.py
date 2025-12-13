import cv2
import pygame
import numpy as np
from ultralytics import YOLO
import sys
import random

# ==========================================
# CONFIGURACIÓN DEL PROYECTO
# ==========================================
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
CAMERA_ID = 0  # Cambiar a 1 si tienes cámara externa
CONFIDENCE_THRESHOLD = 0.5

# Colores (R, G, B)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_RED = (255, 50, 50)
COLOR_BLUE = (50, 50, 255)
COLOR_GREEN = (0, 255, 0)

# ==========================================
# CLASE 1: MOTOR DE VISIÓN 
# ==========================================
class VisionEngine:
    def __init__(self):
        print("Cargando modelo YOLOv8 Pose... (Esto puede tardar la primera vez)")
        self.model = YOLO("yolov8n-pose.pt") # Descarga automática si no existe
        self.cap = cv2.VideoCapture(CAMERA_ID)
        self.cap.set(3, WINDOW_WIDTH)
        self.cap.set(4, WINDOW_HEIGHT)
    
    def get_frame_and_keypoints(self):
        ret, frame = self.cap.read()
        if not ret:
            return None, None
        
        # Espejar el frame para que se sienta natural (como un espejo)
        frame = cv2.flip(frame, 1)
        
        # Inferencia con YOLO
        results = self.model(frame, stream=True, verbose=False, conf=CONFIDENCE_THRESHOLD)
        
        keypoints = []
        
        # Extraer keypoints solo del primer esqueleto detectado
        for r in results:
            if r.keypoints is not None and len(r.keypoints.xy) > 0:
                # Obtenemos las coordenadas x,y de todos los puntos
                kpts = r.keypoints.xy[0].cpu().numpy()
                keypoints = kpts
                break # Solo nos interesa la primera persona
        
        # Convertir frame de BGR (OpenCV) a RGB (Pygame)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Transponer para Pygame (intercambiar ejes)
        frame_rgb = np.transpose(frame_rgb, (1, 0, 2))
        frame_rgb = pygame.surfarray.make_surface(frame_rgb)
        
        return frame_rgb, keypoints
        
    def release(self):
        self.cap.release()

# ==========================================
# CLASE 2: INTERFAZ Y JUEGO 
# ==========================================
class RhythmGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Proyecto Arquitectura: Ritmo con Visión Artificial")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 36)
        self.small_font = pygame.font.SysFont("Arial", 24)
        
        # Estado del juego
        self.score = 0
        self.combo = 0
        self.multiplier = 1
        self.targets = [] # Lista de objetivos flotantes
        self.spawn_timer = 0
        
        # Tipos de poses (0-4)
        self.pose_names = [
            "BRAZOS ARRIBA",
            "BRAZO DERECHO →",
            "BRAZO IZQUIERDO ←",
            "POSE T",
            "BRAZOS ABAJO"
        ]
        self.pose_colors = [
            (255, 255, 0),   # Amarillo
            (255, 100, 100), # Rojo claro
            (100, 100, 255), # Azul claro
            (0, 255, 255),   # Cyan
            (255, 0, 255)    # Magenta
        ]
        
    def spawn_target(self):
        # Crear un nuevo objetivo con una pose requerida
        pose_type = random.randint(0, 4) # 5 tipos de poses
        y = random.randint(150, WINDOW_HEIGHT - 150)
        
        self.targets.append({
            "x": WINDOW_WIDTH, # Aparecen desde la derecha
            "y": y, 
            "type": pose_type, 
            "width": 120, 
            "height": 80,
            "life": 180, # Tiempo para completar
            "speed": 3
        })

    def detect_pose(self, keypoints):
        """
        Detecta qué pose está haciendo el usuario basándose en ángulos de brazos
        Keypoints relevantes:
        5: Hombro izquierdo, 6: Hombro derecho
        7: Codo izquierdo, 8: Codo derecho
        9: Muñeca izquierda, 10: Muñeca derecha
        11: Cadera izquierda, 12: Cadera derecha
        """
        if len(keypoints) < 13:
            return -1
        
        # Extraer puntos clave
        left_shoulder = keypoints[5]
        right_shoulder = keypoints[6]
        left_elbow = keypoints[7]
        right_elbow = keypoints[8]
        left_wrist = keypoints[9]
        right_wrist = keypoints[10]
        
        # Verificar que los puntos estén detectados
        if (left_wrist[0] == 0 or right_wrist[0] == 0 or 
            left_shoulder[0] == 0 or right_shoulder[0] == 0):
            return -1
        
        # Calcular posiciones relativas
        left_wrist_above_shoulder = left_wrist[1] < left_shoulder[1] - 50
        right_wrist_above_shoulder = right_wrist[1] < right_shoulder[1] - 50
        
        left_wrist_below_shoulder = left_wrist[1] > left_shoulder[1] + 80
        right_wrist_below_shoulder = right_wrist[1] > right_shoulder[1] + 80
        
        # Brazos horizontales (diferencia Y pequeña)
        left_arm_horizontal = abs(left_wrist[1] - left_shoulder[1]) < 60
        right_arm_horizontal = abs(right_wrist[1] - right_shoulder[1]) < 60
        
        # POSE 0: Brazos arriba
        if left_wrist_above_shoulder and right_wrist_above_shoulder:
            return 0
        
        # POSE 1: Brazo derecho horizontal (extendido)
        if right_arm_horizontal and right_wrist[0] > right_shoulder[0] + 80:
            return 1
        
        # POSE 2: Brazo izquierdo horizontal (extendido)
        if left_arm_horizontal and left_wrist[0] < left_shoulder[0] - 80:
            return 2
        
        # POSE 3: Pose T (ambos brazos horizontales)
        if left_arm_horizontal and right_arm_horizontal:
            if abs(left_wrist[0] - left_shoulder[0]) > 80 and abs(right_wrist[0] - right_shoulder[0]) > 80:
                return 3
        
        # POSE 4: Brazos abajo
        if left_wrist_below_shoulder and right_wrist_below_shoulder:
            return 4
        
        return -1  # Ninguna pose detectada

    def draw_skeleton(self, keypoints):
        """Dibuja el esqueleto del jugador con líneas"""
        if len(keypoints) < 13:
            return
        
        connections = [
            (5, 6),   # Hombros
            (5, 7),   # Hombro izq - Codo izq
            (7, 9),   # Codo izq - Muñeca izq
            (6, 8),   # Hombro der - Codo der
            (8, 10),  # Codo der - Muñeca der
            (5, 11),  # Hombro izq - Cadera izq
            (6, 12),  # Hombro der - Cadera der
        ]
        
        for start, end in connections:
            if (keypoints[start][0] != 0 and keypoints[end][0] != 0):
                pygame.draw.line(self.screen, COLOR_GREEN, 
                               (int(keypoints[start][0]), int(keypoints[start][1])),
                               (int(keypoints[end][0]), int(keypoints[end][1])), 4)
        
        # Dibujar puntos articulares
        for i in [5, 6, 7, 8, 9, 10, 11, 12]:
            if keypoints[i][0] != 0:
                pygame.draw.circle(self.screen, COLOR_WHITE, 
                                 (int(keypoints[i][0]), int(keypoints[i][1])), 8)

    def update_game_logic(self, keypoints):
        # Generar objetivos cada cierto tiempo
        self.spawn_timer += 1
        if self.spawn_timer > 60: # Velocidad de aparición
            self.spawn_target()
            self.spawn_timer = 0
        
        # Detectar pose actual del jugador
        current_pose = self.detect_pose(keypoints)
        
        # Zona de activación (lado izquierdo de la pantalla) - AMPLIADA
        activation_zone_x = 350  # Más amplia para dar más tiempo
        
        for target in self.targets[:]:
            target["life"] -= 1
            target["x"] -= target["speed"] # Mover de derecha a izquierda
            
            # Dibujar objetivo
            color = self.pose_colors[target["type"]]
            rect = pygame.Rect(target["x"] - target["width"]//2, 
                              target["y"] - target["height"]//2,
                              target["width"], target["height"])
            
            # Efecto de brillo si está en zona de activación
            in_zone = target["x"] <= activation_zone_x and target["x"] >= 50
            if in_zone:
                pygame.draw.rect(self.screen, (255, 255, 255), rect, 5)
            else:
                pygame.draw.rect(self.screen, color, rect, 3)
            
            # Dibujar nombre de la pose
            pose_text = self.small_font.render(self.pose_names[target["type"]], True, color)
            text_rect = pose_text.get_rect(center=(target["x"], target["y"]))
            self.screen.blit(pose_text, text_rect)
            
            # Lógica de acierto
            hit = False
            if in_zone and current_pose == target["type"]:
                hit = True
            
            if hit:
                # Sistema de combos
                self.combo += 1
                if self.combo > 5:
                    self.multiplier = 3
                elif self.combo > 3:
                    self.multiplier = 2
                else:
                    self.multiplier = 1
                
                points = 100 * self.multiplier
                self.score += points
                self.targets.remove(target)
                
                # Efecto visual de acierto
                pygame.draw.rect(self.screen, COLOR_GREEN, rect, 8)
                combo_text = self.font.render(f"+{points} pts!", True, COLOR_GREEN)
                self.screen.blit(combo_text, (target["x"] - 50, target["y"] - 60))
                
            elif target["x"] < 0:  # Solo eliminar cuando salga completamente de la pantalla
                # Falló el objetivo - resetear combo
                self.combo = 0
                self.multiplier = 1
                self.targets.remove(target)

    def draw_ui(self):
        # Zona de activación visual - DIBUJADA PRIMERO
        pygame.draw.rect(self.screen, (100, 255, 100), (0, 0, 350, WINDOW_HEIGHT), 2)
        
        # Línea central de la zona de activación
        pygame.draw.line(self.screen, (255, 255, 100), (200, 0), (200, WINDOW_HEIGHT), 3)
        
        # Puntuación
        score_text = self.font.render(f"Puntuación: {self.score}", True, COLOR_WHITE)
        bg_rect = score_text.get_rect(topleft=(20, 20))
        bg_rect.inflate_ip(20, 10)
        pygame.draw.rect(self.screen, COLOR_BLACK, bg_rect)
        self.screen.blit(score_text, (30, 25))
        
        # Combo y Multiplicador
        if self.combo > 0:
            combo_text = self.font.render(f"COMBO x{self.combo}  |  Multiplicador: {self.multiplier}x", True, (255, 255, 0))
            combo_rect = combo_text.get_rect(topright=(WINDOW_WIDTH - 20, 20))
            combo_rect.inflate_ip(20, 10)
            pygame.draw.rect(self.screen, COLOR_BLACK, combo_rect)
            self.screen.blit(combo_text, (WINDOW_WIDTH - combo_text.get_width() - 30, 25))
        
        # Instrucciones con fondo negro para que se vea bien
        instr_text = self.small_font.render("Realiza las poses cuando lleguen a la LINEA AMARILLA", True, COLOR_WHITE)
        instr_rect = instr_text.get_rect(bottomleft=(20, WINDOW_HEIGHT - 20))
        instr_rect.inflate_ip(20, 10)
        pygame.draw.rect(self.screen, COLOR_BLACK, instr_rect)
        self.screen.blit(instr_text, (30, WINDOW_HEIGHT - 40))

    def run(self, vision_engine):
        running = True
        while running:
            # 1. Manejo de eventos (Cerrar ventana)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            # 2. Obtener datos del mundo real (Visión)
            frame_surface, keypoints = vision_engine.get_frame_and_keypoints()
            
            if frame_surface is None:
                break

            # 3. Dibujar fondo (Cámara)
            self.screen.blit(frame_surface, (0, 0))

            # 4. Lógica del juego y Dibujado de Overlay
            if len(keypoints) > 0:
                self.draw_skeleton(keypoints)
                self.update_game_logic(keypoints)
            
            self.draw_ui()

            # 5. Actualizar pantalla
            pygame.display.flip()
            self.clock.tick(30) # Limitar a 30 FPS

        vision_engine.release()
        pygame.quit()
        sys.exit()

# ==========================================
# MAIN ENTRY POINT
# ==========================================
if __name__ == "__main__":
    try:
        # Instanciar módulos
        vision = VisionEngine()
        game = RhythmGame()
        
        # Iniciar bucle principal
        game.run(vision)
        
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        pygame.quit()
