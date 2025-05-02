module radix2_div (
    input clk,
    input rst,
    input sign,
    input [7:0] dividend,
    input [7:0] divisor,
    input opn_valid,
    output reg res_valid,
    output reg [15:0] result
);

    reg [15:0] SR;
    reg [7:0] abs_dividend, abs_divisor, NEG_DIVISOR;
    reg [3:0] cnt;
    reg start_cnt;
    reg dividend_sign, divisor_sign;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            SR <= 16'b0;
            cnt <= 4'b0;
            start_cnt <= 1'b0;
            res_valid <= 1'b0;
            result <= 16'b0;
        end else if (opn_valid && !res_valid) begin
            // Save inputs and initialize
            if (sign) begin
                dividend_sign <= dividend[7];
                divisor_sign <= divisor[7];
                abs_dividend <= dividend[7] ? (~dividend + 1'b1) : dividend;
                abs_divisor <= divisor[7] ? (~divisor + 1'b1) : divisor;
            end else begin
                abs_dividend <= dividend;
                abs_divisor <= divisor;
            end

            NEG_DIVISOR <= ~abs_divisor + 1'b1;
            SR <= {8'b0, abs_dividend} << 1;
            cnt <= 4'b0001;
            start_cnt <= 1'b1;
            res_valid <= 1'b0;
        end else if (start_cnt) begin
            // Division process
            if (cnt[3]) begin
                // Division complete
                start_cnt <= 1'b0;
                cnt <= 4'b0;
                res_valid <= 1'b1;

                // Adjust the result for sign if necessary
                if (sign && (dividend_sign ^ divisor_sign)) begin
                    // Quotient should be negative
                    result[7:0] <= ~SR[7:0] + 1'b1;
                end else begin
                    result[7:0] <= SR[7:0];
                end

                if (sign && dividend_sign) begin
                    // Remainder should be negative
                    result[15:8] <= ~SR[15:8] + 1'b1;
                end else begin
                    result[15:8] <= SR[15:8];
                end
            end else begin
                // Increment counter
                cnt <= cnt + 1'b1;

                // Subtract and shift
                if (SR[15:8] >= abs_divisor) begin
                    SR <= {SR[14:0], 1'b1} + {NEG_DIVISOR, 8'b0};
                end else begin
                    SR <= {SR[14:0], 1'b0};
                end
            end
        end else if (res_valid) begin
            // Result has been consumed
            res_valid <= 1'b0;
        end
    end
endmodule