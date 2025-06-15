import cv2
import math

import os

def silence_native_stderr():
    """Redireciona stderr (fd 2) para /dev/null no nível do sistema."""
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 2)

# ==========================
# BARRAR EM CASO DE QUEDA
# ==========================
#silence_native_stderr()

import mediapipe as mp

hands = mp.solutions.hands.Hands()


mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

TOUCH_THRESHOLD = .2

lastHandX = None
lastHandY = None
lastHandZ = None

def calculate_distance(point1, point2):
    return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2 + (point1.z - point2.z)**2)

def get_hand_data(image):
    if (image is None):
            return True

    with mp_hands.Hands(
        min_detection_confidence=.7, # Aumentei a confiança para detecção mais estável
        min_tracking_confidence=.7,
        max_num_hands=1) as hands:
        global lastHandX
        global lastHandY
        global lastHandZ
    
        results = hands.process(image)

        # Desenha as anotações da mão na imagem.
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Obtenha os landmarks específicos
                thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP] # Usei o dedo indicador como exemplo, mas você pode usar o dedo médio se preferir
                index_finger_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP] 
                avg_closure = 0
                '''
                # distancia entre ponta do polegar e ponta do indicador
                distanceThumbIndex = calculate_distance(thumb_tip, index_finger_tip)
                # distancia index base
                distanceIndexBase = calculate_distance(index_finger_tip, index_finger_mcp) * 1.2
            
                distance = ((distanceThumbIndex * 100) / distanceIndexBase)
                # capa valores altos e baixos
                if distance <= 10:
                    avg_closure = 0
                else:
                    avg_closure = min(distance, 100)
                print(avg_closure)
                '''
                wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
                deltaX = wrist.x - (wrist.x if lastHandX is None else lastHandX)
                deltaY = wrist.y - (wrist.y if lastHandY is None else lastHandY)
                deltaZ = wrist.z - (wrist.z if lastHandZ is None else lastHandZ)
                
            

                lastHandX = wrist.x
                lastHandY = wrist.y
                lastHandZ = wrist.z

                '''
                distance = math.sqrt(
                    (thumb_tip.x - index_finger_tip.x)**2 +
                    (thumb_tip.y - index_finger_tip.y)**2 +
                    (thumb_tip.z - index_finger_tip.z)**2
                )
                '''
                return (avg_closure, deltaX, deltaY, deltaZ, get_hand_rotation(hand_landmarks))
        else:
                return (None, 0, 0, 0, (0, 0))
            
'''
def get_hand_closure_percentage(image):
    # Get relevant landmark points
    # Fingertips
    # cv2.


    if (image is None):
            return False

    with mp_hands.Hands(
        min_detection_confidence=0.7, # Aumentei a confiança para detecção mais estável
        min_tracking_confidence=0.7,
        max_num_hands=1) as hands:
    
        results = hands.process(image)

        # Desenha as anotações da mão na imagem.
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        print(get_hand_data(image))

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:

                thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]

                # Wrist for normalization
                wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]

                # For thumb, you might compare to the base of the thumb or wrist
                distance = calculate_distance(thumb_tip, index_tip)
            
                mp_drawing.draw_landmarks(
                        image,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(121, 22, 76), thickness=2, circle_radius=4),
                        mp_drawing.DrawingSpec(color=(250, 44, 250), thickness=2, circle_radius=2)
                    )
                log2(distance)
                # Flip the image horizontally for a selfie-view display.
                cv2.imshow('MediaPipe Hand Tracking - Thumb and Middle Finger', cv2.flip(image, 1))

                # Retorna procentagem
                avg_closure = max(0, min(1, avg_closure)) 
                return avg_closure * 100 # Return as percentage
'''

lastAngleX = None
lastAngleY = None
lastAngleZ = None

def get_hand_rotation(hand_landmarks) -> tuple:
    global lastAngleX, lastAngleY, lastAngleZ

    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    middle_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]

    cathetY = middle_finger_tip.y - wrist.y
    cathetX = thumb_tip.x - wrist.x
    cathetZ = thumb_tip.z - wrist.z
    
    angleX = math.atan2(cathetY, cathetX)
    angleY = math.atan2(cathetY, cathetZ)
    angleZ = math.atan2(cathetX, cathetZ)

    deltaX = 0 if lastAngleX is None else angleX - lastAngleX
    deltaY = 0 if lastAngleY is None else angleY - lastAngleY
    deltaZ = 0 if lastAngleZ is None else angleZ - lastAngleZ

    lastAngleX = angleX
    lastAngleY = angleY
    lastAngleZ = angleZ

    print(f"deltaX: {math.degrees(deltaX):.4f}, deltaY: {math.degrees(deltaY):.4f}, deltaZ: {math.degrees(deltaZ):.4f}")
    return (deltaX, deltaZ)


if (__name__ == '__main__') :
    
    # ==========================
    # BARRAR EM CASO DE QUEDA
    # ==========================
    #silence_native_stderr()

    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands

    cap = cv2.VideoCapture(2)

    if not cap.isOpened():
        print("Erro ao abrir a câmera.")
        exit()
    
    with mp_hands.Hands(
        min_detection_confidence=0.7, # Aumentei a confiança para detecção mais estável
        min_tracking_confidence=0.9,
        max_num_hands=1) as hands: # Aumentei 
        
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print("Ignorando quadro vazio da câmera.")
                continue

            image.flags.writeable = False
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            results = hands.process(image)

            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    for idx, landmark in enumerate(hand_landmarks.landmark):
                        if idx in [
                            mp_hands.HandLandmark.THUMB_TIP,
                            mp_hands.HandLandmark.INDEX_FINGER_TIP,
                            mp_hands.HandLandmark.WRIST
                        ]:
                            cv2.circle(image, (int(landmark.x * image.shape[1]), int(landmark.y * image.shape[0])), 8, (0, 255, 255), -1)
                        else:
                            continue
                    mp_drawing.draw_landmarks(
                        image,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(121, 22, 76), thickness=2, circle_radius=4),
                        mp_drawing.DrawingSpec(color=(250, 44, 250), thickness=2, circle_radius=2)
                    )
                    get_hand_rotation(hand_landmarks)


            cv2.imshow('MediaPipe Hand Tracking', cv2.flip(image, 1))
            if cv2.waitKey(5) & 0xFF == 27:
                break
    cap.release()
    cv2.destroyAllWindows()