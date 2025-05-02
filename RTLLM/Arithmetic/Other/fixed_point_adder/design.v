module fixed_point_adder #(parameter Q = 8, parameter N = 16) (
    input [N-1:0] a,
    input [N-1:0] b,
    output [N-1:0] c
);

    reg [N-1:0] res;

    always @(a or b) begin
        if (a[N-1] == b[N-1]) begin
            // Both numbers have the same sign, perform addition
            res = a + b;
            if (res[N-1] != a[N-1]) begin
                // Overflow detected, handle overflow
                res = {a[N-1], {(N-1){1'b1}}}; // Set to max positive/negative value
            end
        end else begin
            // Numbers have different signs, perform subtraction
            if (a[N-2:0] >= b[N-2:0]) begin
                res = a - b;
                res[N-1] = a[N-1]; // Sign of the result follows 'a'
            end else begin
                res = b - a;
                res[N-1] = b[N-1]; // Sign of the result follows 'b'
            end
        end
    end

    assign c = res;

endmodule