;=================================================================
; MINI PROJECT : 4-Function Calculator using 8086 Microprocessor
; Tool         : EMU8086 Emulator
; Description  : Reads two signed decimal numbers and a choice of
;                operation (+, -, *, /) and displays the result.
;                Division also displays the remainder.
;=================================================================

.MODEL SMALL
.STACK 100H

.DATA
    msg_menu     DB 10,13,'------------------------------------',10,13
                 DB '   4-FUNCTION CALCULATOR (8086)',10,13
                 DB '------------------------------------',10,13
                 DB '1. Addition',10,13
                 DB '2. Subtraction',10,13
                 DB '3. Multiplication',10,13
                 DB '4. Division',10,13
                 DB 'Enter choice (1-4): $'

    msg_num1     DB 10,13,'Enter first number  : $'
    msg_num2     DB 10,13,'Enter second number : $'
    msg_result   DB 10,13,'Result = $'
    msg_remain   DB 10,13,'Remainder = $'
    msg_err      DB 10,13,'ERROR: Division by zero is not allowed!$'
    msg_bad      DB 10,13,'Invalid choice!$'
    msg_neg      DB '-$'

    choice       DB ?
    num1         DW ?
    num2         DW ?
    result       DW ?
    remain       DW ?

.CODE
MAIN PROC
    MOV AX, @DATA
    MOV DS, AX

    ; ---- Show menu and read choice ----
    LEA DX, msg_menu
    MOV AH, 09H
    INT 21H

    MOV AH, 01H          ; read single character (choice)
    INT 21H
    SUB AL, '0'
    MOV choice, AL

    ; ---- Read first operand ----
    LEA DX, msg_num1
    MOV AH, 09H
    INT 21H
    CALL READ_NUM
    MOV num1, BX

    ; ---- Read second operand ----
    LEA DX, msg_num2
    MOV AH, 09H
    INT 21H
    CALL READ_NUM
    MOV num2, BX

    ; ---- Dispatch on choice ----
    MOV AL, choice
    CMP AL, 1
    JE DO_ADD
    CMP AL, 2
    JE DO_SUB
    CMP AL, 3
    JE DO_MUL
    CMP AL, 4
    JE DO_DIV

    LEA DX, msg_bad
    MOV AH, 09H
    INT 21H
    JMP EXIT_PROG

DO_ADD:
    MOV AX, num1
    ADD AX, num2         ; AX = num1 + num2
    MOV result, AX
    JMP SHOW_RESULT

DO_SUB:
    MOV AX, num1
    SUB AX, num2         ; AX = num1 - num2
    MOV result, AX
    JMP SHOW_RESULT

DO_MUL:
    MOV AX, num1
    IMUL num2            ; DX:AX = num1 * num2 (signed)
    MOV result, AX
    JMP SHOW_RESULT

DO_DIV:
    MOV AX, num2
    CMP AX, 0
    JE DIV_ZERO
    MOV AX, num1
    CWD                  ; sign-extend AX into DX:AX
    IDIV num2            ; AX = quotient, DX = remainder
    MOV result, AX
    MOV remain, DX

    LEA DX, msg_result
    MOV AH, 09H
    INT 21H
    MOV AX, result
    CALL PRINT_NUM

    LEA DX, msg_remain
    MOV AH, 09H
    INT 21H
    MOV AX, remain
    CALL PRINT_NUM
    JMP EXIT_PROG

DIV_ZERO:
    LEA DX, msg_err
    MOV AH, 09H
    INT 21H
    JMP EXIT_PROG

SHOW_RESULT:
    LEA DX, msg_result
    MOV AH, 09H
    INT 21H
    MOV AX, result
    CALL PRINT_NUM

EXIT_PROG:
    MOV AH, 4CH
    INT 21H
MAIN ENDP


;-----------------------------------------------------------------
; READ_NUM: reads a signed decimal number typed by the user
;           (terminated by Enter) into BX.
;-----------------------------------------------------------------
READ_NUM PROC
    PUSH AX
    PUSH CX
    PUSH DX
    MOV BX, 0            ; accumulator
    MOV CX, 0            ; sign flag: 0 = positive, 1 = negative

    MOV AH, 01H
    INT 21H
    CMP AL, '-'
    JNE RN_LOOP
    MOV CX, 1
    MOV AH, 01H
    INT 21H

RN_LOOP:
    CMP AL, 13           ; Enter key ends input
    JE RN_DONE
    SUB AL, '0'
    CBW
    PUSH AX
    MOV AX, BX
    MOV DX, 10
    MUL DX               ; BX = BX * 10
    MOV BX, AX
    POP AX
    ADD BX, AX           ; BX = BX + new digit
    MOV AH, 01H
    INT 21H
    JMP RN_LOOP

RN_DONE:
    CMP CX, 1
    JNE RN_END
    NEG BX

RN_END:
    POP DX
    POP CX
    POP AX
    RET
READ_NUM ENDP


;-----------------------------------------------------------------
; PRINT_NUM: prints the signed 16-bit number in AX as decimal text
;-----------------------------------------------------------------
PRINT_NUM PROC
    PUSH AX
    PUSH BX
    PUSH CX
    PUSH DX
    MOV CX, 0            ; digit counter

    CMP AX, 0
    JGE PN_CONVERT
    PUSH AX
    LEA DX, msg_neg
    MOV AH, 09H
    INT 21H
    POP AX
    NEG AX

PN_CONVERT:
    CMP AX, 0
    JNE PN_LOOP
    MOV DL, '0'
    MOV AH, 02H
    INT 21H
    JMP PN_END

PN_LOOP:
    CMP AX, 0
    JE PN_PRINT
    MOV DX, 0
    MOV BX, 10
    DIV BX               ; AX = AX/10, DX = remainder digit
    PUSH DX
    INC CX
    JMP PN_LOOP

PN_PRINT:
    CMP CX, 0
    JE PN_END
    POP DX
    ADD DL, '0'
    MOV AH, 02H
    INT 21H
    DEC CX
    JMP PN_PRINT

PN_END:
    POP DX
    POP CX
    POP BX
    POP AX
    RET
PRINT_NUM ENDP

END MAIN
