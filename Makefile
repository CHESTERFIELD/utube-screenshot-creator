# call this target to run parser
run:
	python youtube_selenium_parser.py

# call this target to prepare app to call run target
prepare:
	mkdir screenshots

# call this target to cleanup screenshots folder
clear:
	rm -r screenshots/* || true
