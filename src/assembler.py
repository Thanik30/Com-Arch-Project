import sys

opcode_table = {
    "add":   {"opcode": 0b000, "type": "R"},
    "nand":  {"opcode": 0b001, "type": "R"},
    "lw":    {"opcode": 0b010, "type": "I"},
    "sw":    {"opcode": 0b011, "type": "I"},
    "beq":   {"opcode": 0b100, "type": "I"},
    "jalr":  {"opcode": 0b101, "type": "J"},
    "halt":  {"opcode": 0b110, "type": "O"},
    "noop":  {"opcode": 0b111, "type": "O"},
    ".fill": {"opcode": -2,    "type": "F"}
}

def print_error(msg):
    print(f"error: {msg}")
    sys.exit(1)

def is_valid_label(name):
    if len(name) > 6 or len(name) == 0: return False
    if not name[0].isalpha(): return False
    if not name.isalnum(): return False
    return True

def is_number(s):
    return s.lstrip('-').isnumeric()

def has_label(tokens):
    # เช็คว่าบรรทัดนี้มี Label นำหน้าหรือไม่
    if tokens[0] in opcode_table:
        return False
    # ถ้าคำแรกไม่ใช่คำสั่ง และคำที่สองเป็นคำสั่ง (หรือคำที่สองไม่ใช่ตัวเลข) แปลว่าคำแรกคือ Label
    if len(tokens) >= 2 and (tokens[1] in opcode_table or not is_number(tokens[1])):
        return True
    return False

def parse_reg(s, line_num):
    if not is_number(s):
        print_error(f"invalid register operand '{s}' at line {line_num}")
    r = int(s)
    if r < 0 or r > 7:
        print_error(f"register out of range ({r}) at line {line_num}")
    return r

def main():
    if len(sys.argv) != 3:
        print_error("usage: python assembler.py <inputfile> <outputfile>")

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print_error("cannot open file")

    labels = {}

    # ==========================================
    # Pass 1: กวาดหา Label ทั้งหมด
    # ==========================================
    for i, line in enumerate(lines):
        tokens = line.split()
        if has_label(tokens):
            label_name = tokens[0]
            if not is_valid_label(label_name):
                print_error(f"invalid label name '{label_name}' at line {i}")
            if label_name in labels:
                print_error(f"duplicate label '{label_name}' at line {i}")
            labels[label_name] = i

    # ==========================================
    # Pass 2: แปลงคำสั่งเป็น Machine Code
    # ==========================================
    machine_codes = []

    for i, line in enumerate(lines):
        tokens = line.split()

        if has_label(tokens):
            tokens = tokens[1:]

        if len(tokens) == 0:
            print_error(f"missing instruction at line {i}")

        opcode_str = tokens[0]
        if opcode_str not in opcode_table:
            print_error(f"invalid opcode '{opcode_str}' at line {i}")

        op_info = opcode_table[opcode_str]
        op = op_info["opcode"]
        inst_type = op_info["type"]

        # --- กรณี .fill (Type F) ---
        if inst_type == "F":
            if len(tokens) < 2:
                print_error(f"missing operand for .fill at line {i}")
            arg = tokens[1]
            if is_number(arg):
                val = int(arg)
            else:
                if arg not in labels:
                    print_error(f"undefined label '{arg}' at line {i}")
                val = labels[arg]
            machine_codes.append(val)
            print(f"(address {i}): {val} (hex {hex(val & 0xFFFFFFFF)})")
            continue

        # --- กรณี R-Type (add, nand) ---
        if inst_type == "R":
            if len(tokens) < 4:
                print_error(f"invalid operand count at line {i}")
            regA = parse_reg(tokens[1], i)
            regB = parse_reg(tokens[2], i)
            destReg = parse_reg(tokens[3], i)
            mc = (op << 22) | (regA << 19) | (regB << 16) | destReg

        # --- กรณี I-Type (lw, sw, beq) ---
        elif inst_type == "I":
            if len(tokens) < 4:
                print_error(f"invalid operand count at line {i}")
            regA = parse_reg(tokens[1], i)
            regB = parse_reg(tokens[2], i)
            offset_str = tokens[3]

            if is_number(offset_str):
                offset = int(offset_str)
            else:
                if offset_str not in labels:
                    print_error(f"undefined label '{offset_str}' at line {i}")
                label_addr = labels[offset_str]
                if opcode_str == "beq":
                    offset = label_addr - (i + 1)
                else:
                    offset = label_addr

            if offset < -32768 or offset > 32767:
                print_error(f"offsetField out of range ({offset}) at line {i}")

            mc = (op << 22) | (regA << 19) | (regB << 16) | (offset & 0xFFFF)

        # --- กรณี J-Type (jalr) ---
        elif inst_type == "J":
            if len(tokens) < 3:
                print_error(f"invalid operand count at line {i}")
            regA = parse_reg(tokens[1], i)
            regB = parse_reg(tokens[2], i)
            mc = (op << 22) | (regA << 19) | (regB << 16)

        # --- กรณี O-Type (halt, noop) ---
        elif inst_type == "O":
            mc = (op << 22)

        machine_codes.append(mc)
        print(f"(address {i}): {mc} (hex {hex(mc & 0xFFFFFFFF)})")

    with open(output_file, 'w', encoding='utf-8') as f:
        for mc in machine_codes:
            f.write(f"{mc}\n")

    sys.exit(0)

if __name__ == "__main__":
    main()