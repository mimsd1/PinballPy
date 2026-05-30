#PinballPy is a simple simulator/game based around the Pinball Slot Machine, using Pygame
#Made by D Mims
#Last updated 05/28/2026

#A majority of this code is currently based around the Pygame "Line By Line Chimp Tutorial"


# Import Modules
import os
import pygame as pg


#Checking if modules are available
if not pg.font:
    print("Warning, fonts disabled")
if not pg.mixer:
    print("Warning, sound disabled")

#Game FPS Variable
GAME_FPS = 60



#Establishing directories for python file
main_dir = os.path.split(os.path.abspath(__file__))[0]
data_dir = os.path.join(main_dir, "data")


#Function that loads images from a filename
def load_image(name, colorkey=None, scale=1):
    fullname = os.path.join(data_dir, name)
    image = pg.image.load(fullname)

    size = image.get_size()
    size = (size[0] * scale, size[1] * scale)
    image = pg.transform.scale(image, size)

    image = image.convert()
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, pg.RLEACCEL)
    return image, image.get_rect()


#Function that loads sound data from a filename
def load_sound(name):
    class NoneSound:
        def play(self):
            pass

    if not pg.mixer or not pg.mixer.get_init():
        return NoneSound()

    fullname = os.path.join(data_dir, name)
    sound = pg.mixer.Sound(fullname)

    return sound


#Class declarations for game objects

#Class for Reel 1
class Reel_1(pg.sprite.Sprite):
    def __init__(self):
        pg.sprite.Sprite.__init__(self)  # call Sprite initializer
        self.image, self.rect = load_image("reel.png", -1)
        screen = pg.display.get_surface()
        self.area = screen.get_rect()
        self.rect.topleft = 10, 90
        self.move = 18 #Reel Speed, which I assume can be made variable with a bit of work
        self.active = 0 #This is the flag on whether the reel should spin
        
    #This update function determines the current state of the reel
    def update(self):
        if self.Active:
            self._spin()

    #This is  the function that will have the reel "spin" to its next position
    #The basic idea is that each reel will just be a long sprite that contains each individual symbol
    #This will require me to figure out how to wrap the sprite so it can continuously loop
    def _spin(self):
        newpos = self.rect.move((0, self.move))
        self.rect = newpos
        

        
def main():

    #Initialize Pygame 
    pg.init()
    
    #Build out basic display settings
    screen = pg.display.set_mode((1280, 720), pg.SCALED)
    pg.display.set_caption("PinballPy")
    pg.mouse.set_visible(True)
    
    #Create the background
    background = pg.Surface(screen.get_size())
    background = background.convert()
    background.fill((170, 238, 187))

    #Updates the background to display while everything else loads
    screen.blit(background, (0, 0))
    pg.display.flip()

    #Create an instance of our Reel_1
    ree1_1 = Reel_1()
    
    #Create a group of sprites to be loaded onto the screen
    allsprites = pg.sprite.RenderPlain((reel_1))
    clock = pg.time.Clock()
    
    #Game Loop
    going = True
    while going:
        
        #This limits game FPS to 60
        clock.tick(GAME_FPS)

        #Game event/input handling
        for event in pg.event.get():
            if event.type == pg.QUIT:
                going = False
            elif event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                going = False
                
        #Update sprites
        allsprites.update()

        # Draw Everything
        screen.blit(background, (0, 0))
        allsprites.draw(screen)
        pg.display.flip()

    #Game quit
    pg.quit()    



if __name__ == "__main__":
    main()
    
#Lifes a Gamble
