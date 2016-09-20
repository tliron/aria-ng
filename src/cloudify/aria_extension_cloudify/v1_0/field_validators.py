#
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved.
# 
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
# 
#      http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#

from aria.presentation import report_issue_for_unknown_type
from .utils.data_types import get_primitive_data_type

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
            node_templates = context.presentation.presenter.node_templates or {}
            groups = context.presentation.presenter.groups or {}
            if (value not in node_templates) and (value not in groups):
                report_issue_for_unknown_type(context, presentation, 'node template or group', field.name)

#
# PropertyDefinition
#

def data_type_validator(field, presentation, context):
    """
    Makes sure that the field refers to a valid data type, whether complex or primitive. 
    
    Used with the :func:`field_validator` decorator for :code:`type` fields in :class:`PropertyDefinition`, :class:`AttributeDefinition`, :class:`ParameterDefinition`, and :class:`EntrySchema`.
    
    Extra behavior beyond validation: generated function returns true if field is a complex data type.
    """

    field._validate(presentation, context)

    value = getattr(presentation, field.name)
    if value is not None:
        # Can be a complex data type
        if (context.presentation.presenter.data_types is not None) and (value in context.presentation.presenter.data_types):
            return True
        # Can be a primitive data type
        if get_primitive_data_type(value) is None:
            report_issue_for_unknown_type(context, presentation, 'data type', field.name)

    return False
