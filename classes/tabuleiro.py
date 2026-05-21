import random


class Board:
    def __init__(self, size=10):
        self.size = size
        self.ships = []
        self.attacks = set()

    def place_ship(self, ship):
        while True:
            horizontal = random.choice([True, False])
            row = random.randint(0, self.size - 1)
            col = random.randint(0, self.size - 1)

            positions = []

            for i in range(ship.size):
                if horizontal:
                    pos = (row, col + i)
                else:
                    pos = (row + i, col)

                if not self.is_valid_position(pos):
                    break

                positions.append(pos)

            if len(positions) == ship.size:
                ship.place(positions)
                self.ships.append(ship)
                return

    def is_valid_position(self, pos):
        l, c = pos

        if l >= self.size or c >= self.size:
            return False

        for ship in self.ships:
            if pos in ship.positions:
                return False

        return True

    def attack(self, pos):
        if pos in self.attacks:
            return None

        self.attacks.add(pos)

        for ship in self.ships:
            if pos in ship.positions:
                ship.hit(pos)
                return "hit"

        return "miss"

    def all_sunk(self):
        return all(ship.is_sunk() for ship in self.ships)

    def get_cell_state(self, pos):
        if pos not in self.attacks:
            return "empty"

        for ship in self.ships:
            if pos in ship.positions:
                return "hit"

        return "miss"
