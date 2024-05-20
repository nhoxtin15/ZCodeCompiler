from Emitter import *
from functools import reduce

from Frame import Frame
from abc import ABC
from Visitor import *
from AST import *


#class for code generation

class CodeGenerator:
    def gen(self, ast, path):
        # ast: AST
        # dir_: String
        gc = CodeGenVisitor(ast, path)
        gc.visit(ast, None)

class Access():
    def __init__(self, frame, symbol, isLeft, checkTypeLHS_RHS = False):
        self.frame = frame # frame for simulating the operand stack and get Label
        self.symbol = symbol # list of dictionary (for symbol table)
        self.isLeft = isLeft # for knowing lft hand side or not (load or store)
        self.checkTypeLHS_RHS = checkTypeLHS_RHS # for checking type of LHS or RHS (if true)


class CodeGenVisitor(BaseVisitor):
    def __init__(self, astTree, path):
        self.astTree = astTree
        self.path = path
        self.className = "ZCodeClass" #for class
        self.emit = Emitter(self.path + "/" + self.className  + ".j")
        self.Listfunction = [] #list of function
        self.function = None #current function (for return to change current function type)
        self.Return = False
        self.arrayCell = "" 
    
    ################################
    #                              #
    #           Utility            #
    #                              #
    ################################

    #for type infereing
    def CheckTypeLHS_RHS(self, LHS, RHS, o):
        #visit right -> left
        _, rightType = self.visit(RHS, Access(o.frame, o.symbol, False, True))
        _, leftType = self.visit(LHS, Access(o.frame, o.symbol, True, True))
        
        #if left is empty -> change left
        if isinstance(leftType, Zcode):
            leftType.typ = rightType
            self.emit.setType(leftType) 
        #if right is empty -> change right
        elif isinstance(rightType, Zcode):
           rightType.typ = leftType
           self.emit.setType(leftType) 
    
    ################################
    #                              #
    #             Type             #
    #                              #
    ################################

    def visitNumberLiteral(self, ast, o):
        #visit the number
        return self.emit.emitPUSHCONST(ast.value, NumberType(), o.frame) if not o.checkTypeLHS_RHS else None, NumberType()
    def visitBooleanLiteral(self, ast, o):
        #visit the boolean
        return self.emit.emitPUSHCONST(ast.value, BoolType(), o.frame) if not o.checkTypeLHS_RHS else None, BoolType()
    def visitStringLiteral(self, ast, o):
        #visit the string
        return self.emit.emitPUSHCONST("\"" + ast.value + "\"", StringType(), o.frame) if not o.checkTypeLHS_RHS else None, StringType()
    
    def visitArrayType(self, ast, param):
        #for type checking 
        return None, ast
    def visitNumberType(self, ast, param):
        #for type checking 
        return None, NumberType()
    def visitVoidType(self, ast, param):
        #for type checking 
        return None, VoidType()
    def visitBoolType(self, ast, param):
        #for type checking 
        return None, BoolType()
    def visitStringType(self, ast, param):
        #for type checking 
        return None, StringType()
    def visitFuncZcode(self, ast, param):
        #for type checking 
        return None, ast.typ if ast.typ else ast
    def visitVarZcode(self, ast, param):
        #for type checking 
        return None, ast.typ if ast.typ else ast
    
    ################################
    #                              #
    #  Block, Continue and Break   #
    #                              #
    ################################
    def visitBlock(self, ast, o):
        symbolnew = [{}] + o.symbol 
        o.frame.enterScope(False) 
        self.emit.printout(self.emit.emitLABEL(o.frame.getStartLabel(), o.frame)) #* đánh số tầm vực mới
        for item in ast.stmt: 
            if(item): #if comment -> ignore
                self.visit(item,Access(o.frame, symbolnew, False))   
        self.emit.printout(self.emit.emitLABEL(o.frame.getEndLabel(), o.frame)) #* đánh số tầm vực mới
        o.frame.exitScope()  
    
    def visitContinue(self, ast, o):
        self.emit.printout(self.emit.emitGOTO(o.frame.getContinueLabel(), o.frame))

    def visitBreak(self, ast, o):
        self.emit.printout(self.emit.emitGOTO(o.frame.getBreakLabel(), o.frame))


    ################################
    #                              #
    #              ID              #
    #                              #
    ################################


    def visitId(self, ast, o):
        #frame and symbol
        frame = o.frame
        Symbol = o.symbol
        
        #check type and infer type of LHS or RHS
        if o.checkTypeLHS_RHS:
            for item in Symbol:
                if item.get(ast.name):
                    
                    return None, item[ast.name].typ if item[ast.name].typ else item[ast.name]
        
        #extract the variable from the symbol table
        index = 0
        sym = None
        for i in range(len(Symbol)):
            if(Symbol[i].get(ast.name)):
                sym = Symbol[i][ast.name]
                index = i
                break
        #if symbol is at the end -> static
        #else -> local variable
        if(index == len(Symbol)-1):
            #static
            if(o.isLeft):
                return self.emit.emitPUTSTATIC(self.className + "/" + ast.name, Symbol[-1][ast.name].typ, frame), Symbol[-1][ast.name].typ
            else:

                return self.emit.emitGETSTATIC(self.className + "/" + ast.name, Symbol[-1][ast.name].typ, frame), Symbol[-1][ast.name].typ
        else:
            if(o.isLeft):
                return self.emit.emitWRITEVAR(ast.name,sym.typ, sym.index, frame), sym.typ
            else:
                
                return self.emit.emitREADVAR(ast.name, sym.typ, sym.index, frame), sym.typ


        
        #if symbol size 
        if len(Symbol) > 1:
            #find the ID
            sym = None
            for symDict in Symbol:
                if(symDict.get(ast.name)):
                    sym = symDict[ast.name]
                    break
            

            
            if(o.isLeft):
                return self.emit.emitWRITEVAR(ast.name, sym.index, frame), sym.typ
            else:
                return self.emit.emitREADVAR(ast.name, sym.typ, sym.index, frame), sym.typ
        else:
            #Static
            if(o.isLeft):
                return self.emit.emitPUTSTATIC(self.className + "." + ast.name, Symbol[0][ast.name].index, frame), Symbol[0][ast.name].typ
            else:
                return self.emit.emitGETSTATIC(self.className + "." + ast.name, Symbol[0][ast.name].index, frame), Symbol[0][ast.name].typ





    ################################
    #                              #
    #       Binary and Unary       #
    #                              #
    ################################

    def visitBinaryOp(self, ast, o):
        op = ast.op
        
        
        
        if op in ['+','-']:
            if o.checkTypeLHS_RHS:
                #visit Left infer type
                self.CheckTypeLHS_RHS(ast.left, NumberType(), o)
                #visit Right infer type
                self.CheckTypeLHS_RHS(ast.right, NumberType(), o)
                return None, NumberType()
            #visit left and right(extract the code)
            codeLeft, _ = self.visit(ast.left, Access(o.frame, o.symbol, False))
            codeRight, _ = self.visit(ast.right, Access(o.frame, o.symbol, False))
            return codeLeft + codeRight + self.emit.emitADDOP(op, NumberType(), o.frame), NumberType()
        elif op in ['*','/']:
            if o.checkTypeLHS_RHS:
                #visit Left infer type
                self.CheckTypeLHS_RHS(ast.left, NumberType(), o)
                #visit Right infer type
                self.CheckTypeLHS_RHS(ast.right, NumberType(), o)
                return None, NumberType()
            #visit left and right(extract the code)
            codeLeft, _ = self.visit(ast.left, Access(o.frame, o.symbol, False))
            codeRight, _ = self.visit(ast.right, Access(o.frame, o.symbol, False))
            return codeLeft + codeRight + self.emit.emitMULOP(op, NumberType(), o.frame), NumberType()
        elif op in ['%']:
            if o.checkTypeLHS_RHS:
                #visit Left infer type
                self.CheckTypeLHS_RHS(ast.left, NumberType(), o)
                #visit Right infer type
                self.CheckTypeLHS_RHS(ast.right, NumberType(), o)
                return None, NumberType()
            #visit left and right(extract the code)
            codeLeft, _ = self.visit(ast.left, Access(o.frame, o.symbol, False))
            codeRight, _ = self.visit(ast.right, Access(o.frame, o.symbol, False))
            #visit the operand again (for simulating the stack)
            codeLeft, _ = self.visit(ast.left, Access(o.frame, o.symbol, False))
            codeRight, _ = self.visit(ast.right, Access(o.frame, o.symbol, False))
            return codeLeft + codeRight +codeLeft + codeRight + self.emit.emitMOD(o.frame) , NumberType() 
        elif op in ['=','!=', '<', '>', '>=', '<=']:
            if o.checkTypeLHS_RHS:
                #visit Left infer type
                self.CheckTypeLHS_RHS(ast.left, NumberType(), o)
                #visit Right infer type
                self.CheckTypeLHS_RHS(ast.right, NumberType(), o)
                return None, BoolType()
            #visit left and right(extract the code)
            codeLeft, _ = self.visit(ast.left, Access(o.frame, o.symbol, False))
            codeRight, _ = self.visit(ast.right, Access(o.frame, o.symbol, False))
            return codeLeft + codeRight + self.emit.emitREOP(op, NumberType(), o.frame), BoolType()
        elif op == 'and':
            if o.checkTypeLHS_RHS:
                #visit Left infer type
                self.CheckTypeLHS_RHS(ast.left, BoolType(), o)
                #visit Right infer type
                self.CheckTypeLHS_RHS(ast.right, BoolType(), o)
                return None, BoolType()
            #visit left and right(extract the code)
            codeLeft, _ = self.visit(ast.left, Access(o.frame, o.symbol, False))
            codeRight, _ = self.visit(ast.right, Access(o.frame, o.symbol, False))
            return codeLeft + codeRight + self.emit.emitANDOP(o.frame), BoolType()
        elif op == 'or':
            if o.checkTypeLHS_RHS:
                #visit Left infer type
                self.CheckTypeLHS_RHS(ast.left, BoolType(), o)
                #visit Right infer type
                self.CheckTypeLHS_RHS(ast.right, BoolType(), o)
                return None, BoolType()
            #visit left and right(extract the code)
            codeLeft, _ = self.visit(ast.left, Access(o.frame, o.symbol, False))
            codeRight, _ = self.visit(ast.right, Access(o.frame, o.symbol, False))
            return codeLeft + codeRight + self.emit.emitOROP(o.frame), BoolType()
        elif op in ['==']:
            if o.checkTypeLHS_RHS:
                #visit Left infer type
                self.CheckTypeLHS_RHS(ast.left, StringType(), o)
                #visit Right infer types
                self.CheckTypeLHS_RHS(ast.right, StringType(), o)
                return None, BoolType()
            #visit left and right(extract the code)
            codeLeft, _ = self.visit(ast.left, Access(o.frame, o.symbol, False))
            codeRight, _ = self.visit(ast.right, Access(o.frame, o.symbol, False))
            return codeLeft + codeRight + self.emit.emitINVOKEVIRTUAL("java/lang/String/equals",FuncZcode("java/lang/String/equals",BoolType(),[""]), o.frame), BoolType()
        elif op in ['...']:
            if o.checkTypeLHS_RHS:
                #visit Left infer type
                self.CheckTypeLHS_RHS(ast.left, StringType(), o)
                #visit Right infer type
                self.CheckTypeLHS_RHS(ast.right, StringType(), o)
                return None, StringType()
            #visit left and right(extract the code)
            codeLeft, _ = self.visit(ast.left, Access(o.frame, o.symbol, False))
            codeRight, _ = self.visit(ast.right, Access(o.frame, o.symbol, False))
            return codeLeft + codeRight + self.emit.emitINVOKEVIRTUAL("java/lang/String/concat",FuncZcode("java/lang/String/concat",StringType(),[StringType()]), o.frame), StringType()
        
    

    def visitUnaryOp(self, ast, o):
        op = ast.op
        #type
        if o.checkTypeLHS_RHS:
            if op in ['-']:
                self.CheckTypeLHS_RHS(ast.operand, NumberType(), o)
                return None, NumberType()
            elif op in ['not']:
                self.CheckTypeLHS_RHS(ast.operand, BoolType(), o)
                return None, BoolType()
        
        #visit the operand
        code, _ = self.visit(ast.operand, o)
        if op in ['-']:
            return code + self.emit.emitNEGOP(NumberType(), o.frame), NumberType()
        elif op in ['not']:
            return code + self.emit.emitNOT(BoolType(),o.frame), BoolType()

    ################################
    #                              #
    #            ARRAY             #
    #                              #
    ################################

    
    def visitArrayLiteral(self, ast, o):
        frame = o.frame
        #type checking
        if o.checkTypeLHS_RHS:
            mainTyp = None
            for item in ast.value:
                _, checkTyp = self.visit(item, o)
                if mainTyp is None and isinstance(checkTyp, (BoolType, StringType, NumberType, ArrayType)):
                    mainTyp = checkTyp
                    break
        
            for item in ast.value:
                self.CheckTypeLHS_RHS(mainTyp, item, o)
            
            if isinstance(mainTyp, (BoolType, StringType, NumberType)):
                return None, ArrayType([len(ast.value)], mainTyp)
            return None, ArrayType([float(len(ast.value))] + mainTyp.size, mainTyp.eleType)

        #visit the it self but with type checking to extract the type
        _,typeArr = self.visitArrayLiteral(ast,Access(frame,o.symbol,False,True))
        code = ""
        
        #init the array
        if not isinstance(ast.value[0],ArrayLiteral):
            #1d Array

            #size of the array 
            codesize = self.emit.emitPUSHCONST(len(ast.value), NumberType(), frame)
            code += codesize
            code+= self.emit.emitF2I(frame)

            #create the array
            codeCreateArray = self.emit.emitNEWARRAY(typeArr.eleType, frame)
            code+= codeCreateArray

            #init the value
            for i in range(len(ast.value)):
                #get the address of the array
                code+= self.emit.emitDUP(frame)
                #index
                code += self.emit.emitPUSHCONST(i, NumberType(), frame)
                code += self.emit.emitF2I(frame)
                #the value
                codeValue, _ = self.visit(ast.value[i], Access(frame,o.symbol,False))
                code+= codeValue
                #store the value in the indexed of the array
                code += self.emit.emitASTORE(typeArr.eleType, frame)
        else:
            #size of the multi array (use array of address)
            codesize = self.emit.emitPUSHCONST(len(ast.value), NumberType(), frame)
            code += codesize
            code += self.emit.emitF2I(frame)
            #create the array
            code += self.emit.emitANEWARRAY(ArrayType(typeArr.size[1:],typeArr.eleType), frame)
            
            #init the value
            for i in range(len(ast.value)):
                #get the address of the array
                code += self.emit.emitDUP(frame)
                #index
                code += self.emit.emitPUSHCONST(i, NumberType(), frame)
                code += self.emit.emitF2I(frame)
                #the value
                codeValue, _ = self.visit(ast.value[i], o)
                code+= codeValue
                #store the value in the indexed of the array
                code+=self.emit.emitASTORE(ArrayType([len(ast.value)], typeArr.eleType), frame)
        return code, ArrayType([len(ast.value)], NumberType())
    

       
    def visitArrayCell(self, ast, o):
        #type checking
        if o.checkTypeLHS_RHS:
            _, arr = self.visit(ast.arr, Access(o.frame, o.symbol, False, False))
            for i in ast.idx:
                self.CheckTypeLHS_RHS(NumberType(), i, o)
            if len(arr.size) == len(ast.idx): return None, arr.eleType
            
            return None, ArrayType(arr.size[len(ast.idx):], arr.eleType)   
        

        
        #extract the type
        codeArr,typeArr = self.visit(ast.arr, Access(o.frame, o.symbol, False))
        code = codeArr
        
        
        #if less than -> return an array
        if len(ast.idx) < len(typeArr.size) :
            
            for i in range(len(ast.idx)-1):
                code += self.visit(ast.idx[i], o)[0]
                code += self.emit.emitF2I(o.frame)
                code += self.emit.emitALOAD(typeArr,o.frame)
            code+=self.visit(ast.idx[-1],Access(o.frame,o.symbol,False))[0]
            code+=self.emit.emitF2I(o.frame)
            if o.isLeft:
                self.arrayCell = typeArr
            else:
                code+=self.emit.emitALOAD(typeArr,o.frame)
            
            return code, ArrayType(typeArr.size[len(ast.idx):], typeArr.eleType)   
        else:
            
            for i in range(len(ast.idx)-1):
                code += self.visit(ast.idx[i], o)[0]
                code += self.emit.emitF2I(o.frame)
                code += self.emit.emitALOAD(typeArr,o.frame)
            
            code+=self.visit(ast.idx[-1],Access(o.frame,o.symbol,False))[0]
            code+=self.emit.emitF2I(o.frame)
            if o.isLeft:
                self.arrayCell = typeArr.eleType
                
            else:
                code+=self.emit.emitALOAD(typeArr.eleType,o.frame)
            
        
            return code, typeArr.eleType
        
    ################################
    #                              #
    #        FUNCTION CALL         #
    #                              #
    ################################

    def visitCallExpr(self, ast, o):
        
        #io
        if ast.name.name in ["readNumber", "readBool", "readString"]:
            if ast.name.name == "readNumber": 
                if o.checkTypeLHS_RHS: return None, NumberType()
                return self.emit.emitINVOKESTATIC(f"io/{ast.name.name}", FuncZcode(ast.name.name, NumberType(), []), o.frame), NumberType
            elif ast.name.name == "readBool": 
                if o.checkTypeLHS_RHS: return None, BoolType()
                return self.emit.emitINVOKESTATIC(f"io/{ast.name.name}", FuncZcode(ast.name.name, BoolType(), []), o.frame), NumberType
            elif ast.name.name == "readString": 
                if o.checkTypeLHS_RHS: return None, StringType()
                return self.emit.emitINVOKESTATIC(f"io/{ast.name.name}", FuncZcode(ast.name.name, StringType(), []), o.frame), NumberType

        #* find the function
        function = None
        for item in self.Listfunction:
            if item.name == ast.name.name:
                function = item
        
        #infer type
        if o.checkTypeLHS_RHS:
            for i in range(len(function.param)):
                self.CheckTypeLHS_RHS(function.param[i], ast.args[i], o)
            return None, function.typ if function.typ else function            
            
        
        #* visit the argument -> load to stack -> right(for loading)
        code = ""
        for item in ast.args:
            code += self.visit(item, Access(o.frame,o.symbol,False))[0]
        #call the function
        return code + self.emit.emitINVOKESTATIC(self.className + "/" + ast.name.name, function, o.frame), function.typ if function.typ else function
    
    def visitCallStmt(self, ast, o):
        
        #* phần io
        if ast.name.name in ["writeNumber", "writeBool", "writeString"]:
            if ast.name.name == "writeNumber": self.CheckTypeLHS_RHS(NumberType(), ast.args[0], o)
            elif ast.name.name == "writeBool": self.CheckTypeLHS_RHS(BoolType(), ast.args[0], o)
            elif ast.name.name == "writeString": self.CheckTypeLHS_RHS(StringType(), ast.args[0], o)
            
            argsCode, argsType = self.visit(ast.args[0], o)
            
            self.emit.printout(argsCode)
            self.emit.printout(self.emit.emitINVOKESTATIC(f"io/{ast.name.name}", FuncZcode(ast.name.name, VoidType(), [argsType]), o.frame))
            return

        
        code = ""
        for item in ast.args:
            
            code += self.visit(item,Access(o.frame,o.symbol,False))[0]
            
        self.emit.printout(code)
        
        codeFunction = self.emit.emitINVOKESTATIC(self.className + "/" + ast.name.name, FuncZcode(ast.name.name, VoidType(), [self.visit(i,o)[1] for i in ast.args]), o.frame)
        self.emit.printout(codeFunction)

    ################################
    #                              #
    #          Statement           #
    #                              #
    ################################
    def visitReturn(self, ast, o):
        #Check type
        self.CheckTypeLHS_RHS(self.function, ast.expr if ast.expr else VoidType(),o)
        
        self.Return = True 
        frame = o.frame
        #return stmt
        if ast.expr is None:
            self.emit.printout(self.emit.emitRETURN(VoidType(), frame)) 
        else:
            code, _ = self.visit(ast.expr, o)
            self.emit.printout(code)
            self.emit.printout(self.emit.emitRETURN(self.function.typ, frame))


    def visitAssign(self, ast, o):
        
        self.CheckTypeLHS_RHS(ast.lhs, ast.rhs, o)
        
        frame = o.frame
        rightCode, _ = self.visit(ast.rhs, Access(frame, o.symbol, False))
        leftCode, _ = self.visit(ast.lhs, Access(frame, o.symbol, True))
        
        
        if(isinstance(ast.lhs, ArrayCell)):
            #store array
                #-> print left for geting the address
                #-> print right for getting the value
                #-> store the value in the address
                
            self.emit.printout(leftCode)
            self.emit.printout(rightCode)
            self.emit.printout(self.emit.emitASTORE(self.arrayCell, frame))
            
        else:
            
            self.emit.printout(rightCode)
            self.emit.printout(leftCode)
            
            
            
            
            
  
    
    
  
          
       
    def visitIf(self, ast, o):
        #check type all the expr
        
        self.CheckTypeLHS_RHS(BoolType(), ast.expr, o)        
        for item in ast.elifStmt:
            self.CheckTypeLHS_RHS(BoolType(), item[0], o)   
        
        frame = o.frame

        #label for ending the if
        label_end_if = frame.getNewLabel() 
        
        #first expr 
            #label ending the first stmt
        label_end_first_stmt = frame.getNewLabel()
        codeExpr, _ = self.visit(ast.expr, o)
        self.emit.printout(codeExpr)
        self.emit.printout(self.emit.emitIFFALSE(label_end_first_stmt,o.frame))
        tempCurrentIndex = frame.currIndex

        
        self.visit(ast.thenStmt, o)

        


        self.emit.printout(self.emit.emitGOTO(label_end_if, o.frame))
        self.emit.printout(self.emit.emitLABEL(label_end_first_stmt, o.frame))
        for item in ast.elifStmt:
            label_end_elif = frame.getNewLabel()
            codeExpr, _ = self.visit(item[0], o)
            self.emit.printout(codeExpr)
            self.emit.printout(self.emit.emitIFFALSE(label_end_elif,o.frame))
            frame.currIndex = tempCurrentIndex
            self.visit(item[1], o)
            self.emit.printout(self.emit.emitGOTO(label_end_if, o.frame))
            self.emit.printout(self.emit.emitLABEL(label_end_elif, o.frame))
        if ast.elseStmt:
            frame.currIndex = tempCurrentIndex
            
            self.visit(ast.elseStmt, o)
        


        self.emit.printout(self.emit.emitLABEL(label_end_if, o.frame))


        
        
        
        
    def visitFor(self, ast, o):
        
        #* CHECK TYPE BTL3
        
        self.CheckTypeLHS_RHS(NumberType(), ast.name, o)        
        
        
        self.CheckTypeLHS_RHS(BoolType(), ast.condExpr, o) 
        self.CheckTypeLHS_RHS(NumberType(), ast.updExpr, o) 

        frame = o.frame
        self.visit(ast.name, o)
        
        #class For(Stmt):
            # name: Id
            # condExpr: Expr
            # updExpr: Expr
            # body: Stmt
        
        #label
        labelStartLoop = frame.getNewLabel()
        

        
        #store the for variable (for restoring it)
        self.visit(Assign(Id("for"), ast.name), o)
        #TODO implement
        frame.enterLoop()
        self.emit.printout(self.emit.emitLABEL(labelStartLoop, frame))
        
        #check cond
        self.emit.printout(self.visit(ast.condExpr, Access(frame, o.symbol, False))[0])
        self.emit.printout(self.emit.emitIFTRUE(frame.getBreakLabel(), frame))
        
        #visit the body
        self.visit(ast.body, o)
        
        self.emit.printout(self.emit.emitLABEL(frame.getContinueLabel(), frame))
        
        #update the for variable
        self.visit(Assign(ast.name, BinaryOp('+', ast.name, ast.updExpr)), o)
        self.emit.printout(self.emit.emitGOTO(labelStartLoop, frame))

        #emit label break
        self.emit.printout(self.emit.emitLABEL(frame.getBreakLabel(), frame))
        frame.exitLoop()

        self.visit(Assign(ast.name, Id("for")), o)

    
    ################################
    #                              #
    #           Program            #
    #                              #
    ################################

    def visitProgram(self, ast:Program, o):
        
        codeProLog  = self.emit.emitPROLOG(self.className, "java.lang.Object")
        self.emit.printout(codeProLog)
        
        Symbol = [{}] #list of dictionary
        Main = None
        function = None
        #init all the global variable and function (only init function with the body)
        for item in ast.decl:
            if type(item) is VarDecl:
                index = -1
                Zcode1 = VarZcode(item.name.name, item.varType, index, True if item.varInit else False)
                Symbol[0][item.name.name]= Zcode1
                
                codeEmitAttribute = self.emit.emitATTRIBUTE(item.name.name, item.varType if item.varType else Symbol[0][item.name.name],False,self.className)
                self.emit.printout(codeEmitAttribute)
                Symbol[0][item.name.name].line = self.emit.printIndexNew()

            elif type(item) is FuncDecl and item.body is not None:
                #only visit function with body
                self.Listfunction += [FuncZcode(item.name.name, None, [i.varType for i in item.param])]
                if item.name.name == "main":
                    function = self.Listfunction[-1]
                    Main = item
        
    
        #init all the static variable (<init> function for declaring static varialbe)
        frame = Frame("<init>", VoidType)

        codeEmitMethodInit = self.emit.emitMETHOD(lexeme="<init>", in_=FuncZcode("init", VoidType(), []), isStatic=False, frame=frame)
        self.emit.printout(codeEmitMethodInit)
        frame.enterScope(True)
        codeEmitLabel = self.emit.emitLABEL(frame.getStartLabel(), frame)
        self.emit.printout(codeEmitLabel)

        self.emit.printout(self.emit.emitVAR(frame.getNewIndex(), "this", Zcode(), frame.getStartLabel(), frame.getEndLabel(), frame))

        self.emit.printout(self.emit.emitREADVAR("this", self.className, 0, frame))

        self.emit.printout(self.emit.emitINVOKESPECIAL(frame))

        self.emit.printout(self.emit.emitRETURN(VoidType(), frame))   

        self.emit.printout(self.emit.emitLABEL(frame.getEndLabel(), frame))

        self.emit.printout(self.emit.emitENDMETHOD(frame))

        frame.exitScope()


        #* hàm khởi tạo biến static Zcode (contructor cho static)
        frame = Frame("<clinit>", VoidType)

        self.emit.printout(self.emit.emitMETHOD(lexeme="<clinit>", in_=FuncZcode("clinit", VoidType(), []), isStatic=True, frame=frame))

        frame.enterScope(True)

        self.emit.printout(self.emit.emitLABEL(frame.getStartLabel(), frame))

        #init static variable (init with value)
        for var in ast.decl:
            if type(var) is VarDecl and var.varInit is not None:
                #create an assign for doing the work
                self.visit(Assign(var.name, var.varInit), Access(frame, Symbol, False)) 

            elif type(var) is VarDecl and type(var.varType) is ArrayType:
                #array need init with size
                if len(var.varType.size) == 1:
                    #init array 1D
                    #size of the array
                    codeSize, _ =self.visit(NumberLiteral(var.varType.size[0]), Access(frame, Symbol, False))
                    self.emit.printout(codeSize)
                    self.emit.printout(self.emit.emitF2I(frame)) #change from float to int (size of the array)
                    #create the array
                    self.emit.printout(self.emit.emitNEWARRAY(var.varType.eleType, frame))
                    #store it (this is static)
                    self.emit.printout(self.emit.emitPUTSTATIC(self.className + "/" + var.name.name, var.varType, frame))
                else:
                    #init array multiD
                    for i in var.varType.size:
                        #size of the array
                        
                        codeSize, _ = self.visit(NumberLiteral(i), Access(frame, Symbol, False))
                        self.emit.printout(codeSize)
                        self.emit.printout(self.emit.emitF2I(frame))
                    #create the array
                    self.emit.printout(self.emit.emitMULTIANEWARRAY(var.varType, frame))
                    #store it (this is static)
                    self.emit.printout(self.emit.emitPUTSTATIC(self.className + "/" + var.name.name, var.varType, frame))
        #the return type is VoidType
        self.emit.printout(self.emit.emitRETURN(VoidType(), frame)) 


        self.emit.printout(self.emit.emitLABEL(frame.getEndLabel(), frame))  
        self.emit.printout(self.emit.emitENDMETHOD(frame))
        frame.exitScope()    
    
    
        
        #visit all the function
        i = 0
        for item in ast.decl:
            if type(item) is FuncDecl and item.body is not None and item.name.name != "main":
                self.function = self.Listfunction[i]
                self.visit(item, Symbol)
            if type(item) is FuncDecl and item.body is not None:
                i += 1
                
        
        #the main function
        frame = Frame("main", VoidType)
        #main function declaration
        self.emit.printout(self.emit.emitMETHOD(lexeme="main", in_=FuncZcode("main", VoidType(), [ArrayType([1], StringType())]), isStatic=True, frame=frame))
        
        frame.enterScope(True)

        self.emit.printout(self.emit.emitLABEL(frame.getStartLabel(), frame))

        self.emit.printout(self.emit.emitVAR(frame.getNewIndex(), "args", ArrayType([], StringType()), frame.getStartLabel(), frame.getEndLabel(), frame))

        index = frame.getNewIndex()
        #the for variable for storing for loop state (the variable is the same after the for loop)
        typeParam = {"for": VarZcode("for", NumberType(), index, True)}
        self.emit.printout(self.emit.emitVAR(index, "for", NumberType(), frame.getStartLabel(), frame.getEndLabel(), frame))

        #add main function
        self.function = function
        #visit the body
        self.visit(Main.body, Access(frame, [typeParam] + Symbol, False))
        #the main has to return Void
        self.emit.printout(self.emit.emitRETURN(VoidType(), frame))

        self.emit.printout(self.emit.emitLABEL(frame.getEndLabel(), frame))   
        self.emit.printout(self.emit.emitENDMETHOD(frame))
        
        frame.exitScope()   
        #end of the program 
        self.emit.emitEPILOG()
    

    ################################
    #                              #
    #     VarDecl and FuncDecl     #
    #                              #
    ################################

    
    def visitVarDecl(self, ast, o):
        '''Vardecl
            ast:
                name: Id
                varType: Type
                varInit: Expr
            Work to do:
                - Declare the variable (emit the VAR code)
                - Assign the variable if it has the init value
                - Init the array if it has the size (all array need to be init with the size)
        '''

        # codeEmitVAR = self.emit.emitVAR(o.frame.getNewIndex(),ast.name.name,ast.varType,o.frame.getStartLabel(),o.frame.getEndLabel(),o.frame)
        
        #Declare the variable
        VarialbeZcode = (VarZcode(ast.name.name, ast.varType, o.frame.getNewIndex(), True if ast.varInit else False))
        codeEmitVAR = self.emit.emitVAR(VarialbeZcode.index,VarialbeZcode.name,VarialbeZcode.typ if VarialbeZcode.typ else VarialbeZcode,o.frame.getStartLabel(),o.frame.getEndLabel(),o.frame) 
        o.symbol[0][ast.name.name] = VarialbeZcode
        self.emit.printout(codeEmitVAR)
        o.symbol[0][ast.name.name].line = self.emit.printIndexNew()
        
        #init the variable if the variable has the init value or it is array
        if ast.varInit is not None:
            #init the variable
            self.visit(Assign(ast.name, ast.varInit), o)
        elif type(ast.varType) is ArrayType:
            #init the array
            if len(ast.varType.size) == 1:
                #init array 1D
                self.emit.printout(self.visit(NumberLiteral(ast.varType.size[0]), Access(o.frame, o.symbol, False))[0])
                self.emit.printout(self.emit.emitF2I(o.frame))
                self.emit.printout(self.emit.emitNEWARRAY(ast.varType.eleType, o.frame))
                self.emit.printout(self.visit(ast.name,Access(o.frame,o.symbol,True))[0])
                
            else:
                #init array multiD
                for i in ast.varType.size:
                    self.emit.printout(self.visit(NumberLiteral(i), Access(o.frame, o.symbol, False))[0])
                    self.emit.printout(self.emit.emitF2I(o.frame))
                self.emit.printout(self.emit.emitMULTIANEWARRAY(ast.varType, o.frame))
                self.emit.printout(self.visit(ast.name,Access(o.frame,o.symbol,True))[0])

      
                              
    def visitFuncDecl(self, ast, Symbol):
        '''
        FuncDecl
            ast:
                name: Id
                param: List[VarDecl]
                returnType: Type
                body: stmt
            Work to do:
                - Create the function (emit the METHOD code)
                - Visit the body
                - Return the function (emit the RETURN code) (if the function has no return value, return VoidType)

        '''
        self.Return = False
        
        #dont know the return type -> None
        frame = Frame(ast.name.name, None)
        
        #define the function
        codeCreateFunction = self.emit.emitMETHOD(ast.name.name, self.function, True, frame)
        self.emit.printout(codeCreateFunction)
        #add the function to the list
        self.function = FuncZcode(ast.name.name, None, [i.varType for i in ast.param])
        self.Listfunction += [self.function]
        #get the index
        self.function.line = self.emit.printIndexNew()
        
        #new Symbol
        Symbol = [{}] + Symbol
        
        frame.enterScope(True)
        
        self.emit.printout(self.emit.emitLABEL(frame.getStartLabel(), frame))
        
        #param
        for i in ast.param:
            #just emit the VAR code
                #not that array here doesn't need to init as it take the value from the caller
            VarialbeZcode = (VarZcode( i.name.name, i.varType, frame.getNewIndex(), False))
            codeEmitVAR = self.emit.emitVAR(VarialbeZcode.index,VarialbeZcode.name,VarialbeZcode.typ if VarialbeZcode.typ else VarialbeZcode,frame.getStartLabel(),frame.getEndLabel(),frame) 
            Symbol[0][i.name.name] = VarialbeZcode
            self.emit.printout(codeEmitVAR)

            # newParam = VarZcode(ast.param[i].name.name, ast.param[i].varType, frame.getNewIndex(), True)
            # Symbol[0][ast.param[i].name.name] = newParam
            # self.emit.printout(self.emit.emitVAR(newParam.index, newParam.name, newParam.typ, frame.getStartLabel(), frame.getEndLabel(), frame))
            # Symbol[0][ast.param[i].name.name].line = self.emit.printIndexNew()
        
        #for variable (for loop)
        index = frame.getNewIndex()
        forVariable = VarZcode("for", NumberType(), index, True)
        Symbol[0]["for"] = forVariable
        self.emit.printout(self.emit.emitVAR(index, "for", NumberType(), frame.getStartLabel(), frame.getEndLabel(), frame))

        #visit the body
        if ast.body:
            self.visit(ast.body, Access(frame, Symbol, False))
            #if not return -> return VoidType
            if not self.Return:
                #change the type of the function
                self.CheckTypeLHS_RHS(self.function,VoidType(), Access(frame, Symbol, False))
                self.emit.printout(self.emit.emitRETURN(VoidType(), frame))

        
        
        self.emit.printout(self.emit.emitLABEL(frame.getEndLabel(), frame))
        self.emit.printout(self.emit.emitENDMETHOD(frame))
        frame.exitScope()

        

    

     

    
        

                                     
        
        

     

        
        


       
        
    





    
        

