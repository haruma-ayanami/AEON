import re, sys
def shift(fn, start, delta):
    s = open(fn).read()
    def sh(m):
        r = float(m.group(2))
        return f'{m.group(1)}{round(r + delta, 2):g}' if r >= start else m.group(0)
    s = re.sub(r'(d\.(?:act|n)\("[a-z0-9]+", (?:"[a-z]+", )?\d, )([0-9.]+)', sh, s)
    s = re.sub(r'(Diagram\(.*\), )([0-9.]+)(, rowh)', lambda m: f'{m.group(1)}{round(float(m.group(2)) + delta, 2):g}{m.group(3)}', s)
    open(fn, 'w').write(s)
def rep(fn, a, b):
    s = open(fn).read(); assert a in s, (fn, a); open(fn, 'w').write(s.replace(a, b))
