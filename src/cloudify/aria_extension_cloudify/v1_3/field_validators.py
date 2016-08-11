
from aria.presentation import report_issue_for_unknown_type

#
# GroupDefinition
#

def node_templates_or_groups_validator(field, presentation, context):
    """
    Makes sure that the field's elements refer to either node templates or groups.

    Used with the :func:`field_validator` decorator for the "targets" field in :class:`PolicyDefinition`.
    """
    
    field._validate(presentation, context)
    
    values = getattr(presentation, field.name)
    if values is not None:
        for value in values:
            node_templates = context.presentation.node_templates or {}
            groups = context.presentation.groups or {}
            if (value not in node_templates) and (value not in groups):
                report_issue_for_unknown_type(context, presentation, 'node template or group', field.name, value)