import os, stat, itertools

def mkdirp(path):
    try:
        os.makedirs(path)
    except OSError:
        # "path already exists", presumably... should verify
        pass

def chmodPlusX(path):
    originalStat = os.stat(path).st_mode
    os.chmod(path, originalStat | stat.S_IXUSR)

def listConcat(lsts):
    return list(itertools.chain(*lsts))
