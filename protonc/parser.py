class ASTNode:
    def __init__(self,type_,value=None):
        self.type = type_
        self.value = value
        self.children = {}
        self.attribs = {}

    def add_child(self,where,child):
        self.children[where] = child
        return True

    def add_attrib(self,key,value):
        self.attribs[key] = value
        return True

    def __repr__(self, level=0):
        indent = "  " * level
        s = f"ASTNode(\n"
        s += f"{indent}  type={self.type!r},\n"
        s += f"{indent}  value={self.value!r},\n"

        # Children
        if self.children:
            s += f"{indent}  children:\n"
            for k, v in self.children.items():
                s += f"{indent}    {k}: {v.__repr__(level + 2)}\n"
        else:
            s += f"{indent}  children={{}},\n"

        # Attributes
        if self.attribs:
            s += f"{indent}  attribs:\n"
            for k, v in self.attribs.items():
                s += f"{indent}    {k}: {v!r}\n"
        else:
            s += f"{indent}  attribs={{}},\n"

        s += f"{indent})"
        return s


def peek(tokens,skip=0):
    if skip >= len(tokens):
        return {"type" : "null"}
    return tokens[skip]

def consume(tokens):
    if len(tokens) != 0:
        return tokens.pop(0)

#TODO: expect and proper errors

def get_keyword(token):
    keywords = {
        # qualifiers
        "const"    : "CONST",      # defining constants
        "inline"   : "INLINE",     # basic macro

        # types
        "void"     : "VOID",       # undefined type

        # control flow lul
        "if"       : "IF",         # conditional
        "goto"     : "GOTO",       # goto statement to make loops out of

        # macros
        "macro"    : "MACRO",      # define sets of features
        "asttrans" : "ASTTRANS",   # AST transform
        "codegen"  : "CODEGEN",    # code generation routine
        "enable"   : "ENABLE",     # enable sets of features
        "disable"  : "DISABLE",    # disable sets of features
        "delete"   : "DELETE",     # undefine sets of features
    }

    if token["type"]  != "misc":
        return None

    if not token["value"] in keywords:
        return None

    return keywords[token["value"]]

def parse_expr_until(tokens,until):
    expr = ASTNode("none",None)

    while (next := peek(tokens)) and next["type"] not in until:
        match expr.type:
            case "none":
                match next["type"]:
                    case "strlit": # string literals
                        expr = ASTNode("strlit",next["value"])
                        expr.add_attrib("row",next["row"])
                        expr.add_attrib("col",next["col"])
                    case "misc": # things starting with identifiers or literals
                        if next["value"][0].isdigit() or next["value"][0] == "-":
                            expr = ASTNode("intlit",int(next["value"],0))
                        elif peek(tokens,1)["type"] == "lparen": # HACK HACK HACK: calling operator merged with called expression makes it rigid af
                            name = consume(tokens)
                            expr = ASTNode("func_call",name["value"])
                            expr.add_attrib("row",name["row"])
                            expr.add_attrib("col",name["col"])

                            while peek(tokens) and peek(tokens)["type"] != "rparen":
                                consume(tokens) #lparen or comma
                                param = parse_expr_until(tokens,["comma","rparen"])

                                if param == None:
                                    print("Error: invalid parameter")
                                    break

                                expr.add_child("arg" + str(len(expr.children)),param)
                        else:
                            expr = ASTNode("ident",next["value"])
                    case "minus": # unary minus operator
                        if peek(tokens,1)["type"] == "misc": # HACK HACK HACK: unary minus doesnt only work for negative numbers but for negating any statement!
                            consume(tokens) # minus
                            expr = ASTNode("intlit",int("-" + peek(tokens)["value"],0))
                    case _:
                        expr = ASTNode("unknown",[next])
            case "unknown": # unknown value, pass raw tokens to AST transformations
                expr.value.append(next)

            case _: # TODO: binary operators with precedence
                print("unexpected token:", next)
                exit(1)

        if not consume(tokens): # the token
            return None

    return expr

def parse_statements_until(block,tokens,until):
    while (next := peek(tokens)) and next["type"] not in until:
        stmt = None

        if get_keyword(next) or (next["type"] == "misc" and next["value"][0] in ("i", "u")):
            if peek(tokens)["value"] == "goto":
                goto = ASTNode("goto")

                consume(tokens)# misc

                name = consume(tokens)

                if name["type"] != "misc":
                    print("error: expected where to goto")
                    return toret

                goto.add_child("target",ASTNode("ident",name["value"]))

                stmt = goto
            else:
                decl = ASTNode("declaration")
                qtype = [] # qualifiers and type

                # HACK HACK HACK: this solution is very rigid and doesnt allow for custom qualifiers
                while next := peek(tokens):
                    if next["type"] == "star":
                        qtype.append("POINTER")
                    elif next["type"] == "misc":
                        if next_kw := get_keyword(next):
                            qtype.append(next_kw)
                        elif ((next["value"][0] == "i" or
                              next["value"][0] == "u" ) and
                                int(next["value"][1:]) > 2): # integer types

                                qtype.append(next["value"].upper())
                        else:
                            break
                    else:
                        break

                    consume(tokens) #the token
                decl.add_child("type",ASTNode("type_expr",qtype))

                name = consume(tokens) #name

                if (not name["type"] == "misc"):
                    print("Error: expected identifier as name for declaration") 
                    return False

                decl.add_child("name",ASTNode("ident",name["value"]))

                if (next := consume(tokens))["type"] == "equals":
                    expr = parse_expr_until(tokens,["semi"])
                    decl.add_child("value",expr)

                stmt = decl

            if next["type"] != "semi":
                consume(tokens) #semi


        elif next["type"] == "misc" and peek(tokens,1)["type"] == "equals": # HACK HACK HACK: assignment operator merged with veriable identifier is rigid af
            node = ASTNode("assignment")

            name = consume(tokens)
            node.add_child("name",ASTNode("ident",name["value"]))

            consume(tokens) # equals

            value = parse_expr_until(tokens,["semi"])
            node.add_child("value",value)

            stmt = node

            consume(tokens) #semi
        elif next["type"] == "misc" and peek(tokens,1)["type"] == "colon":
            node = ASTNode("label")
            name = consume(tokens)

            if name["type"] != "misc":
                print("error: expected where to goto")
                return toret

            node.add_child("target",ASTNode("ident",name["value"]))

            stmt = node

            consume(tokens) #colon

        elif next["type"] == "lcurly":
            consume(tokens) #lcurly
            node = ASTNode("block")

            parse_statements_until(node,tokens,["rcurly"])

            stmt = node

            consume(tokens) #rcurly
        elif eval_val := parse_expr_until(tokens,["semi"]):
                eval = ASTNode("eval",None)
                eval.add_child(0,eval_val)

                consume(tokens)# semi

                stmt = eval
        block.add_child(len(block.children),stmt)

def parse(tokens):
    tree = ASTNode("block")

    parse_statements_until(tree,tokens,["eof"])

    return tree