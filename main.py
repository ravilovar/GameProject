import os
import sys
import pygame
import pygame_gui
import random
import datetime as dt
from db_requests import db_save_result, db_select_result
from camera_class import Camera


FPS = 20
size = WIDTH, HEIGHT = 700, 600
STEP = 50
tile_width = tile_height = 50
GRAVITY = 1
DATA_DIR = 'data'
IMG_DIR = 'data/img'


def load_image(name, colorkey=None):
    fullname = os.path.join(IMG_DIR, name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


class Particle(pygame.sprite.Sprite):
    def __init__(self, sprites, pos, dx, dy):
        # сгенерируем частицы разного размера
        self.fire = [tile_images['fire']]
        for scale in (15, 20, 30):
            self.fire.append(pygame.transform.scale(self.fire[0], (scale, scale)))

        super().__init__(*sprites)
        self.image = random.choice(self.fire)
        self.rect = self.image.get_rect()

        # у каждой частицы своя скорость — это вектор
        self.velocity = [dx, dy]
        # и свои координаты
        self.rect.x, self.rect.y = pos

        # гравитация будет одинаковой (значение константы)
        self.gravity = GRAVITY

    def update(self):
        # применяем гравитационный эффект:
        # движение с ускорением под действием гравитации
        self.velocity[1] += self.gravity
        # перемещаем частицу
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        # убиваем, если частица ушла за экран
        screen_rect = (0, 0, WIDTH, HEIGHT)
        if not self.rect.colliderect(screen_rect):
            self.kill()


def create_particles(sprites, position):
    # количество создаваемых частиц
    particle_count = 20
    # возможные скорости
    numbers = range(-26, 26)
    for _ in range(particle_count):
        Particle(sprites, position, random.choice(numbers), random.choice(numbers))


class Tile(pygame.sprite.Sprite):
    def __init__(self, tiles_group, tile_type, pos_x, pos_y):
        super().__init__(*tiles_group)
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)


class Bag(pygame.sprite.Sprite):
    def __init__(self, tiles_group, tile_type, pos_x, pos_y):
        super().__init__(*tiles_group)
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        self.mystery_bag = MysteryPlayer(
            tile_width * pos_x, tile_height * pos_y, self.rect.width, self.rect.height)
        self.flower = False


class MysteryPlayer(pygame.sprite.Sprite):
    def __init__(self, coor_x, coor_y, width, height):
        super().__init__()
        self.rect = pygame.Rect(coor_x, coor_y, width, height)


class Player(pygame.sprite.Sprite):
    def __init__(self, tiles_group, pos_x, pos_y):
        super().__init__(*tiles_group)
        self.image = tile_images['hero']
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        self.pos = (pos_x, pos_y)
        self.mystery_player = MysteryPlayer(
            tile_width * pos_x, tile_height * pos_y, self.rect.width, self.rect.height)
        self.push = False

    def update_skin(self, direction):
        if self.push is False:
            if direction == 'UP':
                self.image = tile_images['hero_up']
            elif direction == 'DOWN':
                self.image = tile_images['hero']
            elif direction == 'RIGHT':
                self.image = tile_images['hero_right']
            elif direction == 'LEFT':
                self.image = tile_images['hero_left']
        if self.push is True:
            if direction == 'UP':
                self.image = tile_images['hero_up_push']
            elif direction == 'DOWN':
                self.image = tile_images['hero_push']
            elif direction == 'RIGHT':
                self.image = tile_images['hero_right_push']
            elif direction == 'LEFT':
                self.image = tile_images['hero_left_push']


def load_level(filename):
    filename = filename
    # читаем уровень, убирая символы перевода строки
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]
    # и подсчитываем максимальную длину
    max_width = max(map(len, level_map))
    # дополняем каждую строку пустыми клетками ('.')
    return list(map(lambda x: x.ljust(max_width, '.'), level_map))


def terminate():
    pygame.quit()
    sys.exit()


def start_screen():
    player, level = 'Имя игрока', '0 ТЕСТ'
    fon = pygame.transform.scale(load_image('open-image.png'), (WIDTH, HEIGHT))
    game_screen.blit(fon, (0, 0))
    manager_start = pygame_gui.UIManager((WIDTH, HEIGHT))
    pygame_gui.elements.ui_drop_down_menu.UIDropDownMenu(
        options_list=['0 ТЕСТ', '1 уровень', '2 уровень', '3 уровень'], starting_option=level,
        relative_rect=pygame.Rect((10, 220), (100, 25)), manager=manager_start
    )
    text = [
        'Перемести ведра с водой в пустые лужи и сад зацветёт!',
        '',
        'Управление героем стрелками',
        'G - начать новую игру',
        'N - перезапустить уровень',
        'T - таблица результатов'
    ]
    pygame_gui.elements.UITextBox(
        relative_rect=pygame.Rect((10, 10), (260, 200)),
        html_text='\n'.join(text), manager=manager_start
    )
    pygame_gui.elements.UITextEntryLine(
        relative_rect=pygame.Rect((110, 220), (160, 25)), initial_text=player,
        manager=manager_start
    )

    while True:
        time_delta = clock.tick(FPS) / 1000.0
        for start_event in pygame.event.get():
            if start_event.type == pygame.QUIT:
                pygame_gui.windows.UIConfirmationDialog(
                    rect=pygame.Rect((200, 120), (300, 200)),
                    manager=manager_start,
                    window_title='Подтверждение',
                    action_long_desc='Вы уверены, что хотите выйти?',
                    action_short_name='ОК',
                    blocking=True

                )
            if start_event.type == pygame.USEREVENT:
                if start_event.user_type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
                    terminate()
                if start_event.user_type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
                    player = start_event.text
                if start_event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                    level = start_event.text
            if start_event.type == pygame.KEYDOWN:
                if start_event.key == pygame.K_g:
                    return player, level.split()[0]
                if start_event.key == pygame.K_t:
                    result_table_screen()
            manager_start.process_events(start_event)

        game_screen.blit(fon, (0, 0))
        manager_start.update(time_delta)
        manager_start.draw_ui(game_screen)
        pygame.display.flip()


def result_table_screen():
    fon = pygame.transform.scale(load_image('open-image.png'), (WIDTH, HEIGHT))
    game_screen.blit(fon, (0, 0))
    manager_table = pygame_gui.UIManager((WIDTH, HEIGHT))
    text = db_select_result()
    pygame_gui.elements.UITextBox(
        relative_rect=pygame.Rect((20, 20), (WIDTH // 2 + 80, HEIGHT - 40)),
        html_text='\n'.join(text), manager=manager_table
    )

    while True:
        time_delta = clock.tick(FPS) / 1000.0
        for table_event in pygame.event.get():
            if table_event.type == pygame.QUIT:
                pygame_gui.windows.UIConfirmationDialog(
                    rect=pygame.Rect((200, 120), (300, 200)),
                    manager=manager_table,
                    window_title='Подтверждение',
                    action_long_desc='Вы уверены, что хотите выйти?',
                    action_short_name='ОК',
                    blocking=True

                )
            if table_event.type == pygame.USEREVENT:
                if table_event.user_type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
                    terminate()
            if table_event.type == pygame.KEYDOWN and table_event.key == pygame.K_SPACE:
                return
            manager_table.process_events(table_event)

        game_screen.blit(fon, (0, 0))
        manager_table.update(time_delta)
        manager_table.draw_ui(game_screen)
        pygame.display.flip()


class Game:
    def __init__(self, level):
        # группы спрайтов
        self.all_sprites = pygame.sprite.Group()
        self.tiles_group = pygame.sprite.Group()
        self.wall_group = pygame.sprite.Group()
        self.bag_group = pygame.sprite.Group()
        self.store_group = pygame.sprite.Group()
        self.player_group = pygame.sprite.Group()
        self.fire = pygame.sprite.Group()

        new_player, x, y = None, None, None
        for y in range(len(level)):
            for x in range(len(level[y])):
                if level[y][x] == '.':
                    Tile([self.all_sprites, self.tiles_group], 'empty', x, y)
                elif level[y][x] == '#':
                    Tile([self.all_sprites, self.wall_group], 'wall', x, y)
                elif level[y][x] == '*':
                    Tile([self.all_sprites, self.store_group], 'store', x, y)
                elif level[y][x] == '+':
                    Tile([self.all_sprites, self.tiles_group], 'empty', x, y)
                    Bag([self.all_sprites, self.bag_group], 'bag', x, y)
                elif level[y][x] == '@':
                    Tile([self.all_sprites, self.tiles_group], 'empty', x, y)
                    new_player = Player([self.all_sprites, self.player_group], x, y)
                    level[y] = level[y][:x] + '.' + level[y][x + 1:]
        # вернем игрока, а также размер поля в клетках
        self.player, self.x, self.y = new_player, x, y
        self.over = None
        self.time = dt.datetime.now()

    def render(self, screen):
        self.tiles_group.draw(screen)
        self.wall_group.draw(screen)
        self.store_group.draw(screen)
        self.bag_group.draw(screen)
        self.player_group.draw(screen)
        self.fire.update()
        self.fire.draw(screen)

    def move_player(self, direction, step):
        if self.allow_move_player(direction, step):
            if direction == 'UP':
                self.player.rect.y -= step
            elif direction == 'DOWN':
                self.player.rect.y += step
            elif direction == 'RIGHT':
                self.player.rect.x += step
            elif direction == 'LEFT':
                self.player.rect.x -= step
            self.player.update_skin(direction)

    def allow_move_player(self, direction, step):
        self.player.mystery_player.rect.x = self.player.rect.x
        self.player.mystery_player.rect.y = self.player.rect.y

        if direction == 'UP':
            self.player.mystery_player.rect.y -= step
        elif direction == 'DOWN':
            self.player.mystery_player.rect.y += step
        elif direction == 'RIGHT':
            self.player.mystery_player.rect.x += step
        elif direction == 'LEFT':
            self.player.mystery_player.rect.x -= step

        if pygame.sprite.spritecollideany(self.player.mystery_player, self.wall_group):
            return False
        elif pygame.sprite.spritecollideany(self.player.mystery_player, self.bag_group):
            coll_bag = pygame.sprite.spritecollideany(self.player.mystery_player, self.bag_group)
            if self.allow_move_bag(coll_bag, direction, step):
                self.player.push = True
                self.move_bag(coll_bag, direction, step)
                return True
            else:
                return False
        else:
            self.player.push = False
        return True

    def move_bag(self, bag, direction, step):
        if direction == 'UP':
            bag.rect.y -= step
        elif direction == 'DOWN':
            bag.rect.y += step
        elif direction == 'RIGHT':
            bag.rect.x += step
        elif direction == 'LEFT':
            bag.rect.x -= step
        self.bag_is_store(bag)

    def allow_move_bag(self, bag, direction, step):
        bag.mystery_bag.rect.x = bag.rect.x
        bag.mystery_bag.rect.y = bag.rect.y

        if direction == 'UP':
            bag.mystery_bag.rect.y -= step
        elif direction == 'DOWN':
            bag.mystery_bag.rect.y += step
        elif direction == 'RIGHT':
            bag.mystery_bag.rect.x += step
        elif direction == 'LEFT':
            bag.mystery_bag.rect.x -= step

        # проверям столкновение ящика со стеной
        if pygame.sprite.spritecollideany(bag.mystery_bag, self.wall_group):
            return False
        # проверям столкновение ящиков, те если ли рядом ящик в направлении движения
        elif pygame.sprite.spritecollideany(bag.mystery_bag, self.bag_group):
            check = pygame.sprite.spritecollideany(bag.mystery_bag, self.bag_group)
            if abs(bag.mystery_bag.rect.x - check.rect.x) < step and abs(bag.mystery_bag.rect.y - check.rect.y) < step:
                return False
        return True

    # проверям установлен ли ящик на место хранения, обновляем внешний вид
    def bag_is_store(self, bag):
        if pygame.sprite.spritecollideany(bag, self.store_group):
            store = pygame.sprite.spritecollideany(bag, self.store_group)
            if abs(bag.rect.x - store.rect.x) < 5 and abs(bag.rect.y - store.rect.y) < 5:
                bag.image = tile_images['store_full']
                bag.flower = True
            else:
                bag.image = tile_images['bag']
                bag.flower = False

    def is_win(self):
        result = all(map(lambda x: x.flower, self.bag_group))
        if self.over is None and result:
            self.over = result
        return result

    def animate_win(self):
        create_particles([self.all_sprites, self.fire], (WIDTH // 2, HEIGHT // 3 - 40))
        for wall in self.wall_group:
            wall.image = tile_images['win']


if __name__ == '__main__':
    pygame.init()
    pygame.display.set_caption('MySokoban')
    game_screen = pygame.display.set_mode(size)
    background = pygame.Surface(size)
    background.fill((30, 190, 113))
    manager = pygame_gui.UIManager(size)
    win_message = pygame_gui.elements.UITextBox(
        relative_rect=pygame.Rect((200, 120), (300, 200)),
        visible=False,
        html_text='\n'.join([
            '',
            ' ' * 14 + 'ПОБЕДА',
            ' ' * 10 + 'Уровень пройден!',
            '',
            '',
            ' ' * 6 + 'SPACE для выбора уровня'
        ]), manager=manager
    )

    clock = pygame.time.Clock()
    player_name, download_level = start_screen()
    level_file = DATA_DIR + '/map_' + download_level + '.txt'
    cur_level = load_level(level_file)
    tile_images = {
        'hero': load_image('character.png'),
        'hero_up': load_image('character-back.png'),
        'hero_right': load_image('character-right.png'),
        'hero_left': load_image('character-left.png'),
        'hero_push': load_image('character-push.png'),
        'hero_up_push': load_image('character-push-back.png'),
        'hero_right_push': load_image('character-push-right.png'),
        'hero_left_push': load_image('character-push-left.png'),
        'wall': load_image('bush.png'),
        'empty': load_image('grass.png'),
        'bag': load_image('water_bucket.png'),
        'store': load_image('pit.png'),
        'store_full': load_image('puddle.png'),
        'win': load_image('blooming_bush.png'),
        'fire': load_image('flower.png'),
        'favicon': load_image('flower.png'),
        'expectation-0': load_image('expectation-1.png'),
        'expectation-1': load_image('expectation-2.png'),
        'expectation-2': load_image('expectation-3.png'),
        'expectation-3': load_image('expectation-4.png'),
        'expectation-4': load_image('expectation-5.png')
    }
    pygame.display.set_icon(tile_images['favicon'])

    game = Game(cur_level)
    camera = Camera()
    running = True
    time = 0

    while running:  # главный игровой цикл
        for event in pygame.event.get():
            # обработка событий
            if event.type == pygame.QUIT:
                confirmation_dialog = pygame_gui.windows.UIConfirmationDialog(
                    rect=pygame.Rect((200, 120), (300, 200)),
                    manager=manager,
                    window_title='Подтверждение',
                    action_long_desc='Вы уверены, что хотите выйти?',
                    action_short_name='ОК',
                    blocking=True
                )
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
                    running = False
            if game.is_win():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    player_name, download_level = start_screen()
                    level_file = DATA_DIR + '/map_' + download_level + '.txt'
                    cur_level = load_level(level_file)
                    game = Game(cur_level)
            else:
                if event.type == pygame.KEYDOWN:
                    time = 0
                    game.player.image = tile_images['hero']
                    if event.key == pygame.K_UP:
                        game.move_player('UP', STEP)
                    if event.key == pygame.K_DOWN:
                        game.move_player('DOWN', STEP)
                    if event.key == pygame.K_RIGHT:
                        game.move_player('RIGHT', STEP)
                    if event.key == pygame.K_LEFT:
                        game.move_player('LEFT', STEP)
                    if event.key == pygame.K_n:
                        player_name, download_level = start_screen()
                        level_file = DATA_DIR + '/map_' + download_level + '.txt'
                        cur_level = load_level(level_file)
                        game = Game(cur_level)

            manager.process_events(event)

        # амимация, если игрок долго не делает ход
        if time > FPS * 100 and (time // (FPS * 20)) % 5 >= 0:
            game.player.image = tile_images[f'expectation-{str((time // (FPS * 20)) % 5)}']

        # обновление ракурса камеры
        camera.update(game.player, WIDTH, HEIGHT)
        for sprite in game.all_sprites:
            camera.apply(sprite)

        # формирование кадра
        game_screen.blit(background, (0, 0))
        game.render(game_screen)

        # проверка выйгрыша
        if game.is_win():
            # запуск анимации
            game.animate_win()
            if game.over is True:
                # запись результата игрока в базу
                period = dt.datetime.now() - game.time
                period = (str(period.seconds // 60).rjust(2, '0')
                          + ':' + str(period.seconds % 60).rjust(2, '0')
                          + ':' + str(period.microseconds)[:2])
                db_save_result(player_name, download_level, period)
                game.over = False
        # отображать ли окно выйгрыша
        if game.over is None:
            win_message.visible = False
        else:
            win_message.visible = True

        # смена кадра
        manager.update(FPS)
        manager.draw_ui(game_screen)
        pygame.display.flip()
        time += FPS
        clock.tick(FPS)

    pygame.quit()
