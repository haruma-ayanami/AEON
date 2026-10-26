#!/bin/zsh
# Рендер всех рисунков в 1,25x и обрезка белых полей
cd "$(dirname "$0")"
for f in a1 a2 a3 a4 a5 a6 a7 a8 a9 a10 a11 n1 n2 n3 menu g1 g2; do
  read W H <<< "$(python3 $f.py)"
  ./render.sh $f $W $H 1.25
  python3 -c "
from PIL import Image, ImageChops
im=Image.open('$f.png').convert('RGB')
bg=Image.new('RGB', im.size, (255,255,255))
bb=ImageChops.difference(im,bg).getbbox()
p=24
im.crop((max(bb[0]-p,0),max(bb[1]-p,0),min(bb[2]+p,im.width),min(bb[3]+p,im.height))).save('final/$f.png', optimize=True)
print('$f', im.size)"
done
