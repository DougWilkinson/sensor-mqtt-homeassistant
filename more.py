def more(file):
    import uio
    t = uio.open(file)
    l = t.readline()
    while l != "":
        print(l)
        l = t.readline()
    t.close()

