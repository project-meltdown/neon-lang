import sys
import lexer
import parser
import codegen

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python",sys.argv[0],"<file>")
        exit(1) 
    f = open(sys.argv[1],"rt")
    src = f.read()

    lexed = lexer.lex(src)

    #print(lexed)

    root = parser.parse(lexed)

    print(root)

    #assembly = codegen.gen_assembly(root)

    #print(assembly)