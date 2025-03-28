cd ./data/microbenchmarks
pdflatex -interaction=nonstopmode result.tex
rm -f *.aux *.log *.out
cd ../..