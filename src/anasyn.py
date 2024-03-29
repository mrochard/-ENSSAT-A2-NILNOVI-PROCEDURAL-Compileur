#!/usr/bin/python

# @package anasyn
# 	Syntactical Analyser package.
#

from copy import copy
import sys
import argparse
import re
import logging

import analex
import primitives
from codeGenerator import *

logger = logging.getLogger('anasyn')
codeGenerator = CodeGenerator()
operationGenerator = None
DEBUG = False
LOGGING_LEVEL = logging.DEBUG
lines = []
lineNumber = 0

class AnaSynException(Exception):
    def __init__(self, value,line,number):
        self.value = value
        self.line = "ln:"+str(number+1)+":: "+line+""



    def __str__(self):
        return ("\n\t\033[93m"+self.value+"\033[93m\n\t\t\033[91m"+self.line+"\033[91m")

########################################################################
# Syntactical Diagrams
########################################################################


def program(lexical_analyser):
    global codeGenerator, lines, lineNumber
    specifProgPrinc(lexical_analyser)
    lexical_analyser.acceptKeyword("is")
    lineNumber +=1
    corpsProgPrinc(lexical_analyser)


def specifProgPrinc(lexical_analyser):
    global codeGenerator, lines, lineNumber
    lexical_analyser.acceptKeyword("procedure")

    ident = lexical_analyser.acceptIdentifier()
    logger.debug("Name of program : "+ident)


def corpsProgPrinc(lexical_analyser):
    global codeGenerator, lines, lineNumber
    codeGenerator.addUnite(debutProg())
    if not lexical_analyser.isKeyword("begin"):
        logger.debug("Parsing declarations")

        partieDecla(lexical_analyser)
        
        logger.debug("End of declarations")
    lexical_analyser.acceptKeyword("begin")
    lineNumber +=1
    
    if not lexical_analyser.isKeyword("end"):
        logger.debug("Parsing instructions")
        suiteInstr(lexical_analyser)
        logger.debug("End of instructions")

    lexical_analyser.acceptKeyword("end")
    
    lexical_analyser.acceptFel()
    codeGenerator.addUnite(finProg())
    logger.debug("End of program")


def partieDecla(lexical_analyser):
    global codeGenerator, lines, lineNumber
    if lexical_analyser.isKeyword("procedure") or lexical_analyser.isKeyword("function"):
        tra1 = tra()
        codeGenerator.addUnite(tra1)
        listeDeclaOp(lexical_analyser)
        tra1.setAd(codeGenerator.getCO())
        if not lexical_analyser.isKeyword("begin"):
            listeDeclaVar(lexical_analyser)
    else:
        
        listeDeclaVar(lexical_analyser)


def listeDeclaOp(lexical_analyser):
    global codeGenerator, lines, lineNumber
    declaOp(lexical_analyser)
    lexical_analyser.acceptCharacter(";")
    
    if lexical_analyser.isKeyword("procedure") or lexical_analyser.isKeyword("function"):
        listeDeclaOp(lexical_analyser)

def declaOp(lexical_analyser):
    global codeGenerator, lines, lineNumber
    operationGenerator = OperationGenerator(copy(codeGenerator))
    
    codeGenerator = operationGenerator
    if lexical_analyser.isKeyword("procedure"):
        procedure(lexical_analyser)
    if lexical_analyser.isKeyword("function"):
        fonction(lexical_analyser)
    codeGenerator = copy(codeGenerator.getParent())

    codeGenerator.addUnite(copy(operationGenerator))
    operationGenerator = None


def procedure(lexical_analyser):
    global codeGenerator, lines, lineNumber
    lexical_analyser.acceptKeyword("procedure")
    ident = lexical_analyser.acceptIdentifier()
    logger.debug("Name of procedure : "+ident)
    proc = Procedure(ident, codeGenerator.getCO())
    codeGenerator.setOperation(proc)
    partieFormelle(lexical_analyser)

    lexical_analyser.acceptKeyword("is")
    lineNumber +=1
    
    corpsProc(lexical_analyser)
    codeGenerator.addUnite(retourProc())
    proc.setSymbols(copy(codeGenerator.symboleTable))


def fonction(lexical_analyser):
    global codeGenerator, lines, lineNumber
    lexical_analyser.acceptKeyword("function")
    ident = lexical_analyser.acceptIdentifier()
    logger.debug("Name of function : "+ident)
    func = Function(ident, codeGenerator.getCO())
    codeGenerator.setOperation(func)
    partieFormelle(lexical_analyser)

    lexical_analyser.acceptKeyword("return")
    ret = nnpType(lexical_analyser)

    # definie le type de retour de l'opération
    func.setReturnType(ret)
    lexical_analyser.acceptKeyword("is")
    lineNumber +=1
    
    corpsFonct(lexical_analyser)
    func.setSymbols(copy(codeGenerator.symboleTable))

def corpsProc(lexical_analyser):
    global codeGenerator, lines, lineNumber
    if not lexical_analyser.isKeyword("begin"):
        partieDeclaProc(lexical_analyser)
    lexical_analyser.acceptKeyword("begin")
    lineNumber +=1
    
    suiteInstr(lexical_analyser)
    lexical_analyser.acceptKeyword("end")
    lineNumber +=1


def corpsFonct(lexical_analyser):
    global codeGenerator, lines, lineNumber
    if not lexical_analyser.isKeyword("begin"):
        partieDeclaProc(lexical_analyser)
    lexical_analyser.acceptKeyword("begin")
    lineNumber +=1
    
    suiteInstrNonVide(lexical_analyser)
    lexical_analyser.acceptKeyword("end")
    lineNumber +=1


def partieFormelle(lexical_analyser):
    global codeGenerator, lines, lineNumber
    lexical_analyser.acceptCharacter("(")
    codeGenerator.toggleParamState()
    if not lexical_analyser.isCharacter(")"):
        listeSpecifFormelles(lexical_analyser)
    lexical_analyser.acceptCharacter(")")
    codeGenerator.toggleParamState()


def listeSpecifFormelles(lexical_analyser):
    global codeGenerator, lines, lineNumber
    specif(lexical_analyser)
    if not lexical_analyser.isCharacter(")"):
        lexical_analyser.acceptCharacter(";")
        
        listeSpecifFormelles(lexical_analyser)


def specif(lexical_analyser):
    global codeGenerator, lines, lineNumber
    nb = listeIdent(lexical_analyser)
    lexical_analyser.acceptCharacter(":")
    if lexical_analyser.isKeyword("in"):
        m = mode(lexical_analyser)
        codeGenerator.setParamMode(m)

    nnpType(lexical_analyser)


def mode(lexical_analyser):
    global codeGenerator, lines, lineNumber
    lexical_analyser.acceptKeyword("in")
    if lexical_analyser.isKeyword("out"):
        lexical_analyser.acceptKeyword("out")
        logger.debug("in out parameter")
        return 'in out'
    else:
        logger.debug("in parameter")
        return 'in'


def nnpType(lexical_analyser):
    global codeGenerator, lines, lineNumber
    if lexical_analyser.isKeyword("integer"):
        lexical_analyser.acceptKeyword("integer")
        codeGenerator.setVariableType(primitives.INTEGER)
        logger.debug("integer type")
        return primitives.INTEGER
    elif lexical_analyser.isKeyword("boolean"):
        lexical_analyser.acceptKeyword("boolean")
        codeGenerator.setVariableType(primitives.BOOLEAN)
        logger.debug("boolean type")
        return primitives.BOOLEAN
    else:
        logger.error("Unknown type found <" +
                     lexical_analyser.get_value() + ">!")
        raise AnaSynException("Unknown type found <" +
                              lexical_analyser.get_value() + ">!",lines[lineNumber],lineNumber)


def partieDeclaProc(lexical_analyser):
    global codeGenerator, lines, lineNumber
    listeDeclaVar(lexical_analyser)


def listeDeclaVar(lexical_analyser):
    global codeGenerator, lines, lineNumber
    declaVar(lexical_analyser)
    
    if lexical_analyser.isIdentifier():
        listeDeclaVar(lexical_analyser)


def declaVar(lexical_analyser):
    global codeGenerator, lines, lineNumber
    nb = listeIdent(lexical_analyser)
    lexical_analyser.acceptCharacter(":")
    logger.debug("now parsing type...")
    codeGenerator.addUnite(reserver(nb))
    nnpType(lexical_analyser)
    lexical_analyser.acceptCharacter(";")
    lineNumber +=1


def listeIdent(lexical_analyser):
    global codeGenerator, lines, lineNumber
    ident = lexical_analyser.acceptIdentifier()
    logger.debug("identifier found: "+str(ident))
    codeGenerator.addVariable(ident)

    if lexical_analyser.isCharacter(","):
        lexical_analyser.acceptCharacter(",")
        return listeIdent(lexical_analyser)+1
    return 1


def suiteInstrNonVide(lexical_analyser):
    global codeGenerator, lines, lineNumber
    instr(lexical_analyser)
    
    if lexical_analyser.isCharacter(";"):
        lexical_analyser.acceptCharacter(";")
        
        suiteInstrNonVide(lexical_analyser)


def suiteInstr(lexical_analyser):
    global codeGenerator, lines, lineNumber
    if not lexical_analyser.isKeyword("end"):
        suiteInstrNonVide(lexical_analyser)


def instr(lexical_analyser):
    global codeGenerator, lines, lineNumber
    
    if lexical_analyser.isKeyword("while"):
        boucle(lexical_analyser)
    elif lexical_analyser.isKeyword("if"):
        altern(lexical_analyser)
    elif lexical_analyser.isKeyword("get") or lexical_analyser.isKeyword("put"):
        es(lexical_analyser)
    elif lexical_analyser.isKeyword("return"):
        retour(lexical_analyser)
    elif lexical_analyser.isIdentifier():
        ident = lexical_analyser.acceptIdentifier()
        if lexical_analyser.isSymbol(":="):
            # affectation
            # empiler(ident, true) --> adresse / empiler(ident, false) --> valeur
            if(codeGenerator.isOperation()):
                var = codeGenerator.getSymboleTable()[ident]
                if(var.isParam()):
                    if(var.isOut()):
                        codeGenerator.addUnite(empilerParam(ident))
                    else:
                        raise AnaSynException(
                            "%s is not set to 'out' but is beeing modified" % ident,lines[lineNumber],lineNumber)
                else:
                    codeGenerator.addUnite(empilerAd(ident))
            else:
                codeGenerator.addUnite(empiler(ident))

            lexical_analyser.acceptSymbol(":=")
            type = expression(lexical_analyser)
            if codeGenerator.getSymboleTable()[ident].type != type:
                raise AnaSynException(
                    "Type mismatch. Expected %s but got %s " %(codeGenerator.getSymboleTable()[ident].type,type),lines[lineNumber],lineNumber)
            codeGenerator.addUnite(affectation())
            logger.debug("parsed affectation")
        elif lexical_analyser.isCharacter("("):
            lexical_analyser.acceptCharacter("(")
            codeGenerator.addUnite(reserverBloc())
            nombre = 0
            if not lexical_analyser.isCharacter(")"):
                types = listePe(lexical_analyser)
                nombre = len(types)
                params = codeGenerator.getSymboleTable()[ident].params
                for t,p,i in zip(types,params,range(0,len(params))):
                    if t!=p.type:
                        raise AnaSynException(
                            "%s Expected a %s as its %d parameter but got a %s" % (str(ident), p.type,(i+1),t),lines[lineNumber],lineNumber)

            expected = codeGenerator.getSymboleTable()[ident].nombreParam()
            if(nombre != expected):
                raise AnaSynException(
                    "%s Expected %d parameters but got %d" % (str(ident), expected, nombre),lines[lineNumber],lineNumber)

            codeGenerator.addUnite(traStat(ident, nombre))
            lexical_analyser.acceptCharacter(")")
            logger.debug("parsed procedure call")
        else:
            logger.error("Expecting procedure call or affectation!")
            raise AnaSynException("Expecting procedure call or affectation!",lines[lineNumber],lineNumber)

    else:
        logger.error("Unknown Instruction <" +
                     lexical_analyser.get_value() + ">!")
        raise AnaSynException("Unknown Instruction <" +
                              lexical_analyser.get_value() + ">!",lines[lineNumber],lineNumber)
    lineNumber +=1


def listePe(lexical_analyser):
    global codeGenerator, lines, lineNumber
    type = expression(lexical_analyser)
    t = [type]
    if lexical_analyser.isCharacter(","):
        lexical_analyser.acceptCharacter(",")
        t.extend(listePe(lexical_analyser))
        return t
    return t


def expression(lexical_analyser):
    global codeGenerator, lines, lineNumber
    logger.debug("parsing expression: " + str(lexical_analyser.get_value()))

    type = exp1(lexical_analyser)
    if lexical_analyser.isKeyword("or"):
        lexical_analyser.acceptKeyword("or")
        exp1(lexical_analyser)
        type = primitives.BOOLEAN
        codeGenerator.addUnite(ou())
    return type


def exp1(lexical_analyser):
    global codeGenerator, lines, lineNumber
    logger.debug("parsing exp1")

    type = exp2(lexical_analyser)
    if lexical_analyser.isKeyword("and"):
        lexical_analyser.acceptKeyword("and")
        exp2(lexical_analyser)
        type = primitives.BOOLEAN
        codeGenerator.addUnite(et())
    return type


def exp2(lexical_analyser):
    global codeGenerator, lines, lineNumber
    logger.debug("parsing exp2")
    op = None
    type = exp3(lexical_analyser)
    if lexical_analyser.isSymbol("<") or \
            lexical_analyser.isSymbol("<=") or \
            lexical_analyser.isSymbol(">") or \
            lexical_analyser.isSymbol(">="):
        op = opRel(lexical_analyser)
        exp3(lexical_analyser)
        type = primitives.BOOLEAN
    elif lexical_analyser.isSymbol("=") or \
            lexical_analyser.isSymbol("/="):
        op = opRel(lexical_analyser)
        exp3(lexical_analyser)
        type = primitives.BOOLEAN
    if op != None :
        codeGenerator.addUnite(op)
    return type


def opRel(lexical_analyser):
    global codeGenerator, lines, lineNumber
    logger.debug("parsing relationnal operator: " +
                 lexical_analyser.get_value())

    if lexical_analyser.isSymbol("<"):
        lexical_analyser.acceptSymbol("<")
        return inf()
    elif lexical_analyser.isSymbol("<="):
        lexical_analyser.acceptSymbol("<=")
        return infeg()
    elif lexical_analyser.isSymbol(">"):
        lexical_analyser.acceptSymbol(">")
        return sup()
    elif lexical_analyser.isSymbol(">="):
        lexical_analyser.acceptSymbol(">=")
        return supeg()
    elif lexical_analyser.isSymbol("="):
        lexical_analyser.acceptSymbol("=")
        return egal()
    elif lexical_analyser.isSymbol("/="):
        lexical_analyser.acceptSymbol("/=")
        return diff()
    else:
        msg = "Unknown relationnal operator <" + lexical_analyser.get_value() + ">!"
        logger.error(msg)
        raise AnaSynException(msg,lines[lineNumber],lineNumber)


def exp3(lexical_analyser):
    global codeGenerator, lines, lineNumber
    logger.debug("parsing exp3")
    type = exp4(lexical_analyser)

    op = None
    if lexical_analyser.isCharacter("+") or lexical_analyser.isCharacter("-"):
        op = opAdd(lexical_analyser)
        type = primitives.INTEGER
        exp4(lexical_analyser)
    if op != None :
        codeGenerator.addUnite(op)
    return type


def opAdd(lexical_analyser):
    global codeGenerator, lines, lineNumber
    logger.debug("parsing additive operator: " + lexical_analyser.get_value())
    if lexical_analyser.isCharacter("+"):
        lexical_analyser.acceptCharacter("+")
        return add()
    elif lexical_analyser.isCharacter("-"):
        lexical_analyser.acceptCharacter("-")
        return sous()
    else:
        msg = "Unknown additive operator <" + lexical_analyser.get_value() + ">!"
        logger.error(msg)
        raise AnaSynException(msg,lines[lineNumber],lineNumber)


def exp4(lexical_analyser):
    global codeGenerator, lines, lineNumber
    logger.debug("parsing exp4")
    op = None
    type = prim(lexical_analyser)
    if lexical_analyser.isCharacter("*") or lexical_analyser.isCharacter("/"):
        op = opMult(lexical_analyser)
        type = prim(lexical_analyser)
    if op != None :
        codeGenerator.addUnite(op)
    return type


def opMult(lexical_analyser):
    global codeGenerator, lines, lineNumber
    logger.debug("parsing multiplicative operator: " +
                 lexical_analyser.get_value())
    if lexical_analyser.isCharacter("*"):
        lexical_analyser.acceptCharacter("*")
        return mult()
    elif lexical_analyser.isCharacter("/"):
        lexical_analyser.acceptCharacter("/")
        return div()
    else:
        msg = "Unknown multiplicative operator <" + lexical_analyser.get_value() + ">!"
        logger.error(msg)
        raise AnaSynException(msg,lines[lineNumber],lineNumber)


def prim(lexical_analyser):
    global codeGenerator, lines, lineNumber
    logger.debug("parsing prim")
    op = None
    if lexical_analyser.isCharacter("+") or lexical_analyser.isCharacter("-") or lexical_analyser.isKeyword("not"):
        op = opUnaire(lexical_analyser)
    type = elemPrim(lexical_analyser)
    if op != None :
        codeGenerator.addUnite(op)
    return type


def opUnaire(lexical_analyser):
    global codeGenerator, lines, lineNumber
    logger.debug("parsing unary operator: " + lexical_analyser.get_value())
    if lexical_analyser.isCharacter("+"):
        lexical_analyser.acceptCharacter("+")
        return None
    elif lexical_analyser.isCharacter("-"):
        lexical_analyser.acceptCharacter("-")
        return moins()

    elif lexical_analyser.isKeyword("not"):
        lexical_analyser.acceptKeyword("not")
        return non()
    else:
        msg = "Unknown additive operator <" + lexical_analyser.get_value() + ">!"
        logger.error(msg)
        raise AnaSynException(msg,lines[lineNumber],lineNumber)


def elemPrim(lexical_analyser):
    global codeGenerator, lines, lineNumber
    logger.debug("parsing elemPrim: " + str(lexical_analyser.get_value()))
    type = None
    if lexical_analyser.isCharacter("("):
        lexical_analyser.acceptCharacter("(")
        type = expression(lexical_analyser)
        lexical_analyser.acceptCharacter(")")
    elif lexical_analyser.isInteger() or lexical_analyser.isKeyword("true") or lexical_analyser.isKeyword("false"):
        return valeur(lexical_analyser)
    elif lexical_analyser.isIdentifier():
        ident = lexical_analyser.acceptIdentifier()
        if lexical_analyser.isCharacter("("):              # Appel opération
            lexical_analyser.acceptCharacter("(")
            if not codeGenerator.getSymboleTable()[ident].isFunction():
                raise AnaSynException("%s is not a function"%ident,lines[lineNumber],lineNumber)
            codeGenerator.addUnite(reserverBloc())
            nbParam = 0
            if not lexical_analyser.isCharacter(")"):
                types = listePe(lexical_analyser)
                nbParam = len(types)
                params = codeGenerator.getSymboleTable()[ident].params
                for t,p,i in zip(types,params,range(0,len(params))):
                    if t!=p.type:
                        raise AnaSynException(
                            "%s Expected a %s as its %d parameter but got a %s" % (str(ident), p.type,(i+1),t),lines[lineNumber],lineNumber)
            expected = codeGenerator.getSymboleTable()[ident].nombreParam()
            if(nbParam != expected):
                raise AnaSynException(
                    "%s Expected %d parameters but got %d" % (str(ident), expected, nbParam),lines[lineNumber],lineNumber)

            lexical_analyser.acceptCharacter(")")
            logger.debug("parsed procedure call")
            logger.debug("Call to function: " + ident)
            codeGenerator.addUnite(traStat(ident, nbParam))
        else:
            logger.debug("Use of an identifier as an expression: " + ident)
            if(codeGenerator.isOperation()):
                if(codeGenerator.getSymboleTable()[ident].isOut()):
                    codeGenerator.addUnite(empilerParam(ident))
                else:
                    codeGenerator.addUnite(empilerAd(ident))
            else:
                codeGenerator.addUnite(empiler(ident))
            codeGenerator.addUnite(valeurPile())
        type = codeGenerator.getSymboleTable()[ident].type
    else:
        logger.error("Unknown Value!")
        raise AnaSynException("Unknown Value!",lines[lineNumber],lineNumber)
    return type


def valeur(lexical_analyser):
    global codeGenerator, lines, lineNumber
    if lexical_analyser.isInteger():
        entier = lexical_analyser.acceptInteger()
        logger.debug("integer value: " + str(entier))
        logger.debug("entier:"+str(entier))
        codeGenerator.addUnite(empiler(entier, False))
        return primitives.INTEGER
    elif lexical_analyser.isKeyword("true") or lexical_analyser.isKeyword("false"):
        valBool(lexical_analyser)
        return primitives.BOOLEAN
    else:
        logger.error("Unknown Value! Expecting an integer or a boolean value!")
        raise AnaSynException(
            "Unknown Value ! Expecting an integer or a boolean value!",lines[lineNumber],lineNumber)


def valBool(lexical_analyser):
    global codeGenerator, lines, lineNumber
    if lexical_analyser.isKeyword("true"):
        lexical_analyser.acceptKeyword("true")
        codeGenerator.addUnite(empiler(1, False))
        logger.debug("boolean true value")
    else:
        logger.debug("boolean false value")
        lexical_analyser.acceptKeyword("false")
        codeGenerator.addUnite(empiler(0, False))


def es(lexical_analyser):
    global codeGenerator, lines, lineNumber
    logger.debug("parsing E/S instruction: " + lexical_analyser.get_value())
    if lexical_analyser.isKeyword("get"):
        lexical_analyser.acceptKeyword("get")
        lexical_analyser.acceptCharacter("(")
        ident = lexical_analyser.acceptIdentifier()
        lexical_analyser.acceptCharacter(")")
        if(codeGenerator.isSymbolTypeBool(ident)):
                raise AnaSynException(
                    "Type mismatch. Expected : integer",lines[lineNumber],lineNumber)
        if(codeGenerator.isOperation()):
            codeGenerator.addUnite(empilerAd(ident, True))
        else:            
            codeGenerator.addUnite(empiler(ident, True))
        codeGenerator.addUnite(get())
        logger.debug("Call to get "+ident)
    elif lexical_analyser.isKeyword("put"):

        lexical_analyser.acceptKeyword("put")
        lexical_analyser.acceptCharacter("(")
        type = expression(lexical_analyser)
        if(type != primitives.INTEGER):
            raise AnaSynException(
                "Type mismatch. Expected : integer got " + type,lines[lineNumber],lineNumber)
        lexical_analyser.acceptCharacter(")")
        logger.debug("Call to put")
        codeGenerator.addUnite(put())
    else:
        logger.error("Unknown E/S instruction!")
        raise AnaSynException("Unknown E/S instruction!",lines[lineNumber],lineNumber)


def boucle(lexical_analyser):
    global codeGenerator, lines, lineNumber
    logger.debug("parsing while loop: ")
    lexical_analyser.acceptKeyword("while")
    ad1 = codeGenerator.getCO()
    type = expression(lexical_analyser)
    if(type != primitives.BOOLEAN):
        raise AnaSynException("Type mismatch. Expected : bool",lines[lineNumber],lineNumber)
    lexical_analyser.acceptKeyword("loop")
    tze1 = tze()
    codeGenerator.addUnite(tze1)
    
    suiteInstr(lexical_analyser)
    lexical_analyser.acceptKeyword("end")
    tra1 = tra()
    codeGenerator.addUnite(tra1)
    tra1.setAd(ad1)
    tze1.setAd(codeGenerator.getCO())
    logger.debug("end of while loop ")


def altern(lexical_analyser):
    global codeGenerator, lines, lineNumber
    logger.debug("parsing if: ")
    lexical_analyser.acceptKeyword("if")

    type = expression(lexical_analyser)
    if(type != primitives.BOOLEAN):
        raise AnaSynException("Type mismatch. Expected : bool",lines[lineNumber],lineNumber)
    jump = tze()
    codeGenerator.addUnite(jump)
    lexical_analyser.acceptKeyword("then")
    lineNumber +=1
    
    suiteInstr(lexical_analyser)
    if lexical_analyser.isKeyword("else"):
        lexical_analyser.acceptKeyword("else")
        lineNumber +=1
        jump2 = tra()
        codeGenerator.addUnite(jump2)
        jump.setAd(codeGenerator.getCO())
        suiteInstr(lexical_analyser)
        jump = jump2
    jump.setAd(codeGenerator.getCO())

    lexical_analyser.acceptKeyword("end")
    logger.debug("end of if")


def retour(lexical_analyser):
    global codeGenerator, lines, lineNumber
    logger.debug("parsing return instruction")
    lexical_analyser.acceptKeyword("return")
    type = expression(lexical_analyser)
    if(type != codeGenerator.operation.type):
        raise AnaSynException("Type mismatch. Expected : %s but operation returned %s" %(codeGenerator.operation.type,type),lines[lineNumber],lineNumber)
    codeGenerator.addUnite(retourFonct())

def displaySymboleTable(symboles,tab=0,parent=None):
    for symbole in symboles.values():
        msg = ""
        for t in range(0,tab):
            msg += "\t"
        if (symbole.isOperation()):
            
            msg += str(symbole.getIdent())+"("
            for p in symbole.params :
                msg += " "+str(p.getIdent())+" in"
                if p.isOut():
                    msg += " out"
                if p.isBool():
                    msg += " boolean"
                else:
                    msg += " integer"
                msg += ';'
            if(msg[-1]==';'):
                msg = msg.rstrip(msg[-1])

            msg +=")"
            
        elif not symbole.isOperation():
            msg += "'"+str(symbole.getIdent())+"'"
            if symbole.isBool():
                msg += " boolean"
            else:
                msg += " integer"
        msg +=" at "+str(symbole.getAdresse())
        print(msg)
        if (symbole.isOperation() and symbole.getIdent()!=parent):
            displaySymboleTable(symbole.symboles,tab+1,symbole.getIdent())

########################################################################
def main():
    global lines
    parser = argparse.ArgumentParser(
        description='Do the syntactical analysis of a NNP program.')
    parser.add_argument('inputfile', type=str, nargs=1,
                        help='name of the input source file')
    parser.add_argument('-o', '--outputfile', dest='outputfile', action='store',
                        default="", help='name of the output file (default: stdout)')
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s 1.0')
    parser.add_argument('-d', '--debug', action='store_const', const=logging.DEBUG,
                        default=logging.INFO, help='show debugging info on output')
    parser.add_argument('-p', '--pseudo-code', action='store_const', const=True, default=False,
                        help='enables output of pseudo-code instead of assembly code')
    parser.add_argument('--show-ident-table', action='store_true',
                        help='shows the final identifiers table')
    args = parser.parse_args()

    filename = args.inputfile[0]
    f = None
    try:
        f = open(filename, 'r')
    except:
        print("Error: can\'t open input file!")
        return

    outputFilename = args.outputfile

    # create logger
    LOGGING_LEVEL = args.debug
    logger.setLevel(LOGGING_LEVEL)
    ch = logging.StreamHandler()
    ch.setLevel(LOGGING_LEVEL)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if args.pseudo_code:
        True
    else:
        True

    lexical_analyser = analex.LexicalAnalyser()
    lines = []
    lineIndex = 0
    for line in f:
        line = line.rstrip('\r\n')
        
        lexical_analyser.analyse_line(lineIndex, line)
        if(len(line)>0):
            if (line[0]!='/'):
                lines.append(line)
        lineIndex = lineIndex + 1
    f.close()
    
    # launch the analysis of the program
    lexical_analyser.init_analyser()
    program(lexical_analyser)

    if args.show_ident_table:
        print("------ IDENTIFIER TABLE ------")
        displaySymboleTable(codeGenerator.getSymboleTable())
        print("------ END OF IDENTIFIER TABLE ------")

    if outputFilename != "":
        try:
            output_file = open(outputFilename, 'w')
        except:
            print("Error: can\'t open output file!")
            return
    else:
        output_file = sys.stdout

    # Outputs the generated code to a file
    instrIndex = 0
    while instrIndex < len(codeGenerator.compilationUnits):
        output_file.write("%s\n" % str(
            codeGenerator.get_instruction_at_index(instrIndex)))
        instrIndex += 1

    if outputFilename != "":
        output_file.close()

########################################################################


if __name__ == "__main__":
    main()
