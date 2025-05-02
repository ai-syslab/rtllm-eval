module div_16bit (
    input [15:0] A,  // 16-bit dividend
    input [7:0] B,   // 8-bit divisor
    output [15:0] result, // 16-bit quotient
    output [15:0] odd     // 16-bit remainder
);

    reg [15:0] quotient;
    reg [15:0] remainder;
    reg [15:0] a_reg;
    reg [7:0] b_reg;

    integer i;

    always @(A or B) begin
        a_reg = A;
        b_reg = B;
        quotient = 0;
        remainder = 0;

        for (i = 15; i >= 0; i = i - 1) begin
            remainder = {remainder[14:0], a_reg[15]};
            a_reg = {a_reg[14:0], 1'b0};

            if (remainder[15:8] >= b_reg) begin
                remainder[15:8] = remainder[15:8] - b_reg;
                quotient[i] = 1'b1;
            end else begin
                quotient[i] = 1'b0;
            end
        end
    end

    assign result = quotient;
    assign odd = remainder;

endmodule