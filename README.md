# WhoPY
WhoPY was developed to solve some of the many issues facing previous whois wrappers for Python. 
It provides better TLD coverage, and structured data for use in your application.

## Installation

To install run `pip install whopy`

## Usage
Include the import statement below:

```python
import whopy
```

Example of usage is below:

```python
res = whopy.get_whois('asu.edu')
print(res)
```

## Attribution
This repo was pulled from https://github.com/joepie91/python-whois. My goal is to have more active development on this version as it is used in some production systems. 

We aim to never break backwards compatibility! If there must be a change, we will ensure this readme is up to date.