.PHONY: clean all

all: \
	smard_consumption_forecast.fixed.csv \
	consumption_cycles.csv

smard_consumption_forecast.fixed.csv: consumption_forecast_fixup.py smard_consumption_forecast.csv smard_consumption.csv
	./consumption_forecast_fixup.py smard_consumption_forecast.csv smard_consumption.csv $@ > consumption_forecast_fixup.txt

consumption_cycles.csv: consumption_cycles.py smard_consumption.csv
	./consumption_cycles.py smard_consumption.csv $@ > consumption_cycles.txt

clean:
	rm -f smard_consumption_forecast.fixed.csv
	rm -f consumption_forecast_fixup.txt
	rm -f consumption_cycles.csv
	rm -f consumption_cycles.txt

install:
