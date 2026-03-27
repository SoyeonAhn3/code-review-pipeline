import os


def f(a, b, c, d, e):
    x = []
    for i in range(len(a)):
        if a[i] > 100:
            if b[i] != 0:
                if c[i] == 1:
                    t = a[i] * 0.15 + d
                    if t > 500:
                        x.append(t)
                    else:
                        x.append(t * 1.1)
    return x


def proc(data):
    r = []
    for item in data:
        v = item[0] * 3.14159 * item[1] ** 2
        if v > 42:
            r.append({"val": v, "s": 1})
        else:
            r.append({"val": v, "s": 0})
    return r


def calc(n):
    if n < 0:
        return -1
    s = 0
    for i in range(n):
        for j in range(n):
            s += i * j
    return s
