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
from __future__ import print_function

import logging
import threading
import grpc
import objectModelPlayground.orchestrator_pb2 as orchestrator_pb2
import objectModelPlayground.orchestrator_pb2_grpc as orchestrator_pb2_grpc

from typing import Dict, Any



DEFAULT_QUEUE_SIZE = 0
DEFAULT_ITERATIONS = 0
observer_namefilter = '.*'
observer_componentfilter = '.*'



class OrchestrationObserver(threading.Thread):
    """
    Observer class that connects to a gRPC server to observe events.
    """
    def __init__(self, endpoint: str, message_display: bool, server_configuration: orchestrator_pb2.OrchestrationObservationConfiguration):
        super().__init__(daemon=False)
        self.endpoint = endpoint
        self.message_display = message_display
        assert isinstance(server_configuration, orchestrator_pb2.OrchestrationObservationConfiguration)
        self.server_configuration = server_configuration
        self.stop_event = threading.Event()

    def run(self) -> None:
        """Thread's run method."""
        try:
            logging.info("observing")
            channel = grpc.insecure_channel(self.endpoint)
            stub = orchestrator_pb2_grpc.OrchestratorStub(channel)
            self.observe_events(stub)

        except KeyboardInterrupt:
            pass
        except Exception as e:
            logging.error(f"observer thread terminated with exception: {e}", exc_info=True)

    def observe_events(self, stub) -> None:
        for event in stub.observe(self.server_configuration):
            if self.stop_event.is_set():
                logging.info("Stopping the observer thread.")
                break
            self.handle_event(event)
        
    def handle_event(self, event) -> None:
        if event.name == 'exception':
            logging.warning("%s produced exception in method %s with traceback\n%s", 
                            event.component, event.detail['method'], event.detail['traceback'])
        else:
            display_detail: Dict[str, Any] = event.detail if self.message_display else {
                k: v for k, v in event.detail.items() if k not in 'message'
            }
            detailstr = ' '.join(f"{k}={repr(v)}" for k, v in display_detail.items())
            logging.info("%s produced event '%s' with details %s", event.component, event.name, detailstr)

    def stop(self):
        self.stop_event.set()

def observe(endpoint: str) -> threading.Thread:
    """
    Create observer thread and start it.
    """
    message_display = False
    server_configuration = orchestrator_pb2.OrchestrationObservationConfiguration(
        name_regex=observer_namefilter,
        component_regex=observer_componentfilter
    )
    oot = OrchestrationObserver(endpoint, message_display, server_configuration)
    oot.start()
    return oot

def init_run(orchestrator, endpoint):
    print("Calling init and run stubs..")
    with grpc.insecure_channel(endpoint) as channel:
        stub = orchestrator_pb2_grpc.OrchestratorStub(channel)

        print(stub.initialize(orchestrator_pb2.OrchestrationConfiguration(
                    blueprint=orchestrator.get_blueprint(),
                    dockerinfo=orchestrator.get_docker_info(),
                    protofiles=orchestrator.get_protofiles(),
                    queuesize=DEFAULT_QUEUE_SIZE,
                    iterations=DEFAULT_ITERATIONS,
                    )))
        print(stub.run(orchestrator_pb2.RunLabel()))
        


if __name__ == '__main__':
    logging.basicConfig()
    init_run()
    observe()

