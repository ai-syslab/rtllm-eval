module adder_pipe_64bit(
    input clk,
    input rst_n,
    input i_en,
    input [63:0] adda,
    input [63:0] addb,
    output [64:0] result,
    output o_en
);

    reg [63:0] adda_reg1, addb_reg1;
    reg [63:0] adda_reg2, addb_reg2;
    reg [63:0] sum_stage1;
    reg [64:0] sum_stage2;
    reg carry_stage1;
    reg o_en_reg1, o_en_reg2, o_en_reg3;

    // Stage 1: Register input operands and calculate partial sum
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            adda_reg1 <= 64'b0;
            addb_reg1 <= 64'b0;
            sum_stage1 <= 64'b0;
            carry_stage1 <= 1'b0;
            o_en_reg1 <= 1'b0;
        end else if (i_en) begin
            adda_reg1 <= adda;
            addb_reg1 <= addb;
            {carry_stage1, sum_stage1} <= adda + addb;
            o_en_reg1 <= 1'b1;
        end else begin
            o_en_reg1 <= 1'b0;
        end
    end

    // Stage 2: Register the output of stage 1
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            adda_reg2 <= 64'b0;
            addb_reg2 <= 64'b0;
            sum_stage2 <= 65'b0;
            o_en_reg2 <= 1'b0;
        end else begin
            adda_reg2 <= sum_stage1;
            addb_reg2 <= {63'b0, carry_stage1};
            sum_stage2 <= {carry_stage1, sum_stage1} + {64'b0, carry_stage1};
            o_en_reg2 <= o_en_reg1;
        end
    end

    // Output stage: Register the final result
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            result <= 65'b0;
            o_en_reg3 <= 1'b0;
        end else begin
            result <= sum_stage2;
            o_en_reg3 <= o_en_reg2;
        end
    end

    assign o_en = o_en_reg3;

endmodule