import sys
import tkinter as tk
from tkinter import messagebox, ttk
import random

# Перевірка версії Python
if sys.version_info < (3, 6):
    print("Ця програма потребує Python 3.6 або новішої версії")
    sys.exit(1)

# Перевірка наявності Tkinter
try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    print("Помилка: Tkinter не встановлено. Будь ласка, встановіть його для вашої версії Python.")
    sys.exit(1)

BOARD_SIZE = 10
SHIP_SIZES = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]

MISS_SCORE = 1
HIT_SCORE = 2 
KILL_SCORE = 3

class BattleshipGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Морський Бій")
        self.root.state('zoomed')  # на весь екран (Windows)

        # Показуємо вітальне вікно
        self.show_welcome_screen()

        self.player_board = [[' ']*BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.ai_board = [[' ']*BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.ai_ships = []
        self.player_ships = []

        self.player_score = 1000  # Змінено на 1000 балів для тестування
        self.player_turn = True
        self.ship_index = 0  # Індекс корабля, який розставляємо
        self.placing_horizontal = True
        self.current_board_size = BOARD_SIZE  # Додаємо відстеження поточного розміру
        self.selected_ship = None  # Вибраний корабель для переміщення
        self.moving_ship = False   # Режим переміщення корабля
        
        # Розширені бонуси
        self.bonuses = {
            "extra_point": 0,  # Додаткові бали за влучання
            "double_shot": 0,  # Подвійний постріл
            "shield": 0,       # Щит від пострілу противника
            "radar": 0,        # Показує 1 корабель противника
            "expand_board": 0, # Розширення поля на 5х5
            "bomb": 0,        # Бомба, що знищує область 3х3
            "move_ship": 0    # Переміщення корабля
        }
        
        # Додаткові змінні для бонусів
        self.double_shot_active = False
        self.shield_active = False
        self.revealed_ships = []
        self.radar_active = False
        self.radar_animation_cells = []
        self.radar_animation_step = 0
        self.bomb_active = False
        self.bomb_animation_step = 0
        self.protected_cells = set()
        self.move_ship_active = False
        self.ship_to_move = None
        self.moving_horizontal = True
        
        # Створення інтерфейсу
        self.setup_interface()
        self.ai_place_ships()
        self.update_status(f"Розставте кораблі. Розмір: {SHIP_SIZES[self.ship_index]}")
        
    def show_welcome_screen(self):
        welcome = tk.Toplevel(self.root)
        welcome.title("Ласкаво просимо!")
        welcome.geometry("400x300")
        welcome.transient(self.root)  # Робимо вікно модальним
        welcome.grab_set()
        
        # Налаштовуємо центрування
        welcome.geometry("+%d+%d" % (
            self.root.winfo_screenwidth()/2 - 200,
            self.root.winfo_screenheight()/2 - 150))
        
        # Створюємо Canvas для можливості використання різних кольорів тексту
        canvas = tk.Canvas(welcome, width=380, height=280, bg='white')
        canvas.pack(padx=10, pady=10)
        
        # Додаємо український прапор як фон
        canvas.create_rectangle(0, 0, 380, 140, fill='#005BBB', outline='')  # Синій
        canvas.create_rectangle(0, 140, 380, 280, fill='#FFD500', outline='')  # Жовтий
        
        # Додаємо текст
        canvas.create_text(190, 70, text="Made in Ukraine", 
                         font=('Arial', 24, 'bold'), fill='white')
        
        canvas.create_text(190, 120, text="by", 
                         font=('Arial', 18), fill='white')
        
        # Створюємо градієнт для "Gionix"
        colors = ['#FF0000', '#FF7F00', '#FFFF00', '#00FF00', '#0000FF', '#4B0082']
        text = "Gionix"
        x = 190
        y = 170
        for i, char in enumerate(text):
            color = colors[i % len(colors)]
            canvas.create_text(x + (i - len(text)/2) * 20, y, 
                             text=char, font=('Arial', 28, 'bold'), 
                             fill=color)
        
        # Додаємо Discord
        canvas.create_text(190, 220, text="Discord:", 
                         font=('Arial', 16), fill='#7289DA')  # Discord колір
        canvas.create_text(190, 250, text="gionix", 
                         font=('Arial', 16, 'bold'), fill='#7289DA')
        
        # Кнопка закриття
        def close_welcome():
            welcome.destroy()
            
        close_btn = tk.Button(welcome, text="Почати гру!", 
                            command=close_welcome, 
                            font=('Arial', 12, 'bold'))
        close_btn.pack(pady=10)
        
        # Чекаємо поки вікно закриється
        self.root.wait_window(welcome)

    def setup_interface(self):
        # Головний контейнер
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(expand=True)
        
        # Статус та бали зверху
        self.status_frame = tk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = tk.Label(self.status_frame, text="", wraplength=400, font=("Arial", 12))
        self.status_label.pack(pady=5)
        
        self.score_label = tk.Label(self.status_frame, text=f"💰 Бали: {self.player_score}", font=("Arial", 12, "bold"))
        self.score_label.pack(pady=5)
        
        # Фрейми для дошок
        self.boards_frame = tk.Frame(self.main_frame)
        self.boards_frame.pack(fill=tk.X)
        
        self.player_frame = tk.Frame(self.boards_frame)
        self.player_frame.pack(side=tk.LEFT, padx=20)
        
        self.ai_frame = tk.Frame(self.boards_frame)
        self.ai_frame.pack(side=tk.LEFT, padx=20)
        
        # Мітки для дошок
        tk.Label(self.player_frame, text="Ваша дошка").pack()
        tk.Label(self.ai_frame, text="Дошка противника").pack()
        
        # Створюємо кнопки для дошок
        self.player_buttons = []
        self.ai_buttons = []
        
        # Створюємо фрейми для кнопок
        player_board = tk.Frame(self.player_frame)
        player_board.pack()
        
        ai_board = tk.Frame(self.ai_frame)
        ai_board.pack()
        
        for i in range(BOARD_SIZE):
            # Створюємо рядки
            player_row = tk.Frame(player_board)
            player_row.pack()
            
            ai_row = tk.Frame(ai_board)
            ai_row.pack()
            
            row_p = []
            row_ai = []
            
            for j in range(BOARD_SIZE):
                # Кнопки гравця
                btn_p = tk.Button(player_row, width=2, height=1,
                                command=lambda x=j, y=i: self.place_ship(x, y))
                btn_p.pack(side=tk.LEFT)
                # Додаємо обробники для перетягування
                btn_p.bind('<B1-Motion>', lambda e, x=j, y=i: self.on_drag(e, x, y))
                btn_p.bind('<ButtonRelease-1>', lambda e, x=j, y=i: self.on_drop(e, x, y))
                row_p.append(btn_p)
                
                # Кнопки AI
                btn_ai = tk.Button(ai_row, width=2, height=1,
                                 command=lambda x=j, y=i: self.player_fire(x, y))
                btn_ai.pack(side=tk.LEFT)
                row_ai.append(btn_ai)
                
            self.player_buttons.append(row_p)
            self.ai_buttons.append(row_ai)
            
        # Контрольна панель
        self.control_frame = tk.Frame(self.main_frame)
        self.control_frame.pack(side=tk.LEFT, padx=20)
        
        # Кнопки керування
        self.rotate_btn = tk.Button(self.control_frame, text="Повернути корабель",
                                  command=self.toggle_orientation)
        self.rotate_btn.pack(pady=5)
        
        self.shop_btn = tk.Button(self.control_frame, text="Магазин",
                                 command=self.open_shop)
        self.shop_btn.pack(pady=5)

    def update_status(self, message):
        """Оновлює текст статусу гри."""
        self.status_label.config(text=message)
        self.root.update()

    def update_buttons(self):
        for i in range(self.current_board_size):
            for j in range(self.current_board_size):
                if self.player_board[i][j] == 'S':
                    if (j, i) in self.protected_cells:
                        self.player_buttons[i][j].config(bg="gold")
                    else:
                        self.player_buttons[i][j].config(bg="gray")
                elif self.player_board[i][j] == 'X':
                    self.player_buttons[i][j].config(bg="red")
                elif self.player_board[i][j] == 'O':
                    self.player_buttons[i][j].config(bg="blue")
                else:
                    self.player_buttons[i][j].config(bg="SystemButtonFace")
                    
                if self.ai_board[i][j] == 'X':
                    self.ai_buttons[i][j].config(bg="red")
                elif self.ai_board[i][j] == 'O':
                    self.ai_buttons[i][j].config(bg="blue")
                else:
                    self.ai_buttons[i][j].config(bg="SystemButtonFace")

    def toggle_orientation(self):
        self.placing_horizontal = not self.placing_horizontal
        self.update_status(f"Орієнтація: {'горизонтальна' if self.placing_horizontal else 'вертикальна'}")
        
    def place_ship(self, x, y):
        # Якщо ми в режимі переміщення корабля
        if self.moving_ship and self.selected_ship:
            # Спроба розмістити корабель на новому місці
            if self.try_move_ship(x, y):
                messagebox.showinfo("Успіх", "Корабель переміщено!")
                self.moving_ship = False
                self.selected_ship = None
            return

        # Якщо клікнули по кораблю - вибираємо його для переміщення
        if self.player_board[y][x] == 'S' and not self.moving_ship:
            for ship in self.player_ships:
                if (x, y) in ship["coords"]:
                    self.selected_ship = ship
                    self.moving_ship = True
                    # Видаляємо корабель з поточної позиції
                    for sx, sy in ship["coords"]:
                        self.player_board[sy][sx] = ' '
                    self.update_buttons()
                    messagebox.showinfo("Інформація", "Корабель виділено! Тепер клацніть, куди його перемістити.")
                    break
            return

        if self.shield_active and self.player_board[y][x] == 'S':
            # Додаємо захист на конкретну клітинку корабля
            if (x, y) not in self.protected_cells:
                self.protected_cells.add((x, y))
                self.bonuses["shield"] -= 1
                # Змінюємо колір захищеної клітинки
                self.player_buttons[y][x].config(bg="gold")
                self.update_status("Клітинку корабля захищено!")
            else:
                self.update_status("Ця клітинка вже захищена!")
            self.shield_active = False
            return

        if self.ship_index >= len(SHIP_SIZES):
            return
            
        size = SHIP_SIZES[self.ship_index]
        coords = []
        
        # Перевірка можливості розміщення
        for i in range(size):
            if self.placing_horizontal:
                if x + i >= BOARD_SIZE:
                    self.update_status("Корабель виходить за межі поля!")
                    return
                coords.append((x + i, y))
            else:
                if y + i >= BOARD_SIZE:
                    self.update_status("Корабель виходить за межі поля!")
                    return
                coords.append((x, y + i))
                
        # Перевірка перетину з іншими кораблями
        for coord in coords:
            cx, cy = coord
            if self.player_board[cy][cx] != ' ':
                self.update_status("Тут вже є корабель!")
                return
                
        # Розміщення корабля
        for coord in coords:
            cx, cy = coord
            self.player_board[cy][cx] = 'S'
            
        self.player_ships.append({"coords": coords, "hits": 0})
        self.ship_index += 1
        self.update_buttons()
        
        if self.ship_index < len(SHIP_SIZES):
            self.update_status(f"Розставте корабель розміром {SHIP_SIZES[self.ship_index]}")
        else:
            self.update_status("Всі кораблі розставлені. Починайте гру!")
            
    def ai_place_ships(self):
        for size in SHIP_SIZES:
            while True:
                horizontal = random.choice([True, False])
                if horizontal:
                    x = random.randint(0, BOARD_SIZE - size)
                    y = random.randint(0, BOARD_SIZE - 1)
                else:
                    x = random.randint(0, BOARD_SIZE - 1)
                    y = random.randint(0, BOARD_SIZE - size)
                    
                coords = []
                valid = True
                
                for i in range(size):
                    if horizontal:
                        coords.append((x + i, y))
                    else:
                        coords.append((x, y + i))
                        
                for coord in coords:
                    cx, cy = coord
                    if self.ai_board[cy][cx] != ' ':
                        valid = False
                        break
                        
                if valid:
                    for coord in coords:
                        cx, cy = coord
                        self.ai_board[cy][cx] = 'S'
                    self.ai_ships.append({"coords": coords, "hits": 0})
                    break
                    
    def mark_hit(self, ships, x, y):
        for ship in ships:
            if (x, y) in ship["coords"]:
                ship["hits"] += 1
                if ship["hits"] == len(ship["coords"]):
                    self.update_status("Корабель потоплено!")
                    self.player_score += KILL_SCORE
                break
                
    def check_win(self, ships):
        return all(ship["hits"] == len(ship["coords"]) for ship in ships)
        
    def reset_game(self):
        self.root.destroy()
        root = tk.Tk()
        game = BattleshipGame(root)
        root.mainloop()

    def player_fire(self, x, y):
        if self.ship_index < len(SHIP_SIZES):
            self.update_status("Спочатку розставте всі кораблі!")
            return
        if not self.player_turn:
            self.update_status("Чекайте на свій хід.")
            return

        if self.radar_active:
            self.animate_radar_scan(x, y)
            return

        if self.bomb_active:
            self.animate_bomb(x, y)
            return

        cell = self.ai_board[y][x]
        if cell in ['X', 'O']:
            self.update_status("Тут вже стріляли!")
            return

        if cell == 'S':
            self.ai_board[y][x] = 'X'
            self.mark_hit(self.ai_ships, x, y)
            bonus_points = self.bonuses["extra_point"]
            self.player_score += HIT_SCORE + bonus_points
            
            if self.double_shot_active:
                self.update_status("Влучили! У вас ще один постріл (подвійний постріл активний)")
                self.double_shot_active = False
            else:
                self.update_status("Влучили! Ваш хід ще раз.")
            
            self.score_label.config(text=f"💰 Бали: {self.player_score}")
        else:
            self.ai_board[y][x] = 'O'
            self.player_score += MISS_SCORE
            
            if self.double_shot_active:
                self.update_status("Промах! У вас ще один постріл (подвійний постріл активний)")
                self.double_shot_active = False
            else:
                self.update_status("Промах. Хід супротивника.")
                self.player_turn = False
                self.update_buttons()
                self.root.after(1000, self.ai_turn)

        self.update_buttons()
        if self.check_win(self.ai_ships):
            messagebox.showinfo("Виграш", f"Ви виграли! Бали: {self.player_score}")
            self.reset_game()

    def ai_turn(self):
        if self.shield_active:
            self.shield_active = False
            self.update_status("Щит захистив вас від пострілу! Ваш хід.")
            self.player_turn = True
            return

        while True:
            x = random.randint(0, self.current_board_size-1)
            y = random.randint(0, self.current_board_size-1)
            cell = self.player_board[y][x]
            if cell not in ['X', 'O']:
                break

        if cell == 'S':
            # Перевіряємо чи клітинка захищена
            if (x, y) in self.protected_cells:
                # Видаляємо захист з клітинки
                self.protected_cells.remove((x, y))
                self.update_status("Щит на клітинці знищено!")
                # Повертаємо звичайний колір клітинки
                self.player_buttons[y][x].config(bg="gray")
                self.player_turn = True
            else:
                # Звичайна логіка влучання
                self.player_board[y][x] = 'X'
                self.mark_hit(self.player_ships, x, y)
                self.update_status("Супротивник влучив! Він ходить ще.")
                self.update_buttons()
                if self.check_win(self.player_ships):
                    messagebox.showinfo("Програш", "Ви програли!")
                    self.reset_game()
                    return
                self.root.after(1000, self.ai_turn)
        else:
            self.player_board[y][x] = 'O'
            self.update_status("Супротивник промахнувся. Ваш хід.")
            self.player_turn = True
            self.update_buttons()

    def use_bonus(self, bonus_type):
        if bonus_type == "move_ship" and self.bonuses["move_ship"] > 0:
            # Видаляємо старі обробники, якщо вони є
            for row in self.player_buttons:
                for button in row:
                    button.unbind('<Button-1>')
                    button.unbind('<Motion>')
                    button.unbind('<MouseWheel>')

            def select_ship(event):
                button = event.widget
                x = y = None
                # Знаходимо координати кнопки
                for i, row in enumerate(self.player_buttons):
                    if button in row:
                        y = i
                        x = row.index(button)
                        break
                
                if x is not None and y is not None:
                    if self.player_board[y][x] == 'S':
                        # Знаходимо корабель за координатами
                        for ship in self.player_ships:
                            if (x, y) in ship["coords"]:
                                self.start_ship_movement(ship)
                                break
                    else:
                        self.update_status("Виберіть корабель для переміщення!")

            # Додаємо нові обробники
            for row in self.player_buttons:
                for button in row:
                    button.bind('<Button-1>', select_ship)

            self.update_status("Виберіть корабель для переміщення")
            
        elif bonus_type == "shield" and self.bonuses["shield"] > 0:
            self.shield_active = True
            self.update_status("Виберіть клітинку корабля для захисту!")
        elif bonus_type == "double_shot" and self.bonuses["double_shot"] > 0:
            self.bonuses["double_shot"] -= 1
            self.double_shot_active = True
            self.update_status("Активовано подвійний постріл!")
            
        elif bonus_type == "radar" and self.bonuses["radar"] > 0:
            self.bonuses["radar"] -= 1
            self.radar_active = True
            self.update_status("Виберіть область для сканування радаром!")
            return

        elif bonus_type == "bomb" and self.bonuses["bomb"] > 0:
            self.bonuses["bomb"] -= 1
            self.bomb_active = True
            self.update_status("Виберіть область для вибуху бомби!")
            return

    def animate_radar_scan(self, center_x, center_y):
        # Очищаємо попередню анімацію
        for x, y in self.radar_animation_cells:
            if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
                self.ai_buttons[y][x].config(bg="SystemButtonFace")
        
        # Визначаємо клітинки для поточного кроку анімації
        animation_patterns = [
            [(0,0)],  # Центр
            [(0,-1), (1,0), (0,1), (-1,0)],  # Хрест
            [(-1,-1), (1,-1), (1,1), (-1,1)]  # Діагоналі
        ]
        
        if self.radar_animation_step < len(animation_patterns):
            pattern = animation_patterns[self.radar_animation_step]
            self.radar_animation_cells = []
            
            for dx, dy in pattern:
                new_x = center_x + dx
                new_y = center_y + dy
                if 0 <= new_x < BOARD_SIZE and 0 <= new_y < BOARD_SIZE:
                    self.radar_animation_cells.append((new_x, new_y))
                    self.ai_buttons[new_y][new_x].config(bg="cyan")
            
            self.radar_animation_step += 1
            if self.radar_animation_step < len(animation_patterns):
                self.root.after(300, lambda: self.animate_radar_scan(center_x, center_y))
            else:
                self.radar_animation_step = 0
                self.radar_active = False
                # Показуємо результат сканування
                self.show_radar_result(center_x, center_y)
                
    def show_radar_result(self, center_x, center_y):
        # Перевіряємо область 3x3 навколо вибраної точки
        ships_found = False
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                x = center_x + dx
                y = center_y + dy
                if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
                    if self.ai_board[y][x] == 'S':
                        ships_found = True
                        self.ai_buttons[y][x].config(bg="yellow")
        
        # Очищаємо анімацію через 2 секунди
        def clear_radar():
            for x, y in self.radar_animation_cells:
                if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
                    if self.ai_board[y][x] not in ['X', 'O']:
                        self.ai_buttons[y][x].config(bg="SystemButtonFace")
        
        self.root.after(2000, clear_radar)
        
        if ships_found:
            self.update_status("Радар виявив корабель!")
        else:
            self.update_status("Радар нічого не виявив в цій області.")

    def expand_player_board(self):
        if self.current_board_size >= 25:  # Обмеження максимального розміру
            messagebox.showinfo("Помилка", "Досягнуто максимальний розмір поля!")
            return

        new_size = self.current_board_size + 5
        
        # Створюємо нове поле
        new_board = [[' ']*new_size for _ in range(new_size)]
        
        # Копіюємо старе поле
        for y in range(self.current_board_size):
            for x in range(self.current_board_size):
                new_board[y][x] = self.player_board[y][x]
                
        self.player_board = new_board
        self.current_board_size = new_size
        
        # Оновлюємо інтерфейс
        for widget in self.player_frame.winfo_children():
            widget.destroy()
            
        # Створюємо нові кнопки
        tk.Label(self.player_frame, text="Ваша дошка").pack()
        
        player_board = tk.Frame(self.player_frame)
        player_board.pack()
        
        self.player_buttons = []
        for i in range(new_size):
            row_frame = tk.Frame(player_board)
            row_frame.pack()
            row_p = []
            
            for j in range(new_size):
                btn_p = tk.Button(row_frame, width=2, height=1,
                                command=lambda x=j, y=i: self.place_ship(x, y))
                btn_p.pack(side=tk.LEFT)
                row_p.append(btn_p)
                
                # Відновлюємо кольори кнопок
                if self.player_board[i][j] == 'S':
                    btn_p.config(bg="gray")
                elif self.player_board[i][j] == 'X':
                    btn_p.config(bg="red")
                elif self.player_board[i][j] == 'O':
                    btn_p.config(bg="blue")
            
            self.player_buttons.append(row_p)
            
        self.update_status(f"Поле розширено до {new_size}x{new_size}!")

    def open_shop(self):
        shop_win = ShopWindow(self)

    def animate_bomb(self, center_x, center_y):
        # Очищаємо попередню анімацію
        for x, y in self.radar_animation_cells:
            if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
                if self.ai_board[y][x] not in ['X', 'O']:
                    self.ai_buttons[y][x].config(bg="SystemButtonFace")
        
        # Анімація вибуху
        animation_patterns = [
            [(0,0)],  # Центр
            [(0,-1), (1,0), (0,1), (-1,0)],  # Хрест
            [(-1,-1), (1,-1), (1,1), (-1,1)]  # Діагоналі
        ]
        
        if self.bomb_animation_step < len(animation_patterns):
            pattern = animation_patterns[self.bomb_animation_step]
            self.radar_animation_cells = []
            
            for dx, dy in pattern:
                new_x = center_x + dx
                new_y = center_y + dy
                if 0 <= new_x < BOARD_SIZE and 0 <= new_y < BOARD_SIZE:
                    self.radar_animation_cells.append((new_x, new_y))
                    self.ai_buttons[new_y][new_x].config(bg="cyan")
            
            self.bomb_animation_step += 1
            if self.bomb_animation_step < len(animation_patterns):
                self.root.after(200, lambda: self.animate_bomb(center_x, center_y))
            else:
                self.bomb_animation_step = 0
                self.bomb_active = False
                # Застосовуємо вибух
                self.apply_bomb_damage(center_x, center_y)
                
    def apply_bomb_damage(self, center_x, center_y):
        hits = 0
        ships_destroyed = 0
        
        # Перевіряємо область 3x3 навколо вибуху
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                x = center_x + dx
                y = center_y + dy
                if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
                    if self.ai_board[y][x] == 'S':
                        self.ai_board[y][x] = 'X'
                        hits += 1
                        # Перевіряємо чи корабель знищено
                        for ship in self.ai_ships:
                            if (x, y) in ship["coords"]:
                                ship["hits"] += 1
                                if ship["hits"] == len(ship["coords"]):
                                    ships_destroyed += 1
                    elif self.ai_board[y][x] == ' ':
                        self.ai_board[y][x] = 'O'
        
        # Оновлюємо очки
        self.player_score += hits * HIT_SCORE + ships_destroyed * KILL_SCORE
        self.score_label.config(text=f"💰 Бали: {self.player_score}")
        
        # Оновлюємо дошку
        self.update_buttons()
        
        # Виводимо результат
        if hits > 0:
            message = f"Бомба влучила {hits} раз"
            if ships_destroyed > 0:
                message += f" і знищила {ships_destroyed} кораблів"
            self.update_status(message + "!")
        else:
            self.update_status("Бомба не влучила в жоден корабель!")
            
        # Перевіряємо перемогу
        if self.check_win(self.ai_ships):
            messagebox.showinfo("Виграш", f"Ви виграли! Бали: {self.player_score}")
            self.reset_game()

    def start_ship_movement(self, ship):
        self.ship_to_move = ship
        self.move_ship_active = True
        self.moving_horizontal = True
        
        # Видаляємо старий корабель
        for x, y in self.ship_to_move["coords"]:
            self.player_board[y][x] = ' '
        self.update_buttons()
        
        def on_mouse_move(event):
            if not self.move_ship_active:
                return
                
            button = event.widget
            x = y = None
            # Знаходимо координати кнопки
            for i, row in enumerate(self.player_buttons):
                if button in row:
                    y = i
                    x = row.index(button)
                    break
            
            if x is not None and y is not None:
                # Показуємо попередній перегляд корабля
                self.preview_ship_position(x, y)

        def on_mouse_wheel(event):
            if not self.move_ship_active:
                return
            # Змінюємо орієнтацію при прокрутці колеса миші
            self.moving_horizontal = not self.moving_horizontal
            # Оновлюємо попередній перегляд
            button = event.widget
            x = y = None
            for i, row in enumerate(self.player_buttons):
                if button in row:
                    y = i
                    x = row.index(button)
                    break
            if x is not None and y is not None:
                self.preview_ship_position(x, y)

        def on_click(event):
            if not self.move_ship_active:
                return
                
            button = event.widget
            x = y = None
            for i, row in enumerate(self.player_buttons):
                if button in row:
                    y = i
                    x = row.index(button)
                    break
            
            if x is not None and y is not None:
                # Спроба розмістити корабель
                if self.try_move_ship(x, y):
                    # Видаляємо всі обробники після успішного розміщення
                    for row in self.player_buttons:
                        for btn in row:
                            btn.unbind('<Button-1>')
                            btn.unbind('<Motion>')
                            btn.unbind('<MouseWheel>')
                    self.move_ship_active = False
                    self.ship_to_move = None
                    self.bonuses["move_ship"] -= 1

        # Додаємо обробники для всіх кнопок
        for row in self.player_buttons:
            for button in row:
                button.bind('<Motion>', on_mouse_move)
                button.bind('<Button-1>', on_click)
                button.bind('<MouseWheel>', on_mouse_wheel)

        self.update_status("Використовуйте колесо миші для повороту корабля")

    def on_drag(self, event, x, y):
        if not self.dragging_ship and self.player_board[y][x] == 'S':
            # Знаходимо корабель за координатами
            for ship in self.player_ships:
                if (x, y) in ship["coords"]:
                    self.dragging_ship = ship
                    # Видаляємо корабель з поточної позиції
                    for sx, sy in ship["coords"]:
                        self.player_board[sy][sx] = ' '
                    break
        
        if self.dragging_ship:
            # Знаходимо кнопку під курсором
            for i, row in enumerate(self.player_buttons):
                for j, button in enumerate(row):
                    if button == event.widget:
                        # Показуємо попередній перегляд
                        self.preview_ship_position(j, i)
                        break

    def on_drop(self, event, x, y):
        if self.dragging_ship:
            # Спроба розмістити корабель
            success = self.try_move_ship(x, y)
            if not success:
                # Повертаємо корабель на початкову позицію
                for cx, cy in self.dragging_ship["coords"]:
                    self.player_board[cy][cx] = 'S'
            self.dragging_ship = None
            self.update_buttons()

    def preview_ship_position(self, x, y):
        if not self.dragging_ship:
            return
            
        # Спочатку очищаємо попередній перегляд
        self.update_buttons()
        
        ship_size = len(self.dragging_ship["coords"])
        preview_coords = []
        
        # Перевіряємо чи поміститься корабель
        can_place = True
        for i in range(ship_size):
            new_x = x + i
            new_y = y
            
            if new_x >= self.current_board_size or new_y >= self.current_board_size:
                can_place = False
                break
                
            preview_coords.append((new_x, new_y))
            
            # Перевіряємо перетин з іншими кораблями
            if self.player_board[new_y][new_x] == 'S':
                can_place = False
        
        # Показуємо попередній перегляд
        for cx, cy in preview_coords:
            if 0 <= cx < self.current_board_size and 0 <= cy < self.current_board_size:
                self.player_buttons[cy][cx].config(bg="lightgreen" if can_place else "pink")

    def try_move_ship(self, new_x, new_y):
        if not self.selected_ship:
            return False
            
        ship_size = len(self.selected_ship["coords"])
        new_coords = []
        
        # Перевіряємо чи поміститься корабель
        for i in range(ship_size):
            if new_x + i >= self.current_board_size:
                messagebox.showinfo("Помилка", "Корабель виходить за межі поля!")
                # Повертаємо корабель на місце
                for x, y in self.selected_ship["coords"]:
                    self.player_board[y][x] = 'S'
                self.update_buttons()
                return False
            new_coords.append((new_x + i, new_y))
        
        # Перевіряємо перетин з іншими кораблями
        for coord in new_coords:
            cx, cy = coord
            if self.player_board[cy][cx] == 'S':
                messagebox.showinfo("Помилка", "Тут вже є інший корабель!")
                # Повертаємо корабель на місце
                for x, y in self.selected_ship["coords"]:
                    self.player_board[y][x] = 'S'
                self.update_buttons()
                return False
        
        # Розміщуємо корабель на новому місці
        for x, y in new_coords:
            self.player_board[y][x] = 'S'
            
        # Оновлюємо координати корабля
        self.selected_ship["coords"] = new_coords
        
        self.update_buttons()
        return True

class ShopWindow:
    def __init__(self, game):
        self.game = game
        self.items = [
            {
                "name": "Додатковий бал",
                "description": "+1 бал за кожне влучання",
                "cost": 10,
                "key": "extra_point",
                "max": 5
            },
            {
                "name": "Подвійний постріл",
                "description": "Можливість стріляти двічі за хід",
                "cost": 20,
                "key": "double_shot",
                "max": 3
            },
            {
                "name": "Щит",
                "description": "Захищає клітинку корабля від одного пострілу",
                "cost": 15,
                "key": "shield",
                "max": 3
            },
            {
                "name": "Радар",
                "description": "Показує розташування кораблів в області 3х3",
                "cost": 25,
                "key": "radar",
                "max": 2
            },
            {
                "name": "Розширення поля",
                "description": "Збільшує ваше поле на 5х5 клітинок",
                "cost": 100,
                "key": "expand_board",
                "max": 3
            },
            {
                "name": "Бомба",
                "description": "Знищує всі кораблі в області 3х3",
                "cost": 50,
                "key": "bomb",
                "max": 2
            },
            {
                "name": "Переміщення корабля",
                "description": "Дозволяє перемістити корабель в нову позицію",
                "cost": 40,
                "key": "move_ship",
                "max": 3
            }
        ]

        self.win = tk.Toplevel(game.root)
        self.win.title("Магазин бонусів")
        self.win.geometry("400x600")
        self.win.grab_set()

        # Заголовок
        title_frame = tk.Frame(self.win)
        title_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(title_frame, text="Магазин бонусів", 
                font=("Arial", 20, "bold")).pack(pady=10)
        
        self.score_label = tk.Label(title_frame, 
                                  text=f"Ваші бали: {self.game.player_score}", 
                                  font=("Arial", 14))
        self.score_label.pack(pady=5)

        # Контейнер для прокрутки
        container = tk.Frame(self.win)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Канвас і скролбар
        self.canvas = tk.Canvas(container)
        scrollbar = tk.Scrollbar(container, orient="vertical", 
                               command=self.canvas.yview)
        
        # Фрейм для елементів магазину
        self.scrollable_frame = tk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Створюємо вікно в канвасі для скролінгу
        self.canvas.create_window((0, 0), window=self.scrollable_frame, 
                                anchor="nw", width=380)
        
        # Налаштовуємо прокрутку
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Додаємо обробник колеса миші
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Пакуємо канвас і скролбар
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Додаємо товари
        self.create_shop_items()
        
        # Зберігаємо посилання на вікно в грі для можливості закриття
        self.game.shop_window = self
        
        # Обробник закриття вікна
        self.win.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _on_mousewheel(self, event):
        # Прокрутка на Windows (-120 або 120)
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def create_shop_items(self):
        for item in self.items:
            # Фрейм для товару
            item_frame = tk.Frame(self.scrollable_frame, relief="solid", 
                                borderwidth=1)
            item_frame.pack(fill=tk.X, padx=10, pady=5)

            # Інформація про товар
            tk.Label(item_frame, text=item['name'], 
                    font=("Arial", 12, "bold")).pack(pady=5)
            tk.Label(item_frame, text=item['description'], 
                    font=("Arial", 10)).pack()
            tk.Label(item_frame, 
                    text=f"У вас: {self.game.bonuses[item['key']]} / {item['max']}", 
                    font=("Arial", 10)).pack()
            tk.Label(item_frame, text=f"Ціна: {item['cost']} балів", 
                    font=("Arial", 10)).pack(pady=5)

            # Кнопки
            button_frame = tk.Frame(item_frame)
            button_frame.pack(pady=5)

            buy_btn = tk.Button(button_frame, text="Купити", 
                              command=lambda i=item: self.buy_item(i))
            buy_btn.pack(side=tk.LEFT, padx=5)
            
            if self.game.bonuses[item['key']] >= item['max']:
                buy_btn.configure(state="disabled")

            if item['key'] in ['double_shot', 'shield', 'radar', 'bomb']:
                use_btn = tk.Button(button_frame, text="Використати",
                    command=lambda k=item['key']: self.use_bonus(k))
                use_btn.pack(side=tk.LEFT, padx=5)
                
                if self.game.bonuses[item['key']] <= 0:
                    use_btn.configure(state="disabled")

    def on_closing(self):
        self.game.shop_window = None
        self.win.destroy()

    def buy_item(self, item):
        if self.game.player_score >= item["cost"]:
            if self.game.bonuses[item["key"]] >= item["max"]:
                messagebox.showinfo("Помилка", 
                                  "Досягнуто максимальну кількість цього бонусу!")
                return
                
            self.game.player_score -= item["cost"]
            self.game.bonuses[item["key"]] += 1
            
            if item["key"] == "expand_board":
                self.game.expand_player_board()
                
            self.game.score_label.config(text=f"Бали: {self.game.player_score}")
            self.score_label.config(text=f"Ваші бали: {self.game.player_score}")
            
            messagebox.showinfo("Успіх", f"Ви купили {item['name']}!")
            self.win.destroy()
            self.game.open_shop()
        else:
            messagebox.showinfo("Помилка", "Недостатньо балів для покупки!")

    def use_bonus(self, bonus_type):
        self.game.use_bonus(bonus_type)
        self.win.destroy()
        self.game.open_shop()

if __name__ == "__main__":
    try:
        root = tk.Tk()
        game = BattleshipGame(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Критична помилка", f"Програма не може запуститися: {str(e)}")
        sys.exit(1)
