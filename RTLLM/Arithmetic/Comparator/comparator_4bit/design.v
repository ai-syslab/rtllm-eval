module comparator_4bit (
    input [3:0] A,
    input [3:0] B,
    output A_greater,
    output A_equal,
    output A_less
);
    
    wire [3:0] diff;
    wire borrow3, borrow2, borrow1, borrow0;

    // Subtraction logic with borrow detection
    assign {borrow3, diff[3]} = A[3] - B[3];
    assign {borrow2, diff[2]} = A[2] - B[2] - borrow3;
    assign {borrow1, diff[1]} = A[1] - B[1] - borrow2;
    assign {borrow0, diff[0]} = A[0] - B[0] - borrow1;

    // Determine output conditions
    assign A_greater = ~borrow0 & (diff != 4'b0000);
    assign A_equal = (diff == 4'b0000);
    assign A_less = borrow0;

endmodule