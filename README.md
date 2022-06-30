# yaml_env_var_parser
Implementation of PyYAML Reader with env var parsing. 

Inspired by envyaml: https://github.com/thesimj/envyaml

The Reader is the very first step of the PyYAML parsing process and this is where the environment variable is being parsed.

The environment variable parsing can be **anywhere** in the yaml file, the parsing is done in the very early stages of the PyYAML loading process. It is possible to `inject` a YAML structure using it

The code below is an example of what I mean be **anywere**:
```
import os
from yaml_env_var_parser import load

# env vars are replaced on keys
os.environ['MY_KEY'] = 'key'
# they might also be YAML tags
os.environ['TIMESTAMP_TAG'] = '!!timestamp'
# this will inject `another_key` into the yaml data
os.environ['MY_COMPLEX_DATA'] = """"simple_data"
another_key: "its possible to create new keys with env vars. we might call it YAML INJECTION"
"""
yaml_data_str = """
${MY_KEY}: "data"
complex_data: ${MY_COMPLEX_DATA}
timestamp_tag: ${TIMESTAMP_TAG} 2022-01-01 00:00:00
"""
parsed = load(yaml_data_str)
print(parsed)
``` 
Output:
```
{'key': 'data', 'complex_data': 'simple_data', 'another_key': 'its possible to create new keys with env vars. we might call it YAML INJECTION', 'timestamp_tag': datetime.datetime(2022, 1, 1, 0, 0)}
```
The key `another_key` does not exist in `yaml_data_str` yaml str definition but it is added from the environment variable `${MY_COMPLEX_DATA}`