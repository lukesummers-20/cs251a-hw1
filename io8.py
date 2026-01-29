from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.private_l1_shared_l2_cache_hierarchy import (
    PrivateL1SharedL2CacheHierarchy,
)
from gem5.components.memory.single_channel import SingleChannelDDR4_2400
from gem5.simulate.simulator import Simulator
from gem5.isas import ISA

from gem5.components.processors.base_cpu_core import BaseCPUCore
from gem5.components.processors.base_cpu_processor import BaseCPUProcessor

from m5.objects import X86O3CPU
from m5.objects import X86MinorCPU

from gem5.resources.resource import BinaryResource

import argparse
parser = argparse.ArgumentParser(description="Parse arguments for gem5 O3 config")

parser.add_argument('--cmd', type=str, required=True, help='Binary to run')
parser.add_argument('--options', type=str, default="", help='Arguments for the binary')
args = parser.parse_args()


class MyInorderCore(BaseCPUCore):
    def __init__(self, width):
        super().__init__(X86MinorCPU(), ISA.X86)
        self.core.decodeInputWidth = width
        self.core.executeInputWidth = width
        self.core.executeIssueLimit = width
        self.core.executeCommitLimit = width



class MyInorderProcessor(BaseCPUProcessor):
    def __init__(self, width):
        """
        :param width: sets the width of decode, execute issue/commit stages.
        """
        cores = [MyInorderCore(width)]
        super().__init__(cores)



main_memory = SingleChannelDDR4_2400(size="2GB")

caches = PrivateL1SharedL2CacheHierarchy(
    l1d_size="32KiB",
    l1d_assoc=8,
    l1i_size="32KiB",
    l1i_assoc=8,
    l2_size="2MiB",
    l2_assoc=16,
)

my_io_processor = MyInorderProcessor(width=8)

board = SimpleBoard(
    processor=my_io_processor,
    memory=main_memory,
    cache_hierarchy=caches,
    clk_freq="2GHz",
)

binary = BinaryResource(local_path=args.cmd)
board.set_se_binary_workload(binary, arguments=args.options.split() if args.options else [])

simulator = Simulator(board)
simulator.run()