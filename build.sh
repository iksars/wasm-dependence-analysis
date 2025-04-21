#!/bin/bash

binaryen_tool="./tools/binaryen/bin/wasm-opt"
wassail_tool="./tools/wassail/_build/default/main.exe"
wasma_tool="./tools/wasma/bin/DataFlowGraph"

if [ ! -f "$binaryen_tool" ]; then
    cd tools/binaryen
    git submodule init
    git submodule update
    cmake . && make
    cd ../..
fi

if [ ! -f "$wassail_tool" ]; then
    cd tools/wassail
    make
    cd ../..
fi

if [ ! -f "$wasma_tool" ]; then
    cd tools/wasma
    make build
    cd ../..
fi

