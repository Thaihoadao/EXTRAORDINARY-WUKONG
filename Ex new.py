import pygame
import cv2
import sys
import random
import numpy as np
import mediapipe as mp

# Constants
SCREEN_WIDTH = 580
SCREEN_HEIGHT = 620
CAMERA_WIDTH = 640  # Width of the camera feed on the side
CAMERA_HEIGHT = 505  # Same height as game screen
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH + CAMERA_WIDTH, SCREEN_HEIGHT))  # Increased width for camera
pygame.display.set_caption("Extraordinary wukong - Hand Control")
pygame.mixer.init()

# Load resources (images) once during initialization
player_image = pygame.image.load("player.png")  # Player sprite
player_image = pygame.transform.scale(player_image, (115, 120))  # Scale player image

background_image = pygame.image.load("background.png")  # Background image
background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))  # Scale to fit screen

obstacle_image = pygame.image.load("obstacle.png")  # RED obstacle image
points_image = pygame.image.load("point.png")  # GREEN obstacle image

menu_image = pygame.image.load("menu.png") # Menu image
menu_image = pygame.transform.scale(menu_image, (SCREEN_WIDTH, SCREEN_HEIGHT))  # Scale to fit screen

tutorial_bg_image = pygame.image.load("tutorial_bg.png")
tutorial_bg_image = pygame.transform.scale(tutorial_bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Load sound files
collision_sound = pygame.mixer.Sound("collision.wav")  # Sound effect for collision
pygame.mixer.music.load("theme_2.wav")  # Theme music
pygame.mixer.music.set_volume(0.5)  # Set the volume (optional)

# Game variables
player_x = SCREEN_WIDTH // 3
player_y = SCREEN_HEIGHT - 120
player_velocity_x = 0  # Add horizontal velocity for smoother movement
score = 1
difficulty = 1
obstacle_speed = 4
lives = 3
obstacles = []
obstacle_spawn_time = pygame.time.get_ticks()  # Track time for spawning obstacles
first_obstacle_spawned = False  # Flag to check if the first obstacle has appeared
game_running = False

# Initialize camera using OpenCV
cap = cv2.VideoCapture(0)

# Initialize MediaPipe Hands module (with optimization)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    min_detection_confidence=0.5,  # Lower detection confidence for faster processing
    min_tracking_confidence=0.5,   # Lower tracking confidence for faster processing
    max_num_hands=1                # Only track one hand to reduce computation
)
mp_drawing = mp.solutions.drawing_utils

# Create new obstacle
def create_obstacle():
    size = random.randint(40, 70)  # Random size for the obstacle
    x_pos = random.randint(0, SCREEN_WIDTH - size)  # Random horizontal position
    y_pos = -size  # Spawn above the screen (just out of view)
    speed = obstacle_speed + difficulty * 0.5  # Speed increases with difficulty
    color = RED if random.random() > 0.2 else GREEN  # Randomly choose obstacle color
    return {'rect': pygame.Rect(x_pos, y_pos, size, size), 'speed': speed, 'color': color}

# Function to detect hand position
def detect_hand_position():
    ret, frame = cap.read()
    
    if not ret:
        return None, None

    # Resize the frame for faster processing
    small_frame = cv2.resize(frame, (640, 480))  # Reduce the resolution to improve performance
    
    # Convert the frame to RGB (MediaPipe uses RGB, OpenCV uses BGR)
    frame_rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    
    # Process the frame to get hand landmarks
    results = hands.process(frame_rgb)

    if results.multi_hand_landmarks:
        # Only return the first hand detected
        hand_landmarks = results.multi_hand_landmarks[0]
        mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
        wrist_x = int(hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x * SCREEN_WIDTH)
        wrist_y = int(hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].y * SCREEN_HEIGHT)
        
        # Flip the hand landmarks back to match the mirrored webcam (flip the x-coordinate)
        wrist_x = CAMERA_WIDTH - wrist_x  # Flip the X-axis
        
        return (wrist_x, wrist_y), hand_landmarks
    return None, None

# Function to draw landmarks on the webcam feed
def draw_hand_landmarks(frame, hand_landmarks):
    # Draw lines connecting the hand landmarks based on MediaPipe's predefined connections
    for connection in mp_hands.HAND_CONNECTIONS:
        start_idx, end_idx = connection

        # Get start and end coordinates for the connection
        start = hand_landmarks.landmark[start_idx]
        end = hand_landmarks.landmark[end_idx]

        # Convert to screen coordinates
        start_x = int(start.x * CAMERA_WIDTH)
        start_y = int(start.y * CAMERA_HEIGHT)
        end_x = int(end.x * CAMERA_WIDTH)
        end_y = int(end.y * CAMERA_HEIGHT)

        # Flip the X coordinates to match the mirrored webcam
        start_x = CAMERA_WIDTH - start_x
        end_x = CAMERA_WIDTH - end_x

        # Draw the line between the landmarks
        pygame.draw.line(frame, WHITE, (start_x, start_y), (end_x, end_y), 2)

    # Draw the landmarks as small circles
    for landmark in hand_landmarks.landmark:
        x = int(landmark.x * CAMERA_WIDTH)
        y = int(landmark.y * CAMERA_HEIGHT)

        # Flip the X coordinate to match the mirrored frame
        x = CAMERA_WIDTH - x

        pygame.draw.circle(frame, RED, (x, y), 5)

    return frame


# Function to display the menu screen
def display_menu():
    font = pygame.font.Font(None, 1)
    title_text = font.render("Extrordinary Wukong", True, BLACK)
    font = pygame.font.Font(None, 40)
    play_text = font.render("PLAY", True, BLACK)
    font = pygame.font.Font(None, 40)
    tutorial_text = font.render("TUTORIAL", True, BLACK)
    
    

    # Clear the webcam area
    pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH, 0, CAMERA_WIDTH, SCREEN_HEIGHT))

    # Draw the menu
    screen.blit(menu_image, (0, 0)) # Menu image
    screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))
    screen.blit(play_text, (SCREEN_WIDTH // 2 - play_text.get_width() // 2, SCREEN_HEIGHT // 2 +9))
    screen.blit(tutorial_text, (SCREEN_WIDTH // 2 - tutorial_text.get_width() // 2, SCREEN_HEIGHT // 2 +114))

    pygame.display.flip()

# Function to handle menu actions
def handle_menu():
    menu_running = True
    while menu_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse click
                    mouse_x, mouse_y = pygame.mouse.get_pos()

                    # Check if the "Play" button was clicked
                    if SCREEN_WIDTH // 2 - 100 < mouse_x < SCREEN_WIDTH // 2 + 100 and SCREEN_HEIGHT // 2 - 30 < mouse_y < SCREEN_HEIGHT // 2 +30:
                        return 'play'  # Return 'play' to start the game
                    
                    # Check if the "Tutorial" button was clicked
                    elif SCREEN_WIDTH // 2 - 100 < mouse_x < SCREEN_WIDTH // 2 + 100 and SCREEN_HEIGHT // 2 + 30 < mouse_y < SCREEN_HEIGHT // 2 + 140:
                        return 'tutorial'  # Return 'tutorial' for tutorial screen

        display_menu()

def display_tutorial():
    font = pygame.font.Font(None, 1)
    tutorial_texts = [
        "Welcome "
    ]
    tutorial_running = True
    while tutorial_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                tutorial_running = False
                break

        screen.blit(tutorial_bg_image, (0, 0))
        y_offset = 50
        for line in tutorial_texts:
            text = font.render(line, True, BLACK)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, y_offset))
            y_offset += 40

        pygame.display.flip()
        clock.tick(60)
    
    # Render and display the tutorial text
    y_offset = 50
    for line in tutorial_texts:
        text = font.render(line, True, RED)
        screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, y_offset))
        y_offset += 40

    pygame.display.flip()

    # Wait for player to click anywhere to return to the main menu
    tutorial_running = True
    while tutorial_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:  # Wait for mouse click
                tutorial_running = False  # Close the tutorial and return to the menu
                break
        clock.tick(60)

# Game Over screen function
def display_game_over(score):
    pygame.mixer.music.stop()  # Stop the background music when game is over
    screen.fill((0, 0, 0))  # Fill screen with black background
    font = pygame.font.Font(None, 72)
    
    # Render the "Game Over" message
    game_over_text = font.render("GAME OVER", True, (255, 0, 0))  # Red color
    text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
    screen.blit(game_over_text, text_rect)
    
    # Render the final score
    font = pygame.font.Font(None, 48)
    score_text = font.render(f"Final Score: {score}", True, (255, 255, 255))
    score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(score_text, score_rect)
    
    # Render the restart or quit option
    restart_text = font.render("R: Restart, M: Menu, Q: Quit", True, (255, 255, 255))
    restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 1.5))
    screen.blit(restart_text, restart_rect)
    
    pygame.display.flip()  # Update the display
    
    # Wait for player input to restart or quit
    waiting_for_input = True
    while waiting_for_input:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return 'restart'  # Player wants to restart
                elif event.key == pygame.K_q:
                    pygame.quit()  # Quit the game
                    sys.exit()  # Exit the program completely
                elif event.key == pygame.K_m:
                    return 'menu'

# Function to reset game variables for restart
def reset_game():
    global player_x, player_y, player_velocity_x, score, difficulty, obstacle_speed, lives, obstacles, obstacle_spawn_time, first_obstacle_spawned, game_running
    player_x = SCREEN_WIDTH // 2
    player_y = SCREEN_HEIGHT - 120
    player_velocity_x = 0  # Reset horizontal velocity
    score = 1
    difficulty = 1
    obstacle_speed = 3
    lives = 3
    obstacles.clear()  # Clear all existing obstacles
    obstacle_spawn_time = pygame.time.get_ticks()  # Reset spawn timer
    first_obstacle_spawned = False
    game_running = False  # Reset running state


# Main game loop
clock = pygame.time.Clock()

# Display the menu and handle user input
menu_choice = handle_menu()  # Handle the menu once at the start

while True:
    if menu_choice == 'play':
        pygame.mixer.music.play(-1, 0.0)  # Start background music (looped)
        reset_game()  # Reset the game variables before starting
        menu_choice = None

        # Start the game
        running = True
        while running:
            # Draw the background image first
            screen.blit(background_image, (0, 0))

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Hand detection and control logic
            hand_pos, hand_landmarks = detect_hand_position()
            if hand_pos and hand_landmarks:
                cx, cy = hand_pos

                # Player movement based on hand position
                if cx < SCREEN_WIDTH // 3:
                    player_velocity_x = -14  # Move left with smooth velocity
                elif cx > 2 * SCREEN_WIDTH // 3:
                    player_velocity_x = 14  # Move right with smooth velocity
                else:
                    player_velocity_x = 0  # Stop moving horizontally if hand is in the middle

            # Horizontal movement
            player_x += player_velocity_x
            player_x = max(0, min(SCREEN_WIDTH - 100, player_x))  # Keep player within bounds

            # Spawn obstacles at controlled intervals using time tracking
            if pygame.time.get_ticks() - obstacle_spawn_time > 1600:  # Spawn every 1 second
                obstacles.append(create_obstacle())
                obstacle_spawn_time = pygame.time.get_ticks()

            # Check if the first obstacle has appeared
            if not first_obstacle_spawned and obstacles:
                first_obstacle_spawned = True  # Mark that the first obstacle has appeared

            # Update obstacle positions and handle collisions
            for obstacle in obstacles[:]:
                obstacle['rect'].y += obstacle['speed']

                # Efficient collision detection using the bounding box
                if obstacle['rect'].colliderect(pygame.Rect(player_x + 50, player_y, 70, 70)):
                    if obstacle['color'] == RED:
                        lives -= 1  # Red obstacle collision
                        collision_sound.play()  # Play collision sound
                    elif obstacle['color'] == GREEN:
                        score += 10  # GREEN obstacle collision
                    obstacles.remove(obstacle)

                    if lives == 0:
                        # Trigger the Game Over screen
                        result = display_game_over(score)
                        if result == 'restart':
                            reset_game()  # Reset the game variables for a fresh restart
                            pygame.mixer.music.play(-1, 0.0)  # Start background music again after restart
                            break  # Restart the game
                        elif result == 'quit':
                            running = False  # Quit the game
                            break
                        elif result == 'menu':
                            menu_choice = 'menu'
                            running = False

                if obstacle['rect'].y > SCREEN_HEIGHT:
                    obstacles.remove(obstacle)
                    score += 1

            # Adjust difficulty and obstacle speed
            difficulty = score // 20 + 1
            obstacle_speed = 3 + difficulty * 0.5

            # Draw player and obstacles
            screen.blit(player_image, (player_x, player_y))  # Draw player sprite

            for obstacle in obstacles:
                if obstacle['color'] == RED:
                    screen.blit(pygame.transform.scale(obstacle_image, (obstacle['rect'].width, obstacle['rect'].height)),
                                obstacle['rect'].topleft)
                else:
                    screen.blit(pygame.transform.scale(points_image, (obstacle['rect'].width, obstacle['rect'].height)),
                                obstacle['rect'].topleft)

            # Display score and lives
            font = pygame.font.Font(None, 50)
            score_text = font.render(f"Score: {score}", True, WHITE)
            screen.blit(score_text, (10, 10))

            lives_text = font.render(f"Lives: {lives}", True, WHITE)
            screen.blit(lives_text, (SCREEN_WIDTH - 150, 10))

            # Capture and display mirrored webcam feed
            ret, frame = cap.read()
            if ret:
                # Convert to RGB (for pygame rendering)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Rotate the frame for proper display in pygame (top to bottom)
                frame = np.rot90(frame)

                # Convert numpy array to a pygame surface
                frame = pygame.surfarray.make_surface(frame)

                # Draw hand landmarks on the mirrored frame
                if hand_landmarks:
                    frame = draw_hand_landmarks(frame, hand_landmarks)

                # Draw the mirrored webcam feed on the right side panel
                screen.blit(frame, (SCREEN_WIDTH, 0))

            pygame.display.flip()
            clock.tick(60)

    elif menu_choice == 'tutorial':
        display_tutorial()
        menu_choice = handle_menu()  # Return to menu after the tutorial is done
    
    elif menu_choice == 'menu' or menu_choice is None:
        menu_choice = handle_menu()

# Cleanup
cap.release()
cv2.destroyAllWindows()
pygame.mixer.music.stop()  # Stop music when exiting the game
pygame.quit()
sys.exit()