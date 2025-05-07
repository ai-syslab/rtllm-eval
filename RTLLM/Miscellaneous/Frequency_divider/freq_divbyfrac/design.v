module freq_divbyfrac(clk, rst_n, clk_div);
    input clk;
    input rst_n;
    output clk_div;
    
    reg [2:0] counter;
    reg clk_div_int1, clk_div_int2;
    reg clk_div_phase1, clk_div_phase2;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter <= 3'b0;
            clk_div_int1 <= 1'b0;
            clk_div_int2 <= 1'b0;
            clk_div_phase1 <= 1'b0;
            clk_div_phase2 <= 1'b0;
        end
        else begin
            counter <= counter + 1;
            
            // Generate intermediate clock signals
            if (counter == 3'b011) begin
                clk_div_int1 <= ~clk_div_int1;
                clk_div_int2 <= clk_div_int1;
            end
            else if (counter == 3'b110) begin
                clk_div_int1 <= ~clk_div_int1;
                clk_div_int2 <= ~clk_div_int2;
            end
            
            // Generate phase shifted clocks
            clk_div_phase1 <= clk_div_int1;
            clk_div_phase2 <= clk_div_int2;
        end
    end
    
    assign clk_div = clk_div_phase1 | clk_div_phase2;
endmodule