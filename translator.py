import argparse
import ast
from visitors.GlobalVariables import GlobalVariableExtraction
from visitors.TopLevelProgram import TopLevelProgram
from visitors.FuncTranslate import FuncTranslate
from visitors.LocalVariablesExtraction import LocalVariablesExtraction
from generators.StaticMemoryAllocation import StaticMemoryAllocation
from generators.EntryPoint import EntryPoint
from generators.LocalsGenerator import LocalGenerator
from generators.FuncGenerator import FuncGenerator

def main():
    input_file, print_ast = process_cli()
    with open(input_file) as f:
        source = f.read()
    node = ast.parse(source)
    if print_ast:
        print(ast.dump(node, indent=2))
    else:
        process(input_file, node)
    
def process_cli():
    """"Process Command Line Interface options"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', help='filename to compile (.py)')
    parser.add_argument('--ast-only', default=False, action='store_true')
    args = vars(parser.parse_args())
    return args['f'], args['ast_only']

def process(input_file, root_node):
    print(f'; Translating {input_file}')
    extractor = GlobalVariableExtraction()
    extractor.visit(root_node)
    memory_alloc = StaticMemoryAllocation(extractor.results)
    print('; Branching to top level (tl) instructions')
    print('\t\tBR tl')
    memory_alloc.generate()
    functions = {}
    for node in root_node.body:
        if type(node) == ast.FunctionDef:
            functions[node.name] = [node] #nodes that are in the class ast.FunctionDef

    """iterates through each function to extract the function translations and their variables"""
    for index, function in enumerate(functions.values()):

        """Assigns the local variables and the parameters of the function"""
        localextractor = LocalVariablesExtraction(index)
        localextractor.visit(function[0])
        localVariables = LocalGenerator(localextractor.func_index, localextractor.results, localextractor.arguments)
        args, stacks = localVariables.generate() #It will return the arguments and the size of the stack that must be initialized for the return value

        """Translates the function"""
        localVars = localVariables.local_var #The local variables of the function
        func_tarnslation = FuncTranslate(index, localVariables.local_var)
        func_tarnslation.visit(function[0])
        instructions = func_tarnslation.finalize()[0]
        retVal = func_tarnslation.finalize()[1] #It will return a boolean value of whether the function has a return statement or not
        fg = FuncGenerator(instructions, index ,retVal, memory_alloc.global_vars, stacks, localVars, args, function[0].name)
        fg.generate()

    """Translate the top level program"""
    top_level = TopLevelProgram('tl')
    top_level.visit(root_node)
    ep = EntryPoint(top_level.finalize(), memory_alloc.global_vars)
    ep.generate()
    
if __name__ == '__main__':
    main()
