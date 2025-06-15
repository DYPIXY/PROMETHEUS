import cv2
import mediapipe as mp
import math

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# Variáveis para rastreamento de estado
thumb_middle_touching = False
middle_finger_tip_raised = False

wrist_position = None
wrist_position_delta = None

# Limiar de distância para considerar o toque
TOUCH_THRESHOLD = 0.2 # Ajuste este valor conforme necessário (baseado em coordenadas normalizadas)

# Para webcam input:
cap = cv2.VideoCapture(0)

with mp_hands.Hands(
    min_detection_confidence=0.7, # Aumentei a confiança para detecção mais estável
    min_tracking_confidence=0.7,
    max_num_hands=1) as hands: # Aumentei a confiança para rastreamento mais estável
    
    # Variáveis para armazenar as posições anteriores
    prev_middle_finger_tip_y = None
    
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Ignorando quadro vazio da câmera.")
            continue

        # Para melhorar o desempenho, opcionalmente marque a imagem como não gravável.
        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


        '''


        SERVIDOR

        
        '''
        results = hands.process(image)

        # Desenha as anotações da mão na imagem.
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Obtenha os landmarks específicos
                thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP] # Usei o dedo indicador como exemplo, mas você pode usar o dedo médio se preferir
                wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
                
                middle_finger_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP] # Posição da base do dedo médio

                catetoZ = middle_finger_mcp.z - wrist.z
                catetoY = middle_finger_mcp.y - wrist.y

                anguloPlanoZY = abs(math.degrees(math.atan2(catetoY, catetoZ)))
                # print(f"Ângulo entre pulso e dedo médio: {anguloPlanoZY:.2f} graus")

                thumb_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP] # Posição da base do polegar

                catetoX = thumb_mcp.x - wrist.x
                catetoZ = thumb_mcp.z - wrist.z

                anguloPlanoZY = abs(math.degrees(math.atan2(catetoX, catetoZ)))
                # print(f"Ângulo entre pulso e polegar: {anguloPlanoZY:.2f} graus")

                if (wrist_position is None ):
                    wrist_position = (wrist.x, wrist.y, wrist.z)


                wrist_position_delta = (wrist.x - wrist_position[0], wrist.y - wrist_position[1], wrist.z - wrist_position[2])
                print(f"Posição do pulso: {wrist_position}, Delta: {wrist_position_delta}")


                # --- Lógica de detecção de toque entre polegar e dedo médio ---
                
                # Calcule a distância Euclidiana entre as pontas do polegar e do dedo médio
                distance = math.sqrt(
                    (thumb_tip.x - index_finger_tip.x)**2 +
                    (thumb_tip.y - index_finger_tip.y)**2 +
                    (thumb_tip.z - index_finger_tip.z)**2
                )

                if distance < TOUCH_THRESHOLD:
                    if not thumb_middle_touching:
                        print("Polegar e dedo médio ESTÃO se tocando!")
                        thumb_middle_touching = True
                else:
                    if thumb_middle_touching:
                        print("Polegar e dedo médio NÃO estão mais se tocando!")
                        thumb_middle_touching = False

                # --- Lógica de detecção de elevação/abaixamento da ponta do dedo médio ---
                
                current_index_finger_tip_y = index_finger_tip.y

                print(index_finger_tip)
                '''
                if prev_index_finger_tip_y is not None:
                    # Se o Y atual for menor que o Y anterior, o dedo está subindo (Y no topo é menor)
                    if current_index_finger_tip_y < prev_index_finger_tip_y - 0.02: # Adicione um pequeno limiar para evitar flutuações
                        if not index_finger_tip_raised:
                            print("Ponta do dedo médio SUBINDO!")
                            index_finger_tip_raised = True
                    # Se o Y atual for maior que o Y anterior, o dedo está descendo
                    elif current_index_finger_tip_y > prev_index_finger_tip_y + 0.02:
                        if index_finger_tip_raised: # Só imprime se estava "levantado" antes
                            print("Ponta do dedo médio DESCENDO!")
                            index_finger_tip_raised = False
                '''
                
                prev_index_finger_tip_y = current_index_finger_tip_y

                # Desenhe apenas os landmarks relevantes (polegar e dedo médio)
                # Você pode personalizar o desenho para focar apenas neles, se quiser.
                # Para simplificar, vou desenhar todos os landmarks, mas você pode usar DrawingSpec
                # para destacar apenas os que te interessam.
                
                # Personalizando o desenho para destacar polegar e dedo médio
                for idx, landmark in enumerate(hand_landmarks.landmark):
                    if idx in [
                        mp_hands.HandLandmark.THUMB_TIP,
                        mp_hands.HandLandmark.INDEX_FINGER_TIP,
                        mp_hands.HandLandmark.WRIST
                    ]:
                        # Desenha um círculo maior e de cor diferente para os landmarks de interesse
                        cv2.circle(image, (int(landmark.x * image.shape[1]), int(landmark.y * image.shape[0])), 8, (0, 255, 255), -1) # Amarelo
                    else:
                        continue
                # Desenha as conexões da mão (opcional, pode remover se quiser um visual mais limpo)
                mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(121, 22, 76), thickness=2, circle_radius=4),
                    mp_drawing.DrawingSpec(color=(250, 44, 250), thickness=2, circle_radius=2)
                )

        # Flip the image horizontally for a selfie-view display.
        cv2.imshow('MediaPipe Hand Tracking - Thumb and Middle Finger', cv2.flip(image, 1))
        if cv2.waitKey(5) & 0xFF == 27:
            break
cap.release()
cv2.destroyAllWindows()