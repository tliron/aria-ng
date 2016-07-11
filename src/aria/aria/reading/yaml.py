
from .reader import Reader
from .exceptions import ReaderError
from .map import Map
import ruamel.yaml as yaml

class YamlMap(Map):
    """
    Map for agnostic raw data read from YAML.
    """
    
    def parse(self, node, location):
        if isinstance(node, yaml.SequenceNode):
            self.children = []
            for n in node.value:
                m = YamlMap(location, n.start_mark.line + 1, n.start_mark.column + 1)
                self.children.append(m)
                m.parse(n, location)
        elif isinstance(node, yaml.MappingNode):
            self.children = {}
            for key, n in node.value:
                m = YamlMap(location, key.start_mark.line + 1, key.start_mark.column + 1)
                self.children[key.value] = m
                m.parse(n, location)

class YamlReader(Reader):
    """
    ARIA YAML reader.
    """
    
    def read(self):
        data = self.load()
        try:
            data = str(data)
            yaml_loader = yaml.RoundTripLoader(data)
            node = yaml_loader.get_single_node()
            if node is None:
                return {}
            map = YamlMap(self.loader.location, 0, 0)
            map.parse(node, self.loader.location)
            #map.dump()
            raw = yaml_loader.construct_document(node)
            setattr(raw, '_map', map)
            return raw
            
            #return yaml.load(data, yaml.RoundTripLoader)
        except Exception as e:
            if isinstance(e, yaml.parser.MarkedYAMLError):
                context = e.context or 'while parsing'
                problem = e.problem
                line = e.problem_mark.line
                column = e.problem_mark.column
                snippet = e.problem_mark.get_snippet()
                raise ReaderError('YAML %s: %s %s' % (e.__class__.__name__, problem, context), location=self.loader.location, line=line, column=column, snippet=snippet, cause=e)
            else:
                raise ReaderError('YAML: %s' % e, cause=e)