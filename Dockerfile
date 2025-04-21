FROM ubuntu:20.04
ARG DEBIAN_FRONTEND=noninteractive
# Binaryen dependencies
RUN apt-get update && apt-get install -y \
    ocaml \
    opam \
    git \
    make \
    cmake \
    g++ \
    python3 \
    python3-pip \
    wget \
    curl \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Wasma dependencies
# Install golang
RUN wget https://golang.org/dl/go1.16.3.linux-amd64.tar.gz
RUN tar -C /usr/local -xzf go1.16.3.linux-amd64.tar.gz
ENV PATH=$PATH:/usr/local/go/bin

# Wassail dependencies
RUN opam init --auto-setup --disable-sandboxing --yes --bare
RUN opam switch create system ocaml-base-compiler.5.3.0
RUN eval $(opam env)

RUN pip install numpy
RUN pip install pydot
RUN pip install scipy
RUN pip install networkx

# Copy the wasm-call-graphs repo 
RUN mkdir -p /home/wasm-dependence-analysis
COPY . /home/wasm-dependence-analysis


WORKDIR /home/wasm-dependence-analysis
RUN ./setup.sh


CMD ["/bin/bash"]


