# call this target to prepare app to call run target
prepare:
	python3 -m venv venv
	source venv/bin/activate && pip install -r req.txt
	mkdir -p screenshots

# call this target to run parser
run:
	python youtube_selenium_parser.py

# call this target to cleanup screenshots folder
clear:
	rm -r screenshots/* || true

# call this target to update chromedriver
update-driver:
	python update_chromedriver.py
