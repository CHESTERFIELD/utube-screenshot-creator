# call this target to run parser
run:
	python youtube_selenium_parser.py

prepare:
	tar -zxvf src/chromedriver_mac64.zip

# call this target to cleanup screenshots folder
clear:
	rm -rf screenshots
	mkdir screenshots
