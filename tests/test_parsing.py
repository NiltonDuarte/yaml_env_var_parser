import os
from yaml_env_var_parser import load

os.environ['YAML_TEST_ENV_VAR1'] = 'VAR1'
os.environ['YAML_TEST_ENV_VAR2'] = 'VAR2'


def test_parsing_default_args():
    data = 'test: test_1/$YAML_TEST_ENV_VAR1/${YAML_TEST_ENV_VAR2}/"${NOT_EXIST|abc}" #comment'
    data_loaded = load(data)
    assert data_loaded['test'] == 'test_1/$YAML_TEST_ENV_VAR1/VAR2/"abc"'


def test_parsing_named_true():
    data = 'test: test_1/$YAML_TEST_ENV_VAR1/${YAML_TEST_ENV_VAR2}/"${NOT_EXIST|abc}" #comment'
    data_loaded = load(data, allow_parse_named=True)
    assert data_loaded['test'] == 'test_1/VAR1/VAR2/"abc"'


def test_parsing_key():
    os.environ['VAR_KEY'] = 'my_key'
    os.environ['VAR_COMMENT'] = 'my_comment'
    data = '${VAR_KEY}: test_1/${YAML_TEST_ENV_VAR2}/"${NOT_EXIST|abc}" #comment ${VAR_COMMENT}'
    data_loaded = load(data)
    assert data_loaded['my_key'] == 'test_1/VAR2/"abc"'
