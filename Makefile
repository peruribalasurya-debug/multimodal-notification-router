# Unix/make convenience wrapper. Each target just calls the cross-platform runner
# (tasks.py), which is the primary entry point and works without `make` too --
# see README.md for the `python tasks.py <target>` equivalents.

.PHONY: install run eval test

install:
	python tasks.py install

run:
	python tasks.py run

eval:
	python tasks.py eval

test:
	python tasks.py test
