#!/usr/bin/env python3
import os.path
from typing import List
from aws_cdk import core
from infra.networking import LandingZone, EuroMapRed
src_root_dir = os.path.join(os.path.dirname(__file__))

eu_west_1 = core.Environment(region="eu-west-1", account='581361757134')

class NetworkingApp(core.App):
  def __init__(self, **kwargs) ->None:
    super().__init__(**kwargs)

    self.euro = EuroMapRed(self,'EuroMapRed', env=eu_west_1)

  @property
  def zones(self)->List[LandingZone]:
    return [ self.euro ]

app = NetworkingApp()
app.synth()
