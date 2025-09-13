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
                            tokens.append({ "type": type, "value": value, "row": row, "col": col })
                            buf = ""
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
                    tokens.append({ "type": type, "value": value, "row": row, "col": col })
                    buf = ""

                if c == '"':
                    in_strlit = True
                elif c in chars:
                    tokens.append({ "type": type, "value": value, "row": row, "col": col })

    append(tokens,"eof",None,None,None)

    return tokens