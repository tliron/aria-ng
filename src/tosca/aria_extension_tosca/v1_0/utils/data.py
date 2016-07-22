
from aria import Issue, dsl_specification, import_fullname
from collections import OrderedDict

#
# DataType
#

def coerce_data_type_value(context, presentation, the_type, entry_schema, constraints, value, constraint_key):
    """
    Handles the \_coerce\_data() hook for complex data types.
    
    There are two kinds of handling:
    
    1. If we have a primitive type as our great ancestor, then we do primitive type coersion, and
       just check for constraints.
       
    2. Otherwise, for normal complex data types we return the assigned property values while making
       sure they are defined in our type. The property definition's default value, if available, will
       be used if we did not assign it. We also make sure that required definitions indeed end up with
       a value.
    """

    primitive = the_type._get_primitive_ancestor(context)
    if primitive is not None:
        # Must be coercible to primitive ancestor
        try:
            value = primitive(value)
        except ValueError as e:
            report_issue_for_bad_format(context, presentation, the_type, value, constraint_key, e)
            value = None
    else:
        definitions = the_type._get_properties(context)
        if isinstance(value, dict):
            r = OrderedDict()

            # Fill in our values, but make sure they are defined
            for name, v in value.iteritems():
                if name in definitions:
                    definition = definitions[name]
                    definition_type = definition._get_type(context)
                    definition_entry_schema = definition.entry_schema
                    definition_constraints = definition.constraints
                    r[name] = coerce_value(context, presentation, definition_type, definition_entry_schema, definition_constraints, v)
                else:
                    context.validation.report('assignment to undefined property "%s" in type "%s" for "%s"' % (name, the_type._fullname, presentation._fullname), locator=v._locator, level=Issue.BETWEEN_TYPES)

            # Fill in defaults from the definitions, and check if required definitions have not been assigned
            for name, definition in definitions.iteritems():
                if (r.get(name) is None) and hasattr(definition, 'default'):
                    r[name] = definition.default
    
                if getattr(definition, 'required', False) and (r.get(name) is None):
                    context.validation.report('required property "%s" in type "%s" is not assigned a value for "%s"' % (name, the_type._fullname, presentation._fullname), locator=presentation._get_child_locator('definitions'), level=Issue.BETWEEN_TYPES)
            
            value = r
        else:
            context.validation.report('value of type "%s" is not a dict for "%s"' % (the_type._fullname, presentation._fullname), locator=value._locator, level=Issue.BETWEEN_TYPES)
            value = None
        
    # Check constraints?
    
    return value

#
# PropertyDefinition, AttributeDefinition, EntrySchema
#

def get_data_type(context, presentation, field_name, allow_none=False):
    """
    Returns the type, whether it's a complex data type (a DataType instance) or a primitive (a Python primitive type class).
    
    If the type is not specified, defaults to :class:`str`, per note in section 3.2.1.1 of the
    `TOSCA Simple Profile v1.0 specification <http://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.0/csprd02/TOSCA-Simple-Profile-YAML-v1.0-csprd02.html#_Toc379455072>`__
    """
    
    the_type = getattr(presentation, field_name)
    
    if the_type is None:
        if allow_none:
            return None
        else:
            return str
    
    # Try complex data type
    complex = context.presentation.data_types.get(the_type)
    if complex is not None:
        return complex 
    
    # Try primitive data type
    return get_primitive_data_type(the_type)

#
# ConstraintClause
#

def validate_constraint(context, presentation):
    """
    Makes sure the constraint clause is a dict with exactly one key and that, if appropriate for the constraint, the values match the data type.
    """
    
    # Must have exactly one key
    if len(presentation._raw) != 1:
        context.validation.report('constraint "%s" is not a dict with exactly one key %s' % (presentation._name, presentation._container._fullname), locator=presentation._locator, level=Issue.BETWEEN_FIELDS)
        return
    
    if presentation._is_typed():
        the_type = presentation._container._get_type(context) if hasattr(presentation._container, '_get_type') else presentation._container
        constraint_key = presentation._raw.keys()[0]
        value = presentation._raw.values()[0]
        
        if constraint_key == 'valid_values':
            # All "valid_values" must be coercible
            for v in value:
                coerce_value(context, presentation, the_type, None, None, v, constraint_key)
        elif constraint_key == 'in_range':
            v1, v2 = value
            
            # First "in_range" value must be coercible
            v1 = coerce_value(context, presentation, the_type, None, None, v1, constraint_key)
            
            if v2 != 'UNBOUNDED':
                # Second "in_range" value must be coercible
                v2 = coerce_value(context, presentation, the_type, None, None, v2, constraint_key)
                
                # Second "in_range" value must be greater than first
                if (v1 is not None) and (v2 is not None) and (v1 >= v2):
                    context.validation.report('upper bound of "in_range" constraint is not greater than the lower bound for "%s": %s >= %s' % (presentation._container._fullname, repr(v1), repr(v2)), locator=presentation._locator, level=Issue.FIELD)
        else:
            # Single value must be coercible
            coerce_value(context, presentation, the_type, None, None, value, constraint_key)

#
# Utils
#

PRIMITIVE_DATA_TYPES = {
    # YAML 1.2:
    'tag:yaml.org,2002:str': str,
    'tag:yaml.org,2002:integer': int,
    'tag:yaml.org,2002:float': float,
    'tag:yaml.org,2002:bool': bool,
    'tag:yaml.org,2002:null': None.__class__,

    # TOSCA aliases:
    'string': str,
    'integer': int,
    'float': float,
    'boolean': bool,
    'null': None.__class__}

@dsl_specification('3.2.1', 'tosca-simple-profile-1.0')
def get_primitive_data_type(the_type):
    """
    Many of the types we use in this profile are built-in types from the YAML 1.2 specification (i.e., those identified by the "tag:yaml.org,2002" version tag) [YAML-1.2].
    
    See the `TOSCA Simple Profile v1.0 specification <http://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.0/csprd02/TOSCA-Simple-Profile-YAML-v1.0-csprd02.html#_Toc373867862>`__
    """
    
    return PRIMITIVE_DATA_TYPES.get(the_type)

def get_data_type_name(the_type):
    if hasattr(the_type, '_name'):
        return the_type._name
    return '%s.%s' % (the_type.__module__, the_type.__name__) 

def coerce_value(context, presentation, the_type, entry_schema, constraints, value, constraint_key=None):
    if the_type is None:
        return None

    if the_type == None.__class__:
        if value is not None:
            context.validation.report('field "%s" is of type "null" but has a non-null value: %s' % (presentation._name, repr(value)), locator=presentation._locator, level=Issue.BETWEEN_FIELDS)
            return None
    
    # Delegate to 'coerce_value' extension
    if hasattr(the_type, '_get_extension'):
        coerce_value_fn_name = the_type._get_extension('coerce_value')
        if coerce_value_fn_name is not None:
            coerce_value_fn = import_fullname(coerce_value_fn_name)
            return coerce_value_fn(context, presentation, the_type, entry_schema, constraints, value, constraint_key)
    
    if hasattr(the_type, '_coerce_value'):
        # Complex type (likely a DataType instance)
        value = the_type._coerce_value(context, presentation, entry_schema, constraints, value, constraint_key)
    else:
        # Primitive type
        try:
            value = the_type(value)
        except ValueError as e:
            report_issue_for_bad_format(context, presentation, the_type, value, constraint_key, e)
            value = None
    
    return value

def coerce_to_class(context, presentation, the_type, entry_schema, constraints, value, constraint_key=None):
    try:
        value = the_type(entry_schema, constraints, value, constraint_key)
    except ValueError as e:
        report_issue_for_bad_format(context, presentation, the_type, value, constraint_key, e)
        value = None
    return value

def report_issue_for_bad_format(context, presentation, the_type, value, constraint_key, e):
    context.validation.report('%sfield "%s" is not a valid "%s": %s' % ('"%s" constraint of ' % constraint_key if constraint_key is not None else '', presentation._name or presentation._container._name, get_data_type_name(the_type), repr(value)), locator=presentation._locator, level=Issue.BETWEEN_FIELDS, exception=e)
