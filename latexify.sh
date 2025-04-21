dirPath="$1"
cd "$dirPath"
pdflatex -interaction=nonstopmode result.tex
rm -f *.aux *.log *.out
