/* Generated by Amaranth Yosys 0.40 (PyPI ver 0.40.0.0.post101, git sha1 a1bb0255d) */

(* top =  1  *)
(* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\serial\\serial_to_wishbone.py:27" *)
(* generator = "Amaranth" *)
module serial_to_wishbone(command_tvalid, reply_tready, produce_ack, produce_r_data, clk, rst, command_tready, reply_tdata, reply_tvalid, produce_cyc, produce_stb, produce_addr, produce_w_en, produce_w_data, command_tdata);
  reg \$auto$verilog_backend.cc:2352:dump_module$1  = 0;
  wire \$1 ;
  wire [2:0] \$10 ;
  wire \$11 ;
  wire [2:0] \$12 ;
  wire [46:0] \$13 ;
  wire \$14 ;
  wire [2:0] \$15 ;
  wire \$16 ;
  reg [31:0] \$17 ;
  reg [31:0] \$18 ;
  reg \$19 ;
  wire \$2 ;
  reg [1:0] \$20 ;
  reg [1:0] \$21 ;
  reg [2:0] \$22 ;
  reg [7:0] \$23 ;
  reg [31:0] \$24 ;
  wire \$3 ;
  wire \$4 ;
  wire \$5 ;
  wire \$6 ;
  wire \$7 ;
  wire \$8 ;
  wire \$9 ;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\serial\\serial_to_wishbone.py:33" *)
  reg [31:0] arg = 32'd0;
  (* src = "C:\\Users\\magen\\AppData\\Local\\Packages\\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\\LocalCache\\local-packages\\Python311\\site-packages\\amaranth\\hdl\\_ir.py:283" *)
  input clk;
  wire clk;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\signature.py:65" *)
  input [7:0] command_tdata;
  wire [7:0] command_tdata;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\signature.py:67" *)
  output command_tready;
  reg command_tready;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\signature.py:66" *)
  input command_tvalid;
  wire command_tvalid;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\serial\\serial_to_wishbone.py:30" *)
  reg [1:0] counter = 2'h0;
  (* src = "C:\\Program Files\\WindowsApps\\PythonSoftwareFoundation.Python.3.11_3.11.2544.0_x64_qbz5n2kfra8p0\\Lib\\contextlib.py:144" *)
  reg [2:0] fsm_state = 3'h0;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\serial\\serial_to_wishbone.py:32" *)
  reg [7:0] prefix = 8'h00;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\signature.py:10" *)
  input produce_ack;
  wire produce_ack;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\signature.py:9" *)
  output [31:0] produce_addr;
  reg [31:0] produce_addr = 32'd0;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\signature.py:7" *)
  output produce_cyc;
  reg produce_cyc;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\signature.py:13" *)
  input [31:0] produce_r_data;
  wire [31:0] produce_r_data;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\signature.py:8" *)
  output produce_stb;
  reg produce_stb;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\signature.py:12" *)
  output [31:0] produce_w_data;
  reg [31:0] produce_w_data = 32'd0;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\signature.py:11" *)
  output produce_w_en;
  reg produce_w_en = 1'h0;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\signature.py:65" *)
  output [7:0] reply_tdata;
  reg [7:0] reply_tdata;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\signature.py:67" *)
  input reply_tready;
  wire reply_tready;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\signature.py:66" *)
  output reply_tvalid;
  reg reply_tvalid;
  (* src = "C:\\Users\\magen\\AppData\\Local\\Packages\\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\\LocalCache\\local-packages\\Python311\\site-packages\\amaranth\\hdl\\_ir.py:283" *)
  input rst;
  wire rst;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\serial\\serial_to_wishbone.py:29" *)
  reg [1:0] size = 2'h0;
  assign \$1  = ! (* src = "C:\\Users\\magen\\AppData\\Local\\Packages\\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\\LocalCache\\local-packages\\Python311\\site-packages\\amaranth\\hdl\\_dsl.py:486" *) fsm_state;
  assign \$2  = fsm_state == (* src = "C:\\Users\\magen\\AppData\\Local\\Packages\\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\\LocalCache\\local-packages\\Python311\\site-packages\\amaranth\\hdl\\_dsl.py:486" *) 1'h1;
  assign \$3  = fsm_state == (* src = "C:\\Users\\magen\\AppData\\Local\\Packages\\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\\LocalCache\\local-packages\\Python311\\site-packages\\amaranth\\hdl\\_dsl.py:486" *) 2'h2;
  assign \$4  = fsm_state == (* src = "C:\\Users\\magen\\AppData\\Local\\Packages\\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\\LocalCache\\local-packages\\Python311\\site-packages\\amaranth\\hdl\\_dsl.py:486" *) 2'h3;
  assign \$5  = fsm_state == (* src = "C:\\Users\\magen\\AppData\\Local\\Packages\\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\\LocalCache\\local-packages\\Python311\\site-packages\\amaranth\\hdl\\_dsl.py:486" *) 3'h4;
  assign \$6  = fsm_state == (* src = "C:\\Users\\magen\\AppData\\Local\\Packages\\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\\LocalCache\\local-packages\\Python311\\site-packages\\amaranth\\hdl\\_dsl.py:486" *) 3'h5;
  assign \$7  = fsm_state == (* src = "C:\\Users\\magen\\AppData\\Local\\Packages\\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\\LocalCache\\local-packages\\Python311\\site-packages\\amaranth\\hdl\\_dsl.py:486" *) 3'h6;
  assign \$8  = fsm_state == (* src = "C:\\Users\\magen\\AppData\\Local\\Packages\\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\\LocalCache\\local-packages\\Python311\\site-packages\\amaranth\\hdl\\_dsl.py:486" *) 3'h7;
  assign \$9  = ! (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\serial\\serial_to_wishbone.py:81" *) counter;
  assign \$10  = counter - (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\serial\\serial_to_wishbone.py:88" *) 1'h1;
  assign \$11  = ! (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\serial\\serial_to_wishbone.py:93" *) counter;
  assign \$12  = counter - (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\serial\\serial_to_wishbone.py:96" *) 1'h1;
  assign \$14  = ! (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\serial\\serial_to_wishbone.py:126" *) counter;
  assign \$15  = counter - (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\serial\\serial_to_wishbone.py:129" *) 1'h1;
  assign \$16  = reply_tvalid & (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\serial\\serial_to_wishbone.py:143" *) reply_tready;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\signature.py:9" *)
  always @(posedge clk)
    produce_addr <= \$17 ;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\signature.py:12" *)
  always @(posedge clk)
    produce_w_data <= \$18 ;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\signature.py:11" *)
  always @(posedge clk)
    produce_w_en <= \$19 ;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\serial\\serial_to_wishbone.py:29" *)
  always @(posedge clk)
    size <= \$20 ;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\serial\\serial_to_wishbone.py:30" *)
  always @(posedge clk)
    counter <= \$21 ;
  (* src = "C:\\Program Files\\WindowsApps\\PythonSoftwareFoundation.Python.3.11_3.11.2544.0_x64_qbz5n2kfra8p0\\Lib\\contextlib.py:144" *)
  always @(posedge clk)
    fsm_state <= \$22 ;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\serial\\serial_to_wishbone.py:32" *)
  always @(posedge clk)
    prefix <= \$23 ;
  (* src = "C:\\Users\\magen\\Documents\\Programs\\audio_fpga\\sapf\\serial\\serial_to_wishbone.py:33" *)
  always @(posedge clk)
    arg <= \$24 ;
  always @* begin
    if (\$auto$verilog_backend.cc:2352:dump_module$1 ) begin end
    command_tready = 1'h0;
    casez (fsm_state)
      3'h0:
          command_tready = 1'h1;
      3'h1:
          command_tready = 1'h1;
      3'h5:
          command_tready = 1'h1;
    endcase
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2352:dump_module$1 ) begin end
    produce_stb = 1'h0;
    casez (fsm_state)
      3'h0:
          /* empty */;
      3'h1:
          /* empty */;
      3'h5:
          /* empty */;
      3'h6:
          produce_stb = 1'h1;
    endcase
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2352:dump_module$1 ) begin end
    produce_cyc = 1'h0;
    casez (fsm_state)
      3'h0:
          /* empty */;
      3'h1:
          /* empty */;
      3'h5:
          /* empty */;
      3'h6:
          produce_cyc = 1'h1;
    endcase
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2352:dump_module$1 ) begin end
    reply_tvalid = 1'h0;
    (* full_case = 32'd1 *)
    casez (fsm_state)
      3'h0:
          /* empty */;
      3'h1:
          /* empty */;
      3'h5:
          /* empty */;
      3'h6:
          /* empty */;
      3'h2:
          reply_tvalid = 1'h1;
      3'h7:
          reply_tvalid = 1'h1;
      3'h4:
          reply_tvalid = 1'h1;
      3'h3:
          reply_tvalid = command_tvalid;
    endcase
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2352:dump_module$1 ) begin end
    reply_tdata = 8'h00;
    (* full_case = 32'd1 *)
    casez (fsm_state)
      3'h0:
          /* empty */;
      3'h1:
          /* empty */;
      3'h5:
          /* empty */;
      3'h6:
          /* empty */;
      3'h2:
          reply_tdata = prefix;
      3'h7:
          reply_tdata = arg[31:24];
      3'h4:
          reply_tdata = 8'h0a;
      3'h3:
          reply_tdata = command_tdata;
    endcase
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2352:dump_module$1 ) begin end
    \$17  = produce_addr;
    casez (fsm_state)
      3'h0:
          \$17  = 32'd0;
      3'h1:
          if (command_tvalid) begin
            (* full_case = 32'd1 *)
            casez (counter)
              2'h0:
                  \$17 [7:0] = command_tdata;
              2'h1:
                  \$17 [15:8] = command_tdata;
              2'h2:
                  \$17 [23:16] = command_tdata;
              2'h3:
                  \$17 [31:24] = command_tdata;
            endcase
          end
    endcase
    if (rst) begin
      \$17  = 32'd0;
    end
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2352:dump_module$1 ) begin end
    \$18  = produce_w_data;
    casez (fsm_state)
      3'h0:
          \$18  = 32'd0;
      3'h1:
          /* empty */;
      3'h5:
          if (command_tvalid) begin
            (* full_case = 32'd1 *)
            casez (counter)
              2'h0:
                  \$18 [7:0] = command_tdata;
              2'h1:
                  \$18 [15:8] = command_tdata;
              2'h2:
                  \$18 [23:16] = command_tdata;
              2'h3:
                  \$18 [31:24] = command_tdata;
            endcase
          end
    endcase
    if (rst) begin
      \$18  = 32'd0;
    end
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2352:dump_module$1 ) begin end
    \$19  = produce_w_en;
    casez (fsm_state)
      3'h0:
        begin
          \$19  = 1'h0;
          if (command_tvalid) begin
            casez (command_tdata)
              8'h77:
                  \$19  = 1'h1;
              8'h57:
                  \$19  = 1'h1;
            endcase
          end
        end
    endcase
    if (rst) begin
      \$19  = 1'h0;
    end
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2352:dump_module$1 ) begin end
    \$20  = size;
    casez (fsm_state)
      3'h0:
          if (command_tvalid) begin
            casez (command_tdata)
              8'h77:
                  \$20  = 2'h0;
              8'h57:
                  \$20  = 2'h3;
              8'h72:
                  \$20  = 2'h0;
              8'h52:
                  \$20  = 2'h3;
            endcase
          end
    endcase
    if (rst) begin
      \$20  = 2'h0;
    end
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2352:dump_module$1 ) begin end
    \$21  = counter;
    casez (fsm_state)
      3'h0:
          if (command_tvalid) begin
            casez (command_tdata)
              8'h77:
                  \$21  = 2'h0;
              8'h57:
                  \$21  = 2'h3;
              8'h72:
                  \$21  = 2'h0;
              8'h52:
                  \$21  = 2'h3;
            endcase
          end
      3'h1:
          if (command_tvalid) begin
            (* full_case = 32'd1 *)
            if (\$9 ) begin
              \$21  = size;
            end else begin
              \$21  = \$10 [1:0];
            end
          end
      3'h5:
          if (command_tvalid) begin
            (* full_case = 32'd1 *)
            if (\$11 ) begin
            end else begin
              \$21  = \$12 [1:0];
            end
          end
      3'h6:
          /* empty */;
      3'h2:
          if (reply_tready) begin
            \$21  = 2'h3;
          end
      3'h7:
          if (reply_tready) begin
            (* full_case = 32'd1 *)
            if (\$14 ) begin
            end else begin
              \$21  = \$15 [1:0];
            end
          end
    endcase
    if (rst) begin
      \$21  = 2'h0;
    end
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2352:dump_module$1 ) begin end
    \$22  = fsm_state;
    (* full_case = 32'd1 *)
    casez (fsm_state)
      3'h0:
          if (command_tvalid) begin
            (* full_case = 32'd1 *)
            casez (command_tdata)
              8'h77:
                  \$22  = 3'h1;
              8'h57:
                  \$22  = 3'h1;
              8'h72:
                  \$22  = 3'h1;
              8'h52:
                  \$22  = 3'h1;
              8'h49:
                  \$22  = 3'h2;
              8'h65:
                  \$22  = 3'h3;
              8'h0a:
                  \$22  = 3'h4;
              default:
                  \$22  = 3'h2;
            endcase
          end
      3'h1:
          if (command_tvalid) begin
            if (\$9 ) begin
              (* full_case = 32'd1 *)
              if (produce_w_en) begin
                \$22  = 3'h5;
              end else begin
                \$22  = 3'h6;
              end
            end
          end
      3'h5:
          if (command_tvalid) begin
            if (\$11 ) begin
              \$22  = 3'h6;
            end
          end
      3'h6:
          if (produce_ack) begin
            \$22  = 3'h2;
          end
      3'h2:
          if (reply_tready) begin
            \$22  = 3'h7;
          end
      3'h7:
          if (reply_tready) begin
            if (\$14 ) begin
              \$22  = 3'h4;
            end
          end
      3'h4:
          if (reply_tready) begin
            \$22  = 3'h0;
          end
      3'h3:
          if (\$16 ) begin
            \$22  = 3'h0;
          end
    endcase
    if (rst) begin
      \$22  = 3'h0;
    end
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2352:dump_module$1 ) begin end
    \$23  = prefix;
    casez (fsm_state)
      3'h0:
          if (command_tvalid) begin
            (* full_case = 32'd1 *)
            casez (command_tdata)
              8'h77:
                  /* empty */;
              8'h57:
                  /* empty */;
              8'h72:
                  /* empty */;
              8'h52:
                  /* empty */;
              8'h49:
                  \$23  = 8'h49;
              8'h65:
                  /* empty */;
              8'h0a:
                  /* empty */;
              default:
                  \$23  = 8'h25;
            endcase
          end
      3'h1:
          /* empty */;
      3'h5:
          /* empty */;
      3'h6:
          if (produce_ack) begin
            (* full_case = 32'd1 *)
            if (produce_w_en) begin
              \$23  = 8'h57;
            end else begin
              \$23  = 8'h52;
            end
          end
    endcase
    if (rst) begin
      \$23  = 8'h00;
    end
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2352:dump_module$1 ) begin end
    \$24  = arg;
    casez (fsm_state)
      3'h0:
          if (command_tvalid) begin
            (* full_case = 32'd1 *)
            casez (command_tdata)
              8'h77:
                  /* empty */;
              8'h57:
                  /* empty */;
              8'h72:
                  /* empty */;
              8'h52:
                  /* empty */;
              8'h49:
                  \$24  = 32'd68;
              8'h65:
                  /* empty */;
              8'h0a:
                  /* empty */;
              default:
                  \$24  = { 24'h000000, command_tdata };
            endcase
          end
      3'h1:
          /* empty */;
      3'h5:
          /* empty */;
      3'h6:
          if (produce_ack) begin
            (* full_case = 32'd1 *)
            if (produce_w_en) begin
              \$24  = 32'd1;
            end else begin
              \$24  = produce_r_data;
            end
          end
      3'h2:
          /* empty */;
      3'h7:
          if (reply_tready) begin
            \$24  = \$13 [31:0];
          end
    endcase
    if (rst) begin
      \$24  = 32'd0;
    end
  end
  assign \$13  = { 7'h00, arg, 8'h00 };
endmodule
