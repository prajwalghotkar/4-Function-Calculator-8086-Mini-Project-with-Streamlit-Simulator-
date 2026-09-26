# 4-Function Calculator — 8086 Mini Project (with Streamlit Simulator)

Design, implement, and simulate a 4-function calculator (+, −, ×, ÷) in 8086
assembly using **EMU8086**, with a **Streamlit** frontend that visualizes the
register/flag behaviour instruction-by-instruction.

## Project Structure

```
EMU8086_Calculator_Project/
├── calculator.asm     # 8086 assembly source — open & run in EMU8086
├── app.py             # Streamlit frontend / register-flag simulator
├── requirements.txt   # Python dependencies
└── README.md
```

## Part 1 — Run the real assembly in EMU8086 (Windows)

1. Download and install **EMU8086** (emu8086.com — free trial is enough for this project).
2. Open EMU8086 → **File → Open** → select `calculator.asm`.
3. Click **Compile** (or press F5) to assemble it.
4. Click **Emulate** to launch the emulator, then **Run** (F9) or **Single Step** (F8)
   to step through instructions while watching the **Registers** and **Flags** panel.
5. In the emulator's console window, enter your choice (1–4) and the two numbers when
   prompted, then observe the result (and remainder, for division).

If you're on macOS/Linux, EMU8086 can be run through **Wine** or a lightweight Windows VM.

## Part 2 — Run the Streamlit simulator (cross-platform, in VS Code)

This does not require Windows or EMU8086 — it's a Python reimplementation of the same
instruction logic, useful for demos, generating test tables, and sanity-checking your
EMU8086 run.

### Setup in VS Code

1. Open this folder in VS Code (`File → Open Folder…`).
2. Open a terminal in VS Code (`` Ctrl+` ``) and create a virtual environment (optional
   but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate      # on Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the app:
   ```bash
   streamlit run app.py
   ```
5. It will open automatically at `http://localhost:8501` in your browser.

### What the app gives you

- **🧮 Calculator Simulator** — enter two numbers + pick an operation, see the exact
  instruction-by-instruction register/flag trace (AX, BX, DX, CF, OF, ZF, SF) plus a
  DOS-console-style output preview and the final result.
- **Report sections 1–9** — matches your submission's table of contents (Title, Aim &
  Objective, Hardware & Software Requirements, Theory, Program Code, Program
  Explanation, Output/Screenshots guidance, Test Cases & Results, Conclusion) so the
  whole write-up lives inside the same app.
- **Test Cases & Results** page — auto-generates a table of sample test cases
  (including edge cases like negative numbers and division by zero) you can cross-check
  against your actual EMU8086 run and paste into your report.

## Notes

- `calculator.asm` handles signed multi-digit input, negative results, and guards
  against division by zero (jumps to an error message instead of crashing).
- The Streamlit simulator mirrors 8086 semantics precisely: 16-bit wraparound,
  signed overflow (`OF`), carry (`CF`), sign (`SF`) and zero (`ZF`) flags, and
  truncate-toward-zero integer division — so its numbers will match what EMU8086
  itself shows.
