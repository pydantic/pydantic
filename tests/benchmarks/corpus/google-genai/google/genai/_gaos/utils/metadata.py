# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# pyformat: disable
# pylint: skip-file

# Frozen model corpus; modified from google-genai 2.34.0; see README.md and LICENSE.
from typing import Optional, Union
from dataclasses import dataclass

@dataclass
class SecurityMetadata:
    option: bool = False
    scheme: bool = False
    scheme_type: Optional[str] = None
    sub_type: Optional[str] = None
    field_name: Optional[str] = None
    composite: bool = False

@dataclass
class ParamMetadata:
    serialization: Optional[str] = None
    style: str = 'simple'
    explode: bool = False

@dataclass
class PathParamMetadata(ParamMetadata):
    pass

@dataclass
class QueryParamMetadata(ParamMetadata):
    style: str = 'form'
    explode: bool = True

@dataclass
class HeaderMetadata(ParamMetadata):
    pass

@dataclass
class RequestMetadata:
    media_type: str = 'application/octet-stream'

@dataclass
class MultipartFormMetadata:
    file: bool = False
    content: bool = False
    json: bool = False

@dataclass
class FormMetadata:
    json: bool = False
    style: str = 'form'
    explode: bool = True

class FieldMetadata:
    security: Optional[SecurityMetadata] = None
    path: Optional[PathParamMetadata] = None
    query: Optional[QueryParamMetadata] = None
    header: Optional[HeaderMetadata] = None
    request: Optional[RequestMetadata] = None
    form: Optional[FormMetadata] = None
    multipart: Optional[MultipartFormMetadata] = None

    def __init__(self, security: Optional[SecurityMetadata]=None, path: Optional[Union[PathParamMetadata, bool]]=None, query: Optional[Union[QueryParamMetadata, bool]]=None, header: Optional[Union[HeaderMetadata, bool]]=None, request: Optional[Union[RequestMetadata, bool]]=None, form: Optional[Union[FormMetadata, bool]]=None, multipart: Optional[Union[MultipartFormMetadata, bool]]=None):
        self.security = security
        self.path = PathParamMetadata() if isinstance(path, bool) else path
        self.query = QueryParamMetadata() if isinstance(query, bool) else query
        self.header = HeaderMetadata() if isinstance(header, bool) else header
        self.request = RequestMetadata() if isinstance(request, bool) else request
        self.form = FormMetadata() if isinstance(form, bool) else form
        self.multipart = MultipartFormMetadata() if isinstance(multipart, bool) else multipart
