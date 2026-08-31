import struct, glob, os, argparse

def makeBranch(source: int, dest: int):
    opcode = 0x12 #5 bits
    displacement = (dest - source) // 4 #24 bits
    #flags so that we have a branch instruction
    aa = 0 #1 bit
    lk = 0 #1 bit

    return ((opcode & 0x1F) << 26 | (displacement & 0xFFFFFF) << 2 
        | ((aa & 0x1)) << 1 | (lk & 0x1))

#8 bit write
def patch00(raw: bytearray, address: int, repeat: int, value: int):
    for i in range(repeat+1):
        raw[address+i:address+i+1] = struct.pack(">B", value)

#16 bit write
def patch02(raw: bytearray, address: int, repeat: int, value: int):
    for i in range(repeat+1):
        raw[address+2*i:address+2*i+2] = struct.pack(">H", value)

#32 bit write
def patch04(raw: bytearray, address: int, value: int):
    raw[address:address+4] = struct.pack(">L", value)

#String write
def patch06(raw: bytearray, address: int, numBytes: int, value: bytes):
    raw[address:address+numBytes] = value

#Insert Asm
"""
The C2 patch writes a branch at address to the end of the file
where new assembly instructions are written. Then a branch is
inserted to instruction after the address so the code continues
to execute as normal.
"""
def patchC2(raw, address, numLines, value):
    #align 4 (required for making a branch instruction)
    while len(raw) % 4 != 0:
        raw.extend(b"\x00")
    insertLoc = len(raw)
    numBytes = numLines * 8
    bInst = makeBranch(address, insertLoc)
    patch04(raw, address, bInst)
    raw.extend(b"\x00" * (numBytes-4))
    patch06(raw, insertLoc, numBytes-4, value)
    backBInst = makeBranch(insertLoc + numBytes - 4, address + 4)
    patch04(raw, insertLoc + numBytes - 4, backBInst)

def applyPatchesFromTxt(raw, txt):
    patchCount = 0
    with open(txt, 'r') as f:
        line = f.read()
        if not line: return
        #strip all comments
        commentPos = line.find("#")
        while commentPos != -1:
            newLinePos = line.find("\n", commentPos)
            if newLinePos == -1: newLinePos = len(line)
            line = line[0:commentPos] + line[newLinePos::]
            commentPos = line.find("#")
        line = line.strip().replace(" ", "").replace("\n", "").upper()
    off = 0
    while off < len(line):
        if line[off:off+4] == "FILE":
            endQuote = line.find("\"", off + 5)
            path = os.path.join(os.path.dirname(txt), line[off+5:endQuote])
            with open(path, 'rb') as f:
                raw.extend(f.read())
            off = endQuote + 1
            continue
        #the next patches all have a patch type and an address
        patchType = line[off:off+2]
        address = int(line[off+2:off+8], 16)
        if patchType == "00":
            repeat = int(line[off+8:off+12], 16)
            value = int(line[off+14:off+16], 16)
            patch00(raw, address, repeat, value)
            off += 16
        elif patchType == "02":
            repeat = int(line[off+8:off+12], 16)
            value = int(line[off+12:off+16], 16)
            patch02(raw, address, repeat, value)
            off += 16
        elif patchType == "04":
            value = int(line[off+8:off+16], 16)
            patch04(raw, address, value)
            off += 16
        elif patchType == "06":
            numBytes = int(line[off+8:off+16], 16)
            value = bytes.fromhex(line[off+16:off+16+numBytes*2])
            patch06(raw, address, numBytes, value)
            off += 16 + numBytes * 2
        elif patchType == "C2":
            numLines = int(line[off+8:off+16], 16)
            value = bytes.fromhex(line[off+16:off+16+16*numLines])
            patchC2(raw, address, numLines, value)
            off += 16 + numLines * 16
        else:
            raise AssertionError('Unrecognized patch type')
        patchCount += 1
    return patchCount




if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Wii module patcher')
    parser.add_argument('input')
    parser.add_argument('output')
    parser.add_argument('path')
    args = parser.parse_args()
    with open(args.input, 'rb') as f:
        raw = bytearray(f.read())
    if os.path.isfile(args.path):
        patchCount = applyPatchesFromTxt(raw, args.path)
        fileCount = 1
    elif os.path.isdir(args.path):
        files = glob.glob(f'{args.path}/*.txt')
        patchCount = 0
        fileCount = 0
        for txt in files:
            patchCount += applyPatchesFromTxt(raw, txt)
            fileCount += 1
    print(f'Applied {patchCount} patch(es) from {fileCount} different file(s).')
    with open(args.output, 'wb') as f:
        f.write(raw)
    