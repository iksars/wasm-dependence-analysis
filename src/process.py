def runWassail(inputFile, outputFile, params):
    # Create a new instance of the Wassail class
    wassail = Wassail(inputFile, outputFile, params)
    # Run the Wassail algorithm
    wassail.run()

def runWasmA(inputFile, outputFile, params):
    # Create a new instance of the WasmA class
    wasma = WasmA(inputFile, outputFile, params)
    # Run the WasmA algorithm
    wasma.run()

def runBinaryen(inputFile, outputFile, params):
    # Create a new instance of the Binaryen class
    binaryen = Binaryen(inputFile, outputFile, params)
    # Run the Binaryen algorithm
    binaryen.run()