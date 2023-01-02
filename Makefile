.PHONY: clean all

all: consumption_cycles.csv

consumption_cycles.csv: consumption_cycles.py smard_consumption.csv
	./consumption_cycles.py smard_consumption.csv $@ > consumption_cycles.txt

clean:
	rm -f consumption_cycles.csv
	rm -f consumption_cycles.txt

install:
