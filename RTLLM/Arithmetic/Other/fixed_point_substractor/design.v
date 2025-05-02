module fixed_point_subtractor #(parameter Q = 8, parameter N = 16)(
    input [N-1:0] a,
    input [N-1:0] b,
    output [N-1:0] c
);
    reg [N-1:0] res;
    wire signed [N-1:0] a_signed;
    wire signed [N-1:0] b_signed;
    wire signed [N-1:0] result_signed;

    assign a_signed = a;
    assign b_signed = b;
    assign result_signed = a_signed - b_signed;

    always @(*) begin
        if (result_signed == 0) begin
            // Handle zero result explicitly
            res = {1'b0, {N-1{1'b0}}};
        end else begin
            res = result_signed;
        end
    end

    assign c = res;

endmodule