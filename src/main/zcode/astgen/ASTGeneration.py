from ZCodeVisitor import ZCodeVisitor
from ZCodeParser import ZCodeParser
from AST import *

class ASTGeneration(ZCodeVisitor):

    # program: NEWLINE* list_declared EOF;
    def visitProgram(self, ctx:ZCodeParser.ProgramContext):
        return Program(self.visit(ctx.list_declared()))
    

    # list_declared:  declared list_declared |  declared;
    def visitList_declared(self, ctx:ZCodeParser.List_declaredContext):
        if ctx.list_declared():
            return [self.visit(ctx.declared())] + self.visit(ctx.list_declared())
        return [self.visit(ctx.declared())]


    # declared: function | variables ignore;
    def visitDeclared(self, ctx:ZCodeParser.DeclaredContext):
        if ctx.function():
            return self.visit(ctx.function())
        return self.visit(ctx.variables())


    # variables: implicit_var | keyword_var | implicit_dynamic; 
    def visitVariables(self, ctx:ZCodeParser.VariablesContext):
        if ctx.implicit_var():
            return self.visit(ctx.implicit_var())
        elif ctx.keyword_var():
            return self.visit(ctx.keyword_var())
        return self.visit(ctx.implicit_dynamic())


    # implicit_var: VAR ID ASSIGNINIT expression;
    def visitImplicit_var(self, ctx:ZCodeParser.Implicit_varContext):
        return VarDecl(Id(ctx.ID().getText()), None, "var", self.visit(ctx.expression()))


    # keyword_var: (primitive_decl | array_decl) (ASSIGNINIT expression)?;
    def visitKeyword_var(self, ctx:ZCodeParser.Keyword_varContext):
        if ctx.primitive_decl():
            typ, ID = self.visit(ctx.primitive_decl())
        if ctx.array_decl():
            typ, ID, dims = self.visit(ctx.array_decl())
            typ = ArrayType(dims, typ)

        if ctx.expression():
            return VarDecl(Id(ID), typ, None, self.visit(ctx.expression()))
        return VarDecl(Id(ID), typ, None, None)


    # implicit_dynamic: dynamic_decl (ASSIGNINIT expression)?;
    def visitImplicit_dynamic(self, ctx:ZCodeParser.Implicit_dynamicContext):
        if ctx.expression():
            return VarDecl(self.visit(ctx.dynamic_decl()), None, "dynamic", self.visit(ctx.expression()))
        return VarDecl(self.visit(ctx.dynamic_decl()), None, "dynamic", None)


    # primitive_type: NUMBER | BOOL | STRING ;
    def visitPrimitive_type(self, ctx:ZCodeParser.Primitive_typeContext):
        if ctx.BOOL():
            return BoolType()
        elif ctx.NUMBER():
            return NumberType()
        return StringType()


    # primitive_decl: primitive_type ID;
    def visitPrimitive_decl(self, ctx:ZCodeParser.Primitive_declContext): #return tuple
        return self.visit(ctx.primitive_type()), (ctx.ID().getText()) 


    # array_decl: primitive_type ID LSB list_NUMBER_LIT RSB;
    def visitArray_decl(self, ctx:ZCodeParser.Array_declContext):
        return self.visit(ctx.primitive_type()), (ctx.ID().getText()), (self.visit(ctx.list_NUMBER_LIT())) 


    # dynamic_decl: DYNAMIC ID;
    def visitDynamic_decl(self, ctx:ZCodeParser.Dynamic_declContext):
        return Id(ctx.ID().getText())


    # function: FUNC ID LP (prameters_list)? RP (ignore? return_statement | ignore? block_statement | ignore);
    def visitFunction(self, ctx:ZCodeParser.FunctionContext):
        funcName = Id(ctx.ID().getText())
        lst_param = []
        body = None
        if ctx.return_statement():
            body = self.visit(ctx.return_statement())
        if ctx.block_statement():
            body = self.visit(ctx.block_statement())

        if ctx.prameters_list():
            lst_param = self.visit(ctx.prameters_list())

        return FuncDecl(funcName, lst_param, body)


    # prameters_list: prameter CM prameters_list | prameter;
    def visitPrameters_list(self, ctx:ZCodeParser.Prameters_listContext):
        if ctx.prameters_list():
            return [self.visit(ctx.prameter())] + self.visit(ctx.prameters_list())
        return [self.visit(ctx.prameter())]


    # prameter: primitive_decl | array_decl;
    def visitPrameter(self, ctx:ZCodeParser.PrameterContext):
        if ctx.primitive_decl():
            typ, ID = self.visit(ctx.primitive_decl())
        if ctx.array_decl():
            typ, ID, dims = self.visit(ctx.array_decl())
            typ = ArrayType(dims, typ)
        
        return VarDecl(Id(ID), typ, None, None)


    # expression: expression1 STR_CONCAT expression1 | expression1;
    def visitExpression(self, ctx:ZCodeParser.ExpressionContext):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.expression1()[0])
        
        op = ctx.STR_CONCAT().getText()
        left = self.visit(ctx.expression1()[0])
        right = self.visit(ctx.expression1()[1])
        return BinaryOp(op, left, right)


    # expression1: expression2 (EQUAL | STR_EQ | NOT_EQUAL | LT | GT | LE | GE) expression2 | expression2;
    def visitExpression1(self, ctx:ZCodeParser.Expression1Context):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.expression2()[0])
        
        op = ''
        if ctx.EQUAL():
            op = ctx.EQUAL().getText()
        elif ctx.STR_EQ():
            op = ctx.STR_EQ().getText()
        elif ctx.NOT_EQUAL():
            op = ctx.NOT_EQUAL().getText()
        elif ctx.LT():
            op = ctx.LT().getText()
        elif ctx.GT():
            op = ctx.GT().getText()
        elif ctx.LE():
            op = ctx.LE().getText()
        elif ctx.GE():
            op = ctx.GE().getText()

        left = self.visit(ctx.expression2()[0])
        right = self.visit(ctx.expression2()[1])
        return BinaryOp(op, left, right)


    # expression2: expression2 (AND | OR) expression3 | expression3;
    def visitExpression2(self, ctx:ZCodeParser.Expression2Context):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.expression3())
        
        op = ''
        if ctx.AND():
            op = ctx.AND().getText()
        elif ctx.OR():
            op = ctx.OR().getText()

        left = self.visit(ctx.expression2())
        right = self.visit(ctx.expression3())
        return BinaryOp(op, left, right)


    # expression3: expression3 (ADD | SUB) expression4 | expression4;
    def visitExpression3(self, ctx:ZCodeParser.Expression3Context):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.expression4())
        
        op = ''
        if ctx.ADD():
            op = ctx.ADD().getText()
        elif ctx.SUB():
            op = ctx.SUB().getText()

        left = self.visit(ctx.expression3())
        right = self.visit(ctx.expression4())
        return BinaryOp(op, left, right)

    # expression4: expression4 (MUL | DIV | MOD) expression5 | expression5;
    def visitExpression4(self, ctx:ZCodeParser.Expression4Context):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.expression5())
        
        op = ''
        if ctx.MUL():
            op = ctx.MUL().getText()
        elif ctx.DIV():
            op = ctx.DIV().getText()
        elif ctx.MOD():
            op = ctx.MOD().getText()

        left = self.visit(ctx.expression4())
        right = self.visit(ctx.expression5())
        return BinaryOp(op, left, right)

    # expression5: (NOT) expression5 | expression6;
    def visitExpression5(self, ctx:ZCodeParser.Expression5Context):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.expression6())
        
        return UnaryOp(ctx.getChild(0).getText(), self.visit(ctx.getChild(1)))

    # expression6: (SUB | ADD) expression6 | expression7;
    def visitExpression6(self, ctx:ZCodeParser.Expression6Context):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.expression7())
        
        return UnaryOp(ctx.getChild(0).getText(), self.visit(ctx.getChild(1)))


    # expression7: ID (LP list_expression RP)? LSB (params) RSB | expression8;
    def visitExpression7(self, ctx:ZCodeParser.Expression7Context):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.expression8())
        elif ctx.LP() and ctx.RP():
            return ArrayCell(CallExpr(Id(ctx.ID().getText()), self.visit(ctx.list_expression())), 
                             self.visit(ctx.params()))
        else:
            return ArrayCell(Id(ctx.ID().getText()), self.visit(ctx.params()))


    # expression8: ID | literal | LP expression RP | ID LP list_expression RP;
    def visitExpression8(self, ctx:ZCodeParser.Expression8Context):
        if ctx.ID() and ctx.getChildCount() == 1:
            return Id(ctx.ID().getText())
        if ctx.literal():
            return self.visit(ctx.literal())
        if ctx.expression() and ctx.getChildCount() == 3:
            return self.visit(ctx.expression())
        if ctx.list_expression() and ctx.getChildCount() == 4:
            return CallExpr(Id(ctx.ID().getText()), self.visit(ctx.list_expression()))


    # literal: NUMBER_LIT | STRING_LIT | TRUE | FALSE | array_literal;
    def visitLiteral(self, ctx:ZCodeParser.LiteralContext):
        if ctx.NUMBER_LIT():
            return NumberLiteral(float(ctx.NUMBER_LIT().getText()))
        if ctx.STRING_LIT():
            return StringLiteral(ctx.STRING_LIT().getText())
        if ctx.TRUE():
            return BooleanLiteral(True)
        if ctx.FALSE():
            return BooleanLiteral(False)
        
        return self.visit(ctx.array_literal())


    # array_literal: LSB (params) RSB;
    def visitArray_literal(self, ctx:ZCodeParser.Array_literalContext):
        return ArrayLiteral(self.visit(ctx.params()))


    # list_expression: params | ; // list này có thể rỗng
    def visitList_expression(self, ctx:ZCodeParser.List_expressionContext):
        if ctx.params():
            return self.visit(ctx.params())
        return []


    # params: expression CM params | expression; //params thì không
    def visitParams(self, ctx:ZCodeParser.ParamsContext):
        if ctx.params():
            return [self.visit(ctx.expression())] + self.visit(ctx.params())
        return [self.visit(ctx.expression())]


    # list_NUMBER_LIT: NUMBER_LIT CM list_NUMBER_LIT | NUMBER_LIT;
    def visitList_NUMBER_LIT(self, ctx:ZCodeParser.List_NUMBER_LITContext):
        if ctx.list_NUMBER_LIT():
            return [float(ctx.NUMBER_LIT().getText())] + self.visit(ctx.list_NUMBER_LIT())
        return [float(ctx.NUMBER_LIT().getText())]


    """
    statement: declaration_statement | assignment_statement 
            | if_statement | for_statement 
            | break_statement | continue_statement 
            | return_statement  | call_statement | block_statement;
    """
    def visitStatement(self, ctx:ZCodeParser.StatementContext):
        return self.visit(ctx.getChild(0))


    # declaration_statement: variables ignore;
    def visitDeclaration_statement(self, ctx:ZCodeParser.Declaration_statementContext):
        return self.visit(ctx.variables())


    # assignment_statement: (ID (LSB (params) RSB)?) ASSIGNINIT expression ignore;
    def visitAssignment_statement(self, ctx:ZCodeParser.Assignment_statementContext):
        if ctx.params():
            return Assign(ArrayCell(Id(ctx.ID().getText()), self.visit(ctx.params())), 
                              self.visit(ctx.expression()))
        return Assign(Id(ctx.ID().getText()), self.visit(ctx.expression()))


    # if_statement: IF LP expression RP (ignore? statement) ((list_elif)? (ELSE (ignore? statement))?);
    def visitIf_statement(self, ctx:ZCodeParser.If_statementContext):
        if not ctx.ELSE():
            return If(self.visit(ctx.expression()), self.visit(ctx.statement(0)), 
                          self.visit(ctx.list_elif()), None) 
        
        return If(self.visit(ctx.expression()), self.visit(ctx.statement(0)), 
                          self.visit(ctx.list_elif()), self.visit(ctx.statement(1)))            

    # list_elif: ELIF LP expression RP (ignore? statement) list_elif | ;
    def visitList_elif(self, ctx:ZCodeParser.List_elifContext):
        if ctx.getChildCount() == 0: return []
        cond = self.visit(ctx.expression())
        stmt = self.visit(ctx.statement())
        return [(cond, stmt)] + self.visit(ctx.list_elif())


    # for_statement: FOR ID UNTIL expression BY expression (ignore? statement);
    def visitFor_statement(self, ctx:ZCodeParser.For_statementContext):
        return For(Id(ctx.ID().getText()), self.visit(ctx.expression(0)), 
                       self.visit(ctx.expression(1)), self.visit(ctx.statement()))


    # break_statement: BREAK ignore;
    def visitBreak_statement(self, ctx:ZCodeParser.Break_statementContext):
        return Break()


    # continue_statement: CONTINUE ignore;
    def visitContinue_statement(self, ctx:ZCodeParser.Continue_statementContext):
        return Continue()


    # return_statement: RETURN (expression)? ignore;
    def visitReturn_statement(self, ctx:ZCodeParser.Return_statementContext):
        if ctx.expression():
            return Return(self.visit(ctx.expression()))
        return Return(None)


    # call_statement: ID LP list_expression RP ignore;
    def visitCall_statement(self, ctx:ZCodeParser.Call_statementContext):
        return CallStmt(Id(ctx.ID().getText()), self.visit(ctx.list_expression()))


    # block_statement: BEGIN (ignore statement_inBLK) END ignore; 
    def visitBlock_statement(self, ctx:ZCodeParser.Block_statementContext):
        return Block(self.visit(ctx.statement_inBLK()))


    # statement_inBLK: statement_temp | ;
    def visitStatement_inBLK(self, ctx:ZCodeParser.Statement_inBLKContext):
        if ctx.getChildCount() == 0:
            return []
        return self.visit(ctx.statement_temp())


    # statement_temp: may_ignore_statement statement_temp | may_ignore_statement; 
    def visitStatement_temp(self, ctx:ZCodeParser.Statement_tempContext):
        if ctx.statement_temp():
            return [self.visit(ctx.may_ignore_statement())] + self.visit(ctx.statement_temp()) 
        return [self.visit(ctx.may_ignore_statement())]


    # may_ignore_statement: ignore? statement | ignore;
    def visitMay_ignore_statement(self, ctx:ZCodeParser.May_ignore_statementContext):
        if ctx.statement():
            return self.visit(ctx.statement())
        return None #self.visit(ctx.ignore())


    # Visit a parse tree produced by ZCodeParser#ignore.
    def visitIgnore(self, ctx:ZCodeParser.IgnoreContext):
        return self.visitChildren(ctx)
