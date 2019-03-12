from hand_cost_closed.protocol import ClosedHandCostProtocol
from hand_cost_open.model import OpenHandCostModel


class ClosedHandCostModel(OpenHandCostModel):
    input_size = ClosedHandCostProtocol.input_size
    output_size = ClosedHandCostProtocol.output_size
