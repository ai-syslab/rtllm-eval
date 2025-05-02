module float_multi (
    input clk,
    input rst,
    input [31:0] a,
    input [31:0] b,
    output reg [31:0] z
);

    reg [2:0] counter;
    reg [23:0] a_mantissa, b_mantissa, z_mantissa;
    reg [9:0] a_exponent, b_exponent, z_exponent;
    reg a_sign, b_sign, z_sign;
    reg [49:0] product;
    reg guard_bit, round_bit, sticky;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            counter <= 3'b000;
            z <= 32'b0;
        end else begin
            case (counter)
                3'b000: begin
                    // Extract sign, exponent, and mantissa
                    a_sign <= a[31];
                    b_sign <= b[31];
                    a_exponent <= {2'b00, a[30:23]};
                    b_exponent <= {2'b00, b[30:23]};
                    a_mantissa <= {1'b1, a[22:0]};
                    b_mantissa <= {1'b1, b[22:0]};
                    counter <= 3'b001;
                end
                
                3'b001: begin
                    // Special cases: NaN or infinity
                    if ((a_exponent == 8'hFF && a_mantissa[22:0] != 0) || 
                        (b_exponent == 8'hFF && b_mantissa[22:0] != 0)) begin
                        z <= 32'h7FC00000; // NaN
                        counter <= 3'b000;
                    end else if (a_exponent == 8'hFF || b_exponent == 8'hFF) begin
                        z <= {a_sign ^ b_sign, 8'hFF, 23'b0}; // Infinity
                        counter <= 3'b000;
                    end else if ((a_exponent == 0 && a_mantissa[22:0] == 0) ||
                                 (b_exponent == 0 && b_mantissa[22:0] == 0)) begin
                        z <= {a_sign ^ b_sign, 31'b0}; // Zero
                        counter <= 3'b000;
                    end else begin
                        counter <= 3'b010;
                    end
                end

                3'b010: begin
                    // Multiply mantissas and add exponents
                    product <= a_mantissa * b_mantissa;
                    z_exponent <= a_exponent + b_exponent - 127;
                    z_sign <= a_sign ^ b_sign;
                    counter <= 3'b011;
                end

                3'b011: begin
                    // Normalize product
                    if (product[47]) begin
                        z_mantissa <= product[47:24];
                        guard_bit <= product[23];
                        round_bit <= product[22];
                        sticky <= |product[21:0];
                        z_exponent <= z_exponent + 1;
                    end else begin
                        z_mantissa <= product[46:23];
                        guard_bit <= product[22];
                        round_bit <= product[21];
                        sticky <= |product[20:0];
                    end
                    counter <= 3'b100;
                end

                3'b100: begin
                    // Rounding
                    if (guard_bit && (round_bit || sticky || z_mantissa[0])) begin
                        z_mantissa <= z_mantissa + 1;
                        if (z_mantissa == 24'hFFFFFF) begin
                            z_exponent <= z_exponent + 1;
                        end
                    end
                    counter <= 3'b101;
                end

                3'b101: begin
                    // Handle overflow and underflow
                    if (z_exponent >= 255) begin
                        z <= {z_sign, 8'hFF, 23'b0}; // Infinity
                    end else if (z_exponent <= 0) begin
                        z <= {z_sign, 31'b0}; // Zero
                    end else begin
                        z <= {z_sign, z_exponent[7:0], z_mantissa[22:0]};
                    end
                    counter <= 3'b000;
                end

                default: counter <= 3'b000;
            endcase
        end
    end

endmodule