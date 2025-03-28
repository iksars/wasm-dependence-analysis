#!/bin/bash

DIR="./tools"

if [ ! -d "$DIR" ]; then
    mkdir -p "$DIR"
fi

DIR="./data"

if [ ! -d "$DIR" ]; then
    mkdir -p "$DIR"
fi


cd tools
# Clone the Wassail repo
git clone https://github.com/acieroid/wassail.git
cd wassail 
git reset --hard 768a57fd0eb3f8ea8f9a1af5426b38cda59dfca9
cd ..

# Clone the WasmA repo
git clone https://github.com/stg-tud/wasma.git
cd wasma
git reset --hard a4c9be450c94cad58949676977abd94d3d4216ca
cd ..

# Clone the Binaryen repo and make changes
# We do not use the standard Binaryen tool and instead make some changes to dump the internal IR.
# The changes are documented below. 
git clone https://github.com/WebAssembly/binaryen.git
cd binaryen
git reset --hard 19dd23db3c20214e2e6a73023529c2496f9c2a50
X="std::vector<Function::DebugLocation*> myDebugLocations;\n\
    Function* currFunction = nullptr;\n\
    std::unordered_map<Name, size_t> funcInsCount;\n\
    void releaseMyDebugLocations() {\n\
        for (auto* loc : myDebugLocations) {\n\
            delete loc;\n\
        }\n\
        myDebugLocations.clear();\n\
    }"
sed -i "1428i $X" ./src/wasm-binary.h

sed -i "1476d" ./src/wasm/wasm-binary.cpp

X="size_t line;\n\
    auto insCount = funcInsCount.find(func->name);\n\
    if (insCount != funcInsCount.end()) {\n\
        line = insCount->second;\n\
        insCount->second++;\n\
    } else {\n\
        line = 0;\n\
        funcInsCount[func->name] = 1;\n\
    }\n\
    auto loc = new Function::DebugLocation();\n\
    loc->fileIndex = 0;\n\
    loc->lineNumber = line;\n\
    loc->columnNumber = 1;\n\
    myDebugLocations.emplace_back(loc);\n\
    writeDebugLocation(*loc);"
sed -i "1476i $X" ./src/wasm/wasm-binary.cpp

sed -i "419d" ./src/dataflow/graph.h

X="Node* doVisitConst(Const* curr) { return makeConst(curr); }"
sed -i "419i $X" ./src/dataflow/graph.h

X="Node* makeConst(wasm::Const* origin) {\n\
    auto iter = constantNodes.find(origin->value);\n\
    if (iter != constantNodes.end()) {\n\
      return iter->second;\n\
    }\n\
    // Create one for this literal.\n\
    Builder builder(*module);\n\
    auto* c = builder.makeConst(origin->value);\n\
    auto debugLoc = func->debugLocations[origin];\n\
    if (debugLoc) {\n\
      func->debugLocations[c] = debugLoc;\n\
    }\n\
    auto* ret = addNode(Node::makeExpr(c, c));\n\
    constantNodes[origin->value] = ret;\n\
    return ret;\n\
}"
sed -i "157i $X" ./src/dataflow/graph.h

sed -i "134d" ./src/dataflow/graph.h
X="Node* makeVar(wasm::Type type, Expression* origin = nullptr) {"
sed -i "134i $X" ./src/dataflow/graph.h
sed -i "136d" ./src/dataflow/graph.h
X="auto node = addNode(Node::makeVar(type));\n\
      node->origin = origin;\n\
      return node;
      "
sed -i "136i $X" ./src/dataflow/graph.h
X="if (!node->origin) {node->origin = curr;}"
sed -i "417i $X" ./src/dataflow/graph.h
X="return makeVar(curr->type, curr);"
sed -i "472d" ./src/dataflow/graph.h
sed -i "472i $X" ./src/dataflow/graph.h
sed -i "585d" ./src/dataflow/graph.h
sed -i "585i $X" ./src/dataflow/graph.h
sed -i "625d" ./src/dataflow/graph.h
sed -i "625i $X" ./src/dataflow/graph.h
sed -i "648d" ./src/dataflow/graph.h
X="ifTrue = ensureI1(condition, expr);"
sed -i "648i $X" ./src/dataflow/graph.h
sed -i "650d" ./src/dataflow/graph.h
X="ifFalse = makeZeroComp(condition, true, expr);"
sed -i "650i $X" ./src/dataflow/graph.h

sed -i "72d" ./src/dataflow/utils.h

X='o << "] (origin: " << *node->origin << ", )\\n";'
sed -i "72i $X" ./src/dataflow/utils.h

X='auto it = graph.func->debugLocations.find(node->origin);\n\
  if (it != graph.func->debugLocations.end()) {\n\
      if (it->second) {\n\
          const auto& debugLoc = *(it->second);\n\
          o << \"Debug Info - Node: \" << node.get()\n\
                      << \" | File Index: \" << debugLoc.fileIndex\n\
                      << \" | Line: \" << debugLoc.lineNumber\n\
                      << \" | Column: \" << debugLoc.columnNumber;\n\
          if (debugLoc.symbolNameIndex) {\n\
                o << \" | Symbol Name Index: \" << *(debugLoc.symbolNameIndex);\n\
          }\n\
          o << "\\n\";\n\
      } else {\n\
          o << \"Debug Info - Node: \" << node.get() << \" | No debug location\" << "\\n";\n\
      }\n\
    }'
sed -i "78i $X" ./src/dataflow/utils.h

X='inline std::ostream& dump2dot(Graph& graph, std::ostream& o) {\n\
  int nodeIndex = 0;\n\
  std::unordered_map<Node*, int> nodeIndices;\n\
  o << "digraph {\\n";\n\
  for (auto& nodeWrappre : graph.nodes) {\n\
    auto* node = nodeWrappre.get();\n\
    o << nodeIndex << " [label=\\"";\n\
    nodeIndices[node] = nodeIndex++;\n\
    switch (node->type) {\n\
      case Node::Type::Var:\n\
        o << "var " << node->wasmType << " " << node;\n\
        break;\n\
      case Node::Type::Expr: {\n\
        o << "expr ";\n\
        o << *node->expr;\n\
        break;\n\
      }\n\
      case Node::Type::Phi:\n\
        o << "phi " << node->index;\n\
        break;\n\
      case Node::Type::Cond:\n\
        o << "cond " << node->index;\n\
        break;\n\
      case Node::Type::Block: {\n\
        o << "block (" << node->values.size() << " conds)";\n\
        break;\n\
      }\n\
      case Node::Type::Zext:\n\
        o << "zext";\n\
        break;\n\
      case Node::Type::Bad:\n\
        o << "bad";\n\
        break;\n\
    }\n\
    o << "\\" origin=\\"" << *node->origin << "\\"";\n\
    auto it = graph.func->debugLocations.find(node->origin);\n\
    if (it != graph.func->debugLocations.end()) {\n\
      if (it->second) {\n\
        const auto& debugLoc = *(it->second);\n\
        o << " debugLoc=\\"File Index: " << debugLoc.fileIndex\n\
          << " | Line: " << debugLoc.lineNumber\n\
          << " | Column: " << debugLoc.columnNumber;\n\
        if (debugLoc.symbolNameIndex) {\n\
          o << " | Symbol Name Index: " << *(debugLoc.symbolNameIndex);\n\
        }\n\
        o << "\\"";\n\
      }\n\
    }\n\
    o << "];\\n";\n\
  }\n\
  for (auto& node : graph.nodes) {\n\
    for (auto* value : node->values) {\n\
      o << nodeIndices[node.get()] << " -> " << nodeIndices[value] << ";\\n";\n\
    }\n\
  }\n\
  o << "}\\n";\n\
  return o;\n\
}'
sed -i "117i $X" ./src/dataflow/utils.h

X="#include <fstream>"
sed -i "36i $X" ./src/passes/DataFlowOpts.cpp

X="std::ofstream f;\n\
    f.open(runner->options.arguments[\"data-flow-ir-dump\"] + \"/graph_\" + std::string(func->name.str) + \".dot\");\n\
    dump2dot(graph, f);\n\
    f.close();"
sed -i "64i $X" ./src/passes/DataFlowOpts.cpp

X=".add(\"--data-flow-dump\",\n\
         \"-od\",\n\
         \"Dump data flow graph to a file\",\n\
         WasmOptOption,\n\
         Options::Arguments::One,\n\
         [](Options* o, const std::string& argument) {\n\
           o->extra[\"od\"] = argument;\n\
           Colors::setEnabled(false);\n\
         })"
sed -i "108i $X" ./src/tools/wasm-opt.cpp
X="options.passOptions.arguments[\"data-flow-ir-dump\"] = options.extra[\"od\"];"
sed -i "272i $X" ./src/tools/wasm-opt.cpp

sed -i "418d" ./src/pass.h
X="PassRunner* runner = nullptr;"
sed -i "421i $X" ./src/pass.h

cd ../..

./build.sh