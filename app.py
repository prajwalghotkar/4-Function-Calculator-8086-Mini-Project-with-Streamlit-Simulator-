"""
4-Function Calculator - EMU8086 Mini Project
Streamlit Frontend + Python-based 8086 Register/Flag Simulator

This app does NOT re-implement EMU8086 itself (that's a Windows-only
proprietary tool). Instead it mirrors, instruction by instruction, the
exact logic of calculator.asm, and shows you the AX/BX/CX/DX registers
and CF/OF/ZF/SF flags exactly as EMU8086's own register window would
after each step. Use it to demo the project, generate test-case tables,
and screenshot results for your report.
"""

import streamlit as st
import pandas as pd

# ----------------------------------------------------------------------
# 16-bit signed/unsigned helpers (mirrors how the 8086 actually computes)
# ----------------------------------------------------------------------

def to_u16(x: int) -> int:
    return x & 0xFFFF


def to_s16(x: int) -> int:
    x = x & 0xFFFF
    return x - 0x10000 if x >= 0x8000 else x


def hexw(x: int) -> str:
    return f"{to_u16(x):04X}h"


def add16(a: int, b: int):
    ua, ub = to_u16(a), to_u16(b)
    usum = ua + ub
    result = to_u16(usum)
    CF = 1 if usum > 0xFFFF else 0
    sa, sb, sr = to_s16(a), to_s16(b), to_s16(result)
    OF = 1 if ((sa >= 0 and sb >= 0 and sr < 0) or (sa < 0 and sb < 0 and sr >= 0)) else 0
    ZF = 1 if result == 0 else 0
    SF = 1 if result & 0x8000 else 0
    return result, {"CF": CF, "OF": OF, "ZF": ZF, "SF": SF}


def sub16(a: int, b: int):
    ua, ub = to_u16(a), to_u16(b)
    result = to_u16(ua - ub)
    CF = 1 if ua < ub else 0
    sa, sb, sr = to_s16(a), to_s16(b), to_s16(result)
    OF = 1 if ((sa >= 0 and sb < 0 and sr < 0) or (sa < 0 and sb >= 0 and sr >= 0)) else 0
    ZF = 1 if result == 0 else 0
    SF = 1 if result & 0x8000 else 0
    return result, {"CF": CF, "OF": OF, "ZF": ZF, "SF": SF}


def imul16(a: int, b: int):
    """Simulates IMUL num2 : DX:AX = AX * num2 (signed 16x16 -> 32)."""
    sa, sb = to_s16(a), to_s16(b)
    full = sa * sb
    dx = to_u16((full >> 16) & 0xFFFF)
    ax = to_u16(full & 0xFFFF)
    sign_ext = 0xFFFF if to_s16(ax) < 0 else 0x0000
    CF = OF = 1 if dx != sign_ext else 0
    return ax, dx, {"CF": CF, "OF": OF, "ZF": "-", "SF": "-"}


def idiv16(a: int, b: int):
    """Simulates CWD + IDIV num2 : AX = quotient, DX = remainder."""
    if b == 0:
        return None
    # 8086 IDIV truncates toward 0 (unlike Python's // which truncates toward -inf)
    q = int(to_s16(a) / to_s16(b))
    r = to_s16(a) - q * to_s16(b)
    return to_u16(q), to_u16(r), {"CF": "-", "OF": "-", "ZF": "-", "SF": "-"}


# ----------------------------------------------------------------------
# Instruction-level simulation, mirroring calculator.asm line for line
# ----------------------------------------------------------------------

def simulate(op: str, num1: int, num2: int):
    trace = []
    regs = {"AX": 0, "BX": to_u16(num2), "CX": 0, "DX": 0}
    flags = {"CF": "-", "OF": "-", "ZF": "-", "SF": "-"}

    def snap(instr, note=""):
        trace.append({
            "Instruction": instr,
            "AX": hexw(regs["AX"]),
            "BX": hexw(regs["BX"]),
            "DX": hexw(regs["DX"]),
            "CF": flags["CF"], "OF": flags["OF"], "ZF": flags["ZF"], "SF": flags["SF"],
            "Note": note,
        })

    regs["AX"] = to_u16(num1)
    snap("MOV AX, num1", f"AX <- num1 ({to_s16(num1)})")

    if op == "ADD":
        result, f = add16(num1, num2)
        regs["AX"] = result
        flags.update(f)
        snap("ADD AX, num2", f"AX <- num1 + num2 = {to_s16(result)}")
        snap("MOV result, AX", "store result")
        final = to_s16(result)
        extra = None

    elif op == "SUB":
        result, f = sub16(num1, num2)
        regs["AX"] = result
        flags.update(f)
        snap("SUB AX, num2", f"AX <- num1 - num2 = {to_s16(result)}")
        snap("MOV result, AX", "store result")
        final = to_s16(result)
        extra = None

    elif op == "MUL":
        ax, dx, f = imul16(num1, num2)
        regs["AX"], regs["DX"] = ax, dx
        flags.update(f)
        snap("IMUL num2", f"DX:AX <- num1 * num2 = {to_s16(num1) * to_s16(num2)}")
        snap("MOV result, AX", "store low word of result")
        final = to_s16(num1) * to_s16(num2)
        extra = None
        if to_s16(ax) != final:
            extra = ("note", "Result overflows 16 bits (CF=OF=1); low word shown is what a real 16-bit result register would hold.")

    elif op == "DIV":
        if num2 == 0:
            snap("CMP AX, 0 / JE DIV_ZERO", "num2 == 0 -> jump to error handler")
            return trace, None, None, "DIV0"
        regs["DX"] = 0
        snap("CWD", "sign-extend AX into DX:AX")
        q, r, f = idiv16(num1, num2)
        regs["AX"], regs["DX"] = q, r
        flags.update(f)
        snap("IDIV num2", f"AX <- quotient = {to_s16(q)}, DX <- remainder = {to_s16(r)}")
        snap("MOV result, AX", "store quotient")
        snap("MOV remain, DX", "store remainder")
        final = to_s16(q)
        extra = ("remainder", to_s16(r))
    else:
        return trace, None, None, "BAD"

    return trace, final, extra, "OK"


# ----------------------------------------------------------------------
# Streamlit page config + styling
# ----------------------------------------------------------------------

st.set_page_config(page_title="8086 4-Function Calculator", page_icon="🧮", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0f1117; }
    .reg-table td, .reg-table th { font-family: 'Courier New', monospace; }
    .term {
        background-color: #05070a;
        color: #39ff14;
        font-family: 'Courier New', monospace;
        padding: 18px;
        border-radius: 8px;
        border: 1px solid #1f2937;
        font-size: 15px;
        white-space: pre-wrap;
    }
    .result-box {
        background-color: #111827;
        border-left: 5px solid #39ff14;
        padding: 14px 20px;
        border-radius: 6px;
        font-family: 'Courier New', monospace;
        font-size: 20px;
        color: #f5f5f5;
    }
</style>
""", unsafe_allow_html=True)

PAGES = [
    "🧮 Calculator Simulator",
    "1. Title",
    "2. Aim & Objective",
    "3. Hardware & Software Requirements",
    "4. Theory",
    "5. Program Code",
    "6. Program Explanation",
    "7. Output / Simulation Screenshots",
    "8. Test Cases & Results",
    "9. Conclusion",
]

with st.sidebar:
    st.title("📘 Mini Project")
    st.caption("4-Function Calculator using the EMU8086 microprocessor emulator")
    page = st.radio("Report Sections", PAGES, index=0)
    st.markdown("---")
    st.caption("Built with Streamlit • Assembly runs in EMU8086 • This app simulates the register/flag behaviour for demo & testing.")

# ----------------------------------------------------------------------
# CALCULATOR / SIMULATOR PAGE
# ----------------------------------------------------------------------
if page == "🧮 Calculator Simulator":
    st.title("🧮 4-Function Calculator — 8086 Register Simulator")
    st.write(
        "Enter two integers and pick an operation. This runs the **same logic as `calculator.asm`** "
        "step by step and shows you the register/flag state EMU8086 would show, plus a terminal-style "
        "preview of the DOS console output."
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        num1 = st.number_input("First number", value=25, step=1, format="%d")
    with col2:
        num2 = st.number_input("Second number", value=4, step=1, format="%d")
    with col3:
        op_label = st.selectbox("Operation", ["Addition (+)", "Subtraction (-)", "Multiplication (*)", "Division (/)"])

    op_map = {
        "Addition (+)": "ADD",
        "Subtraction (-)": "SUB",
        "Multiplication (*)": "MUL",
        "Division (/)": "DIV",
    }
    op_symbol = {"ADD": "+", "SUB": "-", "MUL": "*", "DIV": "/"}
    op = op_map[op_label]

    run = st.button("▶ Run on Simulator", type="primary")

    if run:
        num1, num2 = int(num1), int(num2)
        trace, final, extra, status = simulate(op, num1, num2)

        left, right = st.columns([1.3, 1])

        with left:
            st.subheader("Register / Flag Trace")
            df = pd.DataFrame(trace)
            st.dataframe(df, use_container_width=True, hide_index=True)

        with right:
            st.subheader("DOS Console Preview")
            console = "------------------------------------\n"
            console += "   4-FUNCTION CALCULATOR (8086)\n"
            console += "------------------------------------\n"
            console += "1. Addition\n2. Subtraction\n3. Multiplication\n4. Division\n"
            console += f"Enter choice (1-4): {['ADD','SUB','MUL','DIV'].index(op)+1}\n"
            console += f"Enter first number  : {num1}\n"
            console += f"Enter second number : {num2}\n"
            if status == "DIV0":
                console += "ERROR: Division by zero is not allowed!\n"
            elif status == "OK":
                console += f"Result = {final}\n"
                if extra and extra[0] == "remainder":
                    console += f"Remainder = {extra[1]}\n"
            st.markdown(f"<div class='term'>{console}</div>", unsafe_allow_html=True)

            st.subheader("Result")
            if status == "DIV0":
                st.error("Division by zero — the program jumps to DIV_ZERO and prints an error message, exactly as EMU8086 would show if num2 = 0.")
            else:
                st.markdown(
                    f"<div class='result-box'>{num1} {op_symbol[op]} {num2} = <b>{final}</b></div>",
                    unsafe_allow_html=True,
                )
                if extra and extra[0] == "remainder":
                    st.markdown(f"<div class='result-box' style='margin-top:8px;'>Remainder = <b>{extra[1]}</b></div>", unsafe_allow_html=True)
                if extra and extra[0] == "note":
                    st.warning(extra[1])
    else:
        st.info("Set your values and click **Run on Simulator** to see the register trace.")

# ----------------------------------------------------------------------
# 1. TITLE
# ----------------------------------------------------------------------
elif page == "1. Title":
    st.title("Mini Project")
    st.markdown("""
### To design, implement, and simulate a simple 4-function calculator
### using the EMU8086 microprocessor emulator.

---
**Submitted by:** _[Your Name]_
**Class / Roll No.:** _[Fill in]_
**Subject:** Microprocessor & Microcontroller Lab
**Guide:** _[Faculty Name]_
""")

# ----------------------------------------------------------------------
# 2. AIM & OBJECTIVE
# ----------------------------------------------------------------------
elif page == "2. Aim & Objective":
    st.header("2. Aim and Objective")
    st.markdown("""
**Aim:**
To design, implement, and simulate a 4-function (addition, subtraction, multiplication,
and division) calculator using 8086 assembly language on the EMU8086 microprocessor
emulator, and to build a supporting interactive frontend to visualize its execution.

**Objectives:**
- To understand the internal architecture of the 8086 microprocessor (registers, flags, ALU).
- To write, assemble, and execute assembly language instructions for arithmetic operations.
- To use DOS interrupt `INT 21H` services for console input and output.
- To handle signed numbers, multi-digit decimal conversion, and edge cases (e.g. division by zero).
- To simulate and visualize register/flag behaviour for testing and demonstration purposes.
""")

# ----------------------------------------------------------------------
# 3. HARDWARE & SOFTWARE REQUIREMENTS
# ----------------------------------------------------------------------
elif page == "3. Hardware & Software Requirements":
    st.header("3. Hardware and Software Requirements")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Hardware")
        st.markdown("""
- A PC/laptop (Windows, or a VM/Wine layer on Linux/Mac) — minimum requirement to run EMU8086
- Minimum 512 MB RAM, any modern CPU (EMU8086 is extremely lightweight)
- Keyboard for input during simulation
""")
    with c2:
        st.subheader("Software")
        st.markdown("""
- **EMU8086** — 8086 microprocessor emulator & assembler/IDE
- **VS Code** — for editing `.asm` source and project files
- **Python 3.9+** and **Streamlit** — for the interactive simulator frontend
- **pandas** — for the register-trace tables in the frontend
""")

# ----------------------------------------------------------------------
# 4. THEORY
# ----------------------------------------------------------------------
elif page == "4. Theory":
    st.header("4. Theory")
    st.markdown("""
**The 8086 Microprocessor**
The Intel 8086 is a 16-bit microprocessor with four general-purpose registers
(AX, BX, CX, DX), each of which can be accessed as two 8-bit halves (e.g. AH/AL).
Arithmetic instructions update the **FLAGS register**, of which this project uses:

| Flag | Meaning |
|---|---|
| **ZF** (Zero Flag) | Set when the result of an operation is 0 |
| **SF** (Sign Flag) | Set when the result is negative (MSB = 1) |
| **CF** (Carry Flag) | Set on unsigned overflow / borrow |
| **OF** (Overflow Flag) | Set on signed overflow |

**Instructions used**

| Instruction | Purpose |
|---|---|
| `MOV` | Move data between registers/memory |
| `ADD` / `SUB` | Addition / subtraction |
| `IMUL` | Signed multiplication (result in `DX:AX`) |
| `CWD` | Sign-extend `AX` into `DX:AX` before division |
| `IDIV` | Signed division (`AX` = quotient, `DX` = remainder) |
| `INT 21H` | DOS interrupt for console I/O (`AH=01H` read char, `AH=02H` write char, `AH=09H` write string, `AH=4CH` terminate) |

**Why decimal conversion is needed:** the 8086 only understands binary/hex numbers
in registers, but the user types and reads *decimal* digits as ASCII characters.
`READ_NUM` converts typed ASCII digits into a binary number (`value = value*10 + digit`),
and `PRINT_NUM` does the reverse — repeatedly dividing by 10 and printing remainders
in reverse order using the stack.
""")

# ----------------------------------------------------------------------
# 5. PROGRAM CODE
# ----------------------------------------------------------------------
elif page == "5. Program Code":
    st.header("5. Program Code")
    st.write("Full 8086 assembly source — open this in EMU8086 as `calculator.asm`.")
    try:
        with open("calculator.asm", "r") as f:
            code = f.read()
    except FileNotFoundError:
        code = "; calculator.asm not found next to app.py"
    st.code(code, language="nasm", line_numbers=True)
    st.download_button("⬇ Download calculator.asm", code, file_name="calculator.asm")

# ----------------------------------------------------------------------
# 6. PROGRAM EXPLANATION
# ----------------------------------------------------------------------
elif page == "6. Program Explanation":
    st.header("6. Program Explanation")
    st.markdown("""
**1. Data segment (`.DATA`)** — stores all prompt/message strings terminated with `$`
(required by `INT 21H, AH=09H`), plus working variables `num1`, `num2`, `result`, `remain`.

**2. Menu & choice** — `MAIN` prints the menu, then reads a single character via
`INT 21H, AH=01H` and converts it from ASCII to a number by subtracting `'0'`.

**3. Reading operands (`READ_NUM`)** — reads characters one at a time until `Enter`
(ASCII 13). An optional leading `-` sets a sign flag. Each digit is folded into the
accumulator `BX` via `BX = BX*10 + digit`, so multi-digit and negative numbers both work.

**4. Dispatch** — a chain of `CMP`/`JE` instructions jumps to `DO_ADD`, `DO_SUB`,
`DO_MUL`, or `DO_DIV` based on the stored choice.

**5. Arithmetic**
- **Addition/Subtraction:** direct `ADD`/`SUB` on 16-bit registers.
- **Multiplication:** `IMUL num2` — a signed multiply where the full product lands in `DX:AX`.
- **Division:** first checks `num2 == 0` and jumps to `DIV_ZERO` if so (guards against
  a runtime divide error); otherwise `CWD` sign-extends `AX` into `DX:AX` before `IDIV`,
  giving quotient in `AX` and remainder in `DX`.

**6. Printing (`PRINT_NUM`)** — handles negative numbers by printing `-` and negating
first, then repeatedly divides by 10, pushing each remainder digit onto the stack, and
pops them back off to print most-significant-digit first.

**7. Exit** — `INT 21H, AH=4CH` returns control to DOS/EMU8086 cleanly.
""")

# ----------------------------------------------------------------------
# 7. OUTPUT / SCREENSHOTS
# ----------------------------------------------------------------------
elif page == "7. Output / Simulation Screenshots":
    st.header("7. Output and Simulation on Screenshots")
    st.markdown("""
For your report, include screenshots of:
1. The EMU8086 **editor** with `calculator.asm` loaded and successfully compiled (no errors).
2. The EMU8086 **emulator window** paused mid-execution, showing the **Registers panel**
   (AX, BX, CX, DX, Flags) — compare these values against the trace on the
   **Calculator Simulator** tab of this app for the same inputs.
3. The **DOS console output** window for each of the 4 operations, plus one screenshot
   of the division-by-zero error case.

Use the **🧮 Calculator Simulator** page to pre-check expected register values and
outputs before you run the actual EMU8086 emulator — it should match exactly.
""")

# ----------------------------------------------------------------------
# 8. TEST CASES & RESULTS
# ----------------------------------------------------------------------
elif page == "8. Test Cases & Results":
    st.header("8. Test Cases and Results")

    test_cases = [
        ("ADD", 25, 4),
        ("SUB", 25, 4),
        ("SUB", 4, 25),
        ("MUL", 12, 11),
        ("MUL", -6, 7),
        ("DIV", 20, 4),
        ("DIV", 7, 2),
        ("DIV", 9, 0),
    ]
    op_symbol = {"ADD": "+", "SUB": "-", "MUL": "*", "DIV": "/"}
    rows = []
    for op, a, b in test_cases:
        trace, final, extra, status = simulate(op, a, b)
        if status == "DIV0":
            outcome = "Division by zero error"
        else:
            outcome = str(final)
            if extra and extra[0] == "remainder":
                outcome += f" (remainder {extra[1]})"
        rows.append({
            "Operation": op,
            "Expression": f"{a} {op_symbol[op]} {b}",
            "Simulated Result": outcome,
            "Status": "✅ Pass" if True else "❌ Fail",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(
        "Run each expression through EMU8086 itself and confirm the console output matches "
        "the 'Simulated Result' column above — record that as your actual test evidence."
    )

# ----------------------------------------------------------------------
# 9. CONCLUSION
# ----------------------------------------------------------------------
elif page == "9. Conclusion":
    st.header("9. Conclusion")
    st.markdown("""
This mini project successfully demonstrates a 4-function calculator implemented in
8086 assembly language and executed on the EMU8086 emulator. It reinforces core
microprocessor concepts — register usage, the flags register, DOS interrupt-based
I/O, and signed arithmetic (`ADD`, `SUB`, `IMUL`, `CWD`/`IDIV`) — while the
accompanying Streamlit frontend adds an interactive, visual layer that mirrors the
processor's register/flag behaviour, making the internal working of the emulator
easier to understand, test, and present.

**Possible extensions:** supporting floating-point values, adding modulo/exponent
operations, or extending the simulator to interpret arbitrary `.asm` files generically.
""")
