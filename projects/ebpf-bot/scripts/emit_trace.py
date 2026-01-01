import logging
import pathlib
import sys
import time

project_root = pathlib.Path(__file__).resolve().parents[1]
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from ebpf_bot.pipeline import UnifiedPipeline


def main() -> None:
    logger = logging.getLogger("ebpf_bot.emit_trace")
    logger.info("Starting trace emission")
    UnifiedPipeline().collect_and_decide()
    logger.info("Trace emission complete")
    time.sleep(2)


if __name__ == "__main__":
    main()
