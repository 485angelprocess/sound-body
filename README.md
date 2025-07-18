# Risc-V based softcore for audio live-coding

The goal of this project is to run a Forth-like interpreter which translates directly into assembly.
The assembly then runs on a RISC-V softcore and produces sound or other data.

# Risc-V Core

The core is written in Amaranth HDL. Currently it runs most of the instructions from the RV32-I standard, ignoring things like `fence`. I also added multiplication.
Next is to add a floating point unit.

There is a simpler assembler which goes from assembly to byte code. I only have a few instructions setup, but it is easily expansible.

## Serial controller

I am building out a serial controller, to upload programs and to run a debugger. This is `serial_monitor.py`

For sanity checks, writing `I` to UART always returns `ID`.

To write `W` will read the next 4 bytes as the address, and 4 bytes as the data to a wishbone port. Values are address mapped. Similarly, `R` will read from a 4 byte address. Both commands are MSB.

For example if the debugger is mapped as the lowest 256 bytes, writing to a register directly:

```
>W 1 11
```
This sends `'W'` followed by `0x00_00_00_01_00_00_00_0B`

And reading from the register
```
>R 1
```
This sends `'R'` followed by `0x00_00_00_01` and will reply with an `'R'` followed by the echoed address `0x00_00_00_01` and the data in the register `0x00_00_00_0B`.

If the ram DMA is the following address space, reading and writing to the 1st address of ram is done by:
```
>W 257 13
>R 257
```

# Audio out

The audio out is right now going through a DAC chip, which requires an I2S stream and an I2C controller. Drivers for both are in `ser` and tested with `test_serial.py`. 
The I2C controller can run a sucessful scan, next is getting to DAC setup over I2C.

# Interpreter

The interpreter is based on Forth and sapf. It is stack based and translates directly to Risc-V Assembly.
