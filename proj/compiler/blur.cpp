
#include "../solver/array.h"

void blur(const Array<double, 3> &input, Array<double, 3> &output) {
    Array<double, 3> temp(input.sizes);
    for (int y = 0; y < input.height(); y++) {
        for (int x = 0; x < input.width(); x++) {
            if (x < input.width()/2) {
                temp(y, x) = (input(y, x-1) + 2*input(y, x) + input(y,x+1))/4;
            } else {
                temp(y, x) = 1.0;
            }
        }
    }
    for (int y = 0; y < temp.height(); y++) {
        for (int x = 0; x < temp.width(); x++) {
            output(y, x) = (temp(y-1, x) + 2*temp(y, x) + temp(y+1,x))/4;
        }
    }
    output = temp;
}

void main() {
    Type Image = Array(Float(64), 3);

    Function blur("blur");
        Argument input("input", Image), output("output", Image);
    
        Var temp("temp", Image);
        Var x("x"), y("y");
        For loop_temp(input, x, y);
            If (x < input.width()/2);
                temp(y, x) = (input(y, x-1) + 2*input(y, x) + input(y, x+1))/3;
            Else();
                temp(y, x) = 1.0;
            End();
        End();
    
        For loop_output(temp, x, y);
            output(y, x) = (temp(y-1, x) + 2*temp(y, x) + temp(y+1, x))/3;
        End();
    
        Return(output);
    End();
}