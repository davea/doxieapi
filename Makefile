build: clean
	pipenv run python setup.py sdist
	pipenv run python setup.py bdist_wheel --universal

clean:
	rm -rf dist build doxieapi.egg-info

publish: clean build
	pipenv run twine upload dist/*

test_publish: clean build
	pipenv run twine upload --repository testpypi dist/*
