"""Frozen snapshot by default; --download reconstructs from authoritative sources."""
import argparse
from study import main

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--download',action='store_true')
    args=p.parse_args()
    if args.download:
        from download_data import main as download
        download()
    main()
