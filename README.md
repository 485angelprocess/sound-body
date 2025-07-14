# Risc-V based softcore for audio live-coding

The goal of this project is to run a Forth-like interpreter which translates directly into assembly.
The assembly then runs on a RISC-V softcore and produces sound or other data.

# Risc-V Core

The core is written in Amaranth HDL. Currently it runs most of the instructions from the RV32-I standard, ignoring things like `fence`. I also added multiplication.
Next is to add a floating point unit.

There is a simpler assembler which goes from assembly to byte code. I only have a few instructions setup, but it is easily expansible

# Audio out

The audio out is right now going through a DAC chip, which requires an I2S stream and an I2C controller. Drivers for both are in `ser` and tested with `test_serial.py`. 
The I2C controller can run a sucessful scan, next is getting to DAC setup over I2C.

# Interpreter

The interpreter is based on Forth and sapf. It is stack based and translates directly to Risc-V Assembly.
