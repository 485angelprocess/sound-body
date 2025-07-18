/* Generated by Amaranth Yosys 0.40 (PyPI ver 0.40.0.0.post101, git sha1 a1bb0255d) */

(* top =  1  *)
(* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\audio\\square.py:20" *)
(* generator = "Amaranth" *)
module square_generator(clk, rst, produce_tdata, produce_tvalid, produce_tid, produce_tready);
  reg \$auto$verilog_backend.cc:2352:dump_module$1  = 0;
  wire \$1 ;
  wire \$2 ;
  wire \$3 ;
  wire [5:0] \$4 ;
  reg [4:0] \$5 ;
  (* src = "C:\\Users\\magen\\AppData\\Local\\Packages\\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\\LocalCache\\local-packages\\Python311\\site-packages\\amaranth\\hdl\\_ir.py:283" *)
  input clk;
  wire clk;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\audio\\square.py:22" *)
  reg [4:0] counter = 5'h00;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\signature.py:65" *)
  output [31:0] produce_tdata;
  reg [31:0] produce_tdata;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\audio\\square.py:16" *)
  output [2:0] produce_tid;
  wire [2:0] produce_tid;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\signature.py:67" *)
  input produce_tready;
  wire produce_tready;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\signature.py:66" *)
  output produce_tvalid;
  wire produce_tvalid;
  (* src = "C:\\Users\\magen\\AppData\\Local\\Packages\\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\\LocalCache\\local-packages\\Python311\\site-packages\\amaranth\\hdl\\_ir.py:283" *)
  input rst;
  wire rst;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\audio\\square.py:22" *)
  always @(posedge clk)
    counter <= \$5 ;
  assign \$1  = counter < (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\audio\\square.py:24" *) 4'ha;
  assign \$3  = counter == (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\audio\\square.py:32" *) 5'h13;
  assign \$4  = counter + (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\audio\\square.py:35" *) 1'h1;
  always @* begin
    if (\$auto$verilog_backend.cc:2352:dump_module$1 ) begin end
    (* full_case = 32'd1 *)
    if (\$1 ) begin
      produce_tdata = 32'd500;
    end else begin
      produce_tdata = 32'd0;
    end
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2352:dump_module$1 ) begin end
    \$5  = counter;
    if (\$2 ) begin
      (* full_case = 32'd1 *)
      if (\$3 ) begin
        \$5  = 5'h00;
      end else begin
        \$5  = \$4 [4:0];
      end
    end
    if (rst) begin
      \$5  = 5'h00;
    end
  end
  assign produce_tvalid = 1'h1;
  assign produce_tid = { 2'h0, counter[0] };
  assign \$2  = produce_tready;
endmodule
