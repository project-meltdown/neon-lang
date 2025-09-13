import parser

def get_type_size(type):
    toret = 0

    for c in type:
        if c[0] == "I" or c[0] == "U":
            toret = int(c[1:]) / 8
        elif c == "POINTER":
            toret = 8 # TODO: pointer size dependant on architecture

    return toret

def get_dx_variant(size):
    match size:
        case 8:
            return "dq"
        case 4:
            return "dd"
        case 2:
            return "dw"
        case _:
            return "db"

def get_strlit_name(lit):
    return "str_r" + str(lit.attribs["row"]) + "_c" + str(lit.attribs["col"])

def get_reserve_name(lit):
    return "res_r" + str(lit.attribs["row"]) + "_c" + str(lit.attribs["col"])

declaration_table = {}

def resolve_constant_argument(val):
    if val.type == "intlit" or val.type == "strlit":
        return val.value
    elif val.type == "func_call":
        return None # not constant
    elif val.type == "ident":
        if not val.value in declaration_table:
            print("Error: undefined identifier \"", val.value,"\"")
            return None
        if not declaration_table[val.value]["comptime"]:
            print("Error: expected \"", val.value,"\"to be known at compile time")
            return None 

        return declaration_table[val.value]["value"]
    else:
        print("Error: unimplemented val.type in resolve_constant_argument", val.type)

    return None


#HACK HACK HACK: this function is a hack
def handle_declaration(type,name,value,dryrun=False):
    if not name in declaration_table:
        declaration_table[name] = {
            "type"     : type.value,
            "const"    : type.value[0] == "CONST",
            "value"    : None
        }
        if value != None:
            comptime_value = resolve_constant_argument(value)
            declaration_table[name]["comptime"] = comptime_value != None
            declaration_table[name]["value"] = comptime_value

    if dryrun:
        return ""

    if value == None:
        return name + ": " + get_dx_variant(get_type_size(type.value)) + " 0\n"
    elif value.type == "strlit":
        return name + ": dq " + get_strlit_name(value) + "\n"
    elif value.type == "func_call" and value.value == "__ir_reserve":
        return name + ": dq " + get_reserve_name(value) + "\n"
    else:
        if declaration_table[name]["comptime"]:
            return name + ": " + get_dx_variant(get_type_size(type.value)) + " " + str(declaration_table[name]["value"]) + "\n"
        else:
            return name + ": " + get_dx_variant(get_type_size(type.value)) + " 0\n"
    
def look_for_strlits(ast):
    toret = ""

    match ast.type:
        case "block":
            for v in ast.children.items():
                toret += look_for_strlits(v[1])
        case "declaration":
            if "value" in ast.children:
                toret += look_for_strlits(ast.children["value"])
        case "eval":
            toret += look_for_strlits(ast.children[0])
        case "func_call":
            if ast.value == "__ir_reserve":
                return get_reserve_name(ast) + ": resb " + str(resolve_constant_argument(ast.children["arg0"])) + "\n"
            else:
                for v in ast.children.items():
                    toret += look_for_strlits(v[1])
        case "strlit":
            return get_strlit_name(ast) + ": db \"" + ast.value + "\"\n"
    return toret

def populate_decl_table(ast):
    match ast.type:
        case "block":
            for v in ast.children.items():
                populate_decl_table(v[1])
        case "declaration":
                if "value" in ast.children:
                    handle_declaration(ast.children["type"],ast.children["name"].value,ast.children["value"],True) # dryrun
                else:
                    handle_declaration(ast.children["type"],ast.children["name"].value,None,True) # dryrun
        case "eval":
                populate_decl_table(ast.children[0])
        case "func_call":
            for v in ast.children.items():
                populate_decl_table(v[1])

def look_for_globals(ast):
    toret = ""

    match ast.type:
        case "block":
            for v in ast.children.items():
                toret += look_for_globals(v[1])
        case "declaration":
            if "value" in ast.children:
                toret += handle_declaration(ast.children["type"],ast.children["name"].value,ast.children["value"]) # TODO: error handling
            else:
                toret += handle_declaration(ast.children["type"],ast.children["name"].value,None) # TODO: error handling

    return toret

def get_value(ast):
    toret = None
    match ast.type:
        case "block":
            print("error: block passed to get_value")
            return toret
        case "declaration":
            print("error: declaration passed to get_value")
            return toret
        case "ident":
            toret = "[" + ast.value + "]"
        case "eq_check":
            toret = "rax"
        case _:
            toret = ast.value
    return toret

def get_type(ast):
    toret = ["ERROR"]
    if not isinstance(ast,parser.ASTNode):
        return toret

    match ast.type:
        case "block":
            print("error: block passed to get_type")
        case "declaration":
            print("error: declaration passed to get_type")
        case "strlit":
            toret = ["LITERAL","CONST","I8","POINTER"]
        case "intlit":
            toret = ["LITERAL","CONST","I64"] # HACK HACK HACK: always 64 bit
        case "eq_check":
            toret = ["REGISTER", "U64"]
        case "ident":
            toret = declaration_table[ast.value]["type"]
    return toret

# TODO: nongeneral registers
def get_reg_size(reg_name): 
    if reg_name in {"ah", "bh", "ch", "dh", "al", "bl", "cl", "dl", "r8b", "r9b", "r10b", "r11b", "r12b", "r13b", "r14b", "r15b"}:
        return 1
    elif reg_name in {"ax", "bx", "cx", "dx", "r8w", "r9w", "r10w", "r11w", "r12w", "r13w", "r14w", "r15w"}:
        return 2
    elif reg_name in {"eax", "ebx", "ecx", "edx", "edi", "esi", "r8d", "r9d", "r10d", "r11d", "r12d", "r13d", "r14d", "r15d"}:
        return 4
    elif reg_name in {"rax", "rbx", "rcx", "rdx", "rdi", "rsi", "r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15"}:
        return 8
    else:
        return None

def get_size_qualifier(size):
    match size:
        case 8:
            return "qword"
        case 4:
            return "dword"
        case 2:
            return "word"
        case _:
            return "byte"
    
def emit_mov(dest,src,indentation):
    if isinstance(src,str):
        src_type = "reg"
        src_size = get_reg_size(src)
        src_str  = src 
    else:
        src_type = "node"
        src_size = int(get_type_size(get_type(src)))
        src_str  = get_value(src)

    if isinstance(dest,str):
        dest_type = "reg"
        dest_size = get_reg_size(dest)
        dest_str  = dest
    else:
        dest_type = "node"
        dest_size = int(get_type_size(get_type(dest)))
        dest_str  = get_value(dest)

    if src_size != dest_size and dest_type == "reg":
        mov_variant = "movzx"
    else:
        mov_variant = "mov"

    toret = "    "*indentation + mov_variant

    src_qualifier  = "" if src_type == "reg"  or get_type(src)[0] in ["LITERAL","REGISTER"] else get_size_qualifier(src_size)  + " "
    dest_qualifier = "" if dest_type == "reg" or get_type(dest)[0] in ["LITERAL","REGISTER"] else get_size_qualifier(dest_size) + " "

    toret += " " + dest_qualifier + str(dest_str) + ", " + src_qualifier + str(src_str) + "\n"

    return toret


syscall_arg_regs = ["rax","rdi","rsi","rdx","r10","r8","r9"]

def gen_func_call(ast,indentation):
    indent = "    "*indentation
    toret = ""
    if ast.value == "__ir__syscall":
        if len(ast.children) > 7:
            print("error: __ir__syscall takes 6 arguments max")
            return toret
        for i,c in enumerate(ast.children.items()):
            if get_type(c[1])[0] == "REGISTER":
                toret += indent + "pop " + syscall_arg_regs[i] + "\n"
            else:
                toret += emit_mov(syscall_arg_regs[i],c[1],indentation)
        toret += indent + "syscall\n"
    elif ast.value == "__ir_reserve":
        pass # this is not really a function but a static comptime
    else:
        print("unimplemented(codegen): non-builtin functions")

    return toret

def gen_expr(ast,indentation):
    indent = "    "*indentation
    toret = ""

    match ast.type:
        case "func_call":
            for c in ast.children.values():
                toret += gen_expr(c,indentation)
                if get_type(c)[0] == "REGISTER":
                    toret += indent + "push " + get_value(c) + "\n"
            toret += gen_func_call(ast,indentation)
        case "eq_check":
            toret += gen_expr(ast.children["left"],indentation)
            toret += emit_mov("rax", ast.children["left"],indentation)
            toret += indent + "push rax\n"
            toret += gen_expr(ast.children["right"],indentation)
            toret += emit_mov("rcx", ast.children["right"],indentation)
            toret += indent + "pop rax\n"
            toret += indent + "cmp rax, rcx\n"
            toret += indent + "sete al\n"
            toret += emit_mov("rax","al",indentation)
        case _:
            pass
    return toret

def generate_code(ast,indentation):
    indent = "    "*indentation
    toret = ""

    match ast.type:
        case "block":
            for v in ast.children.items():
                toret += generate_code(v[1],indentation+1)
        case "declaration":
            if "value" in ast.children:
                toret += gen_expr(ast.children["value"],indentation)
                if ast.children["value"].type == "func_call" and ast.children["value"].value == "__ir__syscall": # HACK HACK HACK
                    toret += emit_mov(ast.children["name"], "rax\n",indentation)
        case "assignment":
            if declaration_table[ast.children["name"].value]["const"]:
                print("Error: you cannot assign a constant variable")
                exit(1)

            toret += gen_expr(ast.children["value"],indentation)
            if ast.children["value"].type == "func_call" and ast.children["value"].value == "__ir__syscall": # HACK HACK HACK
                toret += emit_mov(ast.children["name"], "rax\n",indentation)
            elif ast.children["value"].type == "intlit":
                toret += emit_mov(ast.children["name"], ast.children["value"],indentation)
        case "eval":
            toret += gen_expr(ast.children[0],indentation)
        case "label":
            toret += indent + ast.children["target"].value + ":\n"
        case "goto":
            toret += indent + "jmp " + ast.children["target"].value + "\n"
    return toret

def gen_assembly(ast):
    #preparations
    populate_decl_table(ast)

    asmbuf = ";generated by ProtoNC Neon compiler\n"
    asmbuf += "global _start\n" # export start

    # generate data section
    asmbuf += "section .data\n\n;string literals and reservations\n"
    asmbuf += look_for_strlits(ast)
    asmbuf += "\n;global variables\n"
    asmbuf += look_for_globals(ast)

    # generate code section
    asmbuf += "\n;code segment\nsection .text\n"
    asmbuf += "_start:\n" #TODO: functions

    asmbuf += generate_code(ast,0)

    return asmbuf