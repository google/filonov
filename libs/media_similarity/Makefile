SHELL=/bin/bash
PYTHON=`which python`

.PHONY: tests
tests:
	docker-compose run --rm --no-deps --entrypoint=pytest similarity /tests/


.PHONY: build
clean:
	@echo "Removing the build/ dist/ and *.egg-info/ directories"
	@rm -rf build dist *.egg-info

upload:
	@echo "Uploading built package to PyPI"
	@${PYTHON} `which twine` upload dist/*

bundle:
	@echo "Bundling the code"; echo
	@${PYTHON} -m build

upload_pypi: | clean bundle upload
