module sub_64bit (
    input [63:0] A,
    input [63:0] B,
    output [63:0] result,
    output overflow
);

    wire [63:0] B_complement;
    wire [63:0] sum;
    wire A_sign, B_sign, result_sign;

    // Take 2's complement of B to perform subtraction
    assign B_complement = ~B + 1;

    // Perform addition of A and 2's complement of B
    assign sum = A + B_complement;

    // Assign the result of subtraction
    assign result = sum;

    // Extract sign bits
    assign A_sign = A[63];
    assign B_sign = B[63];
    assign result_sign = sum[63];

    // Detect overflow
    // Overflow occurs if:
    // A is positive, B is negative, and result is negative
    // A is negative, B is positive, and result is positive
    assign overflow = (A_sign == 0 && B_sign == 1 && result_sign == 1) ||
                      (A_sign == 1 && B_sign == 0 && result_sign == 0);

endmodule