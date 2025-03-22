import math
import mmap
import multiprocessing
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import threading

def r(x):
    return math.ceil(x * 10) / 10

def d():
    return [float('inf'), float('-inf'), 0.0, 0]

def p(l, data_dict, lk):
    ld = defaultdict(d)
    for ln in l:
        if not ln:
            continue
        sp = ln.find(b';')
        if sp == -1:
            continue
        c = ln[:sp]
        sc = ln[sp+1:]
        try:
            s = float(sc)
        except ValueError:
            continue
        e = ld[c]
        e[0] = min(e[0], s)
        e[1] = max(e[1], s)
        e[2] += s
        e[3] += 1
    with lk:
        for c, st in ld.items():
            e = data_dict[c]
            e[0] = min(e[0], st[0])
            e[1] = max(e[1], st[1])
            e[2] += st[2]
            e[3] += st[3]

def r_c(f, s, e):
    data_dict = defaultdict(d)
    lk = threading.Lock()
    with open(f, "rb") as fl:
        mm = mmap.mmap(fl.fileno(), 0, access=mmap.ACCESS_READ)
        sz = len(mm)
        if s != 0:
            mm.seek(s)
            if mm.read(1) != b'\n':
                while mm.tell() < sz and mm.read(1) != b'\n':
                    pass
            s = mm.tell()
        mm.seek(e)
        if mm.read(1) != b'\n':
            while mm.tell() < sz and mm.read(1) != b'\n':
                pass
            e = mm.tell()
        ch = mm[s:e]
        mm.close()
    ln = ch.split(b'\n')
    nt = 4
    lpt = (len(ln) + nt - 1) // nt
    ta = []
    for i in range(nt):
        st = i * lpt
        en = st + lpt
        ta.append((ln[st:en], data_dict, lk))
    with ThreadPoolExecutor(max_workers=nt) as ex:
        ex.map(lambda a: p(*a), ta)
    return data_dict

def m(dl):
    f = defaultdict(d)
    for dt in dl:
        for c, st in dt.items():
            if c not in f:
                f[c] = st
            else:
                fe = f[c]
                fe[0] = min(fe[0], st[0])
                fe[1] = max(fe[1], st[1])
                fe[2] += st[2]
                fe[3] += st[3]
    return f

def w(l, s, e, o):
    with open(o, "a") as f:
        f.writelines(l[s:e])

def main(i="testcase.txt", o="output.txt"):
    with open(i, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        fs = len(mm)
        mm.close()
    np = multiprocessing.cpu_count() * 4
    cs = fs // np
    ch = [(i * cs, (i + 1) * cs if i < np - 1 else fs) for i in range(np)]
    with multiprocessing.Pool(np) as p:
        t = [(i, s, e) for s, e in ch]
        results = p.starmap(r_c, t)
    fd = m(results)
    output = [
        f"{c.decode()}={r(st[0]):.1f}/{r(st[2] / st[3]):.1f}/{r(st[1]):.1f}\n"
        for c, st in sorted(fd.items())
    ]
    with open(o, "w") as f:
        f.writelines(output)

if __name__ == "__main__":
    main()