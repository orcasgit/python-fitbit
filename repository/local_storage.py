from gc import collect


class LocalStorage(object):
    def __init__(self, storage) -> None:
        self.storage = storage
    
    def _log(self, name):
        print(" " + self.storage + "  > " + name + " stored.")