# Differential Testing and Comparative Study of Data Dependency Analysis in WebAssembly Analyzers/Optimizers

This repository contains supplementary material for the paper "Differential Testing and Comparative Study of Data Dependency Analysis in WebAssembly Analyzers/Optimizers" (Nanjing University undergraduate thesis).

## Running Locally

Use following command:
```
git clone <this repo>
cd wasm-dependence-analysis
chmod +x setup.sh && ./setup.sh
python3 src/main.py --help
```
If there are no errors generated during the above process and you see the help information, then everything is ready.

## Running via Docker

### Building the Image
To build the artifact, simply run: 
```
git clone <this repo>
cd wasm-dependence-analysis
docker build -t wasmDependenceAnalysis .
```

### Running the Image 

Use following command:
```
docker run -d -t -i wasmDependenceAnalysis
# The container ID will be written to the console. 
docker exec -it <container-id> /bin/bash
```
Then you can try exec src/main.py.

## License

All our own analysis programs are Apache 2-licensed, see `LICENSE`. We do not assume ownership or copyright of any of the WebAssembly programs we evaluate on and redistribute them here only for research purposes. All programs come from public sources.
