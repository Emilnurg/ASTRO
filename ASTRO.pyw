

from livewires import games, color
import random, math
games.init(screen_width = 1760, screen_height = 990, fps = 50)

class Wrapper(games.Sprite):  #оптимизатор кода
    """Метод огибания объектов экраном"""
    def update(self):
        if self.right < 0:
            self.left = games.screen.width
        if self.left > games.screen.width:
            self.right = 0
        if self.bottom < 0:
            self.top = games.screen.height
        if  self.top > games.screen.height:
            self.bottom = 0

    def die(self):
        """Разрушает объект. пойманный игроком"""
        self.destroy()

class Collider(Wrapper): #взрывы
    """nогибатель. Огибатель(Wrapper), который может сталкиваться с другими объектами и гибнуть"""
    def update(self):
        """Проверяет. нет ли спрайтов. визуально перекрывающихся с данным"""
        super(Collider, self).update()
        if self.overlapping_sprites:
            for sprite in self.overlapping_sprites:
                sprite.die()
            self.die()

    def die(self):
        """Разрушает объект со взрывом"""
        new_explosion = Explosion(x = self.x, y = self.y)
        games.screen.add(new_explosion)
        self.destroy()

class Asteroid(Wrapper):
    SMALL = 1
    NORM = 2
    BIG = 3
    images = {SMALL : games.load_image("asteroid_small.bmp"),
              NORM : games.load_image("asteroid_med.bmp"),
              BIG : games.load_image("asteroid_big.bmp")}
    SPEED = 2
    SPAWN = 2
    POINTS = 30
    total = 0

    def __init__(self, x, y, size, game):
        super(Asteroid, self).__init__(
            image = Asteroid.images[size],
            x = x, y = y,
            dx = random.choice([1, -1])*Asteroid.SPEED*random.random()/size,
            dy = random.choice([1, -1])*Asteroid.SPEED*random.random()/size)
        self.size = size
        Asteroid.total += 1
        self.game = game

    def die(self):
        """Разрушает астероид и делит его пополам"""
#если астероид крупные или средние. заменить двумя более мелкими
        Asteroid.total -= 1
        self.game.score.value += int(Asteroid.POINTS / self.size)
        self.game.score.right = games.screen.width - 10
        if self.size != Asteroid.SMALL:
            for i in range(Asteroid.SPAWN):
                new_asteroid = Asteroid(game = self.game,
                                        x = self.x,
                                        y = self.y,
                                        size = self.size - 1)
                games.screen.add(new_asteroid)
        super(Asteroid, self).die()
#если больше астероидов не осталось. переходим на следующий уровень
        if Asteroid.total == 0:
            self.game.advance()

class Ship(Collider):
    image = games.load_image("ship.bmp")
    sound = games.load_sound("thrust.wav")

    VELOCITY_STEP = 0.03 #ускорение
    VELOCITY_MAX = 2.5  # ограничивает максимальную скорость                               
    MISSILE_DELAY = 20 #задержка между ракетами

    def __init__(self, x, y, game):
        """Инициализирует спрайт с изображением космического корабля."""
        self.game = game
        super(Ship, self).__init__(image = Ship.image, x = x, y = y)
        self.missile_wait = 0


    def update(self):
        """Вращает корабль определенным образом. исходя из нажатых клавиш"""
        super(Ship, self).update()
        if games.keyboard.is_pressed(games.K_LEFT): # клавиатурная константа, в приложении B
            self.angle -= 3 # градус
        if games.keyboard.is_pressed(games.K_RIGHT):
            self.angle += 3 #angle - угол наклона спрайта относительно его начального положения (в градусах).

        if games.keyboard.is_pressed(games.K_UP): # клавиатурная константа, в приложении B
            Ship.sound.play()
#изменение горизонтальной и вертикальной скорости корабля с учетом угла поворота
            angle = self.angle * math.pi / 180 #градусы в радианы
            self.dx += Ship.VELOCITY_STEP * math.sin(angle) #горизонтальное ускорение
            self.dy += Ship.VELOCITY_STEP * -math.cos(angle) #вертикальное

        # ограничение горизонтальной и вертикальной скорости
        self.dx = min(max(self.dx, -Ship.VELOCITY_MAX), Ship.VELOCITY_MAX) # не больше трех
        self.dy = min(max(self.dy, -Ship.VELOCITY_MAX), Ship.VELOCITY_MAX) # в обе стороны                            

        #если нажат Пробел. выпустить pакету
        if self.missile_wait > 0:
            self.missile_wait -= 1
        if games.keyboard.is_pressed(games.K_SPACE) and self.missile_wait == 0:
            new_missile = Missile(self.x, self.y, self.angle)
            games.screen.add(new_missile)
            self.missile_wait = Ship.MISSILE_DELAY

    def die(self):
        """Разрушает корабль и завершает игру."""
        self.game.end()
        super(Ship, self).die()
                                     
class Missile(Collider):
    "Ракетa"
    image = games.load_image("missile.bmp")
    sound = games.load_sound("missile.wav")
    BUFFER = 40 #чтобы ракеты не выпускались из центра корабля
    VELOCITY_FACTOR = 7 # скорость полета ракет
    LIFETIME = 50 #fps

    def __init__(self, ship_x, ship_y, ship_angle):
        """Инициализирует спрайт с изображением ракеты"""
        Missile.sound.play()

        angle = ship_angle * math.pi / 180 #градусы в радианы

        # вычисление начальной позиции ракеты
        buffer_x = Missile.BUFFER * math.sin(angle)
        buffer_y = Missile.BUFFER * -math.cos(angle)
        x = ship_x + buffer_x
        y = ship_y + buffer_y

        # вычисление горизонтальной и вертикальной скорости ракеты
        dx = Missile.VELOCITY_FACTOR * math.sin(angle) #горизонтальное ускорение
        dy = Missile.VELOCITY_FACTOR * -math.cos(angle)

        # создание ракеты
        super(Missile, self).__init__(
            image = Missile.image,
            x = x, y = y,
            dx = dx, dy = dy)
        self.lifetime = Missile.LIFETIME

    def update(self):
        """Перемещает ракету"""
        super(Missile, self).update()
        # еспи "срок годности" ракеты истек. она уничтожается
        self.lifetime -= 1
        if self.lifetime == 0:
            self.destroy()

class Explosion(games.Animation):
    sound = games.load_sound("explosion.wav")
    images = ["explosion1.bmp",
              "explosion2.bmp",
              "explosion3.bmp",
              "explosion4.bmp",
              "explosion5.bmp",
              "explosion6.bmp",
              "explosion7.bmp",
              "explosion8.bmp",
              "explosion9.bmp"]
    def __init__(self, x, y):
        super(Explosion, self).__init__(images = Explosion.images,
                         x = x, y = y, #место взрыва на экране
                         n_repeats = 1,
                         repeat_interval = 4,
                         is_collideable = False) # не перекрывались другими спрайтами
        Explosion.sound.play()

class Game(object):
    """Собственно игра"""
    #sound = games.load_sound("eralash_piu.wav")
    
    def __init__(self):
        """Инициализирует объект Game"""
        # выбор начального игрового уровня
        self.level = 0
        #загрузка звука. сопровождающего переход на следующий уровень
        self.sound = games.load_sound("level.wav")
        #CЧЕТ
        self.score = games.Text(value = 0, size = 75,
                                color = color.white, top = 4,
                                right = games.screen.width - 10,
                                is_collideable = False)
        games.screen.add(self.score)
        #КОРАБЛЬ
        self.ship = Ship(game = self,
                         x = games.screen.width/2,
                         y = games.screen.height/2)
        games.screen.add(self.ship)

    def play(self):
        """Начинает игру"""
        # запуск музыкальной темы
        games.music.load("theme.mid")
        games.music.play(-1) #бесконечно
        nebula_image = games.load_image("space_wall2.jpg")
        games.screen.background = nebula_image
        # переход к уровню 1
        welcome_message1 = games.Message(value = "astro",
                                      size = 300, color = color.dark_red,
                                      x = games.screen.width/2,
                                      y = games.screen.height/2,
                                      lifetime = 2 * games.screen.fps,
                                      is_collideable = False)
        games.screen.add(welcome_message1)
        self.advance()
        # начало игры                
        games.screen.mainloop()                

    def advance(self):
        """Переводит игру на очередной уровень"""
        self.level += 1
        # зарезервированное пространство вокруг корабля
        BUFFER = 150
        # создание новых астероидов
        for i in range(self.level):
#вычислим х и у. чтобы от корабля они отстояли минимум на BUFFER пикcелей
#сначала выберем минимальные отступы по горизонтали и вертикали                        
            x_min = random.randrange(BUFFER)
            y_min = BUFFER - x_min  # чтобы в сумме всегда было BUFFER
    #исходя из этих минимумов. сгенерируем расстояния от корабля по горизонталии вертикали
            x_distance = random.randrange(x_min, games.screen.width - x_min)
            y_distance = random.randrange(y_min, games.screen.height - y_min)
    #исходя из этих расстояний. выЧислим экранные координаты
            x = self.ship.x + x_distance
            y = self.ship.y + y_distance
            # если необходимо. вернем объект внутрь окна
            x %= games.screen.width
            y %= games.screen.height
            # создадим астероид
            new_asteroid = Asteroid(game = self,
                                    x = x, y = y,
                                    size = Asteroid.BIG)
            games.screen.add(new_asteroid)
        # отображение номера уровня                
        level_message = games.Message(value = "Уровень " + str(self.level),
                                      size = 80, color = color.yellow,
                                      x = games.screen.width/2,
                                      y = games.screen.height/10,
                                      lifetime = 3 * games.screen.fps,
                                      is_collideable = False)
        games.screen.add(level_message)
        # звуковой эффект перехода (кроме 1-го уровня)
        if self.level >1:
            self.sound.play()

    def end(self):
        """Завершает игру"""
        #Game.sound.play()
        #5 секундное отображение 'Game Over'
        end_message = games.Message(value = "потрачено",
                                      size = 250, color = color.dark_gray,
                                      x = games.screen.width/2,
                                      y = games.screen.height/2,
                                      lifetime = 10 * games.screen.fps,
                                      is_collideable = False,
                                      after_death = games.screen.quit())
        games.screen.add(end_message)
        
   
def main():
   astrocrash = Game()
   astrocrash.play()                                  
if __name__=="__main__":
    main()
