buf = ""

def append(tokens,type,value,row,col):
    tokens.append({
        "type": type,
        "value": value,
        "row": row,
        "col": col
    })

def flush_buf(tokens,type,i,j):
    global buf
    append(tokens,type,buf,i,j)
    buf = ""

def lex(src):
    global buf
    lines = src.split("\n")
    in_strlit = False
    escape    = False
    tokens = []

    for i,l in enumerate(lines):
        for j,c in enumerate(l):
            if in_strlit:
                match c:
                    case '\\':
                        escape = not escape
                        if buf == "":
                            buf_start = (i, j)
                        buf += c
                    case '"':
                        if escape:
                            if buf == "":
                                buf_start = (i, j)
                            buf += c
                            escape = False
                        else:    
                            flush_buf(tokens,"strlit",buf_start[0],buf_start[1])
                            in_strlit = False
                    case _:
                        if buf == "":
                            buf_start = (i, j)
                        buf += c
            elif c.isalnum() or c == "_":
                if buf == "":
                    buf_start = (i, j)
                buf += c
            else:
                if len(buf) > 0:
                    flush_buf(tokens,"misc",buf_start[0],buf_start[1])
                match c:
                    case '(':
                        append(tokens,"lparen",None,i,j)
                    case ')':
                        append(tokens,"rparen",None,i,j)
                    case '{':
                        append(tokens,"lcurly",None,i,j) # OMFG Curly Brace from motherfucking cave story
                    case '}':
                        append(tokens,"rcurly",None,i,j) # bruh she turned right wing
                    case '[':
                        append(tokens,"lsquare",None,i,j)
                    case ']':
                        append(tokens,"rsquare",None,i,j)
                    case '=':
                        append(tokens,"equals",None,i,j)
                    case '!':
                        append(tokens,"bang",None,i,j)
                    case '%':
                        append(tokens,"percent",None,i,j)
                    case '^':
                        append(tokens,"caret",None,i,j)
                    case '+':
                        append(tokens,"plus",None,i,j)
                    case '-':
                        append(tokens,"minus",None,i,j)
                    case '*':
                        append(tokens,"star",None,i,j)
                    case '/':
                        append(tokens,"division",None,i,j)
                    case ':':
                        append(tokens,"colon",None,i,j)
                    case '?':
                        append(tokens,"question",None,i,j)
                    case ',':
                        append(tokens,"comma",None,i,j)
                    case '"':
                        in_strlit = True
                    case ';':
                        append(tokens,"semi",None,i,j)

    return tokens