class CompileError(Exception):

    def __init__(self, astnode, message=''):
        super().__init__(message)
        self.message = message
        self.line = astnode.lineno
        self.col = astnode.col_offset
        self.node = astnode

    def __str__(self):
        if not self.message:
            self.message = repr(self.node)
        return '{} on line {}, column {}'.format(self.message, self.line, self.col)

class CompileSyntaxError(CompileError):
    pass

class CompileTypeError(CompileError):
    pass

class CompileNameError(CompileError):
    pass
