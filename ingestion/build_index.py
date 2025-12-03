
import argparse
from .index_rebuilder import run_full_reindex
import logging
logging.basicConfig(level=logging.INFO)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", type=str, default=None)
    parser.add_argument("--min-posts", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    res = run_full_reindex(category=args.category, min_posts=args.min_posts, force=args.force)
    print("Reindex result:", res)

if __name__ == "__main__":
    main()
