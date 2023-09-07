C5
=========

This is a simple tool that tries to check various formalities for patches to-be-sent to the Linux kernel mailing lists.
It's intended to automatically pick and run necesary compile and static-check tests on the changes made, which allows to
save time for both the contributor and the list maintainer.

This tool is like a dishwashing machine: it might take two hours to test a series you would spend 20 minutes on but
you can do something else while it runs.

The name "c5" was chosen due to [b4](https://github.com/mricon/b4) being a thing, and because c5 can be read as "check".

> **Note**
> In the current form the tool makes many significant assumptions based on the Author's workflow and might provide
> poor coverage for many possible formalities.

Usage
-----

Run `c5 test` in a Linux git tree, while in a branch managed by `b4`, the tool will check all the commits in the series.
