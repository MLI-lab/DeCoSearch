# Copyright 2023 DeepMind Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Configuration of a FunSearch experiment. Only data classes no methods"""
import dataclasses

@dataclasses.dataclass(frozen=True)
class RabbitMQConfig:
    """Configuration for RabbitMQ connection.

    Attributes:
      host: The hostname of the RabbitMQ server.
      port: The port of the RabbitMQ server.
      username: Username for authentication with the RabbitMQ server.
      password: Password for authentication with the RabbitMQ server.
    """
    host: str = 'mcml-dgx-001.ai.lrz.de' # change to localhost if run from other server than yosemite where rabbitmq container is located 
    port: int = 5691 # to connect on port 5672 need to have tunnel on server script is running to conenct to yosemite ssh -L 5672:localhost:6061 -J ge74met@login01.msv.ei.tum.de:3022 franziska@yosemite.msv.ei.tum.de
    username: str = 'myuser' # 'myuser' for lrz
    password: str = 'mypassword' # 'mypassword' for lrz
    vhost = "temp_1" #for lrz use vhost
    
    ##to connect when running on lrz server use on local machine: ssh -L 15690:localhost:15690 ge74met@login01.msv.ei.tum.de -p 3022
@dataclasses.dataclass(frozen=True)
class ProgramsDatabaseConfig:
  """Configuration of a ProgramsDatabase.

  Attributes:
    functions_per_prompt: Number of previous programs to include in prompts.
    num_islands: Number of islands to maintain as a diversity mechanism.
    reset_period: How often (in seconds) the weakest islands should be reset.
    cluster_sampling_temperature_init: Initial temperature for softmax sampling of clusters within an island.
    cluster_sampling_temperature_period: Period of linear decay of the cluster sampling temperature.
  """
  functions_per_prompt: int = 2
  num_islands: int = 10
  reset_period: int = None
  reset_programs: int= 1200
  cluster_sampling_temperature_init: float = 0.1 # changed from 0.1 to 1
  cluster_sampling_temperature_period: int = 30_000 # after 30_000 reset 
  prompts_per_batch= 10



@dataclasses.dataclass 
class Config:
  """Configuration of a FunSearch experiment.

  Attributes:
    programs_database: Configuration of the evolutionary algorithm.
    num_samplers: Number of independent Samplers in the experiment. 
    num_evaluators: Number of independent program Evaluators in the experiment..
    samples_per_prompt: How many independently sampled program continuations to obtain for each prompt.
  """ 
  # In this case, default_factory=ProgramsDatabaseConfig means that calling ProgramsDatabaseConfig() (without any arguments) will provide the default value.
  programs_database: ProgramsDatabaseConfig = dataclasses.field(default_factory=ProgramsDatabaseConfig)
  rabbitmq: RabbitMQConfig = dataclasses.field(default_factory=RabbitMQConfig)
  num_samplers: int = 1
  num_evaluators: int = 8
  num_pdb: int = 1
  samples_per_prompt: int = 2
  temperature: float = 0.9444444444444444
  max_new_tokens: int = 246
  top_p: float =  0.7777777777777778 
  repetition_penalty: float = 1.222222
  api_key='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'


