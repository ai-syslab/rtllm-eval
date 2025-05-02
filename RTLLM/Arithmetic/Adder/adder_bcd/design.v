module adder_bcd (
    input [3:0] A,
    input [3:0] B,
    input Cin,
    output [3:0] Sum,
    output Cout
);

    wire [4:0] binary_sum;
    wire [4:0] corrected_sum;
    wire correction_needed;

    // Perform binary addition of A, B, and Cin
    assign binary_sum = A + B + Cin;

    // Determine if correction is needed (if sum is greater than 9)
    assign correction_needed = binary_sum > 4'b1001;

    // Correct the sum by adding 6 if correction is needed
    assign corrected_sum = correction_needed ? (binary_sum + 4'b0110) : binary_sum;

    // Assign the corrected sum to the output
    assign Sum = corrected_sum[3:0];

    // Generate carry-out if the corrected sum exceeds 4 bits
    assign Cout = corrected_sum[4];

endmodule