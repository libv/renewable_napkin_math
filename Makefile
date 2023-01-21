.PHONY: clean all

all: \
	consumption_per_year.txt \
	altmaier_missing_capacity.csv \
	altmaier_methane_wasted.txt \
	lifepo4_grid_storage_150GWh_20ys.txt \
	lifepo4_grid_storage_100GWh_20ys.txt \
	lifepo4_grid_storage__50GWh_20ys.txt \
	simulate_2045.txt

consumption_per_year.txt: consumption_per_year.py smard_consumption.csv
	./consumption_per_year.py smard_consumption.csv > consumption_per_year.txt

altmaier_missing_capacity.csv: altmaier_missing_capacity.py
	./altmaier_missing_capacity.py $@ > altmaier_missing_capacity.txt

altmaier_methane_wasted.txt: altmaier_methane_wasted.py smard_generation.csv cegh_at_methane_day-ahead.csv altmaier_missing_capacity.csv
	./altmaier_methane_wasted.py smard_generation.csv cegh_at_methane_day-ahead.csv altmaier_missing_capacity.csv > $@

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

simulation_data_forecast.csv: ./simulation_data_prepare.py smard_consumption_forecast.fixed.csv smard_consumption.csv \
	smard_generation_capacity.csv smard_generation_forecast.fixed.csv smard_generation.csv

	./simulation_data_prepare.py smard_consumption_forecast.fixed.csv smard_consumption.csv smard_generation_capacity.csv smard_generation_forecast.fixed.csv smard_generation.csv $@ simulation_data_actual.csv

simulate_2045.txt: simulate.py simulation_data_forecast.csv simulation_data_actual.csv
	./simulate.py simulation_data_forecast.csv simulation_data_actual.csv 2.0 182.5 70 500 5000 50 100 > $@

clean:
	rm -f consumption_per_year.txt
	rm -f altmaier_missing_capacity.txt
	rm -f altmaier_missing_capacity.csv
	rm -f altmaier_methane_wasted.txt
	rm -f smard_generation_forecast.fixed.csv
	rm -f generation_forecast_fixup.txt
	rm -f smard_consumption_forecast.fixed.csv
	rm -f consumption_forecast_fixup.txt
	rm -f consumption_cycles.csv
	rm -f consumption_cycles.txt
	rm -f lifepo4_grid_storage_150GWh_20ys.txt
	rm -f lifepo4_grid_storage_100GWh_20ys.txt
	rm -f lifepo4_grid_storage__50GWh_20ys.txt
	rm -f simulation_data_forecast.csv
	rm -f simulation_data_actual.csv
	rm -f simulate_2045.txt

install:
