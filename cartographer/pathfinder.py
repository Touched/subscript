#http://theory.stanford.edu/~amitp/GameProgramming/Heuristics.html#breaking-ties

class Node(object):

    def __init__(self, x, y, width=None, height=None, parent=None):
        self.parent = parent
        self.x = x
        self.y = y
        if parent == None:
            if width == None or height == None:
                raise ValueError('Orphan nodes must have dimensions.')
            self.width = width
            self.height = height
        else:
            self.width= parent.width
            self.height = parent.height

    def up(self):
        if self.y - 1 >= 0:
            return self.__class__(self.x, self.y - 1, parent=self)

    def down(self):
        if self.y + 1 < self.height:
            return self.__class__(self.x, self.y + 1, parent=self)

    def left(self):
        if self.x - 1 >= 0:
            return self.__class__(self.x - 1, self.y, parent=self)

    def right(self):
        if self.x + 1 < self.width:
            return self.__class__(self.x + 1, self.y, parent=self)

    def __hash__(self):
        return hash(repr(self))

    def __eq__(self, other):
        try:
            return self.x == other.x and self.y == other.y
        except AttributeError:
            return False

    def __repr__(self):
        return 'Node({}, {})'.format(self.x, self.y)

class Pathfinder(object):
    '''
    A* Path-finding base class.
    '''

    def __init__(self, path, start, end):
        '''
        Constructor
        '''
        self.output = []
        # Set has O(1) lookup instead of O(n) of a list
        x, y = start
        h, w = len(path), len(path[0])
        node = Node(x, y, w, h)
        self.openSet = set([node])
        self.closedSet = set()
        self.path = path
        self.end = Node(end[0], end[1], w, h)
        self.start = node

        self.add(node)
        while True:
            node = next(iter(sorted(self.openSet, key=self.score)))
            self.add(node)

            if self.end in self.closedSet:
                break

            if not len(self.openSet):
                print('No route from ({0[0]:}, {0[1]:}) to ({1[0]:}, {1[1]:})'.format(start, end))
                return

        # Retrace path
        walk = node
        while walk:
            self.output.append((walk.x, walk.y))
            walk = walk.parent

    def add(self, node):
        self.openSet.discard(node)
        self.closedSet.add(node)

        for item in self.adjacent(node):
            if item in self.closedSet:
                # Closed node
                continue

            for i in self.openSet:
                if item == i:
                    # Item is on open list, check if it's better
                    if self.route(item) < self.route(i):
                        # It's better, so reparent
                        self.openSet.remove(i)
                        self.openSet.add(item)
                    break

            else:
                self.openSet.add(item)

    def heuristic(self, node):
        '''
        Estimate the distance from the 'node' Node to the final Node in the path.
        '''
        # Tie break
        dx1 = node.x - self.end.x
        dy1 = node.y - self.end.y

        # Manhattan distance
        return (dx1 + dy1)

    def weight(self, start, end):
        '''
        Return an integer representing how costly it is to move from Node 'start'
        to Node 'end'.
        '''
        return 1

    def valid(self, start, end):
        '''
        Return True if the move from Node start to Node end is valid, and False
        otherwise.
        '''
        if start and end:
            p = self.path[end.y][end.x]
            return p == 12

        return False

    def route(self, node):
        current = node
        score = 0
        while current.parent:
            score += self.weight(current, current.parent)
            current = current.parent
        return score

    def score(self, node):
        return self.route(node) + self.heuristic(node)

    def adjacent(self, node):
        '''
        Return a tuple of nodes that are adjacent to this one.
        '''
        return filter(lambda x: self.valid(node, x), (node.up(), node.down(), node.left(), node.right()))

if __name__ == '__main__':
    path = [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            ]
    p = Pathfinder(path, (2, 3), (4, 3))