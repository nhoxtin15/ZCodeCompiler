

grammar ZCode;

@lexer::header {
from lexererr import *
}

options {
	language=Python3;
}
// //! --------------------------  Lexical structure ----------------------- //

// declared
program: NEWLINE* list_declared EOF;
list_declared:  declared list_declared |  declared;
declared: function | variables ignore;

// Variable declare
variables: implicit_var | keyword_var | implicit_dynamic; 
//TODO implicit_var, keyword_var , implicit_dynamic
implicit_var: VAR ID ASSIGNINIT expression;
keyword_var: (primitive_decl | array_decl) (ASSIGNINIT expression)?;
implicit_dynamic: dynamic_decl (ASSIGNINIT expression)?;

// type:
primitive_type: NUMBER | BOOL | STRING ;
primitive_decl: primitive_type ID;
array_decl: primitive_type ID LSB list_NUMBER_LIT RSB;
dynamic_decl: DYNAMIC ID;

// function declare
function: FUNC ID LP (prameters_list)? RP (ignore? return_statement | ignore? block_statement | ignore);
//TODO prameters_list
prameters_list: prameter CM prameters_list | prameter; 
prameter: primitive_decl | array_decl;

//TODO Expression, Value phần trước
expression: expression1 STR_CONCAT expression1 | expression1;
expression1: expression2 (EQUAL | STR_EQ | NOT_EQUAL | LT | GT | LE | GE) expression2 | expression2;
expression2: expression2 (AND | OR) expression3 | expression3;
expression3: expression3 (ADD | SUB) expression4 | expression4;
expression4: expression4 (MUL | DIV | MOD) expression5 | expression5;
expression5: (NOT) expression5 | expression6;
expression6: (SUB | ADD) expression6 | expression7;
expression7: ID (LP list_expression RP)? LSB (params) RSB | expression8;//expression7: expression8 LSB (params) RSB | expression8; 

expression8: ID | literal | LP expression RP | ID LP list_expression RP;
// function passing trong expression cuối cùng

//! Value
literal: NUMBER_LIT | STRING_LIT | TRUE | FALSE | array_literal;
//array_literal: LSB (list_literal)? RSB;
array_literal: LSB (params) RSB; // array_literal: LSB (list_expression) RSB;
//LSB (params) RSB: LSB (params) RSB;
//LSB (params) RSBs: LSB (params) RSB LSB (params) RSBs | LSB (params) RSB;

// list các tham số 
//list_literal: literal CM list_literal | literal;

list_expression: params | ; // list này có thể rỗng
params: expression CM params | expression; //params thì không -> làm param của index trong mảng

list_NUMBER_LIT: NUMBER_LIT CM list_NUMBER_LIT | NUMBER_LIT; //cần thay NUMBER_LIT bằng INTLIT không?

//TODO Statements phần này hãy hiện thực các statement sau
statement: declaration_statement | assignment_statement 
            | if_statement | for_statement 
            | break_statement | continue_statement 
            | return_statement  | call_statement | block_statement;
declaration_statement: variables ignore;
assignment_statement: (ID (LSB (params) RSB)?) ASSIGNINIT expression ignore;
if_statement: IF LP expression RP (ignore? statement) list_elif (ELSE (ignore? statement))?;
list_elif: ELIF LP expression RP (ignore? statement) list_elif | ;
for_statement: FOR ID UNTIL expression BY expression (ignore? statement);
break_statement: BREAK ignore;
continue_statement: CONTINUE ignore;
return_statement: RETURN (expression)? ignore;
call_statement: ID LP list_expression RP ignore;
block_statement: BEGIN (ignore statement_inBLK) END ignore; 
statement_inBLK: statement_temp | ; //statement_list
statement_temp: may_ignore_statement statement_temp | may_ignore_statement; 
may_ignore_statement: ignore? statement | ignore;

// kí tự bỏ qua
ignore: NEWLINE+;


//! --------------------------  Lexical structure ----------------------- //
// TODO   Lexical
// TODO KeyWord
TRUE: 'true';
FALSE: 'false';
NUMBER: 'number';
BOOL: 'bool';
STRING: 'string'; 
RETURN: 'return';
VAR: 'var'; 
DYNAMIC: 'dynamic';
FUNC: 'func'; 
FOR: 'for';
UNTIL: 'until';
BY: 'by';
BREAK: 'break';
CONTINUE: 'continue'; 
IF: 'if'; 
ELSE: 'else'; 
ELIF: 'elif'; 
BEGIN: 'begin';
END: 'end'; 
NOT: 'not'; 
AND: 'and'; 
OR: 'or';


// TODO Operators fragment
/*+ - * / %  = <- != < <= >
>= ... == */
ADD: '+';
SUB: '-';
MUL: '*';
DIV: '/';
MOD: '%';
EQUAL: '=';
NOT_EQUAL: '!=';
LT: '<';
GT: '>';
LE: '<=';
GE: '>=';

STR_EQ: '==';
STR_CONCAT: '...';
ASSIGNINIT: '<-';

// TODO Separators
/*( ) [ ] , */
LSB: '[';
RSB: ']';
LP: '(';
RP: ')';
CM: ',';

// TODO Identifiers
ID: [a-zA-Z_][a-zA-Z0-9_]*;

// TODO Literal 
//! STRING_LIT nhớ dùng python bỏ đi " " đầu và cuối và NUMBER_LIT
//BOOLLIT: 'true' | 'false'; //vì ở trên keyword khai báo true false rồi
NUMBER_LIT: DIGITS OPT_FRAC OPT_EXP;
fragment DIGIT: [0-9];
fragment DIGITS: DIGIT+;
fragment OPT_FRAC: ('.' DIGIT*)?;
fragment OPT_EXP: ([Ee] [+-]? DIGITS)?;
// hỗ trợ cho array index
INTLIT: DIGIT+;

STRING_LIT: '"' STR_CHAR* '"' {
    self.text = self.text[1:-1] };
fragment STR_CHAR: ~[\r\n\\"] | ESC_SEQ;
fragment ESC_SEQ: '\\' [bfrnt'\\] | '\'"';
fragment ESC_ILLEGAL: [\r] | '\\' ~[bfrnt'\\];

// NEWLINE COMMENTS WS
NEWLINE: [\n]; // 
COMMENTS: '##' ~[\n\r]* -> skip; // Comments
WS : [ \f\b\t\r]+ -> skip ; // skip spaces, tabs

// TODO ERROR
ERROR_CHAR: . {raise ErrorToken(self.text)};

UNCLOSE_STRING: '"' STR_CHAR* ('\r\n' | '\n' | EOF) {
    if(len(self.text) >= 2 and self.text[-1] == '\n' and self.text[-2] == '\r'):
        raise UncloseString(self.text[1:-2])
    elif (self.text[-1] == '\n'):
        raise UncloseString(self.text[1:-1])
    else:
        raise UncloseString(self.text[1:])
};

ILLEGAL_ESCAPE: '"' STR_CHAR* ESC_ILLEGAL {
    raise IllegalEscape(self.text[1:])
};


//!  -------------------------- end Lexical structure ------------------- //