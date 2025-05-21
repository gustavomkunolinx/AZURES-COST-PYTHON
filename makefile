SHELL := /bin/bash

report:
	python3 az-cost-comparison-by-day-vs-lastweek.py
	#python3 az-cost-comparison-by-month.py