.section .text
.globl _start:
	la s7, PUSH
	la s8, POP
	addi x5, sp, 0
	# Push onto stack: (5,)
		addi	x7, x8, 5
		addi	x6, x8, 0
		jalr	x9, s7, 0
	# Push onto stack: (4,)
		addi	x7, x8, 4
		addi	x6, x8, 0
		jalr	x9, s7, 0
	# Add two registers: None
		jalr	x9, s8, 0
		addi	x11, x7, 0
		jalr	x9, s8, 0
		add	x7, x11, x7
		addi	x6, x8, 0
		jalr	x9, s7, 0
		li a0, 10
		ecall
.section .rodata
POP:		lw	x7, 8(x5)
		lw	x6, 4(x5)
		addi	x5, x5, 8
		jalr	x9, x9, 0
PUSH:		sw	x7, 0(x5)
		sw	x6, -4(x5)
		addi	x5, x5, -8
		jalr	x9, x9, 0