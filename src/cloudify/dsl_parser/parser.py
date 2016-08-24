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

from aria import install_aria_extensions
from aria.consumption import ConsumptionContext
from aria.parsing import DefaultParser
from aria_extension_cloudify import Plan

install_aria_extensions()

def parse_from_path(dsl_file_path,
                    resources_base_url=None,
                    resolver=None,
                    validate_version=True,
                    additional_resource_sources=()):
    
    #print '!!! parse_from_path'
    #print dsl_file_path
    #print resources_base_url
    #print resolver
    #print validate_version
    #print additional_resource_sources
    
    parser = DefaultParser(dsl_file_path)
    context = ConsumptionContext()
    parser.parse_and_validate(context)
    if not context.validation.has_issues:
        context.deployment.plan = Plan(context).create_classic_plan()
    context.validation.dump_issues()
    return context
    
def parse(dsl_string,
          resources_base_url=None,
          resolver=None,
          validate_version=True):
    print '!!! parse'
    print dsl_string
    print resources_base_url
    print resolver
    print validate_version
