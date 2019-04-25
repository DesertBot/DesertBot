import glob
from PIL import Image

for filename in glob.glob('data/comics/chars/*'):
    i = Image.open(filename).convert("RGBA")

for filename in glob.glob('data/comics/backgrounds/*'):
    i = Image.open(filename).convert("RGBA")
