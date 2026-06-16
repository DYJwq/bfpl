# -*- coding: GBK -*-
"""
BFPL (Brainfuck Pointer Language) 图灵机模拟器
特性：
- 多图灵机纸带，无限长
- 指针操作 (+ - R L)
- 输入/输出 (I O)
- 整数变量与表达式求值 (D/E)
- 标签与条件跳转 (J JZ JNZ)
- 行注释 (#)
- 调试模式 (-d)
- [] 循环 (支持嵌套)
"""

import re
import sys
from collections import defaultdict

# ---------------------------- 安全表达式求值 ----------------------------
class SafeEvaluator:
    """安全的算术表达式求值器（仅支持整数 + - * / % 和括号）"""
    @staticmethod
    def evaluate(expr, variables):
        def repl_var(m):
            name = m.group(0)
            if name not in variables:
                raise NameError(f"未定义的变量: {name}")
            return str(variables[name])
        expr_with_values = re.sub(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', repl_var, expr)
        if not re.match(r'^[\d\s\+\-\*\/\%\(\)]+$', expr_with_values):
            raise ValueError(f"表达式包含非法字符: {expr}")
        try:
            return eval(expr_with_values, {"__builtins__": None}, {})
        except ZeroDivisionError:
            raise ValueError("除零错误")
        except Exception as e:
            raise ValueError(f"表达式计算失败: {expr} -> {e}")

# ---------------------------- 图灵机纸带 ----------------------------
class TuringMachine:
    def __init__(self, name):
        self.name = name
        self.tape = defaultdict(int)

    def read(self, pos):
        return self.tape[pos]

    def write(self, pos, value):
        self.tape[pos] = value

    def __repr__(self):
        items = sorted(self.tape.items())
        non_zero = [f"{p}:{v}" for p, v in items if v != 0]
        if not non_zero:
            return f"TuringMachine({self.name}): (all zeros)"
        return f"TuringMachine({self.name}): {{{', '.join(non_zero)}}}"

# ---------------------------- 指针 ----------------------------
class Pointer:
    def __init__(self, name, machine, pos=0):
        self.name = name
        self.machine = machine
        self.pos = pos

    def inc(self, delta=1):
        v = self.machine.read(self.pos)
        self.machine.write(self.pos, v + delta)

    def dec(self, delta=1):
        v = self.machine.read(self.pos)
        self.machine.write(self.pos, v - delta)

    def right(self, steps=1):
        self.pos += steps

    def left(self, steps=1):
        self.pos -= steps

    def read_char(self):
        return chr(self.machine.read(self.pos))

    def write_char(self, ch):
        self.machine.write(self.pos, ord(ch))

    def __repr__(self):
        return f"Pointer({self.name} @ {self.machine.name}[{self.pos}] = {self.machine.read(self.pos)})"

# ---------------------------- 模拟器核心 ----------------------------
class TuringSimulator:
    def __init__(self, debug=False):
        self.variables = {}
        self.machines = {}
        self.pointers = {}
        self.labels = {}
        self.statements = []
        self.ip = 0
        self.debug = debug
        self.running = True
        self.bracket_pairs = {}
        self.output = ""   # 用于收集所有输出字符（新增）

    def execute(self, code):
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        raw_lines = [s.strip() for s in code.split(';') if s.strip()]
        
        self.statements = []
        self.labels.clear()
        for line in raw_lines:
            if line.startswith(':'):
                label = line[1:].strip()
                if label in self.labels:
                    raise SyntaxError(f"重复的标签: {label}")
                self.labels[label] = len(self.statements)
            else:
                self.statements.append(line)
        
        self.bracket_pairs = {}
        stack = []
        for idx, stmt in enumerate(self.statements):
            parts = stmt.split(maxsplit=1)
            if not parts:
                continue
            cmd = parts[0]
            if cmd == '[':
                stack.append(idx)
            elif cmd == ']':
                if not stack:
                    raise SyntaxError(f"未匹配的 ']' 在索引 {idx}")
                left = stack.pop()
                self.bracket_pairs[left] = idx
                self.bracket_pairs[idx] = left
        if stack:
            raise SyntaxError(f"未匹配的 '[' 在索引 {stack[0]}")
        
        self.ip = 0
        self.running = True
        while 0 <= self.ip < len(self.statements) and self.running:
            stmt = self.statements[self.ip]
            if self.debug:
                print(f"[DEBUG] IP={self.ip}: {stmt}")
            jumped = self._exec_stmt(stmt)
            if not self.running:
                break
            if not jumped:
                self.ip += 1

    def _get_value(self, arg):
        if re.match(r'^-?\d+$', arg):
            return int(arg)
        return SafeEvaluator.evaluate(arg, self.variables)

    def _exec_stmt(self, stmt):
        parts = stmt.split(maxsplit=3)
        if not parts:
            return False
        cmd = parts[0]

        # ---------- 方括号循环 ----------
        if cmd == '[':
            if len(parts) < 2:
                raise SyntaxError("[ 需要指针名")
            ptr_name = parts[1]
            if ptr_name not in self.pointers:
                raise ValueError(f"指针 {ptr_name} 不存在")
            ptr = self.pointers[ptr_name]
            if ptr.machine.read(ptr.pos) == 0:
                if self.ip not in self.bracket_pairs:
                    raise RuntimeError("括号匹配错误")
                self.ip = self.bracket_pairs[self.ip] + 1
                if self.debug:
                    print(f"[ 条件为0，跳过循环体，跳转到 {self.ip}")
                return True
            else:
                if self.debug:
                    print(f"[ 条件非0，进入循环体")
                return False

        elif cmd == ']':
            if self.ip not in self.bracket_pairs:
                raise RuntimeError("括号匹配错误")
            self.ip = self.bracket_pairs[self.ip]
            if self.debug:
                print(f"] 跳转回 {self.ip}")
            return True

        # ---------- 其余指令（转为大写） ----------
        cmd_upper = cmd.upper()

        # D name = expr
        if cmd_upper == 'D':
            if len(parts) < 3:
                raise SyntaxError(f"D 需要两个参数: {stmt}")
            var_name = parts[1]
            value_expr = parts[2]
            self.variables[var_name] = self._get_value(value_expr)
            if self.debug:
                print(f"定义变量 {var_name} = {self.variables[var_name]}")
            return False

        # N name (打印变量)
        elif cmd_upper == 'N':
            if len(parts) < 2:
                raise SyntaxError(f"N 需要一个参数: {stmt}")
            name = parts[1]
            if name in self.variables:
                msg = f"变量 {name} = {self.variables[name]}"
                print(msg)
                # 注意：不要在这里添加 output 收集，因为 N 是打印变量值，不是输出字符
            else:
                print(f"N: {name} (未定义变量)")
            return False

        # M name
        elif cmd_upper == 'M':
            if len(parts) < 2:
                raise SyntaxError(f"M 需要一个参数: {stmt}")
            tur_name = parts[1]
            if tur_name in self.machines:
                print(f"警告: 图灵机 {tur_name} 已存在，将被覆盖")
            self.machines[tur_name] = TuringMachine(tur_name)
            if self.debug:
                print(f"创建图灵机: {tur_name}")
            return False

        # S ptr_name machine_name
        elif cmd_upper == 'S':
            if len(parts) < 3:
                raise SyntaxError(f"S 需要两个参数: {stmt}")
            pos_name = parts[1]
            tur_name = parts[2]
            if tur_name not in self.machines:
                raise ValueError(f"图灵机 {tur_name} 不存在")
            self.pointers[pos_name] = Pointer(pos_name, self.machines[tur_name], 0)
            if self.debug:
                print(f"定义指针 {pos_name} 指向 {tur_name}[0]")
            return False

        # + ptr [delta]
        elif cmd_upper == '+':
            if len(parts) < 2:
                raise SyntaxError(f"+ 需要一个指针名: {stmt}")
            pos_name = parts[1]
            if pos_name not in self.pointers:
                raise ValueError(f"指针 {pos_name} 不存在")
            delta = 1
            if len(parts) >= 3:
                delta = self._get_value(parts[2])
            self.pointers[pos_name].inc(delta)
            if self.debug:
                print(f"{pos_name} +{delta} -> {self.pointers[pos_name]}")
            return False

        # - ptr [delta]
        elif cmd_upper == '-':
            if len(parts) < 2:
                raise SyntaxError(f"- 需要一个指针名: {stmt}")
            pos_name = parts[1]
            if pos_name not in self.pointers:
                raise ValueError(f"指针 {pos_name} 不存在")
            delta = 1
            if len(parts) >= 3:
                delta = self._get_value(parts[2])
            self.pointers[pos_name].dec(delta)
            if self.debug:
                print(f"{pos_name} -{delta} -> {self.pointers[pos_name]}")
            return False

        # R ptr [steps]
        elif cmd_upper == 'R':
            if len(parts) < 2:
                raise SyntaxError(f"R 需要一个指针名: {stmt}")
            pos_name = parts[1]
            if pos_name not in self.pointers:
                raise ValueError(f"指针 {pos_name} 不存在")
            steps = 1
            if len(parts) >= 3:
                steps = self._get_value(parts[2])
            self.pointers[pos_name].right(steps)
            if self.debug:
                print(f"{pos_name} 右移 {steps} -> {self.pointers[pos_name]}")
            return False

        # L ptr [steps]
        elif cmd_upper == 'L':
            if len(parts) < 2:
                raise SyntaxError(f"L 需要一个指针名: {stmt}")
            pos_name = parts[1]
            if pos_name not in self.pointers:
                raise ValueError(f"指针 {pos_name} 不存在")
            steps = 1
            if len(parts) >= 3:
                steps = self._get_value(parts[2])
            self.pointers[pos_name].left(steps)
            if self.debug:
                print(f"{pos_name} 左移 {steps} -> {self.pointers[pos_name]}")
            return False

        # O ptr (输出字符)
        elif cmd_upper == 'O':
            if len(parts) < 2:
                raise SyntaxError(f"O 需要一个指针名: {stmt}")
            pos_name = parts[1]
            if pos_name not in self.pointers:
                raise ValueError(f"指针 {pos_name} 不存在")
            ch = self.pointers[pos_name].read_char()
            print(ch, end='')
            self.output += ch   # 收集输出（新增）
            if self.debug:
                print(f"输出: '{ch}' (ASCII {ord(ch)})")
            return False

        # I ptr
        elif cmd_upper == 'I':
            if len(parts) < 2:
                raise SyntaxError(f"I 需要一个指针名: {stmt}")
            pos_name = parts[1]
            if pos_name not in self.pointers:
                raise ValueError(f"指针 {pos_name} 不存在")
            if sys.stdin.isatty():
                sys.stdout.write("> ")
                sys.stdout.flush()
            user_input = sys.stdin.readline().strip()
            if user_input:
                ch = user_input[0]
            else:
                ch = '\x00'
            self.pointers[pos_name].write_char(ch)
            if self.debug:
                print(f"输入 '{ch}' 写入 {pos_name}")
            return False

        # J label
        elif cmd_upper == 'J':
            if len(parts) < 2:
                raise SyntaxError(f"J 需要一个标签: {stmt}")
            label = parts[1]
            if label not in self.labels:
                raise ValueError(f"标签 {label} 不存在")
            self.ip = self.labels[label]
            if self.debug:
                print(f"跳转到 {label} (IP={self.ip})")
            return True

        # JZ var label
        elif cmd_upper == 'JZ':
            if len(parts) < 3:
                raise SyntaxError(f"JZ 需要两个参数: 变量 标签")
            var_name = parts[1]
            label = parts[2]
            if label not in self.labels:
                raise ValueError(f"标签 {label} 不存在")
            val = self.variables.get(var_name, 0)
            if val == 0:
                self.ip = self.labels[label]
                if self.debug:
                    print(f"{var_name} == 0 -> 跳转到 {label}")
                return True
            else:
                if self.debug:
                    print(f"{var_name} = {val} != 0, 不跳转")
                return False

        # JNZ var label
        elif cmd_upper == 'JNZ':
            if len(parts) < 3:
                raise SyntaxError(f"JNZ 需要两个参数: 变量 标签")
            var_name = parts[1]
            label = parts[2]
            if label not in self.labels:
                raise ValueError(f"标签 {label} 不存在")
            val = self.variables.get(var_name, 0)
            if val != 0:
                self.ip = self.labels[label]
                if self.debug:
                    print(f"{var_name} != 0 -> 跳转到 {label}")
                return True
            else:
                if self.debug:
                    print(f"{var_name} = 0, 不跳转")
                return False

        # H
        elif cmd_upper == 'H':
            self.running = False
            if self.debug:
                print("停机")
            return False

        # E var = expr
        elif cmd_upper == 'E':
            if len(parts) < 3:
                raise SyntaxError(f"E 需要两个参数: {stmt}")
            var_name = parts[1]
            value_expr = parts[2]
            self.variables[var_name] = self._get_value(value_expr)
            if self.debug:
                print(f"赋值 {var_name} = {self.variables[var_name]}")
            return False

        else:
            raise SyntaxError(f"未知指令: {cmd}")

# ---------------------------- 主程序入口 ----------------------------
if __name__ == "__main__":
    debug = '-d' in sys.argv
    filename = None
    for arg in sys.argv[1:]:
        if arg != '-d':
            filename = arg
            break

    if not filename:
        print("用法: python bfpl.py <源文件.bfpl> [-d]")
        print("示例: python bfpl.py demo.bfpl -d")
        sys.exit(1)

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            program = f.read()
    except FileNotFoundError:
        print(f"错误: 文件不存在 '{filename}'")
        sys.exit(1)
    except UnicodeDecodeError:
        # 如果 UTF-8 失败，尝试 GBK
        try:
            with open(filename, 'r', encoding='gbk') as f:
                program = f.read()
        except Exception as e:
            print(f"无法读取文件，编码错误: {e}")
            sys.exit(1)

    sim = TuringSimulator(debug=debug)
    try:
        sim.execute(program)
    except Exception as e:
        print(f"\n运行时错误: {e}")
        sys.exit(1)

    print("\n=== 最终状态 ===")
    for m in sim.machines.values():
        print(m)
    for p in sim.pointers.values():
        print(p)

    # 新增：打印纯净输出（所有 O 指令输出的字符）
    if sim.output:
        print("\n=== 纯净输出 ===")
        print(sim.output)