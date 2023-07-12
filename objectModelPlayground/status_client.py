# ===================================================================================
# Copyright (C) 2019 Fraunhofer Gesellschaft. All rights reserved.
# ===================================================================================
# This Graphene software file is distributed by Fraunhofer Gesellschaft
# under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============LICENSE_END==========================================================
#!/usr/bin/env python
# ===================================================================================
# Copyright (C) 2021 Fraunhofer Gesellschaft, Peter Schueller. All rights reserved.
# ===================================================================================
# This Acumos software file is distributed by Fraunhofer Gesellschaft
# under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============LICENSE_END========================================================

import logging
import grpc

import objectModelPlayground.orchestrator_pb2 as orchestrator_pb2
import objectModelPlayground.orchestrator_pb2_grpc as orchestrator_pb2_grpc

logger = logging.getLogger("ObjectModelPlayground.status_client")


def get_status_string(status):
    return f'message: {status.message} - active_threads: {status.active_threads} - success: {status.success} - code: {status.code}'


def is_running(endpoint):
    logger.debug("connecting to orchestrator")
    channel = grpc.insecure_channel(endpoint)
    stub = orchestrator_pb2_grpc.OrchestratorStub(channel)
    logger.debug("calling get_status")
    status = stub.get_status(orchestrator_pb2.RunLabel(label="test"))
    logger.info("status orchestrator: "+get_status_string(status))
    return status.active_threads > 0
