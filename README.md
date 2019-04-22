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