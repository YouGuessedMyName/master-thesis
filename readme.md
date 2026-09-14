# Symbolic $\textbf{AdjointPDR}^\downarrow$ with generalization
This repository contains our Python implementation of a symbolic variety of the $\textbf{AdjointPDR}^\downarrow$ algorithm (originally by [Kori *et al.*](https://link.springer.com/chapter/10.1007/978-3-031-37703-7_3)). See *thesis.pdf*.

## Benchmarks
Our implementation accepts a subset of Markov chains in the PRISM format, see Chapter 4 of *thesis.pdf*. The folder *benchmarks* contains all benchmakrs that we adopted to a supported encoding. The folder *benchmarks_included* contains all benchmarks that are included in Chapter 6 of *thesis.pdf*.

## Running
### Installing requirements
```sh
pip install requirements.txt
```

### Benchmarks
Run symbolic $\textbf{AdjointPDR}^\downarrow$ on all all benchmarks in the target folder, and store the result in a .csv file.
```sh
python3 run_benchmarks.py 0 > results.csv
```
The argument 0 specifies that we want to run all experiments (starting from index 0). Other parameters including the timeout (240s by default) and the target folder (*benchmarks_included* by default) can be adjusted in *run_benchmarks.py*.

### Single file
Run symbolic $\textbf{AdjointPDR}^\downarrow$ for a single PRISM file.
```sh
python3 main_sym.py
```
Parameters (including the target file) can be adjusted inside *main_sym.py*.

### Explicit implementation

*sym_adjpdr* contains the symbolic implementation (see Chapter 4 of *thesis.pdf*), whereas *adjpdr* contains a simpler implementation that uses explicit data structures. It does not support any of the generalization methods.