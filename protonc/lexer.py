buf = ""

chars = {
   '(': "lparen",
   ')': "rparen",
   '{': "lcurly", # OMFG Curly Brace from motherfucking cave story
   '}': "rcurly", # bruh she turned right wing
   '[': "lsquare",
   ']': "rsquare",
   '=': "equals",
   '!': "bang",
   '%': "percent",
   '^': "caret",
   '+': "plus",
   '-': "minus",
   '*': "star",
   '/': "division",
   ':': "colon",
   '?': "question",
   ',': "comma",
   ';': "semi"
}

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

                if c == '"':
                    in_strlit = True
                elif c in chars:
                    append(tokens,chars[c],None,i,j)

    append(tokens,"eof",None,None,None)

    return tokens