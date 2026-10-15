import sys

NUMMEMORY = 65536
NUMREGS = 8

class State:
    def __init__(self):
        self.pc = 0
        self.mem = [0] * NUMMEMORY
        self.reg = [0] * NUMREGS
        self.numMemory = 0


def printState(state):
    print("\n@@@\nstate:")
    print(f"\tpc {state.pc}")
    print("\tmemory:")
    for i in range(state.numMemory):
        print(f"\t\tmem[ {i} ] {state.mem[i]}")
    print("\tregisters:")
    for i in range(NUMREGS):
        print(f"\t\treg[ {i} ] {state.reg[i]}")
    print("end state")

# ฟังก์ชันสำหรับแปลงเลข 16 บิตให้เป็น 32 บิตแบบคิดเครื่องหมาย (Sign Extension)
def convertNum(num):
    if num & (1 << 15):
        num -= (1 << 16)
    return num

def print_error(msg):
    print(f"error: {msg}")
    sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("usage: python simulator.py <machine-code file>")
        sys.exit(1)

    file_name = sys.argv[1]
    state = State()


    # 1. โหลด Machine Code ลง Memory

    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if state.numMemory >= NUMMEMORY:
                    print_error("program too large")
                
                val = int(line)
                state.mem[state.numMemory] = val
                print(f"memory[{state.numMemory}]={val}")
                state.numMemory += 1
    except FileNotFoundError:
        print_error("cannot open file")


    # 2. เริ่มวงจร Fetch-Decode-Execute
    instrCount = 0

    while True:
        # กฎ: เรียก printState 1 ครั้ง ก่อน instruction executes
        printState(state)

        # ดึงคำสั่งปัจจุบันออกมา
        if state.pc < 0 or state.pc >= NUMMEMORY:
            print_error("PC out of range")
            
        instr = state.mem[state.pc]

        # Decode (แยกชิ้นส่วนของบิต)
        opcode = (instr >> 22) & 0x7
        rs = (instr >> 19) & 0x7
        rt = (instr >> 16) & 0x7
        rd = instr & 0x7
        imm = instr & 0xFFFF # 16 บิตหลังสำหรับ offset

        # Execute ตาม Opcode
        if opcode == 0:    # add
            state.reg[rd] = state.reg[rs] + state.reg[rt]
            state.pc += 1

        elif opcode == 1:  # nand
            # bitwise NAND ในไพธอนทำด้วย ~(a & b)
            state.reg[rd] = ~(state.reg[rs] & state.reg[rt])
            state.pc += 1

        elif opcode == 2:  # lw
            offset = convertNum(imm)
            addr = state.reg[rs] + offset
            if addr < 0 or addr >= NUMMEMORY: print_error("memory bounds")
            state.reg[rt] = state.mem[addr]
            state.pc += 1

        elif opcode == 3:  # sw
            offset = convertNum(imm)
            addr = state.reg[rs] + offset
            if addr < 0 or addr >= NUMMEMORY: print_error("memory bounds")
            state.mem[addr] = state.reg[rt]
            state.pc += 1

        elif opcode == 4:  # beq
            offset = convertNum(imm)
            if state.reg[rs] == state.reg[rt]:
                state.pc = state.pc + 1 + offset
            else:
                state.pc += 1

        elif opcode == 5:  # jalr
            # 1. เก็บ PC+1 ไว้ใน rt ก่อน
            state.reg[rt] = state.pc + 1
            # 2. ค่อยกระโดดไปที่ address ที่อยู่ใน rs (ถ้า rs == rt ก็จะได้ค่า PC+1 ที่เพิ่งบันทึกไป)
            state.pc = state.reg[rs]

        elif opcode == 6:  # halt
            state.pc += 1
            state.reg[0] = 0 # กฎ: reg[0] ต้องเป็น 0 เสมอ
            instrCount += 1
            
            # halt เสร็จต้องหยุดทำงาน
            print("machine halted")
            print(f"total of {instrCount} instructions executed")
            print("final state of machine:")
            printState(state) # กฎ: เรียกอีก 1 ครั้งก่อน exit
            sys.exit(0)

        elif opcode == 7:  # noop
            state.pc += 1

        else:
            print_error(f"invalid opcode: {opcode}")

        # กฎพื้นฐานที่สุด: register 0 ต้องมีค่า 0 เสมอ
        state.reg[0] = 0
        instrCount += 1

if __name__ == "__main__":
    main()