
#ifndef _ast_h
#define _ast_h

#define DEFAULT_INT_BITS   32
#define DEFAULT_FLOAT_BITS 64

class Type { public:
    bool is_int;
    bool is_uint;
    bool is_float;
    imt dims;
    int bits;
    
    Type(bool is_int_, bool is_uint_, bool is_float_, int dims_, int bits_)
        :is_int(is_int_), is_uint(is_uint_), is_float(is_float_), dims(dims_), bits(bits_) {
        ASSERT(int(is_int)+int(is_uint)+int(is_float) == 1, "expected one of int, uint, float");
    }
    
    string str() {
        return (boost::format("Type(%d, %d, %d, %d, %d)") % is_int, is_uint, is_float, dims, bits).str();
    }
    
    string lower() {
        string ans;
        if (is_int) {
            ans = (boost::format("int%d_t") % bits).str();
        } else if (is_uint) {
            ans = (boost::format("uint%d_t") % bits).str();
        } else if (is_float) {
            if (bits == 32) {
                ans = "float";
            } else if (bits == 64) {
                ans = "double";
            } else {
                ASSERT(false, "Unsupported float bits");
            }
        } else {
            ASSERT(false, "Unknown Type()");
        }
        if (dims > 1) {
            ans = (boost::format("Array<%s>"))
        }
        return ans;
    }
};

Type Int(int bits=DEFAULT_INT_BITS) {
    return Type(1, 0, 0, 0, bits);
}

Type UInt(int bits=DEFAULT_INT_BITS) {
    return Type(0, 1, 0, 0, bits);
}

Type Float(int bits=DEFAULT_FLOAT_BITS) {
    return Type(0, 0, 1, 0, bits);
}

Type Array(Type t, int dims) {
    t.dims = dims;
    return t;
}

int var_count = 0;
string new_var_name() {
    return (boost::format("_x") % var_count++).str();
}

vector<shared_ptr<Node> > ast_stack;

class Node { public:
    vector<shared_ptr<Node> > children;
    virtual string str() = 0;
};

class BlockNode: public Node { public:
    BlockNode() {
        ast_stack.int
    }
};

class Program: public Node { public:

};

class Expr: public Node { public:

};

class MathOp: public Node { public:

};

class If: public Node { public:

};

class Else: public Node { public:

};

class For: public Node { public:

};

class Function: public Node { public:

};

void End() {

}

class Var: public Node { public:
    string name;
    Type type;
    Expr initial;
    
    Var(string name_="", Type type_=Int(), Expr initial_=Expr())
        :name(name_), type(type_), initial(initial_) {
        if (name.size() == 0) {
            name = new_var_name();
        }
    }
    
    virtual string str() {
        return boost::format("Var(\"%s\", %s, %s
    }
};


#endif