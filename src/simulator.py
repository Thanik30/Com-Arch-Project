import sys

# ขนาด Memory ตามที่กำหนดในโจทย์
NUMMEMORY = 65536

class StateStruct:
    def __init__(self):
        # Program Counter
        self.pc = 0
        # memory มีขนาด 65536 words และ Initialize registers ทุกตัวให้เป็น 0[cite: 5, 8]
        self.mem = [0] * NUMMEMORY
        self.reg = [0] * 8
        self.numMemory = 0

# ฟังก์ชันแปลง 16-bit number ให้เป็น 32-bit integer (Sign Extension)
def convertNum(num):
    # เช็คบิตที่ 15 (เครื่องหมายลบใน 16-bit)
    if num & (1 << 15):
        num -= (1 << 16)
    return num

# ฟังก์ชันสำหรับจำลองการเก็บค่าแบบ 32-bit แบบ C/C++
def to_32bit_signed(val):
    val = val & 0xFFFFFFFF
    if val & 0x80000000:
        val -= 0x100000000
    return val

# แล้วตอนทำคำสั่ง add หรือ nand ก็นำฟังก์ชันนี้ไปครอบ เช่น
# state.reg[destReg] = to_32bit_signed(state.reg[regA] + state.reg[regB])

# ฟังก์ชัน printState ห้ามแก้ไขตามกฎของโปรเจกต์[cite: 8]
def printState(state):
    print("\n@@@\nstate:")
    print(f"\tpc {state.pc}")
    print(f"\tmemory:")
    # state.numMemory ต้องเท่ากับจำนวนบรรทัดใน machine-code file[cite: 8]
    for i in range(state.numMemory):
        print(f"\t\tmem[ {i} ] {state.mem[i]}")
    print(f"\tregisters:")
    for i in range(8):
        print(f"\t\treg[ {i} ] {state.reg[i]}")
    print("end state\n")

def main():
    if len(sys.argv) != 2:
        print("Usage: python simulator.py <machine_code_file>")
        sys.exit(1)
        
    filename = sys.argv[1]
    state = StateStruct()
    
    # อ่าน Machine Code เข้ามาเก็บใน Memory
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
            for line in lines:
                val = line.strip()
                if val:
                    state.mem[state.numMemory] = int(val)
                    state.numMemory += 1
    except FileNotFoundError:
        print(f"Error: Cannot open file {filename}")
        sys.exit(1)

    total_instructions_executed = 0
    is_halted = False
    
    # ลูปหลักของการทำงาน (Simulation Loop)
    while not is_halted:
        # 1. Call printState 1 ครั้ง ก่อน instruction executes[cite: 5, 8]
        printState(state)
        
        # 2. Fetch (ดึงคำสั่งปัจจุบันออกมา)
        instruction = state.mem[state.pc]
        
        # 3. Decode (ถอดรหัสคำสั่ง)
        opcode = (instruction >> 22) & 0b111
        regA = (instruction >> 19) & 0b111
        regB = (instruction >> 16) & 0b111
        destReg = instruction & 0b111
        offsetField = instruction & 0xFFFF
        
        # สำหรับ I-type แปลงค่าให้เป็นตัวเลข 32 บิตที่ติดลบได้ถูกต้อง
        offsetField = convertNum(offsetField)
        
        # 4. Execute (ทำงานตามคำสั่ง)
        if opcode == 0:  # add
            # นำฟังก์ชัน to_32bit_signed มาครอบผลบวก
            state.reg[destReg] = to_32bit_signed(state.reg[regA] + state.reg[regB])
        elif opcode == 1:  # nand
            # นำฟังก์ชัน to_32bit_signed มาครอบผลลัพธ์ nand
            state.reg[destReg] = to_32bit_signed(~(state.reg[regA] & state.reg[regB]))
        elif opcode == 2:  # lw
            addr = state.reg[regA] + offsetField
            state.reg[regB] = state.mem[addr]
        elif opcode == 3:  # sw
            addr = state.reg[regA] + offsetField
            state.mem[addr] = state.reg[regB]
        elif opcode == 4:  # beq
            if state.reg[regA] == state.reg[regB]:
                # ถ้า regA เท่ากับ regB ให้กระโดดไปที่ address PC+1+offsetField
                state.pc += offsetField 
        elif opcode == 5:  # jalr
            # 1. เก็บค่า PC+1 ไว้ใน regB ก่อน[cite: 2]
            state.reg[regB] = state.pc + 1
            
            # 2. กระโดดไปที่ address ที่ถูกเก็บไว้ใน regA[cite: 2]
            # (ถ้า regA และ regB เป็นตัวเดียวกัน มันจะดึงค่า PC+1 ที่เพิ่งอัปเดตบรรทัดบนมาใช้อัตโนมัติ)
            state.pc = state.reg[regA] - 1 # ลบ 1 ออกก่อน เพราะท้ายลูปจะบวก PC กลับเข้ามา
        elif opcode == 6:  # halt
            # ให้เครื่อง Simulator รู้ว่ามี Halted เกิดขึ้น[cite: 2]
            print("machine halted")
            print(f"total of {total_instructions_executed + 1} instructions executed")
            print("final state of machine:")
            is_halted = True
        elif opcode == 7:  # noop
            pass # ไม่ทำอะไรเลย[cite: 2]
        else:
            print("Error: Unknown opcode")
            sys.exit(1)

        # 5. เคลียร์ register 0 ให้เป็น 0 เสมอ (ตามหลักการพื้นฐานของ Assembly)[cite: 1]
        state.reg[0] = 0
        
        # เพิ่มค่า PC[cite: 2] (ถ้าไม่ได้กระโดดจากคำสั่ง jalr หรือ beq ก็จะบวก 1 ตามปกติ)
        state.pc += 1 
        total_instructions_executed += 1
        
    # Call printState 1 ครั้ง ก่อน simulator exits[cite: 5, 8]
    printState(state)
    sys.exit(0)

if __name__ == "__main__":
    main()