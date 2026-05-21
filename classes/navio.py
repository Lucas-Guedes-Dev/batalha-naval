class Ship:
    def __init__(self, size):
        self.size = size
        self.positions = []
        self.hits = set()

    def place(self, positions):
        self.positions = positions

    def hit(self, position):
        if position in self.positions:
            self.hits.add(position)

    def is_sunk(self):
        return len(self.hits) == self.size
