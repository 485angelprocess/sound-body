.section .text
.globl _start:
	la s7, PUSH
	la s8, POP
	addi x5, sp, 0

	# Push constant int onto stack: (5,)
		addi	x7, x0, 5
		addi	x6, x0, 0
		jal	x9, PUSH
	# duplicate top of stack
		lw	x7, 8(x1)
		lw	x6, 4(x1)
		jal	x9, PUSH

	# Multiply two registers
		jal	x9, POP
		addi	x11, x7, 0
		jal	x9, POP
		mul	x7, x11, x7
		addi	x6, x0, 0
		jal	x9, PUSH, 0

	# PRINT (TODO)

		li a0, 10
		ecall
.section .rodata
POP:		lw	x7, 8(x1)
		lw	x6, 4(x1)
		addi	x1, x1, 8
		jalr	x9, x9, 0
PUSH:		sw	x7, 0(x1)
		sw	x6, -4(x1)
		addi	x1, x1, -8
		jalr	x9, x9, 0