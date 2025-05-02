module multi_pipe_4bit(
    input clk,
    input rst_n,
    input [3:0] mul_a,
    input [3:0] mul_b,
    output [7:0] mul_out
);

    parameter size = 4;

    reg [7:0] partial_products [size-1:0];
    reg [7:0] sum_stage1, sum_stage2;

    integer i;

    // Generate partial products
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < size; i = i + 1) begin
                partial_products[i] <= 8'd0;
            end
        end else begin
            for (i = 0; i < size; i = i + 1) begin
                if (mul_b[i] == 1'b1) begin
                    partial_products[i] <= {mul_a, 4'b0000} << i;
                end else begin
                    partial_products[i] <= 8'd0;
                end
            end
        end
    end

    // First level of pipeline registers
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum_stage1 <= 8'd0;
        end else begin
            sum_stage1 <= partial_products[0] + partial_products[1] + partial_products[2] + partial_products[3];
        end
    end

    // Second level of pipeline registers
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum_stage2 <= 8'd0;
        end else begin
            sum_stage2 <= sum_stage1;
        end
    end

    // Final product output
    assign mul_out = sum_stage2;

endmodule