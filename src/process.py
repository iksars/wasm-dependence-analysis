from pathlib import Path
import subprocess
import time
import json
import graph

MICRO_BENCHMARKS_PATH = Path("microbenchmarks")
TOOL_WASSAIL = "tools/wassail/_build/default/main.exe"
TOOL_BINARYEN = "tools/binaryen/bin"
TOOL_BINARYEN_OPT = "{}/wasm-opt".format(TOOL_BINARYEN)
TOOL_BINARYEN_AS = "{}/wasm-as".format(TOOL_BINARYEN)
TOOL_WASMA = "tools/wasma/bin/DataFlowGraph"
DATA_PATH = Path("data")
DATA_MICRO_BENCHMARKS_PATH = DATA_PATH / "microbenchmarks"



def executeCommand(command, tool_name):
    # Execute the command
    start_time = time.time()
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    end_time = time.time()
    exec_time = end_time - start_time
    # Check if the command was executed successfully
    if process.returncode != 0:
        # Print the error message
        # print("Error: {} failed to execute cmd {}".format(tool_name, command))
        # print("Error message: {}".format(stderr.decode("utf-8")))
        msg = "Error: {} failed to execute cmd {}. Error message: {}".format(tool_name, command, stderr.decode("utf-8"))
        # Return the status as False
        return False, msg, exec_time
    # Print the output of the command
    # print(tool_shell_output.format(tool_name, stdout.decode("utf-8")))
    msg = stdout.decode("utf-8")
    # Return the status as True
    return True, msg, exec_time


def runWassail(inputDir):
    # find the metadata file
    metadataFile = inputDir / "metadata.json"
    metadata = readMetadata(metadataFile)
    # Iterate over all the functions
    for function in metadata["functions"]:
        # Function index
        funcIndex = function["index"]
        # Output file
        outputFile = DATA_MICRO_BENCHMARKS_PATH/"{}".format(inputDir.name) / "wassail/graph_{}.dot".format(funcIndex)
        # Create the output directory
        outputFile.parent.mkdir(parents=True, exist_ok=True)
        # Create a command to run wassail
        wassailCommand = "{} dependencies {} {} {}".format(TOOL_WASSAIL, inputDir / "{}.wasm".format(inputDir.name), funcIndex, outputFile)
        status, msg, exec_time = executeCommand(wassailCommand, "wassail")
        if not status:
            print(msg)
        else :
            print("wassail analyse function {} in {} took {} seconds".format(funcIndex, inputDir.name, exec_time))

def generateMetadata(inputFile, metadataFile):
    # Generate metadata for the tools
    metadata = {
        "source": inputFile.name,
        "functions": []
    }
    wassailCommand = "{} functions {}".format(TOOL_WASSAIL, inputFile)
    status, msg, _ = executeCommand(wassailCommand, "wassail")
    if not status:
        return False, msg
    # Parse the output of the command
    # print(msg)
    functions = msg.strip().split("\n")
    for function in functions:
        fTuple = function.strip().split("\t")
        # print(fTuple)
        wassailCommand2 = "{} function-instruction-labels {} {}".format(TOOL_WASSAIL, inputFile, fTuple[0])
        status, msg, _ = executeCommand(wassailCommand2, "wassail")
        if not status:
            return False, msg
        instructions = msg.strip().split("\n")
        metadata["functions"].append({"index": fTuple[0], "name": fTuple[1], "count": int(instructions[-1]) + 1})
    # Write the metadata to a file
    with open(metadataFile, "w") as f:
        json.dump(metadata, f)
    return True, _


def readMetadata(metadataFile):
    with open(metadataFile, "r") as f:
        metadata = json.load(f)
    return metadata


def wat2wasm(inputFile):
    # wat2wasm path
    wat2wasmPath = "wat2wasm"
    # Output file
    outputFile = inputFile.with_suffix(".wasm")
    sourceMapFile = inputFile.with_suffix(".wasm.map")
    # Create a command to run wassail
    wat2wasmCommand = "{} {} -sm {} -o {}".format(TOOL_BINARYEN_AS, inputFile, sourceMapFile, outputFile)
    status, msg, _ = executeCommand(wat2wasmCommand, "wasm-as")
    return status, msg


def prepareBenchmark():
    # iterate over all the microbenchmarks dir, and run the tools on them
    for item in MICRO_BENCHMARKS_PATH.iterdir():
        if item.is_dir():
            # Generate metadata for the tools
            inputFile = item / "{}.wat".format(item.name)
            metadataFile = item / "metadata.json"
            status, msg = generateMetadata(inputFile, metadataFile)
            if not status:
                print(msg)
                return False
            status, msg = wat2wasm(inputFile)
            if not status:
                print(msg)
                return False
    return True

def clear():
    clearBenchmark()

def clearBenchmark():
    for item in MICRO_BENCHMARKS_PATH.iterdir():
        if item.is_dir():
            watFile = item / "{}.wat".format(item.name)
            for file in item.iterdir():
                if file == watFile:
                    continue
                else:
                    file.unlink()
        else :
            item.unlink()
    microDataPath = DATA_PATH / "microbenchmarks"
    rmdirHelper(microDataPath)

def rmdirHelper(path):
    for item in path.iterdir():
        if item.is_dir():
            rmdirHelper(item)
        else:
            item.unlink()
    path.rmdir()
    
# ~/wasma/bin/DataFlowGraph -file test2.wasm -fi 0 -cdfg true -out .
def runWasma(inputDir):
    # find the metadata file
    metadataFile = inputDir / "metadata.json"
    metadata = readMetadata(metadataFile)
    # Iterate over all the functions
    for function in metadata["functions"]:
        # Function index
        funcIndex = function["index"]
        # Output directory
        outputDir = DATA_MICRO_BENCHMARKS_PATH/"{}".format(inputDir.name) / "wasma"
        # Create the output directory
        outputDir.mkdir(parents=True, exist_ok=True)
        # Create a command to run wasma
        wasmaCommand = "{} -file {} -fi {} -cdfg true -out {}".format(TOOL_WASMA, inputDir / "{}.wasm".format(inputDir.name), funcIndex, outputDir)
        status, msg, exec_time = executeCommand(wasmaCommand, "wasma")
        if not status:
            print(msg)
        else :
            print("wasma analyse function {} in {} took {} seconds".format(funcIndex, inputDir.name, exec_time))

def runBinaryen(inputDir):
    # Output directory
    outputDir = DATA_MICRO_BENCHMARKS_PATH/"{}".format(inputDir.name) / "binaryen"
    # Create the output directory
    outputDir.mkdir(parents=True, exist_ok=True)
    # Create a command to run binaryen wasm-opt
    wasmOptCommand = "{} {} --flatten --dfo -ism {} -od {}".format(TOOL_BINARYEN_OPT, inputDir / "{}.wasm".format(inputDir.name), inputDir / "{}.wasm.map".format(inputDir.name), outputDir)
    status, msg, exec_time = executeCommand(wasmOptCommand, "binaryen")
    if not status:
        print(msg)
    else :
        print("binaryen wasm-opt analyse function in {} took {} seconds".format(inputDir.name, exec_time))

def getWassailOutFileName(index, testName = ""):
    return "graph_{}.dot".format(index)

def getWasmaOutFileName(index, testName = ""):
    return "{}_{}.dot".format(testName, index)

def getBinaryenOutFileName(index, testName = ""):
    return "graph_{}.dot".format(index)

#  dic of tools
toolRegister = {
    "wassail": [runWassail, getWassailOutFileName, graph.build_graph_from_dot_wassail],
    "wasma": [runWasma, getWasmaOutFileName, graph.build_graph_from_dot_wasma],
    "binaryen": [runBinaryen, getBinaryenOutFileName, graph.build_graph_from_dot_wasmOpt]
}


def runAllTool(inputDir):
    for tool in toolRegister:
        runTool(tool, inputDir)

def runTool(tool, inputDir):
    toolRegister[tool][0](inputDir)


def runBenchmark():
    # iterate over all the microbenchmarks dir, and run the tools on them
    for item in MICRO_BENCHMARKS_PATH.iterdir():
        if item.is_dir():
            runAllTool(item)
    data = {"tools": [], "cases": []}
    data["tools"] = list(toolRegister.keys())
    # transform the data
    for item in DATA_MICRO_BENCHMARKS_PATH.iterdir():
        if item.is_dir():
            caseName = item.name
            metadata = readMetadata(MICRO_BENCHMARKS_PATH / caseName / "metadata.json")
            data_item = {
                "case": caseName,
                "functions": [],
                "average": []
            }
            avg = {}
            for i in range(len(metadata["functions"])):
                graphs = []
                for tool in toolRegister:
                    graphs.append(toolRegister[tool][2](item / tool / toolRegister[tool][1](i, caseName), metadata["functions"][i]["count"]))
                # for graph2 in graphs:
                #     print(graph2.to_dot())
                matrix = graph.compareAdjacentMatrix(graphs)
                data_item["functions"].append({"index": i, "matrix": matrix.tolist()})
                if i == 0:
                    avg = matrix
                else:
                    avg += matrix
            data_item["average"] = (avg / len(metadata["functions"])).tolist()
            data["cases"].append(data_item)
        else :
            # unexcepted file
            item.unlink()
    # Write the data to a file
    with open(DATA_MICRO_BENCHMARKS_PATH / "result.json", "w") as f:
        json.dump(data, f)
    