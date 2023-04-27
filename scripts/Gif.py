import glob
from PIL import Image
def make_gif(frame_folder):
    frames = glob.glob(frame_folder + "/*.png")
    frames.sort(key = lambda x: int(x.split('.')[0].split("/")[-1]))
    frames = frames[:1000]
    frames = list(map(Image.open, frames))
    frame_one = frames[0]
    frame_one.save("my_awesome_illinois.gif", format="GIF", append_images=frames,
               save_all=True, duration=0.0001, loop=0)
    
if __name__ == "__main__":
    make_gif("tmp")