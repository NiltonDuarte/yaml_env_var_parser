import re
import os
from yaml.reader import Reader
from yaml.scanner import Scanner
from yaml.parser import Parser
from yaml.composer import Composer
from yaml.constructor import SafeConstructor
from yaml.resolver import Resolver
from yaml import safe_dump  # noqa

# pattern to extract env variables
RE_PATTERN = re.compile(
    r"(\$(?:"
        r"(?P<escaped>(\$|\d+))"  # noqa
        r"|{"
            r"(?P<braced>(.*?))(\|(?P<braced_default>.*?))?"  # noqa
        r"}"
        r"|(?P<named>[\w\-\.]+)(\|(?P<named_default>.*))?"
    r"))",
    re.MULTILINE | re.UNICODE | re.IGNORECASE | re.VERBOSE,
)


class EnvVarParserReader(Reader):

    def __init__(self, stream, strict, allow_parse_named):
        self.strict = strict
        self.allow_parse_named = allow_parse_named
        self.cfg = os.environ
        # if the stream is a string, we parse is before sending to the Reader
        if isinstance(stream, str):
            stream = self.__parse_yaml_buffer(buffer=stream,
                                              cfg=self.cfg,
                                              strict=self.strict,
                                              allow_parse_named=self.allow_parse_named)
        # else, we send it to the reader and we will parse it at raw_buffer setter
        super().__init__(stream)

    @property
    def raw_buffer(self):
        return self._raw_buffer

    @raw_buffer.setter
    def raw_buffer(self, value):
        self._raw_buffer = self.__parse_yaml_buffer(
            buffer=value,
            cfg=self.cfg,
            strict=self.strict,
            allow_parse_named=self.allow_parse_named
        )

    @staticmethod
    def __parse_yaml_buffer(buffer, cfg, strict, separator="|", allow_parse_named=False):
        # this parser is from https://github.com/thesimj/envyaml with minor adjustments
        # direct link to function:
        # https://github.com/thesimj/envyaml/blob/b7c2396cefd0d9bcc1b6609e78efc4ae16a117cf/envyaml/envyaml.py#L198
        """read and parse yaml file

        :param str file_path: path to file
        :param dict cfg: configuration variables (environ and .env)
        :param bool strict: strict mode
        :return: dict
        """
        # if the buffer is None or empty, just return it
        if not buffer:
            return buffer

        # not found variables
        not_found_variables = set()

        # changes dictionary
        replaces = dict()

        shifting = 0

        # iterate over findings
        for entry in RE_PATTERN.finditer(buffer):
            groups = entry.groupdict()  # type: dict

            # replace
            variable = None
            default = None
            replace = None

            if allow_parse_named and groups["named"]:
                variable = groups["named"]
                default = groups["named_default"]

            elif groups["braced"]:
                variable = groups["braced"]
                default = groups["braced_default"]

            elif groups["escaped"] and "$" in groups["escaped"]:
                span = entry.span()
                buffer = (
                    buffer[: span[0] + shifting]
                    + groups["escaped"]
                    + buffer[span[1] + shifting:]
                )
                # Added shifting since every time we update content we are
                # changing the original groups spans
                shifting += len(groups["escaped"]) - (span[1] - span[0])

            if variable is not None:
                if variable in cfg:
                    replace = cfg[variable]
                elif variable not in cfg and default is not None:
                    replace = default
                else:
                    not_found_variables.add(variable)

            if replace is not None:
                # build match
                search = "${" if groups["braced"] else "$"
                search += variable
                search += separator + default if default is not None else ""
                search += "}" if groups["braced"] else ""

                # store findings
                replaces[search] = replace

        # strict mode
        if strict and not_found_variables:
            raise ValueError(
                "Strict mode enabled, variables "
                + ", ".join(["$" + v for v in not_found_variables])
                + " are not defined!"
            )

        # replace finding with there respective values
        for replace in sorted(replaces, reverse=True):
            buffer = buffer.replace(replace, replaces[replace])

        return buffer

    def update_raw(self):
        # because i'm not handling the data loading process
        # loading partial data might result in partial env vars
        # that will not be parsed in the raw data buffer
        # !! this is a performance issue !!
        data = self.stream.read()
        if self.raw_buffer is None:
            self.raw_buffer = data
        else:
            self.raw_buffer += data
        # because i'm modifying the raw buffer, i'm always setting the new len after the parsing is made
        self.stream_pointer = len(self.raw_buffer)
        if not data:
            self.eof = True


class EnvVarParserSafeLoader(
        EnvVarParserReader,
        Scanner,
        Parser,
        Composer,
        SafeConstructor,
        Resolver
):

    def __init__(self, stream, strict, allow_parse_named):
        EnvVarParserReader.__init__(self, stream, strict, allow_parse_named)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        SafeConstructor.__init__(self)
        Resolver.__init__(self)


def load(stream, strict=True, allow_parse_named=False):
    """
    Parse the first YAML document in a stream
    and produce the corresponding Python object.
    """

    loader = EnvVarParserSafeLoader(stream, strict, allow_parse_named)
    try:
        return loader.get_single_data()
    finally:
        loader.dispose()


__all__ = [load]
