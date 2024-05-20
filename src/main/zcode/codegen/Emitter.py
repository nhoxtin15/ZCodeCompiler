from Utils import *

import CodeGenerator as cgen
from MachineCode import JasminCode
from AST import *
from CodeGenError import *



class Emitter():
    def __init__(self, filename):
        self.filename = filename
        self.buff = list() 
        self.jvm = JasminCode() 

    ################################
    #                              #
    #          Utilities           #
    #                              #
    ################################


    def getJVMType(self, inType):
        typeIn = type(inType)
        if typeIn is BoolType: 
            return "Z"
        elif typeIn is NumberType: 
            return "F"
        elif typeIn is StringType: 
            return "Ljava/lang/String;"
        elif typeIn is VoidType: 
            return "V"
        elif typeIn is ArrayType: 
            return "[" * len(inType.size)  + self.getJVMType(inType.eleType)
        elif typeIn is Zcode: 
            return "LZCodeClass;"
        elif typeIn is VarZcode:
            return "Unknown"
        elif typeIn is FuncZcode: 
            ParamsTypes = ""
            for i in inType.param:
                ParamsTypes += self.getJVMType(i)
            return "(" + ParamsTypes + ")" + self.getJVMType(inType.typ) if inType.typ else "Unknown"
            
        
        return "Ljava/lang/Object;"

    
    
    def emitPROLOG(self, name, parent):
        #& name: String
        #& parent: String
        result = list()
        #print name
        result.append(self.jvm.emitSOURCE(name + ".java"))
        #print class
        result.append(self.jvm.emitCLASS("public " + name))
        #print parent   
        result.append(self.jvm.emitSUPER("java/land/Object" if parent == "" else parent))
        #note that we return a list (for adding to buff)
        return ''.join(result)


    def emitEPILOG(self):
        #start writing to file
        file = open(self.filename, "w")
        file.write(''.join(self.buff))
        file.close()

    def emitLIMITSTACK(self, num):
        
        return self.jvm.emitLIMITSTACK(num)
    def emitLIMITLOCAL(self, num):
        return self.jvm.emitLIMITLOCAL(num)

    
    def printout(self, in_):
        #add into buffer
        self.buff.append(in_)
    
    
    def printIndexNew(self):
        #get the index of the last element printed
            #for storing and later change it to the correct value
        return len(self.buff) - 1
    
    #set the type of the element at index
        #change None to the correct type
    def setType(self, in_):
        if type(in_) is VarZcode: typ = self.getJVMType(in_.typ)
        else: typ = self.getJVMType(in_)
        #replace Unknown with the correct type
        self.buff[in_.line] = self.buff[in_.line].replace("Unknown", typ)

    
    def clearBuff(self):
        self.buff.clear()
        
    
    def updateType(self, index, type):
        pass
    
    
    
    def emitDUP(self, frame):
        # frame: Frame

        frame.push()
        return self.jvm.emitDUP()
    ################################
    #                              #
    #   Function (emit and call)   #
    #                              #
    ################################




    def emitMETHOD(self, lexeme, in_, isStatic, frame):
        #& lexeme: String (name of the function)
        #& in_: Type (if not have -> None (later replacement))
        #& isStatic: Boolean 
        #& frame: Frame
        name = lexeme
        FunctionType = in_


        return self.jvm.emitMETHOD(name, self.getJVMType(FunctionType), True if isStatic else False)

    
    def emitINVOKESTATIC(self, lexeme, in_, frame):
        #& lexeme: String (tên hàm)
        #& in_: Type (kiểu FUNZCODE)
        #& frame: Frame
        
        #pop all the args before calling the function
        typ = in_
        list(map(lambda x: frame.pop(), typ.param))

        #if the return type is not void, push 1 value to the stack
        if not type(typ.typ) is VoidType:
            frame.push()
        #return the invokestatic
        return self.jvm.emitINVOKESTATIC(lexeme, self.getJVMType(in_))
    
    
    def emitINVOKESPECIAL(self, frame, lexeme=None, in_=None):
        #the same as above, but for special functions

        if not lexeme is None and not in_ is None:
            #the same as above
            #pop all the param
            typ = in_
            list(map(lambda x: frame.pop(), typ.param))
            frame.pop()
            #if the return type is not void, push 1 value to the stack
            if not type(typ.rettype) is VoidType:
                frame.push()
            #return the invokespecial
            return self.jvm.emitINVOKESPECIAL(lexeme, self.getJVMType(in_))
        elif lexeme is None and in_ is None:
            # call super
            frame.pop()
            return self.jvm.emitINVOKESPECIAL()

    
    def emitINVOKEVIRTUAL(self, lexeme, in_, frame):
        #for concat and equal
        #the same as above
        typ = in_
        list(map(lambda x: frame.pop(), typ.param))

        if type(typ) is VoidType:
            frame.pop()
        return self.jvm.emitINVOKEVIRTUAL(lexeme, self.getJVMType(in_))
    
    
    
    def emitENDMETHOD(self, frame):
        # frame: Frame
        #end the method
        buffer = list()
        #print limit stack
        buffer.append(self.jvm.emitLIMITSTACK(frame.getMaxOpStackSize()))
        #print limit locals
        buffer.append(self.jvm.emitLIMITLOCAL(frame.getMaxIndex()))
        #print return
        buffer.append(self.jvm.emitENDMETHOD())

        return ''.join(buffer)

    #* return 
    def emitRETURN(self, in_, frame):
        #& in_: Type
            #bool -> int
            #number -> float 
            #string -> array (address)

        if type(in_) is BoolType:
            #need pop
            frame.pop()
            return self.jvm.emitIRETURN()
        
        elif type(in_) is NumberType:
            #need pop
            frame.pop()
            return self.jvm.emitFRETURN()
        elif type(in_) is VoidType:
            #doesn't need pop
            return self.jvm.emitRETURN()
        elif type(in_) is StringType or type(in_) is ArrayType:
            #need pop
            frame.pop()
            return self.jvm.emitARETURN()
    ################################
    #                              #
    #  Emit Var (Static and var)   #
    #                              #
    ################################

    #* global variable -> static
    def emitATTRIBUTE(self, lexeme, in_, isFinal = False, value = None):
        #& lexeme: String (tên)
        #& in_: Type (kiểu)
        
        #static field

        return self.jvm.emitSTATICFIELD(lexeme, self.getJVMType(in_), isFinal)
    
    #emit Var
    def emitVAR(self, in_, varName, inType, fromLabel, toLabel, frame):
        
        return self.jvm.emitVAR(in_, varName, self.getJVMType(inType), fromLabel, toLabel)

    ################################
    #                              #
    #       Get and Put for        #
    #           Variable           #
    #                              #
    ################################
    
    def emitGETSTATIC(self, lexeme, in_, frame):
        #get static vriable (global)

        frame.push()
        return self.jvm.emitGETSTATIC(lexeme, self.getJVMType(in_))

    def emitPUTSTATIC(self, lexeme, in_, frame):
        #put static variable (global)

        frame.pop()

        return self.jvm.emitPUTSTATIC(lexeme, self.getJVMType(in_))

    def emitWRITEVAR(self, name, inType, index, frame):
        frame.pop()
        if type(inType) is NumberType:
            #all number is fstore
            return self.jvm.emitFSTORE(index)
        elif type(inType) is BoolType:
            return self.jvm.emitISTORE(index)
        elif type(inType) is StringType:
            return self.jvm.emitASTORE(index)
        elif type(inType) is ArrayType:
            return self.jvm.emitASTORE(index)
        else:
            raise IllegalOperandException(name)  
        
    
    def emitREADVAR(self, name, inType, index, frame):
        frame.push()
        if name == "this":
            #load class
            return self.jvm.emitALOAD(index)
        elif type(inType) is BoolType:
            #read int
            return self.jvm.emitILOAD(index)
        elif type(inType) is NumberType:
            #read float
            return self.jvm.emitFLOAD(index)
        elif type(inType) is StringType:
            #String -> address
            return self.jvm.emitALOAD(index)
        elif type(inType) is ArrayType:
            #Array -> address
            return self.jvm.emitALOAD(index)
        else:
            raise IllegalOperandException(name)

    ################################
    #                              #
    #           Operator           #
    #                              #
    ################################

    def emitADDOP(self, lexeme, in_, frame):
        #lexeme: String (+ or -)
        #in_: Type (numberType -> float -> doesn;t use it here)
        #pop 2 -> push back 1

        frame.pop()
        if lexeme == "+":
            return self.jvm.emitFADD()
        else:
            return self.jvm.emitFSUB()

    
    def emitMULOP(self, lexeme, in_, frame):
        #lexeme: String (* or /)
        #in_: Type (numberType -> float -> doesn't use it here)
        frame.pop()
        #pop 2 -> push back 1
        if lexeme == "*":
            return self.jvm.emitFMUL()
        else:
            return self.jvm.emitFDIV()
    #op %
    def emitMOD(self,frame):
        code = self.emitMULOP("/",NumberType(),frame)
        code += self.emitF2I(frame)
        code += self.emitI2F(frame)
        code += self.emitMULOP("*",NumberType(),frame)
        code += self.emitADDOP("-",NumberType(),frame)
        return code
    
    
    def emitANDOP(self, frame):
        #pop 2 -> push back 1
        frame.pop()

        return self.jvm.emitIAND()
    
    
    def emitOROP(self, frame):
        #pop 2 -> push back 1
        frame.pop()

        return self.jvm.emitIOR()

    
    def emitREOP(self, op, in_, frame):
        #& op: String
        #& in_: Type
        #& frame: Frame
        

        result = list()
        #label false and true
        labelF = frame.getNewLabel()
        labelO = frame.getNewLabel()

        frame.pop()
        frame.pop()
        #pop 2 -> push back 1
            #push is inside so we pop 2 times
        result.append(self.jvm.emitFCMPL())
        if op == "=":
            #if equal, jump to false
            result.append(self.jvm.emitIFEQ(labelF))   
            result.append(self.emitPUSHCONST(False, BoolType(), frame))
            frame.pop()
            result.append(self.emitGOTO(labelO, frame))
            result.append(self.emitLABEL(labelF, frame))
            result.append(self.emitPUSHCONST(True, BoolType(), frame))
            result.append(self.emitLABEL(labelO, frame)) 
            return ''.join(result)
        elif op == ">":
            #if less than or equal, jump to false
            result.append(self.jvm.emitIFLE(labelF))
        elif op == ">=":
            result.append(self.jvm.emitIFLT(labelF))
        elif op == "<":
            result.append(self.jvm.emitIFGE(labelF))
        elif op == "<=":
            result.append(self.jvm.emitIFGT(labelF))
        elif op == "!=":
            result.append(self.jvm.emitIFEQ(labelF))   
        #beside from "="
            #generate code for the rest
        result.append(self.emitPUSHCONST(True, BoolType(), frame))
        
        frame.pop()

        result.append(self.emitGOTO(labelO, frame))

        result.append(self.emitLABEL(labelF, frame))

        result.append(self.emitPUSHCONST(False, BoolType(), frame))

        result.append(self.emitLABEL(labelO, frame))

        return ''.join(result)
    

    def emitNEGOP(self, in_, frame):
        return self.jvm.emitFNEG()

    
    def emitNOT(self, in_, frame):
        #& in_: Type
        #& frame: Frame
        #if true -> push false
        #if false -> push true
        labelTrue = frame.getNewLabel()
        labelEnd = frame.getNewLabel()
        result = list()
        #if true -> push false (also pop)
        result.append(self.emitIFTRUE(labelTrue, frame))
        #push true
        result.append(self.emitPUSHCONST(True, in_, frame))
        #goto end
        result.append(self.emitGOTO(labelEnd, frame))

        #false -> push true (also pop)
        result.append(self.emitLABEL(labelTrue, frame))
        result.append(self.emitPUSHCONST(False, in_, frame))
        
        #label end
        result.append(self.emitLABEL(labelEnd, frame))
        
        return ''.join(result)


    ################################
    #                              #
    #         F2I and I2F          #
    #                              #
    ################################


    #float to int and int to loaf
    def emitF2I(self, frame):
        return '\tf2i\n'
    def emitI2F(self, frame):
        return self.jvm.emitI2F()
    
    ################################
    #                              #
    #          PUSHCONST           #
    #                              #
    ################################

    
    
    def emitPUSHCONST(self, in_, typ, frame):
        #& in_: String (value)
        #& typ: Type (number/string/bool)
        #& frame: Frame
        frame.push()

        if type(typ) is NumberType:
            #change int to float
            f = float(in_)
            #set format
            rst = "{0:.4f}".format(f)
            #if the value is 0.0, 1.0, 2.0 -> use fconst_
            if rst == "0.0" or rst == "1.0" or rst == "2.0":
                return self.jvm.emitFCONST(rst)
            #else use ldc
            else:
                return self.jvm.emitLDC(rst)    
            
        elif type(typ) is StringType:
            #ldc 
            return self.jvm.emitLDC(in_)
        elif type(typ) is BoolType:
            #if true -> 1 else 0
            if in_:

                return self.jvm.emitICONST(1)
            else:

                return self.jvm.emitICONST(0)
        else:
            raise IllegalOperandException(in_)
    
    ################################
    #                              #
    #       ALOAD and AStore       #
    #                              #
    ################################
    def emitALOAD(self, in_, frame):
        #& in_: Type
        #& frame: Frame

        frame.pop()
        #pop 2 -> push 1 
            #pop 1
        if type(in_) is BoolType:
            #bool address
            return self.jvm.emitBALOAD()
        elif type(in_) is NumberType:
            #number address -> flaot
            return self.jvm.emitFALOAD()
        elif type(in_) is StringType or type(in_) is ArrayType:
            #string or array -> address of address
            return self.jvm.emitAALOAD()
        else:
            raise IllegalOperandException(str(in_))        
        
    def emitASTORE(self, in_, frame):
        
        frame.pop()
        frame.pop()
        frame.pop()
        #pop 3 -> push 0
        if type(in_) is NumberType:
            return self.jvm.emitFASTORE()
        if type(in_) is BoolType:
            return self.jvm.emitBASTORE()
        elif  type(in_) is StringType or type(in_) is ArrayType:
            return self.jvm.emitAASTORE()
        else:
            raise IllegalOperandException(str(in_))


    ################################
    #                              #
    #      JUMPING CONDITION       #
    #                              #
    ################################

    
    def emitIFTRUE(self, label, frame):
        # label: Int (label to jump)
        # frame: Frame
        frame.pop()
        #pop 1 -> push 0
        return self.jvm.emitIFGT(label)
    
    def emitIFFALSE(self, label, frame):
        # label: Int (label to jump)
        # frame: Frame

        frame.pop()
        #pop 1 -> push 0
        return self.jvm.emitIFLE(label)
    #emit label
    def emitLABEL(self, label, frame):
        # label: Int (label to emit)
        # frame: Frame
        return self.jvm.emitLABEL(label)
    #unconditional jump
    def emitGOTO(self, label, frame):
        # label: Int (label to jump)
        # frame: Frame
        return self.jvm.emitGOTO(str(label))


    ################################
    #                              #
    #         Create Array         #
    #                              #
    ################################

    
    
    def emitNEWARRAY(self, in_, frame):
        # in_: Type
        # frame: Frame
        
        #string -> anewarray (array of address)
        if type(in_) is StringType:
            return self.emitANEWARRAY(in_, frame)
        #find the value that store in this
        val = ""
        if type(in_) is NumberType:
            val = "float"
        elif type(in_) is BoolType:
            val = "boolean"
        return self.jvm.emitNEWARRAY(val)
    
    
    def emitANEWARRAY(self, in_, frame):
        # frame: Frame
        # in_: Type
        #find the value that store in this
        val = ""
        if type(in_) is NumberType:
            val = "float"
        elif type(in_) is BoolType:
            val = "boolean"
        elif type(in_) is StringType:
            val = "java/lang/String"
        elif type(in_) is ArrayType:
            val = self.getJVMType(in_)
        #create array
        return self.jvm.emitANEWARRAY(val)


    def emitMULTIANEWARRAY(self, in_, frame):
        # frame: Frame
        # in_: Type
        if type(in_) is ArrayType:
            dimens = len(in_.size)
            return self.jvm.emitMULTIANEWARRAY(self.getJVMType(in_), str(dimens))
    

    

################################
#                              #
#        ZCODE CLASSES         #
#                              #
################################

    #for storing the type of the variable (Mainly for type infering)

 
class Zcode(Type):
    pass

class FuncZcode(Zcode):
    def __init__(self, name, typ, param):
        self.typ = typ
        self.name = name
        self.param = param
        self.line = 0 #index of the method line in buffer (later change when know the return type)
    


class VarZcode(Zcode):
    def __init__(self, name, typ, index, init = False):
        self.typ = typ
        self.name = name
        self.index = index #index in local variable array
        self.line = 0 #index of the variable line in buffer (later change when know the type)
        self.init = init
    

