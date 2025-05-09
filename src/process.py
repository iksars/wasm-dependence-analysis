from pathlib import Path
import subprocess
import time
import json
import graph
import concurrent.futures


MICRO_BENCHMARKS_PATH = Path("microbenchmarks")
TOOL_WASSAIL = "tools/wassail/_build/default/main.exe"
TOOL_BINARYEN = "tools/binaryen/bin"
TOOL_BINARYEN_OPT = "{}/wasm-opt".format(TOOL_BINARYEN)
TOOL_BINARYEN_AS = "{}/wasm-as".format(TOOL_BINARYEN)
TOOL_WASMA = "tools/wasma/bin/DataFlowGraph"
DATA_PATH = Path("data")
DATA_MICRO_BENCHMARKS_PATH = DATA_PATH / "microbenchmarks"
REAL_WORLD_PATH = Path("real-world-programs")
DATA_REAL_WORLD_PATH = DATA_PATH / "real-world-programs"

name_map = {"blake3": "blake3_js_bg", "fonteditor-core": "woff2", "magic": "magic-js", "opusscript": "opusscript_native_wasm", "shiki": "onig", "source-map": "mappings", "wasm-rsa": "rsa_lib_bg"}



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


def runWassail(inputDir, micro = True):
    # find the metadata file
    metadataFile = inputDir / "metadata.json"
    metadata = readMetadata(metadataFile)
    # Iterate over all the functions
    for function in metadata["functions"]:
        # Input file
        inputFile = inputDir / "{}.wasm".format(inputDir.name)
        # Function index
        funcIndex = function["index"]
        # Output file
        outputFile = DATA_MICRO_BENCHMARKS_PATH/"{}".format(inputDir.name) / "wassail/graph_{}.dot".format(funcIndex)
        if not micro:
            outputFile = DATA_REAL_WORLD_PATH/"{}".format(inputDir.name) / "wassail/graph_{}.dot".format(funcIndex)
            inputFile = inputDir / "{}.wasm".format(name_map[inputDir.name])
        # Create the output directory
        outputFile.parent.mkdir(parents=True, exist_ok=True)
        # Create a command to run wassail
        wassailCommand = "{} dependencies {} {} {}".format(TOOL_WASSAIL, inputFile, funcIndex, outputFile)
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
    clearReal()

def clearReal():
    for item in REAL_WORLD_PATH.iterdir():
        if item.is_dir():
            mapFile = item / "{}.wasm.map".format(name_map[item.name])
            metaDataFile = item / "metadata.json"
            for file in item.iterdir():
                if file == mapFile or file == metaDataFile:
                    file.unlink()
        else :
            item.unlink()
    realDataPath = DATA_PATH / "real-world-programs"
    rmdirHelper(realDataPath)

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
def runWasma(inputDir, micro = True):
    # find the metadata file
    metadataFile = inputDir / "metadata.json"
    metadata = readMetadata(metadataFile)
    # Iterate over all the functions
    for function in metadata["functions"]:
        # Input file
        inputFile = inputDir / "{}.wasm".format(inputDir.name)
        # Function index
        funcIndex = function["index"]
        # Output directory
        outputDir = DATA_MICRO_BENCHMARKS_PATH/"{}".format(inputDir.name) / "wasma"
        if not micro:
            outputDir = DATA_REAL_WORLD_PATH/"{}".format(inputDir.name) / "wasma"
            inputFile = inputDir / "{}.wasm".format(name_map[inputDir.name])
        # Create the output directory
        outputDir.mkdir(parents=True, exist_ok=True)
        # Create a command to run wasma
        wasmaCommand = "{} -file {} -fi {} -cdfg true -out {}".format(TOOL_WASMA, inputFile, funcIndex, outputDir)
        status, msg, exec_time = executeCommand(wasmaCommand, "wasma")
        if not status:
            print(msg)
        else :
            print("wasma analyse function {} in {} took {} seconds".format(funcIndex, inputDir.name, exec_time))

def runBinaryen(inputDir, micro = True):
    # input file
    inputFile = inputDir / "{}.wasm".format(inputDir.name)
    # Output directory
    outputDir = DATA_MICRO_BENCHMARKS_PATH/"{}".format(inputDir.name) / "binaryen"
    # map file
    mapFile = inputDir / "{}.wasm.map".format(inputDir.name)
    if not micro:
        outputDir = DATA_REAL_WORLD_PATH/"{}".format(inputDir.name) / "binaryen"
        inputFile = inputDir / "{}.wasm".format(name_map[inputDir.name])
        mapFile = inputDir / "{}.wasm.map".format(name_map[inputDir.name])
    # Create the output directory
    outputDir.mkdir(parents=True, exist_ok=True)
    # Create a command to run binaryen wasm-opt
    wasmOptCommand = "{} {} --flatten --dfo -ism {} -od {}".format(TOOL_BINARYEN_OPT, inputFile, mapFile, outputDir)
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


def runAllTool(inputDir, micro = True):
    for tool in toolRegister:
        runTool(tool, inputDir, micro)

def runTool(tool, inputDir, micro = True):
    toolRegister[tool][0](inputDir, micro)


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
                    graphs.append(toolRegister[tool][2](item / tool / toolRegister[tool][1](i if tool == "binaryen" else metadata["functions"][i]["index"], caseName), metadata["functions"][i]["count"]))
                # if caseName == "stack_and_local":
                #     for graph2 in graphs:
                #         print(graph2.to_dot())
                matrix = graph.compareAdjacentMatrix(graphs)
                data_item["functions"].append({"index": metadata["functions"][i]["index"], "count": metadata["functions"][i]["count"], "matrix": matrix.tolist()})
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




def prepareReal():
    for item in REAL_WORLD_PATH.iterdir():
        if item.is_dir():
            # Generate metadata for the tools
            inputFile = item / "{}.wat".format(name_map[item.name])
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
    
# def runReal():
#     # for item in REAL_WORLD_PATH.iterdir():
#     #     if item.is_dir():
#     #         runAllTool(item, False)
#     data = {"tools": [], "cases": []}
#     data["tools"] = list(toolRegister.keys())
#     # transform the data
#     for item in DATA_REAL_WORLD_PATH.iterdir():
#         if item.is_dir():
#             caseName = item.name
#             metadata = readMetadata(REAL_WORLD_PATH / caseName / "metadata.json")
#             data_item = {
#                 "case": caseName,
#                 "functions": [],
#                 "average": []
#             }
#             avg = {}
#             for i in range(len(metadata["functions"])):
#                 graphs = []
#                 for tool in toolRegister:
#                     graphs.append(toolRegister[tool][2](item / tool / toolRegister[tool][1](i if tool == "binaryen" else metadata["functions"][i]["index"], name_map[caseName]), metadata["functions"][i]["count"]))
#                 # if caseName == "simple_use2":
#                 #     for graph2 in graphs:
#                 #         print(graph2.to_dot())
#                 matrix = graph.compareAdjacentMatrix(graphs)
#                 data_item["functions"].append({"index": metadata["functions"][i]["index"], "count": metadata["functions"][i]["count"], "matrix": matrix.tolist()})
#                 if i == 0:
#                     avg = matrix
#                 else:
#                     avg += matrix
#             data_item["average"] = (avg / len(metadata["functions"])).tolist()
#             data["cases"].append(data_item)
#         else :
#             # unexcepted file
#             item.unlink()
#     # Write the data to a file
#     with open(DATA_REAL_WORLD_PATH / "result.json", "w") as f:
#         json.dump(data, f)

def run_tool_for_process(args):
    idx, tool_name, tool_info, i, func_index, count, path = args
    tool_func = tool_info[2]
    return idx, tool_func(path, count)

def runReal():
    # for item in REAL_WORLD_PATH.iterdir():
    #     if item.is_dir():
    #         runAllTool(item, False)
    data = {"tools": [], "cases": []}
    data["tools"] = list(toolRegister.keys())

    for item in DATA_REAL_WORLD_PATH.iterdir():
        if item.is_dir():
            caseName = item.name
            metadata = readMetadata(REAL_WORLD_PATH / caseName / "metadata.json")
            data_item = {
                "case": caseName,
                "functions": [],
                "average": []
            }
            avg = {}

            for i in range(len(metadata["functions"])):
                graphs = [None] * len(toolRegister)
                futures = []
                
                with concurrent.futures.ProcessPoolExecutor() as executor:
                    args_list = []
                    for idx, tool in enumerate(toolRegister):
                        tool_info = toolRegister[tool]
                        func_index = i if tool == "binaryen" else metadata["functions"][i]["index"]
                        path = item / tool / tool_info[1](func_index, name_map[caseName])
                        args_list.append((idx, tool, tool_info, i, func_index, metadata["functions"][i]["count"], path))

                    futures = [executor.submit(run_tool_for_process, args) for args in args_list]

                    for future in concurrent.futures.as_completed(futures):
                        idx, result = future.result()
                        graphs[idx] = result

                matrix = graph.compareAdjacentMatrix(graphs)
                data_item["functions"].append({
                    "index": metadata["functions"][i]["index"],
                    "count": metadata["functions"][i]["count"],
                    "matrix": matrix.tolist()
                })
                if i == 0:
                    avg = matrix
                else:
                    avg += matrix

            data_item["average"] = (avg / len(metadata["functions"])).tolist()
            data["cases"].append(data_item)

        else:
            # 非预期文件，删除
            item.unlink()

    # 写入结果
    with open(DATA_REAL_WORLD_PATH / "result.json", "w") as f:
        json.dump(data, f)


def evalDataJson(filePath):
    with open(filePath, "r") as f:
        data = json.load(f)
    print("caseName : Fn : Fc")
    for caseItem in data["cases"]:
        caseName = caseItem["case"]
        Fn = len(caseItem["functions"])
        Fc = 0
        for f in caseItem["functions"]:
            matrix = f["matrix"]
            if matrix == [[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0]]:
                Fc = Fc + 1
        print("{} : {} : {}".format(caseName, Fn, Fc))