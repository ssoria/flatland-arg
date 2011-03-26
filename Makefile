all:
	python setup.py py2app

clean:
	rm -rf *.egg dist build
