import os


class HailstormData(object):
    def __init__(self):
        self.server_index = os.getenv('hailstorm_server_index', 0)


if __name__ == '__main__':
    hs = HailstormData()
    print(hs.server_index)
