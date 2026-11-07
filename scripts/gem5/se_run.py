"""gem5 syscall-emulation run for the CS 263 CPython engine study.

Run inside the gem5 image (gem5 v26.0.0.0, X86 build):

    gem5 -d OUTDIR scripts/gem5/se_run.py --hw HW.json --binary BIN \
        [--stdout-file F] [--stderr-file F] [--env K=V ...] -- [ARGS ...]

HW.json is a fully resolved hardware spec (see configs/hardware/baseline.json).
Every parameter the spec names is set explicitly; anything it does not name
keeps the gem5 default and appears in OUTDIR/config.ini. After the guest exits,
OUTDIR/sim_exit.json records the exit cause, guest exit code, and tick.

Usually invoked through scripts/run_gem5.py, which also writes the run
manifest and checks benchmark output.
"""

import argparse
import json
from pathlib import Path

import m5.objects
from m5.objects import L2XBar
from m5.params import NULL

from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.caches.l1dcache import L1DCache
from gem5.components.cachehierarchies.classic.caches.l1icache import L1ICache
from gem5.components.cachehierarchies.classic.caches.l2cache import L2Cache
from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import (
    PrivateL1PrivateL2CacheHierarchy,
)
from gem5.components import memory as gem5_memory
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA
from gem5.resources.resource import BinaryResource
from gem5.simulate.simulator import Simulator

CACHE_KEYS = (
    "size",
    "assoc",
    "tag_latency",
    "data_latency",
    "response_latency",
    "mshrs",
    "tgts_per_mshr",
)


def make_cache(cls, spec):
    """Build a stdlib cache with every spec'd parameter set explicitly."""
    missing = [k for k in CACHE_KEYS if k not in spec]
    if missing:
        raise ValueError(f"cache spec missing {missing}: {spec}")
    cache = cls(**{k: spec[k] for k in CACHE_KEYS})
    prefetcher = spec.get("prefetcher", "none")
    if prefetcher == "none":
        cache.prefetcher = NULL
    else:
        cache.prefetcher = getattr(m5.objects, prefetcher)()
    return cache


class SpecPrivateL1PrivateL2(PrivateL1PrivateL2CacheHierarchy):
    """Stdlib private L1/L2 hierarchy with spec-controlled cache parameters.

    The stdlib version hard-codes associativity and attaches stride
    prefetchers; this subclass mirrors its wiring but takes all cache
    parameters from the hardware spec.
    """

    def __init__(self, spec):
        super().__init__(
            l1i_size=spec["l1i"]["size"],
            l1d_size=spec["l1d"]["size"],
            l2_size=spec["l2"]["size"],
        )
        self._spec = spec

    def incorporate_cache(self, board):
        board.connect_system_port(self.membus.cpu_side_ports)
        for _, port in board.get_mem_ports():
            self.membus.mem_side_ports = port

        cores = board.get_processor().get_cores()
        self.l2buses = [L2XBar() for _ in cores]
        for i, cpu in enumerate(cores):
            l2_node = self.add_root_child(
                f"l2-cache-{i}", make_cache(L2Cache, self._spec["l2"])
            )
            l1i_node = l2_node.add_child(
                f"l1i-cache-{i}", make_cache(L1ICache, self._spec["l1i"])
            )
            l1d_node = l2_node.add_child(
                f"l1d-cache-{i}", make_cache(L1DCache, self._spec["l1d"])
            )
            self.l2buses[i].mem_side_ports = l2_node.cache.cpu_side
            self.membus.cpu_side_ports = l2_node.cache.mem_side
            l1i_node.cache.mem_side = self.l2buses[i].cpu_side_ports
            l1d_node.cache.mem_side = self.l2buses[i].cpu_side_ports
            cpu.connect_icache(l1i_node.cache.cpu_side)
            cpu.connect_dcache(l1d_node.cache.cpu_side)
            self._connect_table_walker(i, cpu)
            if board.get_processor().get_isa() == ISA.X86:
                cpu.connect_interrupt(
                    self.membus.mem_side_ports, self.membus.cpu_side_ports
                )
            else:
                cpu.connect_interrupt()

        if board.has_coherent_io():
            self._setup_io_cache(board)


def make_branch_predictor(spec):
    def build(section, default_class=None):
        cls_name = section.get("class", default_class)
        return getattr(m5.objects, cls_name)(**section.get("params", {}))

    return m5.objects.BranchPredictor(
        conditionalBranchPred=build(spec["conditional"]),
        btb=build(spec["btb"]),
        ras=build(spec["ras"], "ReturnAddrStack"),
        indirectBranchPred=build(spec["indirect"]),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hw", required=True, type=Path)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--stdout-file", type=Path)
    parser.add_argument("--stderr-file", type=Path)
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("args", nargs="*")
    opts = parser.parse_args()

    hw = json.loads(opts.hw.read_text())
    if hw["isa"] != "X86" or hw["mode"] != "SE":
        raise ValueError("this script supports only X86 syscall emulation")
    cpu = hw["cpu"]

    processor = SimpleProcessor(
        cpu_type=getattr(CPUTypes, cpu["type"]),
        isa=ISA.X86,
        num_cores=cpu["num_cores"],
        clk_freq=cpu["clock"],
    )
    if cpu["type"] == "O3":
        for core in processor.get_cores():
            core.get_simobject().branchPred = make_branch_predictor(
                hw["branch_predictor"]
            )
    elif "branch_predictor" in hw:
        raise ValueError("branch_predictor is only applied to O3 cores")

    memory_cls = getattr(gem5_memory, hw["memory"]["class"])
    board = SimpleBoard(
        clk_freq=cpu["clock"],
        processor=processor,
        memory=memory_cls(size=hw["memory"]["size"]),
        cache_hierarchy=SpecPrivateL1PrivateL2(hw["caches"]),
    )
    board.set_se_binary_workload(
        BinaryResource(local_path=opts.binary.as_posix()),
        arguments=opts.args,
        env_list=opts.env,
        stdout_file=opts.stdout_file,
        stderr_file=opts.stderr_file,
    )

    simulator = Simulator(board=board)
    simulator.run()

    result = {
        "exit_cause": simulator.get_last_exit_event_cause(),
        "exit_code": simulator.get_last_exit_event_code(),
        "final_tick": simulator.get_current_tick(),
    }
    outdir = Path(m5.options.outdir)
    (outdir / "sim_exit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"se_run: {json.dumps(result)}")


main()
