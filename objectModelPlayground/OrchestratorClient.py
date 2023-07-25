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

import grpc
import logging
import threading
import traceback
import sys


import objectModelPlayground.orchestrator_pb2 as orchestrator_pb2
import objectModelPlayground.orchestrator_pb2_grpc as orchestrator_pb2_grpc




DEFAULT_QUEUE_SIZE = 0
DEFAULT_ITERATIONS = 0
observer_namefilter = '.*'
observer_componentfilter = '.*'



class OrchestrationObserver(threading.Thread):
    def __init__(self, endpoint: str, message_display: bool, server_configuration: orchestrator_pb2.OrchestrationObservationConfiguration):
        super().__init__(daemon=False)
        self.endpoint = endpoint
        self.message_display = message_display
        assert isinstance(server_configuration, orchestrator_pb2.OrchestrationObservationConfiguration)
        self.server_configuration = server_configuration

    def run(self):
        try:
            print("observing")
            channel = grpc.insecure_channel(self.endpoint)
            stub = orchestrator_pb2_grpc.OrchestratorStub(channel)
            for event in stub.observe(self.server_configuration):

                # omit event.run because we do not use it yet
                if event.name == 'exception':

                    # display exceptions in a special way
                    print("%s produced exception in method %s with traceback\n%s" % (
                        event.component, event.detail['method'], event.detail['traceback']))

                else:

                    if self.message_display:
                        display_detail = event.detail
                    else:
                        display_detail = {
                            k: v
                            for k, v in event.detail.items()
                            if k not in 'message'
                        }

                    # generic display
                    detailstr = ''
                    if len(display_detail) > 0:
                        detailstr = ' with details ' + ' '.join(
                            [f"{k}={repr(v)}" for k, v in display_detail.items()]
                        )
                    print("%s produced event '%s'%s" % (event.component, event.name, detailstr)) # ToDo: save/observe these for issue #53 to see whether pipeline is running
                    # if event.name == RPC.finished..

                    ### Microservices
                    # print(message)
                    # if "[svc=OCR,rpc=ocr] produced event 'thread.terminate'" in message:
                    #     print("Pipeline finished. Terminating now.")
                    #     raise KeyboardInterrupt'''

                    ### Monolith
                    # print(message)
                    # if "[svc=Recognaize,rpc=recognaize] produced event 'thread.terminate'" in message:
                    #     print("Pipeline finished. Terminating now.")
                    #     raise KeyboardInterrupt'''


                sys.stdout.flush()

        except KeyboardInterrupt:
            # CTRL+C or SIGTERM should just terminate, not write any exception info
            pass
        except Exception:
            logging.error("observer thread terminated with exception: %s", traceback.format_exc())


def observe(endpoint: str, message_display, server_configuration) -> threading.Thread:
    '''
    create observer thread and start
    '''
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

def observee(endpoint):
    print("Calling observe stub..")
    server_configuration = orchestrator_pb2.OrchestrationObservationConfiguration(
        name_regex=observer_namefilter,
        component_regex=observer_componentfilter
    )
    oot = observe(endpoint=endpoint, message_display=False, server_configuration=server_configuration)
    return oot


if __name__ == '__main__':
    logging.basicConfig()
    init_run()
    observe()



# pathSolutions = "solutions/"
# userName = "CheckMorePipelines"
# namespace = "pipelinebmono-407f63f861af4fbbb901263aafd36c22"
# namespace = "recognaizestream-c907a48be05c4a778f4c7d242509dde4"
# namespace = "ai4industrypilot-5fac072e53bf48e6a7d883e38b36e1f7"
# orchestrator = Orchestrator(pathSolutions + "/" + userName + "/" + namespace)



# port = 30012
# port = 30039
# port = 30002

# endpoint = 'localhost:{}'.format(port)
