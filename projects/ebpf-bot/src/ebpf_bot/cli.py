# cli.py

from ebpf_bot.pipeline import UnifiedPipeline

def main():
    print("[CLI] Starting eBPF Coverage Bot...")
    pipeline = UnifiedPipeline()
    next_probe = pipeline.collect_and_decide()
    print(f"[CLI] Next probe to activate: {next_probe}")

if __name__ == "__main__":
    main()
