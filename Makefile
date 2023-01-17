.PHONY: clean all

all: \
	consumption_per_year.txt \
	lifepo4_grid_storage_150GWh_20ys.txt \
	lifepo4_grid_storage_100GWh_20ys.txt \
	lifepo4_grid_storage__50GWh_20ys.txt \
	generation_data.csv

consumption_per_year.txt: consumption_per_year.py smard_consumption.csv
	./consumption_per_year.py smard_consumption.csv > consumption_per_year.txt

smard_generation_forecast.fixed.csv: generation_forecast_fixup.py smard_generation_forecast.csv smard_generation.csv
	./generation_forecast_fixup.py smard_generation_forecast.csv smard_generation.csv $@ > generation_forecast_fixup.txt

smard_consumption_forecast.fixed.csv: consumption_forecast_fixup.py smard_consumption_forecast.csv smard_consumption.csv
	./consumption_forecast_fixup.py smard_consumption_forecast.csv smard_consumption.csv $@ > consumption_forecast_fixup.txt

consumption_cycles.csv: consumption_cycles.py smard_consumption.csv
	./consumption_cycles.py smard_consumption.csv $@ > consumption_cycles.txt

lifepo4_grid_storage_150GWh_20ys.txt: lifepo4_grid_storage.py consumption_cycles.csv
	./lifepo4_grid_storage.py consumption_cycles.csv 150 20 > $@

lifepo4_grid_storage_100GWh_20ys.txt: lifepo4_grid_storage.py consumption_cycles.csv
	./lifepo4_grid_storage.py consumption_cycles.csv 100 20 > $@

lifepo4_grid_storage__50GWh_20ys.txt: lifepo4_grid_storage.py consumption_cycles.csv
	./lifepo4_grid_storage.py consumption_cycles.csv 50 20 > $@

generation_data.csv: ./generation_data_prepare.py smard_consumption_forecast.fixed.csv smard_consumption.csv \
	smard_generation_capacity.csv smard_generation_forecast.fixed.csv smard_generation.csv

	./generation_data_prepare.py smard_consumption_forecast.fixed.csv smard_consumption.csv smard_generation_capacity.csv smard_generation_forecast.fixed.csv smard_generation.csv $@

clean:
	rm -f consumption_per_year.txt
	rm -f smard_generation_forecast.fixed.csv
	rm -f generation_forecast_fixup.txt
	rm -f smard_consumption_forecast.fixed.csv
	rm -f consumption_forecast_fixup.txt
	rm -f consumption_cycles.csv
	rm -f consumption_cycles.txt
	rm -f lifepo4_grid_storage_150GWh_20ys.txt
	rm -f lifepo4_grid_storage_100GWh_20ys.txt
	rm -f lifepo4_grid_storage__50GWh_20ys.txt
	rm -f generation_data.csv

install:
