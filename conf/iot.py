"""
Copyright 2018 ShipChain, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import os
from .base import ENVIRONMENT

# IoT Thing <-> Device Settings
IOT_THING_INTEGRATION = ENVIRONMENT in ('PROD', 'DEMO', 'STAGE', 'DEV')
IOT_AWS_HOST = os.environ.get('IOT_AWS_HOST', None)
IOT_GATEWAY_STAGE = ENVIRONMENT.lower()
IOT_DEVICES_PAGE_SIZE = 10
