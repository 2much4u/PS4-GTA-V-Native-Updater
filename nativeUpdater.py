# Predefined system native hashes
# System native hashes do not change between updates
systemNatives = [
    0x4EDE34FBADD967A6,
    0xE81651AD79516E48,
    0xB8BA7F44DF1575E1,
    0xEB1C67C3A5333A92,
    0xC4BB298BD441BE78,
    0x83666F9FB8FEBD4B,
    0xC9D9444186B5A374,
    0xC1B1E9A034A63A62,
    0x5AE11BC36633DE4E,
    0x0000000050597EE2,
    0x0BADBFA3B172435F,
    0xD0FFB162F40A139C,
    0x71D93B57D07F9804,
    0xE3621CC40F31FE2E,
    0xE816E655DE37FE20,
    0x652D2EEEF1D3E62C,
    0xA8CEACB4F35AE058,
    0x2A488C176D52CCA5,
    0xB7A628320EFF8E47,
    0xEDD95A39E5544DE8,
    0x97EF1E5BCE9DC075,
    0xF34EE736CF047844,
    0x11E019C8F43ACC8A,
    0xF2DB717A73826179,
    0xBBDA792448DB5A89,
    0x42B65DEEF2EDF2A1
]

# Read crossmap file into dictionary
def parseCrossmap():
    fileName = AskFile(False, "", "Choose a crossmap file")
    file = open(fileName, "r")

    raw_lines = file.readlines()
    crossmap = dict()
    nativeCount = 0

    for line in raw_lines:
        values = line.replace('\n', '').split(',')
        crossmap[int(values[1], 16)] = int(values[0], 16)
        nativeCount += 1

    file.close()

    print("Found " + str(nativeCount) + " natives in crossmap")
    return crossmap
    
# Read native hashes and functions into dictionary from binary
def findNativeFunctions():
    global registerNative
    registerNative = choose_func("Select registerNative function")
    functionMap = dict()
    nativeCount = 0
    
    for xref in XrefsTo(registerNative):
        addr = xref.frm

        # Start at xref to function and work backwards
        while True:
            addr = PrevHead(addr)
            if GetMnem(addr) == "mov":
                opnd = GetOpnd(addr, 0)
                if "edi" in opnd or "rdi" in opnd:
                    break

        # Function address is always the line before the hash
        hash = GetOperandValue(addr, 1)
        func = GetOperandValue(PrevHead(addr), 1)
        functionMap[hash] = func
        nativeCount += 1
    
    print("Found " + str(nativeCount) + " natives in EBOOT")
    return functionMap

# Merge the crossmap and function map dictionaries
def mergeMaps(crossmap, functionMap):
    mergedMap = dict()
    nativeCount = 0

    for new_hash in functionMap:
        old_hash = crossmap.get(new_hash)
        if old_hash:
            mergedMap[old_hash] = functionMap[new_hash]
            nativeCount += 1
        #else:
        #    print("Failed to find hash " + hex(new_hash) + " in crossmap")

    print("Merged " + str(nativeCount) + " natives in the maps")
    return mergedMap

# Find system natives (usually excluded from crossmap)
def findSystemNatives(mergedMap):
    # Find registerNativeInTable address from registerNative address
    addr = registerNative
    registerNativeInTable = 0
    while True:
        if GetMnem(addr) == "jmp":
            registerNativeInTable = GetOperandValue(addr, 0)
            break
        addr = NextHead(addr)
    
    # Search xrefs to registerNativeInTable
    for xref in XrefsTo(registerNativeInTable):
        addr = xref.frm

        # Start at xref to function and work backwards
        hash = 0
        function = 0
        while True:
            addr = PrevHead(addr)

            if hash != 0 and function != 0:
                break

            if GetMnem(addr) == "mov" and hash == 0:
                opnd = GetOpnd(addr, 0)
                if "esi" in opnd or "rsi" in opnd:
                    hash = GetOperandValue(addr, 1)
                    if hash not in systemNatives:
                        hash = 0
                        break

            if GetMnem(addr) == "lea" and function == 0:
                opnd = GetOpnd(addr, 0)
                if "rdx" in opnd:
                    function = GetOperandValue(addr, 1)

        if hash != 0:
            mergedMap[hash] = function

    return mergedMap

# Overwrite native hashes in clean header with function addresses
def createHeader(mergedMap):
    fileName = AskFile(False, "", "Choose a native header file")
    file = open(fileName, "r")
    raw_lines = file.readlines()

    missedNatives = 0
    for i in range(0, len(raw_lines)):
        line = raw_lines[i]
        if "invoke" in line:
            openParenthSplit = line.split(">(")
            closeParenthSplit = openParenthSplit[1].split(")")
            
            hash = None
            commaSplit = None

            if len(closeParenthSplit[0]) > 10:
                commaSplit = closeParenthSplit[0].split(",")
                hash = commaSplit[0]
            else:
                hash = closeParenthSplit[0]

            function = mergedMap.get(int(hash, 16))
            newLine = openParenthSplit[0] + ">("
            
            if function:
                formFunc = hex(function).split("0x")
                formFunc = formFunc[1].replace('L', '').upper()
                newLine += "0x" + formFunc
            else:
                # Write DEADBEEF for hashes not found
                newLine += "0xDEADBEEF"
                missedNatives += 1
                print("Failed to find address for " + hex(int(hash, 16)))
            
            newLine += closeParenthSplit[0].split(hash)[1] + ")"
            newLine += closeParenthSplit[1]
            
            raw_lines[i] = newLine    

    file.close()

    newFile = open("newHeader.h", "w")
    newFile.writelines(raw_lines)
    newFile.close()

    print("newHeader.h created")
    print("Unable to replace " + str(missedNatives) + " natives")

crossmap = parseCrossmap()
functionMap = findNativeFunctions()
mergedMap = mergeMaps(crossmap, functionMap)

# Feel free to comment out this line if your crossmap includes system natives
mergedMap = findSystemNatives(mergedMap)

createHeader(mergedMap)
