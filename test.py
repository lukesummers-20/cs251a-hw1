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


class MyOutOfOrderCore(BaseCPUCore):
    def __init__(self, width, rob_size, num_int_regs, num_fp_regs):
        super().__init__(X86O3CPU(), ISA.X86)
        self.core.fetchWidth = width
        self.core.decodeWidth = width
        self.core.renameWidth = width
        self.core.dispatchWidth = width
        self.core.issueWidth = width
        self.core.wbWidth = 8
        self.core.commitWidth = 8

        self.core.numROBEntries = rob_size

        self.core.numPhysIntRegs = num_int_regs
        self.core.numPhysFloatRegs = num_fp_regs

        self.core.LQEntries = 128
        self.core.SQEntries = 128


class MyInorderProcessor(BaseCPUProcessor):
    def __init__(self, width):
        """
        :param width: sets the width of decode, execute issue/commit stages.
        """
        cores = [MyInorderCore(width)]
        super().__init__(cores)


class MyOutOfOrderProcessor(BaseCPUProcessor):
    def __init__(self, width, rob_size, num_int_regs, num_fp_regs):
        """
        :param width: sets the width of fetch, decode, rename, issue, wb, and
        commit stages.
        :param rob_size: determines the number of entries in the reorder buffer.
        :param num_int_regs: determines the size of the integer register file.
        :param num_fp_regs: determines the size of the vector/floating point
        register file.
        """
        cores = [MyOutOfOrderCore(width, rob_size, num_int_regs, num_fp_regs)]
        super().__init__(cores)


main_memory = SingleChannelDDR4_2400(size="2GB")

caches = PrivateL1SharedL2CacheHierarchy(
    l1d_size="32KiB",
    l1d_assoc=8,
    l1i_size="32KiB",
    l1i_assoc=8,
    l2_size="256KiB",
    l2_assoc=16,
)

my_ooo_processor = MyOutOfOrderProcessor(
    width=8, rob_size=192, num_int_regs=256, num_fp_regs=256
)

board = SimpleBoard(
    processor=my_ooo_processor,
    memory=main_memory,
    cache_hierarchy=caches,
    clk_freq="3GHz",
)

binary = BinaryResource(local_path=args.cmd)
board.set_se_binary_workload(binary, arguments=args.options.split() if args.options else [])

simulator = Simulator(board)
simulator.run()