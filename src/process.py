from pathlib import Path
import subprocess
import time
import json

MICRO_BENCHMARKS_PATH = Path("microbenchmarks")
TOOL_WASSAIL = "wassail"
TOOL_BINARYEN = "~/binaryen/bin"
TOOL_BINARYEN_OPT = "{}/wasm-opt".format(TOOL_BINARYEN)
TOOL_BINARYEN_AS = "{}/wasm-as".format(TOOL_BINARYEN)
TOOL_WASMA = "~/wasma/bin/DataFlowGraph"
DATA_PATH = Path("data")


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
        outputFile = DATA_PATH / "microbenchmarks/{}".format(inputDir.name) / "wassail/graph_{}.dot".format(funcIndex)
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
        metadata["functions"].append({"index": fTuple[0], "name": fTuple[1]})
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
        outputDir = DATA_PATH / "microbenchmarks/{}".format(inputDir.name) / "wasma"
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
    outputDir = DATA_PATH / "microbenchmarks/{}".format(inputDir.name) / "wasm-opt"
    # Create the output directory
    outputDir.mkdir(parents=True, exist_ok=True)
    # Create a command to run binaryen wasm-opt
    wasmOptCommand = "{} {} --flatten --dfo -ism {} -od {}".format(TOOL_BINARYEN_OPT, inputDir / "{}.wasm".format(inputDir.name), inputDir / "{}.wasm.map".format(inputDir.name), outputDir)
    status, msg, exec_time = executeCommand(wasmOptCommand, "wasm-opt")
    if not status:
        print(msg)
    else :
        print("binaryen wasm-opt analyse function in {} took {} seconds".format(inputDir.name, exec_time))

def runBenchmark():
    # iterate over all the microbenchmarks dir, and run the tools on them
    for item in MICRO_BENCHMARKS_PATH.iterdir():
        if item.is_dir():
            runWassail(item)
            runWasma(item)
            runBinaryen(item)