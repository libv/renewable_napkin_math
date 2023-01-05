.PHONY: clean all

all: \
	smard_generation_forecast.fixed.csv \
	smard_consumption_forecast.fixed.csv \
	lifepo4_lifespan_150GWh_20ys.txt

smard_generation_forecast.fixed.csv: generation_forecast_fixup.py smard_generation_forecast.csv smard_generation.csv
	./generation_forecast_fixup.py smard_generation_forecast.csv smard_generation.csv $@ > generation_forecast_fixup.txt

smard_consumption_forecast.fixed.csv: consumption_forecast_fixup.py smard_consumption_forecast.csv smard_consumption.csv
	./consumption_forecast_fixup.py smard_consumption_forecast.csv smard_consumption.csv $@ > consumption_forecast_fixup.txt

consumption_cycles.csv: consumption_cycles.py smard_consumption.csv
	./consumption_cycles.py smard_consumption.csv $@ > consumption_cycles.txt

lifepo4_lifespan_150GWh_20ys.txt: lifepo4_lifespan.py consumption_cycles.csv
	./lifepo4_lifespan.py consumption_cycles.csv 150 20 > lifepo4_lifespan_150GWh_20ys.txt

clean:
	rm -f smard_generation_forecast.fixed.csv
	rm -f generation_forecast_fixup.txt
	rm -f smard_consumption_forecast.fixed.csv
	rm -f consumption_forecast_fixup.txt
	rm -f consumption_cycles.csv
	rm -f consumption_cycles.txt
	rm -f lifepo4_lifespan_150GWh_20ys.txt

install:
