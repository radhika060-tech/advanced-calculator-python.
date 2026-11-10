"""
Advanced Calculator using Tkinter
---------------------------------
- Scientific functions (angles are in degrees)
- Small History option: click "History" to show or hide the panel
- Keyboard support
- Safe expression evaluation using the ast module (no eval())
"""
import ast
import math
import operator
import tkinter as tk

# ---------------------------------------------------------------- colours
NAVY = "#1F2A44"       # display and equals-button text
BG = "#F4F6F8"         # window background
WHITE = "#FFFFFF"      # number buttons
FUNC_BG = "#E8ECF3"    # function buttons
OP_BG = "#C9D3E3"      # operator buttons
CLEAR_BG = "#D5DBE6"   # C and backspace
EQUALS_BG = "#2F5FD0"  # equals button
MUTED = "#9FB0CC"      # small text on the display
BORDER = "#D0D7E2"

# ---------------------------------------------------------- maths engine
BIN_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}
UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def factorial(x):
    if x != int(x) or x < 0 or x > 170:
        raise ValueError("invalid factorial")
    return math.factorial(int(x))


def cube_root(x):
    return math.copysign(abs(x) ** (1 / 3), x)


FUNCS = {
    "sin": lambda v: math.sin(math.radians(v)),
    "cos": lambda v: math.cos(math.radians(v)),
    "tan": lambda v: math.tan(math.radians(v)),
    "asin": lambda v: math.degrees(math.asin(v)),
    "acos": lambda v: math.degrees(math.acos(v)),
    "atan": lambda v: math.degrees(math.atan(v)),
    "ln": math.log, "log": math.log10,
    "sqrt": math.sqrt, "cbrt": cube_root,
    "fact": factorial, "abs": abs,
}
CONSTS = {"pi": math.pi, "e": math.e}


def safe_eval(text):
    """Evaluate a math expression safely by walking its syntax tree."""

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in BIN_OPS:
            left, right = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 1000:
                raise ValueError("exponent too large")
            return BIN_OPS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPS:
            return UNARY_OPS[type(node.op)](ev(node.operand))
        if isinstance(node, ast.Name) and node.id in CONSTS:
            return CONSTS[node.id]
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in FUNCS and len(node.args) == 1
                and not node.keywords):
            return FUNCS[node.func.id](ev(node.args[0]))
        raise ValueError("unsupported expression")

    # Convert display symbols to Python syntax
    for old, new in (("×", "*"), ("÷", "/"), ("^", "**"), ("√", "sqrt"),
                     ("∛", "cbrt"), ("π", "pi"), ("%", "/100")):
        text = text.replace(old, new)
    return ev(ast.parse(text, mode="eval"))


def fmt(value):
    """Format a number neatly for the display."""
    value = round(value, 12)
    if isinstance(value, float) and value.is_integer() and abs(value) < 1e15:
        return str(int(value))
    return f"{value:.10g}"


# ------------------------------------------------------------------- GUI
class AdvancedCalculator:
    BUTTONS = [
        ["C",    "⌫",    "(",    ")",   "%",   "|x|", "÷"],
        ["sin",  "cos",  "tan",  "7",   "8",   "9",   "×"],
        ["asin", "acos", "atan", "4",   "5",   "6",   "-"],
        ["ln",   "log",  "√",    "1",   "2",   "3",   "+"],
        ["x²",   "xʸ",   "n!",   "0",   ".",   "00",  "="],
        ["π",    "e",    "1/x",  "∛",   "10ˣ", "eˣ",  "Ans"],
    ]
    # Text inserted when a function button is pressed
    INSERTS = {
        "sin": "sin(", "cos": "cos(", "tan": "tan(",
        "asin": "asin(", "acos": "acos(", "atan": "atan(",
        "ln": "ln(", "log": "log(", "√": "√(", "∛": "∛(",
        "|x|": "abs(", "n!": "fact(", "1/x": "1/(",
        "10ˣ": "10^(", "eˣ": "e^(", "x²": "^2", "xʸ": "^",
    }
    OPERATORS = "+-×÷^%"

    def __init__(self, root):
        self.root = root
        root.title("Advanced Calculator")
        root.configure(bg=BG)
        root.resizable(False, False)

        self.expr = ""
        self.last_answer = "0"
        self.fresh = False            # True right after "=" is pressed
        self.history_visible = False

        self.build_display()
        self.build_buttons()
        self.build_history()
        root.bind("<Key>", self.on_key)

    # ---------- layout ----------
    def build_display(self):
        frame = tk.Frame(self.root, bg=NAVY)
        frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        top = tk.Frame(frame, bg=NAVY)
        top.pack(fill="x", padx=10, pady=(8, 0))
        self.history_btn = tk.Button(
            top, text="History", bg=NAVY, fg=MUTED, bd=0, relief="flat",
            activebackground=NAVY, activeforeground=WHITE, cursor="hand2",
            font=("Segoe UI", 9, "underline"), command=self.toggle_history)
        self.history_btn.pack(side="left")

        self.top_var = tk.StringVar()
        self.main_var = tk.StringVar(value="0")
        tk.Label(top, textvariable=self.top_var, anchor="e", bg=NAVY, fg=MUTED,
                 font=("Segoe UI", 10)).pack(side="right", fill="x", expand=True)
        tk.Label(frame, textvariable=self.main_var, anchor="e", bg=NAVY,
                 fg=WHITE, font=("Segoe UI", 26, "bold")
                 ).pack(fill="x", padx=10, pady=(0, 8))

    def build_buttons(self):
        frame = tk.Frame(self.root, bg=BG)
        frame.grid(row=1, column=0, padx=10, pady=(0, 10))
        for r, row in enumerate(self.BUTTONS):
            for c, label in enumerate(row):
                if label == "=":
                    bg, fg = EQUALS_BG, WHITE
                elif label in ("C", "⌫"):
                    bg, fg = CLEAR_BG, NAVY
                elif label in "÷×-+":
                    bg, fg = OP_BG, NAVY
                elif label.isdigit() or label == ".":
                    bg, fg = WHITE, NAVY
                else:
                    bg, fg = FUNC_BG, NAVY
                tk.Button(frame, text=label, width=5, height=2, bg=bg, fg=fg,
                          relief="flat", bd=0, highlightthickness=1,
                          highlightbackground=BORDER, activebackground="#DCE6FA",
                          font=("Segoe UI", 11),
                          command=lambda x=label: self.press(x)
                          ).grid(row=r, column=c, padx=2, pady=2)

    def build_history(self):
        self.history_frame = tk.Frame(self.root, bg=BG)
        self.history_frame.grid(row=0, column=1, rowspan=2, padx=(0, 10),
                                pady=10, sticky="ns")
        tk.Label(self.history_frame, text="History", bg=BG, fg=NAVY,
                 font=("Segoe UI", 11, "bold")).pack()
        self.history = tk.Listbox(self.history_frame, width=24, height=14,
                                  bg=WHITE, fg=NAVY, bd=0,
                                  highlightthickness=1,
                                  highlightbackground=BORDER,
                                  selectbackground="#DCE6FA",
                                  selectforeground=NAVY, font=("Consolas", 10))
        self.history.pack(fill="y", expand=True)
        self.history.bind("<<ListboxSelect>>", self.recall)
        tk.Button(self.history_frame, text="Clear history", bg=OP_BG, fg=NAVY,
                  relief="flat", command=lambda: self.history.delete(0, "end")
                  ).pack(pady=(6, 0), fill="x")
        self.history_frame.grid_remove()   # hidden until the user asks for it

    def toggle_history(self):
        if self.history_visible:
            self.history_frame.grid_remove()
        else:
            self.history_frame.grid()
        self.history_visible = not self.history_visible

    # ---------- logic ----------
    def update_display(self):
        self.main_var.set(self.expr if self.expr else "0")

    def insert(self, text):
        # After a result, start fresh unless the user continues with an operator
        if self.fresh and text[0] not in self.OPERATORS:
            self.expr = ""
        self.fresh = False
        self.expr += text
        self.update_display()

    def press(self, label):
        if self.main_var.get() == "Error":
            self.expr = ""
            self.top_var.set("")
        if label == "C":
            self.expr, self.fresh = "", False
            self.top_var.set("")
            self.update_display()
        elif label == "⌫":
            self.expr = self.expr[:-1]
            self.update_display()
        elif label == "=":
            self.calculate()
        elif label == "Ans":
            self.insert(self.last_answer)
        elif label in self.INSERTS:
            self.insert(self.INSERTS[label])
        else:
            self.insert(label)

    def calculate(self):
        if not self.expr:
            return
        # Close any brackets the user left open
        expression = self.expr + ")" * (self.expr.count("(") - self.expr.count(")"))
        try:
            result = fmt(safe_eval(expression))
        except ZeroDivisionError:
            return self.show_error("Cannot divide by 0")
        except Exception:
            return self.show_error("Invalid expression")
        self.history.insert(0, f"{expression} = {result}")
        self.top_var.set(expression + " =")
        self.expr = result
        self.last_answer = result
        self.fresh = True
        self.update_display()

    def show_error(self, message):
        self.top_var.set(message)
        self.main_var.set("Error")
        self.expr = ""
        self.fresh = False

    def recall(self, _event):
        selection = self.history.curselection()
        if selection:
            self.expr = self.history.get(selection[0]).split(" = ")[-1]
            self.fresh = False
            self.update_display()

    def on_key(self, event):
        key = event.char
        if key and key in "0123456789.()%+-":
            self.press(key)
        elif key == "^":
            self.press("xʸ")
        elif key == "*":
            self.press("×")
        elif key == "/":
            self.press("÷")
        elif key == "=" or event.keysym in ("Return", "KP_Enter"):
            self.press("=")
        elif event.keysym == "BackSpace":
            self.press("⌫")
        elif event.keysym == "Escape":
            self.press("C")


if __name__ == "__main__":
    root = tk.Tk()
    AdvancedCalculator(root)
    root.mainloop()
