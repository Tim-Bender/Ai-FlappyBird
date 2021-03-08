import os
import random
import neat
import pygame

pygame.font.init()
WIDTH = 800
HEIGHT = 800

BIRDS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),
         pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),
         pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png")))]
PIPES = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BACKGROUND = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

font = pygame.font.SysFont("comicsans", 50)
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
generation = 0


class Bird:
    IMAGES = BIRDS
    MAX_ROT = 25
    VEL = 20
    TICK_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMAGES[0]

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1

        d = self.vel * self.tick_count + 1.5 * self.tick_count ** 2
        if d >= 15:
            d = 15
        if d < 0:
            d -= 2
        self.y += d

        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROT:
                self.tilt = self.MAX_ROT
        else:
            if self.tilt > -90:
                self.tilt -= self.VEL

    def draw(self, win):
        self.img_count += 1

        if self.img_count < self.TICK_TIME:
            self.img = self.IMAGES[0]
        elif self.img_count < self.TICK_TIME * 2:
            self.img = self.IMAGES[1]
        elif self.img_count < self.TICK_TIME * 3:
            self.img = self.IMAGES[2]
        elif self.img_count < self.TICK_TIME * 4:
            self.img = self.IMAGES[1]
        elif self.img_count < self.TICK_TIME * 4 + 1:
            self.img = self.IMAGES[0]
            self.img_count = 0
        if self.tilt <= -80:
            self.img = self.IMAGES[1]
            self.img_count = self.TICK_TIME * 2
        rotated_img = pygame.transform.rotate(self.img, self.tilt)
        rect = rotated_img.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_img, rect.topleft)

    def getMask(self):
        return pygame.mask.from_surface(self.img)


class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPES, False, True)
        self.PIPE_BOTTOM = PIPES

        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.getMask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            return True
        return False


class Base:
    VEL = 5
    WIDTH = BASE_IMAGE.get_width()
    IMG = BASE_IMAGE

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, birds, pipes, base, score, gen, pipe_ind):
    win.blit(BACKGROUND, (0, 0))
    win.blit(BACKGROUND, (BACKGROUND.get_width(), 0))
    for pipe in pipes:
        pipe.draw(win)
    text = font.render("Score: " + str(score), True, (255, 255, 255))
    win.blit(text, (WIDTH - 10 - text.get_width(), 10))

    text = font.render("Gen: " + str(gen), True, (255, 255, 255))
    win.blit(text, (10, 10))
    base.draw(win)
    for bird in birds:
        try:
            pygame.draw.line(win, (255, 0, 0),
                             (bird.x + bird.img.get_width() / 2, bird.y + bird.img.get_height() / 2),
                             (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width() / 2, pipes[pipe_ind].height),
                             5)
            pygame.draw.line(win, (255, 0, 0),
                             (bird.x + bird.img.get_width() / 2, bird.y + bird.img.get_height() / 2), (
                                 pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width() / 2,
                                 pipes[pipe_ind].bottom), 5)
        except:
            pass

        bird.draw(win)
    pygame.display.update()


def main(genomes, config):
    nets = []
    ge = []
    birds = []
    for _, g in genomes:
        g.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        ge.append(g)

    base = Base(730)
    pipes = [Pipe(700)]
    score = 0
    global generation
    generation += 1
    clock = pygame.time.Clock()
    global WINDOW
    run_bool = True

    while run_bool and len(birds) > 0:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run_bool = False
                pygame.quit()
                quit()

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1

        for x, bird in enumerate(birds):
            ge[x].fitness += 0.1
            bird.move()

            output = nets[x].activate(
                (bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:
                bird.jump()
        rem = []
        add_pipe = False
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)
            pipe.move()
        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(700))
        for r in rem:
            pipes.remove(r)
        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() > 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)
        base.move()
        draw_window(WINDOW, birds, pipes, base, score, generation, pipe_ind)


def run(config_loc):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation, config_loc)
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    winner = p.run(main, 50)


if __name__ == "__main__":
    local_directory = os.path.dirname(__file__)
    config_path = os.path.join(local_directory, "neatsconfig.txt")
    run(config_path)
