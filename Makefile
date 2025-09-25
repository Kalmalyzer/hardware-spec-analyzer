.PHONY: clean analyze

clean:
	rm cache/*.bin
	rm cache/*.txt
	rm output/*.csv

analyze:
	python3 analyze.py