module multi_pipe_4bit(clk, rst_n, mul_a, mul_b, mul_out);
  parameter size = 4;

  input clk;
  input rst_n;
  input [size-1:0] mul_a;
  input [size-1:0] mul_b;
  output [2*size-1:0] mul_out;

  reg [2*size-1:0] partial_products[size-1:0];
  reg [2*size-1:0] sum_lvl1;
  reg [2*size-1:0] sum_lvl2;
  reg [2*size-1:0] product;

  integer i;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      for (i = 0; i < size; i = i + 1) begin
        partial_products[i] <= 0;
      end
      sum_lvl1 <= 0;
      sum_lvl2 <= 0;
      product <= 0;
    end else begin
      // Generate partial products
      for (i = 0; i < size; i = i + 1) begin
        if (mul_b[i])
          partial_products[i] <= mul_a << i;
        else
          partial_products[i] <= 0;
      end

      // First level of addition
      sum_lvl1 <= partial_products[0] + partial_products[1];

      // Second level of addition
      sum_lvl2 <= partial_products[2] + partial_products[3];

      // Final product calculation
      product <= sum_lvl1 + sum_lvl2;
    end
  end

  assign mul_out = product;

endmodule