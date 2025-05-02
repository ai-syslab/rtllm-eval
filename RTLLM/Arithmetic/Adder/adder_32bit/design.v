module adder_32bit (A, B, S, C32);
    input [32:1] A;
    input [32:1] B;
    output [32:1] S;
    output C32;
    wire C16;

    // Instantiate two 16-bit CLA modules
    cla_16bit cla0 (.A(A[16:1]), .B(B[16:1]), .S(S[16:1]), .C16(C16));
    cla_16bit cla1 (.A(A[32:17]), .B(B[32:17]), .S(S[32:17]), .C16(C32), .Cin(C16));
    
endmodule

module cla_16bit (A, B, S, C16, Cin);
    input [16:1] A;
    input [16:1] B;
    input Cin;
    output [16:1] S;
    output C16;
    wire [16:1] P;  // Propagate
    wire [16:1] G;  // Generate
    wire [16:0] C;  // Carry

    assign C[0] = Cin;

    genvar i;
    generate
        for (i = 1; i <= 16; i = i + 1) begin: bit
            assign P[i] = A[i] ^ B[i];
            assign G[i] = A[i] & B[i];

            assign C[i] = G[i] | (P[i] & C[i-1]);
            assign S[i] = P[i] ^ C[i-1];
        end
    endgenerate

    assign C16 = C[16];
endmodule