# eBPF Probes

This directory contains Go code for the eBPF runtime sensing layer of
CAAT.  eBPF (extended Berkeley Packet Filter) allows us to attach
programs to kernel events such as system calls, network packets and
tracepoints with minimal overhead.  CAAT uses eBPF probes to
collect detailed system telemetry that feeds into the policy and
budget engines.

The current implementation is a skeleton demonstrating how such
probes can be loaded and managed.  Building and loading eBPF
programs typically requires Linux kernel version 5.8 or later and
the `github.com/cilium/ebpf` Go library.  If these dependencies
are not available, the code will not build; however the structure
serves as a reference for future implementation.