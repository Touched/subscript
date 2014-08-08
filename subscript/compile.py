import ast
import time
import os
import operator
import collections
import subscript.datatypes as datatypes
import subscript.script as script
import subscript.langtypes as langtypes
import subscript.functions as functions
import subscript.errors as errors
import runpy

class Compile(object):
    '''
    '''

    def __init__(self, source, base):
        '''
        Constructor.
        @param source: The source to be parsed, as a string.
        '''

        # Convert line endings
        self.source = source.replace('\r\n', '\n')

        # Use None so that we base line numbers from 1 instead of 0
        self.lines = [None] + self.source.split('\n')

        # State variables
        self.script = script.Script(base)
        self.symbols = {
                        'PLAYERFACING': langtypes.Var(self.script, 0x800C),
                        'LASTRESULT': langtypes.Var(self.script, 0x800D),
                        'LASTTALKED': langtypes.Var(self.script, 0x800F)
                        }

        self.nextsection = None
        self.section = self.script.add()
        self.returnhere = None

        # Create the tree, and begin to parse
        tree = ast.parse(self.source)
        for node in tree.body:
            self._handle_node(node)

    def output(self):
        for section in self.script.sections:
            print('@{}:'.format(section.name))
            if type(section) == script.Section:
                for cmd in section.commands:
                    print('', cmd, sep='\t')
            else:
                print('', section.data, sep='\t')

    def status(self):

        out = ''
        for section in self.script.sections:
            offset = section.dynamic().value + 0x08000000
            if type(section) == script.Section:
                out += 'Section ({} bytes) at 0x{:08X} (@{})\n'.format(section.size, offset, section.name.strip())
                for command in section.commands:
                    out += '\t{}\n'.format(command)
            else:
                out += 'Raw data ({} bytes) at 0x{:08X} (@{})\n'.format(section.size, offset, section.name.strip())
        return out

    def bytecode(self):
        data = bytearray()

        for section in self.script.sections:
            if type(section) == script.Section:
                for command in section.commands:
                    data.extend(command.compile())
            elif type(section) == script.SectionRaw:
                data.extend(section.data)
                pass
            else:
                raise Exception

        return bytes(data)

    def _add_command(self, command, *args):
        self.section.append(script.Command.create(command, *args))

    def _handle_node(self, node):
        if type(node) == ast.Assign:
            self._handle_assign(node)
        elif type(node) == ast.Expr:
            self._handle_expr(node)
        elif type(node) == ast.If:
            self._handle_if(node)
        elif type(node) == ast.While:
            self._handle_while(node)
        elif type(node) == ast.AugAssign:
            self._handle_aug_assign(node)
        elif type(node) == ast.FunctionDef:
            self._handle_function_def(node)
        elif type(node) == ast.Return:
            self._handle_return(node)
        elif type(node) == ast.Import:
            self._handle_import(node)
        elif type(node) == ast.ImportFrom:
            self._handle_import_from(node)
        else:
            raise errors.CompileSyntaxError(node)

    def _handle_import(self, node):
        for name in node.names:
            # Get the target name for the import
            target = name.name
            asname = name.asname if name.asname else target

            # Find what we're importing
            search_path = ['/home/james/here/code']
            for path in search_path:
                for file in os.listdir(path):
                    # Just loop over files
                    absolute = os.path.join(path, file)

                    if os.path.isfile(absolute):
                        base, ext = os.path.splitext(file)

                        if base != target:
                            # Don't bother, the file doesn't match the import
                            continue

                        # FIXME: All extensions
                        if ext in ['.py', '.pyc']:
                            # Python module. These will register custom functions
                            runpy.run_path(absolute, init_globals={'register': functions.register})
                            return
                        elif ext in ['.sub']:
                            # TODO: Compile this file first
                            raise ImportError('Script import not yet supported.')
                            return
                        elif ext in ['.asm', '.s']:
                            # TODO: Assemble
                            raise ImportError('Assembly import not yet supported.')
                            return
                        elif ext in ['.c']:
                            # TODO: Compile C code
                            raise ImportError('C import not yet supported.')
                            return
                        elif ext in ['.bin', '.raw']:
                            # Raw copy
                            self.symbols[asname] = langtypes.RawFile(self.script, absolute)
                            return
                        elif ext in ['.json']:
                            # TODO: Definitions?
                            raise ImportError('Definition import not yet supported.')
                            return
                        elif ext in ['.rbt']:
                            # TODO: Definitions?
                            raise ImportError('Definition import not yet supported.')
                            return
            else:
                # Import not found
                # TODO: Create special import exception
                raise ImportError('Import of "{}" unresolved.'.format(name.name))

    def _handle_import_from(self, node):
        # TODO
        print(node.__dict__)

    def _handle_function_def(self, node):
        if node.decorator_list:
            raise errors.CompileSyntaxError(node.decorator_list[0])

        # Arguments don't make sense, so they're forbidden
        if node.args.args or node.args.kwarg or node.args.vararg:
            raise errors.CompileSyntaxError(node.args)

        # Save state
        store = self.section

        # Create a new section for the function
        self.section = self.script.add()

        for item in node.body:
            self._handle_node(item)

        # Register the function in the symbol table by adding a script command to it
        if self.section.last().name in ['end']:
            # The last function was an end, so we use goto instead of call
            self.symbols[node.name] = script.Command.create('goto', self.section.dynamic())
        else:
            # We must return to the caller
            self._add_command('return')
            self.symbols[node.name] = script.Command.create('call', self.section.dynamic())

        # Restore state
        self.section = store

    def _handle_return(self, node):
        if node.value:
            fake = ast.Assign(targets=[ast.Name('LASTRESULT', ast.Load())], value=node.value)
            self._handle_assign(fake)

    def _handle_type(self, node):
        if type(node) == ast.Call:
            # Specific types
            return self._handle_explicit_type(node)
        elif type(node) == ast.Str:
            # Messages, etc.
            return langtypes.String(self.script, node.s)
        elif type(node) == ast.Bytes:
            # Raws
            return langtypes.Raw(self.script, node.s)
        elif type(node) == ast.List:
            # Movements
            return langtypes.Movement(self.script, node.elts)
        elif type(node) == ast.Num:
            return node.n
        elif isinstance(node, langtypes.Type):
            return node
        else:
            raise errors.CompileTypeError(node)

    def _handle_explicit_type(self, node):
        # Creation of a type, with a function call-like statement
        if len(node.keywords):
            # No keyword arguments for types
            raise errors.CompileSyntaxError(node.keywords)

        # Make sure the function is correct
        if type(node.func) != ast.Name:
            raise errors.CompileSyntaxError(node.func)

        name = node.func.id

        # Verify that the name actually names a type
        if name not in langtypes.Type:
            raise errors.CompileTypeError(node.func)

        if len(node.args) != 1:
            raise errors.CompileSyntaxError(node.args)

        argument = node.args[0]
        if type(argument) == ast.Num:
            value = argument.n
        else:
            value = self._handle_arithmetic(argument)

        return langtypes.Type[name](self.script, value)

    def _op_bin(self, op):
        if type(op) == ast.Mult:
            return operator.mul
        elif type(op) == ast.Add:
            return operator.add
        elif type(op) == ast.Div:
            return operator.truediv
        elif type(op) == ast.FloorDiv:
            return operator.floordiv
        elif type(op) == ast.Sub:
            return operator.sub
        elif type(op) == ast.BitAnd:
            return operator.and_
        elif type(op) == ast.BitXor:
            return operator.xor
        elif type(op) == ast.BitOr:
            return operator.or_
        elif type(op) == ast.LShift:
            return operator.lshift
        elif type(op) == ast.Mod:
            return operator.mod
        elif type(op) == ast.RShift:
            return operator.rshift
        elif type(op) == ast.Pow:
            return operator.pow
        else:
            raise errors.CompileSyntaxError(op)

    def _op_unary(self, op):
        if type(op) == ast.Not:
            return operator.not_
        elif type(op) == ast.USub:
            return operator.neg
        elif type(op) == ast.UAdd:
            return operator.pos
        elif type(op) == ast.Invert:
            return operator.invert
        else:
            raise errors.CompileSyntaxError(op)

    def _handle_arithmetic(self, node):
        if type(node) == ast.Name:
            # Resolve variable
            return self._handle_arithmetic(self.symbols[node.id])
        elif type(node) == ast.BinOp:
            left = self._handle_arithmetic(node.left)
            right = self._handle_arithmetic(node.right)
            return self._op_bin(node.op)(left, right)
        elif type(node) == ast.UnaryOp:
            value =  self._handle_arithmetic(node.operand)
            return self._op_unary(node.op)(value)
        elif type(node) == ast.Num:
            return node.n
        else:
            return node

    # Assignment
    def _handle_assign(self, node):

        if len(node.targets) != 1:
            raise errors.CompileSyntaxError(node.targets[1])

        if type(node.targets[0]) != ast.Name:
            raise errors.CompileSyntaxError(node.targets[0])

        what = node.targets[0].id

        if type(node.value) == ast.NameConstant:
            # Just numbers
            self._handle_set_value(what, node.value.value)
        elif type(node.value) == ast.Num:
            self._handle_set_value(what, node.value.n)
        elif type(node.value) == ast.Name:
            self._handle_set_value(what, self.symbols[node.value.id])
        else:
            self.symbols[what] = self._handle_type(node.value)

    def _handle_aug_assign(self, node):
        if type(node.target) != ast.Name:
            raise errors.CompileSyntaxError(node.target)

        what = self.symbols[node.target.id]

        if type(what) == langtypes.Var:
            value = self._handle_arithmetic(node.value)
            if type(value) != int:
                raise errors.CompileSyntaxError(node)

            if type(node.op) == ast.Add:
                self._add_command('addvar', what.value, value)
            elif type(node.op) != ast.Sub:
                self._add_command('subvar', what.value, value)
            else:
                raise errors.CompileSyntaxError(node.op)

    def _handle_set_value(self, target, value):
        if target not in self.symbols:
            self.symbols[target] = value
            return

        if type(self.symbols[target]) == langtypes.Flag:
            # We need to either set or clear the flag
            if value:
                self.section.append(script.Command.create('setflag', self.symbols[target].value))
            else:
                self.section.append(script.Command.create('clearflag', self.symbols[target].value))
        elif type(self.symbols[target]) == langtypes.Var:
            if type(value) == langtypes.Var:
                self._add_command('copyvar', self.symbols[target].value, value.value)
            elif type(value) == int:
                self._add_command('setvar', self.symbols[target].value, value)
        else:
            print(self.symbols[target])
            raise Exception

    # Expressions
    def _handle_expr(self, node):
        if type(node.value) == ast.Call:
            self._handle_function(node.value)
        elif type(node.value) == ast.Name:
            self._handle_keyword(node.value)
        else:
            raise errors.CompileSyntaxError(node.value)

    def _handle_function(self, node):
        # Handles ast.Call objects

        call = node.func.id

        # If the name is in the symbol table, we have a user-defined function
        if call in self.symbols:
            self.section.append(self.symbols[call])


            # We don't want to handle the next case
            return

        # Otherwise, we have a built-in function
        args = []
        for arg in node.args:
            args.append(self._handle_function_arg(arg))

        kwargs = {}
        for keyword in node.keywords:
            key, value = keyword.arg, self._handle_function_arg(keyword.value)
            kwargs[key] = value

        if call not in functions.registry:
            raise errors.CompileNameError(call)

        cmd = functions.registry[call](*args, **kwargs)
        self.section.append(cmd)

    def _handle_function_arg(self, node):
        if type(node) == ast.Name:
            # Resolve variables
            try:
                return self._handle_function_arg(self.symbols[node.id])
            except KeyError:
                raise errors.CompileNameError(node)
        elif type(node) == ast.NameConstant:
            return node.value
        elif type(node) == ast.Num:
            return node.n
        else:
            return self._handle_type(node)

    def _handle_keyword(self, node):
        if type(node) == ast.Name:
            if node.id == 'exit':
                self.section.append(script.Command.create('end'))
        else:
            raise errors.CompileSyntaxError(node)

    # Control flow
    def _handle_if(self, node):
        store3 = self.section
        store = self.nextsection
        rethere = self.returnhere
        self.nextsection = self.script.add()
        self._handle_condition(node.test, allow_return=True)

        if len(node.orelse):
            if type(node.orelse[0]) == ast.If:
                self._handle_if(node.orelse[0])
            else:
                store2 = self.nextsection
                self.nextsection = self.script.add()
                self._add_command('goto', self.nextsection.dynamic())
                self._handle_control_body(node.orelse)
                self._handle_control_end()
                self.nextsection = store2

        self._handle_control_body(node.body)
        self._handle_control_end()
        self.nextsection = store
        self.section = store3
        self.returnhere = rethere

    def _handle_while(self, node):
        store = self.nextsection
        self.nextsection = self.script.add()
        self._handle_condition(node.test)

        if len(node.orelse):
            errors.CompileSyntaxError(node.orelse)

        store2 = self.section
        self._handle_control_body(node.body)
        self._handle_condition(node.test, allow_return=False)
        self._handle_control_end()
        self.section = store2
        self.nextsection = store

    def _handle_control_body(self, node):
        self.section = self.nextsection
        for item in node:
            self._handle_node(item)

    def _handle_control_end(self):
        # The the last command ends the section, don't return
        if self.section.last().name not in ['end', 'return', 'goto']:
            #self.section.append(script.Command.create('return'))
            self.section.append(script.Command.create('goto', self.returnhere))

    def _handle_condition(self, node, allow_return=True, invert=False):
        # We need to resolve the comparison into left, right and op
        if type(node) == ast.Name:
            left = self.symbols[node.id]
            right = 1
            op = ast.Eq()
        elif type(node) == ast.Compare:
            if len(node.comparators) != 1:
                errors.CompileSyntaxError(node.comparators[1])

            if len(node.ops) != 1:
                errors.CompileSyntaxError(node.ops[1])

            if type(node.left) == ast.Name:
                left = self.symbols[node.left.id]
            else:
                left = self._handle_type(node.left)

            op = node.ops[0]

            if type(node.comparators[0]) == ast.Name:
                right = self.symbols[node.comparators[0].id]
            else:
                right = self._handle_type(node.comparators[0])
        elif type(node) == ast.UnaryOp:
            if type(node.op) == ast.Not:
                self._handle_condition(node.operand, invert=True)
            else:
                raise errors.CompileSyntaxError(node.op)

            # We don't want to add this condition too, so return
            return
        elif type(node) == ast.BoolOp:
            if type(node.op) == ast.And:
                for term in node.values:
                    self.nextsection = self.script.add()
                    self._handle_condition(term, allow_return)
                    self.section = self.nextsection
            elif type(node.op) == ast.Or:
                for term in node.values:
                    self._handle_condition(term, allow_return)
            return
        else:
            raise errors.CompileSyntaxError(node)

        if invert:
            op = self._invert_operator(op)

        try:
            self._handle_comparision(left, op, right, allow_return)
        except errors.CompileTypeError:
            # Swap operands and try again
            op = self._swap_operator(op)
            self._handle_comparision(right, op, left, allow_return)

    def _swap_operator(self, op):
        '''
        Change the operator for when the sides of the comparison are swapped.
        '''
        if type(op) == ast.Lt:
            return ast.Gt()
        elif type(op) == ast.Gt:
            return ast.Lt()
        elif type(op) == ast.LtE:
            return ast.GtE()
        elif type(op) == ast.GtE:
            return ast.LtE()

    def _invert_operator(self, op):
        '''
        Invert the operator for an opposite (not) comparison
        '''
        if type(op) == ast.Lt:
            return ast.GtE()
        elif type(op) == ast.Gt:
            return ast.LtE()
        elif type(op) == ast.LtE:
            return ast.Gt()
        elif type(op) == ast.GtE:
            return ast.Lt()
        elif type(op) == ast.Eq:
            return ast.NotEq()
        elif type(op) == ast.NotEq:
            return ast.Eq()

    def _op(self, op):
        # Convert op to its script value
        if type(op) == ast.Lt:
            return 0
        elif type(op) == ast.Gt:
            return 2
        elif type(op) == ast.LtE:
            return 3
        elif type(op) == ast.GtE:
            return 4
        elif type(op) == ast.Eq:
            return 1
        elif type(op) == ast.NotEq:
            return 5

    def _add_jump(self, op, allow_return):
        self.section.append(script.Command.create('if1', self._op(op), self.nextsection.dynamic()))
        if allow_return:
            self.returnhere = self.section.dynamic(len(self.section.commands))

    def _handle_comparision(self, left, op, right, allow_return):
        if type(left) == langtypes.Flag and type(right):
            if not right:
                # Switch the comparison to limit the amount of testing
                op = self._invert_operator(op)

            if type(op) != ast.NotEq and type(op) != ast.Eq:
                raise errors.CompileSyntaxError(op, "Invalid comparison")

            self._add_command('checkflag', left.value)
            self._add_jump(op, allow_return)
        elif type(left) == langtypes.Var:
            if type(right) == int:
                self._add_command('compare', left.value, right)
            elif type(right) == langtypes.Var:
                self._add_command('comparevars', left.value, right.value)
            else:
                raise errors.CompileTypeError(right, "Invalid comparison")
            self._add_jump(op, allow_return)
        elif type(left) == langtypes.Bank:
            if type(right) == langtypes.Bank:
                self._add_command('comparebanks', left.value, right.value)
            elif type(right) == int:
                self._add_command('comparebanktobyte', left.value, right.value)
            elif type(right) == langtypes.Pointer:
                self._add_command('comparebanktofarbyte', left.value, right.value)
            else:
                raise errors.CompileTypeError(right, "Invalid comparison")
        elif type(left) == langtypes.Pointer:
            if type(right) == langtypes.Bank:
                self._add_command('comparefarbytetobank', left.value, right.value)
            elif type(right) == int:
                self._add_command('comparefarbytetobyte', left.value, right.value)
            elif type(right) == langtypes.Pointer:
                self._add_command('comparefarbytes', left.value, right.value)
            else:
                raise errors.CompileTypeError(right, "Invalid comparison")
        elif type(left) == langtypes.HiddenVar and type(right) == int:
            self._add_command('comparehiddenvar', right)
        else:
            raise errors.CompileTypeError(left, "Invalid comparison")

import json
import sys
import subscript.codec, codecs

def pdecode(data):
    out = ''
    for b in data:
        if b == 255:
            break
        ch = subscript.codec.decoding_dict[b]
        if ch:
            out += ch
    return out

pokemon_table = []
items_table = []
attacks_table = []

if __name__ == '__main__':
    #https://github.com/thekaratekid552/Secret-Tool/blob/master/PokeRoms.ini
    #https://github.com/shinyquagsire23/MEH/tree/master/src/us/plxhack/MEH
    with open('tables/text.json') as table:
        table = json.loads(table.read())
    decode = [k for k, v in sorted(table['normal'].items())]

    with open('test.sub') as file:
        try:
            c = Compile(file.read(), 0)
            c.output()
        except errors.CompileSyntaxError as e:
            print(e)
