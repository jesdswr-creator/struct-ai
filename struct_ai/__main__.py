"""Module launcher with frozen multiprocessing support. Units: none."""

import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()
    from struct_ai.app_entry import main

    raise SystemExit(main())
