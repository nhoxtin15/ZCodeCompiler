
from AST import *
from Visitor import *
from Utils import Utils
from StaticError import *
from functools import reduce

class Zcode(Type):
    pass

class FuncZcode(Zcode):
    def __init__(self, param = [], typ = None, body = False):
        self.param = param
        self.typ = typ
        self.body = body
    def __str__(self):
        return f"FuncZcode(param=[{', '.join(str(i) for i in self.param)}],typ={str(self.typ)},body={self.body})"

class VarZcode(Zcode):
    def __init__(self, typ = None):
        self.typ = typ    
    def __str__(self):
        return f"VarZcode(type={self.typ})"

class ArrayZcode(Type):
    def __init__(self, eleType,ast):
        self.eleType = eleType
        self.ast = ast
    def __str__(self):
        return f"ArrayZcode(eleType=[{', '.join(str(i) for i in self.eleType)}])"
    
class CannotBeInferredZcode(Type):
    def __str__(self):
        return "CannotBeInferredZcode()"

class StaticChecker(BaseVisitor, Utils):
    def __init__(self,ast):
        self.ast = ast 
        self.BlockFor = 0
        self.function = None
        self.Return = False
        self.listFunction = {
            "readNumber" : FuncZcode([], NumberType(), True),
            "readBool" : FuncZcode([], BoolType(), True),
            "readString" : FuncZcode([], StringType(), True),
            "writeNumber" : FuncZcode([NumberType()], VoidType(), True),
            "writeBool" : FuncZcode([BoolType()], VoidType(), True),
            "writeString" : FuncZcode([StringType()], VoidType(), True)
        }
    
    def print(self):
        print(f"BlockFor {self.BlockFor}")
        print(f"function {str(self.function)}")
        print(f"Return {self.Return}")
        print(f"listFunction :")
        for key, value in self.listFunction.items():
            print(f"    {key}  {str(value)}")       
    
    def check(self):
        self.visit(self.ast, [{}])
        return None

    def LHS_RHS_stmt(self,LHS : Type, RHS : Type, ast, param):
        
        # print(f"LHS_RHS_STMT {LHS} {RHS}")
        #check cannot be infered -> final desitnation, if error -> raise
        if isinstance(LHS,CannotBeInferredZcode) or isinstance(RHS,CannotBeInferredZcode):
            
            raise TypeCannotBeInferred(ast)
        elif isinstance(LHS,Zcode) and isinstance(RHS,Zcode):
            raise TypeCannotBeInferred(ast)
        elif isinstance(LHS,Zcode) and isinstance(RHS,ArrayZcode):
            
            raise TypeCannotBeInferred(ast)
        elif isinstance(LHS,ArrayType) and isinstance(RHS,ArrayZcode):
            RHS = self.visitArrayLiteral(RHS.ast, param, LHS)
            self.LHS_RHS_stmt(LHS,RHS,ast,param)
        elif isinstance(RHS,ArrayZcode):
            raise TypeCannotBeInferred(ast)
        elif isinstance(LHS,Zcode):
            LHS.typ = RHS
            
        elif isinstance(RHS,Zcode):
            RHS.typ = LHS
        elif not self.comparType(LHS,RHS):
            raise TypeMismatchInStatement(ast)
            
        
    def LHS_RHS_expr(self, LHS : Type, RHS : Type,ast, param) -> bool:
        # print(f"LHS_RHS_EXPR {LHS} {RHS}")
        #check cannot be infered -> pass canot infereed upward
        
        if isinstance(LHS,CannotBeInferredZcode) or isinstance(RHS,CannotBeInferredZcode):
            return True
        elif isinstance(LHS,Zcode) and isinstance(RHS,Zcode):
            return True
        elif isinstance(LHS,Zcode) and isinstance(RHS,ArrayZcode):
            return True
        elif isinstance(LHS,ArrayType) and isinstance(RHS,ArrayZcode):
            
            RHS = self.visitArrayLiteral(RHS.ast, param, LHS)
            return self.LHS_RHS_expr(LHS,RHS,ast,param)
        elif isinstance(RHS,ArrayZcode):
            return True
        elif isinstance(LHS,Zcode):
            LHS.typ = RHS
            return False
        elif isinstance(RHS,Zcode):
            RHS.typ = LHS
            return False
        else:
            if not self.comparType(LHS,RHS):
                raise TypeMismatchInExpression(ast)
            return False
             
        

    def comparType(self, LHS : Type, RHS : Type) -> bool:
        if(isinstance(LHS, ArrayType) and isinstance(RHS, ArrayType)):
            if(LHS.size != RHS.size):
                return False
            for i in range(len(LHS.size)):
                if(LHS.size[i] != RHS.size[i]):
                    return False
            return self.comparType(LHS.eleType, RHS.eleType)
        else:
            return type(LHS) == type(RHS)


    def comparListType(self, LHS, RHS):
        if(len(LHS) != len(RHS)):
            return False
        for i in range(len(LHS)):
            if not self.comparType(LHS[i], RHS[i]):
                return False
        return True
    
    def setTypeArray(self, typeArray, typeArrayZcode):
        
        #check length
        if typeArray.size[0] != len(typeArrayZcode.eleType):
            return False
        #1 dimension array
        
        if len(typeArray.size) == 1:
            for i in range(len(typeArrayZcode.eleType)):
                if isinstance(typeArrayZcode.eleType[i], Zcode):
                    typeArrayZcode.eleType[i].typ = typeArray.eleType
                elif isinstance(typeArrayZcode.eleType[i], ArrayZcode):
                    #multiple dimension to 1 -> return false
                    return False
                else:
                    if not self.comparType(typeArray.eleType, typeArrayZcode.eleType[i]): return False
                
            
            
        #multiple dimension array
        
        else:
            #iterate through the array
                #if the element is Zcode -> define the type of the Zcode by the array typ
                #if the element is ArrayZcode -> check the type of the array 
                #if the element is not Zcode or ArrayZcode -> check the type of the element
            for i in range(len(typeArrayZcode.eleType)):
                if isinstance(typeArrayZcode.eleType[i], Zcode):
                    typeArrayZcode.eleType[i].typ = ArrayType(typeArray.size[1:], typeArray.eleType)
                elif isinstance(typeArrayZcode.eleType[i], ArrayZcode):
                    if not self.setTypeArray(ArrayType(typeArray.size[1:], typeArray.eleType), typeArrayZcode.eleType[i]):
                        
                        return False
                else:
                    if not self.comparType(ArrayType(typeArray.size[1:], typeArray.eleType), typeArrayZcode.eleType[i]):
                        return False
        
        return True

    def visitProgram(self, ast, param):
        for i in ast.decl: 
            self.visit(i, param)
        #check no definition for a function in self.listFunction
        for i in self.listFunction:
            if(self.listFunction.get(i).body == False): raise NoDefinition(i)
        

        #check no entry point in self.listFunction
        
        if (self.listFunction.get('main') is None): raise NoEntryPoint()
        elif (self.listFunction.get('main').body == False): raise NoEntryPoint()
        elif (len(self.listFunction.get('main').param) != 0): raise NoEntryPoint()
        elif (not isinstance(self.listFunction['main'].typ,VoidType)): raise NoEntryPoint()

        
    def visitVarDecl(self, ast, param):
        
        if param[0].get(ast.name.name):
            raise Redeclared(Variable(), ast.name.name)
        
        param[0][ast.name.name] = VarZcode(ast.varType)
        
        
        if ast.varInit:
            right = self.visit(ast.varInit, param)
            left = self.visit(ast.name, param)
            self.LHS_RHS_stmt(left, right, ast,param)

    def visitFuncDecl(self, ast, param):
        if self.listFunction.get(ast.name.name) is not None:
            if self.listFunction.get(ast.name.name).body:
                raise Redeclared(Function(), ast.name.name)
            elif ast.body is None:
                raise Redeclared(Function(), ast.name.name)
        
        
        if ast.body is None:
            typeParam = [] 
            for i in ast.param:
                typeParam.append(i.varType)
            
            self.listFunction[ast.name.name] = FuncZcode(typeParam, None, False)
            return

         
        listParam = {} 
        typeParam = [] 
        
        for i in ast.param:
            if listParam.get(i.name.name) is None:
            
                listParam[i.name.name] = VarZcode(i.varType)
                typeParam.append(i.varType)
            else:
                raise Redeclared(Parameter(), i.name.name)
        
        
        if self.listFunction.get(ast.name.name):
            #there is a definition for this
                #check if the param is the same
                    #if the param it not the same -> Redeclared
            if(self.comparListType(self.listFunction[ast.name.name].param, typeParam)):
                self.function = self.listFunction[ast.name.name]

                self.listFunction[ast.name.name].body = True
                self.Return = False 
            
                self.visit(ast.body,[listParam] + param)
            else:
                raise Redeclared(Function(), ast.name.name)
        else:
            #there is no definition for this
                #create a new function
                #add the function to the listFunction
            self.listFunction[ast.name.name] = FuncZcode(typeParam, None, True)
            
            self.Return = False
            self.function = self.listFunction[ast.name.name] 
            
            self.visit(ast.body, [listParam] + param)
        
        
        if not self.Return:
            if self.listFunction[ast.name.name].typ is None: 
                self.listFunction[ast.name.name].typ = VoidType()
            elif not isinstance(self.listFunction[ast.name.name].typ, VoidType):
                raise TypeMismatchInStatement(Return(None))
                
 
    def visitId(self, ast, param):
        #find the variable in the list of variable
        temp_id = None
        
        for i in param:
            if i.get(ast.name) is not None:
                temp_id = i[ast.name]
                break

        #check the id
            #if the id is not declared -> Undeclared
            #if the type of the id is not defined -> return the Varzcode (for changing it)
            #if the type of the id is defined -> return the type of the id (for using)
        if temp_id is None:
            raise Undeclared(Identifier(), ast.name)
        elif temp_id.typ is None:
            return temp_id
        return temp_id.typ



    def visitCallExpr(self, ast, param):
        if self.listFunction.get(ast.name.name) is None:
            raise Undeclared(Function(), ast.name.name)
        
        #check param
            #if arrs's type is not defined -> define
            #if different type -> raise TypeMismatchInStatement
        list_args_type = [self.visit(x, param) for x in ast.args]
        list_param = self.listFunction[ast.name.name].param
        
        #check the args and the parameters
            #on the way, if found Zcode -> define the type of the Zcode
            #if the type of the args is different from the type of the parameters -> raise TypeMismatchInStatement
        if(len(list_args_type) != len(list_param)):
            raise TypeMismatchInExpression(ast)
        
        for i in range(len(list_args_type)):
            right = list_args_type[i]
            left = list_param[i]
            canNotInferred = self.LHS_RHS_expr(left, right, ast,param)
            if canNotInferred:
                return CannotBeInferredZcode()
        
        
        #return type of function
            #if the type of the function is not defined -> return the function
            #if the type of the function is VoidType -> raise TypeMismatchInExpression
            
        
        if self.comparType(self.listFunction[ast.name.name].typ, VoidType()):
            raise TypeMismatchInExpression(ast)
        if self.listFunction[ast.name.name].typ is None:
            return self.listFunction[ast.name.name]
        return self.listFunction[ast.name.name].typ


    def visitCallStmt(self, ast, param):
        #check undeclared
        if self.listFunction.get(ast.name.name) is None:
            raise Undeclared(Function(), ast.name.name)
        
        #check param
        if len(self.listFunction[ast.name.name].param) != len(ast.args):
            raise TypeMismatchInStatement(ast)
        
        list_args_type = [self.visit(x, param) for x in ast.args]
        list_param = self.listFunction[ast.name.name].param
        
        #compare the list type
            #try to infer the type or detect type cannot be inferred
        if(len(list_args_type) != len(list_param)):
            raise TypeMismatchInStatement(ast)
        
        for i in range(len(list_args_type)):
            Right = list_args_type[i]
            Left = list_param[i]
            self.LHS_RHS_stmt(Left, Right, ast,param)


                
        if(self.listFunction[ast.name.name].typ is None):
            self.listFunction[ast.name.name].typ = VoidType()
        elif not self.comparType(self.listFunction[ast.name.name].typ, VoidType()):
            raise TypeMismatchInStatement(ast)
        

    def visitIf(self, ast, param):
        #condition
        type_cond = self.visit(ast.expr, param)
        
        self.LHS_RHS_stmt(BoolType(), type_cond, ast,param)
        
        #visit then
        self.visit(ast.thenStmt, param)
        
        #elif
            #tuple (condition, stmt)
        for i in ast.elifStmt:
            cond = self.visit(i[0], param)
            self.LHS_RHS_stmt(BoolType(), cond, ast,param)
            self.visit(i[1], param)
        
        #else
        if ast.elseStmt is not None:
            self.visit(ast.elseStmt,param)
        
    def visitFor(self, ast, param):
        # name: Id
        # condExpr: Expr
        # updExpr: Expr
        # body: Stmt
        if(param[0].get(ast.name.name) is not None):
            type_if = self.visit(ast.name,param)
            self.LHS_RHS_stmt(NumberType(), type_if, ast,param)
        
        #check the type of ast.condExpr
        type_cond = self.visit(ast.condExpr,param)
        self.LHS_RHS_stmt(BoolType(), type_cond, ast,param)

        #check the type of ast.updExpr
        updExpr = self.visit(ast.updExpr,param)
        self.LHS_RHS_stmt(NumberType(), updExpr, ast,param)
        
        
        self.BlockFor += 1 #! vào trong vòng for nào anh em
        self.visit(ast.body, param)
        self.BlockFor -= 1 #! cút khỏi vòng for nào anh em
    
    def visitReturn(self, ast, param):
        self.Return = True
        Right = self.visit(ast.expr, param) if ast.expr else VoidType()
        Left = self.function.typ if self.function.typ else self.function
        
        self.LHS_RHS_stmt(Left, Right, ast,param)

    def visitAssign(self, ast, param):
        right = self.visit(ast.rhs, param)
        left = self.visit(ast.lhs, param)
        
        self.LHS_RHS_stmt(left, right, ast,param)
            
    def visitBinaryOp(self, ast, param):
        op = ast.op
        if op in ['+', '-', '*', '/', '%']:
            left = self.visit(ast.left, param)
            canNotInferLeft = self.LHS_RHS_expr(NumberType(),left, ast,param)
            
            if canNotInferLeft:
                return CannotBeInferredZcode()
            right = self.visit(ast.right, param)
            canNotInferRight = self.LHS_RHS_expr(NumberType(),right, ast,param)
            if canNotInferRight:
                return CannotBeInferredZcode()
            
            
            
            return NumberType()

            
        elif op in ['=', '!=', '<', '>', '>=', '<=']:
            left = self.visit(ast.left, param)
            canNotInferLeft = self.LHS_RHS_expr(NumberType(),left, ast, param)
            if canNotInferLeft:
                return CannotBeInferredZcode()
            right = self.visit(ast.right, param)
            canNotInferRight = self.LHS_RHS_expr(NumberType(),right, ast,param)
            if canNotInferRight:
                return CannotBeInferredZcode()
            return BoolType()
        elif op in ['and', 'or']:
            left = self.visit(ast.left, param)
            canNotInferLeft = self.LHS_RHS_expr(BoolType(), left, ast,param)
            if canNotInferLeft:
                return CannotBeInferredZcode()
            right = self.visit(ast.right, param)
            canNotInferRight = self.LHS_RHS_expr(BoolType(), right, ast,param)
            if canNotInferRight:
                return CannotBeInferredZcode()
            return BoolType()
        elif op in ['==']:
            left = self.visit(ast.left, param)
            canNotInferLeft = self.LHS_RHS_expr(StringType(), left, ast,param)
            if canNotInferLeft:
                return CannotBeInferredZcode()
            right = self.visit(ast.right, param)
            canNotInferRight = self.LHS_RHS_expr(StringType(), right, ast,param)
            if canNotInferRight:
                return CannotBeInferredZcode()
            return BoolType()
        elif op in ['...']:
            left = self.visit(ast.left, param)
            canNotInferLeft = self.LHS_RHS_expr(StringType(), left, ast,param)
            if canNotInferLeft:
                return CannotBeInferredZcode()
            right = self.visit(ast.right, param)
            canNotInferRight = self.LHS_RHS_expr(StringType(), right, ast,param)
            if canNotInferRight:
                return CannotBeInferredZcode()
            return StringType()
        
        
    def visitUnaryOp(self, ast, param):
        op = ast.op
        if op in ['+', '-']:
            right = self.visit(ast.operand, param)
            canNotInferRight = self.LHS_RHS_expr(right, NumberType(), ast,param)
            if canNotInferRight:
                return CannotBeInferredZcode()
            return NumberType()
        if op in ['not']:

            right = self.visit(ast.operand, param)
            canNotInferRight = self.LHS_RHS_expr(right, BoolType(), ast,param)
            if canNotInferRight:
                return CannotBeInferredZcode()
            return BoolType()
            
    def visitArrayCell(self, ast, param):
        arr = self.visit(ast.arr, param)
        if isinstance(arr, (BoolType, StringType, NumberType)):
            raise TypeMismatchInExpression(ast)
        elif not isinstance(arr, ArrayType):
            return CannotBeInferredZcode()

        for item in ast.idx:
            checkTyp = self.visit(item, param)
            if self.LHS_RHS_expr(checkTyp, NumberType(), ast,param):
                return CannotBeInferredZcode()

            
        if len(arr.size) < len(ast.idx): raise TypeMismatchInExpression(ast)
        elif len(arr.size) == len(ast.idx): return arr.eleType
        return ArrayType(arr.size[len(ast.idx):], arr.eleType)   

    def visitArrayLiteral(self, ast, param, mainTyp = None):
        
        if mainTyp is not None:
            result = mainTyp
            mainTyp = mainTyp.eleType if len(mainTyp.size) == 1 else ArrayType(mainTyp.size[1:],mainTyp.eleType)
            
            for item in ast.value:
                RHS  = self.visit(item, param)
                
                if isinstance(RHS,CannotBeInferredZcode) or isinstance(mainTyp,CannotBeInferredZcode):
                    return CannotBeInferredZcode()
                if isinstance(mainTyp,ArrayType) and isinstance(RHS,ArrayZcode):
                    mainTyp = self.visitArrayLiteral(RHS.ast, param, mainTyp)
                elif isinstance(RHS, ArrayZcode):
                    return CannotBeInferredZcode()
                elif isinstance(RHS, Zcode):
                    RHS.typ = mainTyp
            
            return self.visitArrayLiteral(ast, param)
        
        
        
        for item in ast.value:
            checkTyp = self.visit(item, param)
            if mainTyp is None and isinstance(checkTyp, (BoolType, StringType, NumberType, ArrayType)):
                mainTyp = checkTyp
            elif isinstance(checkTyp, CannotBeInferredZcode):
                return CannotBeInferredZcode()
        
        
        if mainTyp is None:
            
            return ArrayZcode([self.visit(i, param) for i in ast.value],ast)
        
        for item in ast.value:
            
            left = mainTyp
            right = self.visit(item, param)
            canNotInfer = self.LHS_RHS_expr(left, right, ast,param)
            
            if canNotInfer:
                
                return CannotBeInferredZcode()
        
        if type(mainTyp) in [StringType, BoolType, NumberType]:
            return ArrayType([len(ast.value)], mainTyp)
        else:
            return ArrayType([len(ast.value)] + mainTyp.size, mainTyp.eleType)

        
        
            
        
            
    
    def visitBlock(self, ast, param):
        paramNew = [{}] + param
        for item in ast.stmt: 
            self.visit(item,paramNew)   
    def visitContinue(self, ast, param):
        
        if self.BlockFor == 0: raise MustInLoop(ast)
    def visitBreak(self, ast, param):
    
        if self.BlockFor == 0: raise MustInLoop(ast)   
    def visitNumberType(self, ast, param): return ast
    def visitBoolType(self, ast, param): return ast
    def visitStringType(self, ast, param): return ast
    def visitArrayType(self, ast, param): return ast
    def visitNumberLiteral(self, ast, param): return NumberType()
    def visitBooleanLiteral(self, ast, param): return BoolType()
    def visitStringLiteral(self, ast, param): return StringType()

        
        





