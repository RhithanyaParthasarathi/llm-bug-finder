#!/usr/bin/env python3
"""
Inspect the real schema of nuprl/AgentPack by streaming the first 5-10 records.
Prints the complete key structure, types, and truncated example values.
"""
import json
import sys
from datasets import load_dataset

sys.stdout.reconfigure(encoding='utf-8')


def truncate_val(val, max_len=120):
    if isinstance(val, str):
        if len(val) > max_len:
            return repr(val[:max_len] + "...")
        return repr(val)
    elif isinstance(val, list):
        if len(val) == 0:
            return "[]"
        sample = val[0]
        return f"list of {len(val)} items, first item ({type(sample).__name__}): {truncate_val(sample, max_len=80)}"
    elif isinstance(val, dict):
        keys = list(val.keys())
        return f"dict with keys {keys}"
    return repr(val)


def main():
    print("Streaming records from nuprl/AgentPack...")
    ds = load_dataset("nuprl/AgentPack", split="train", streaming=True)
    
    records = []
    for i, record in enumerate(ds):
        if i >= 8:
            break
        records.append(record)
        print(f"\n{'='*40} RECORD #{i+1} {'='*40}")
        print(f"Top-level keys ({len(record)}): {list(record.keys())}")
        for k, v in record.items():
            print(f"  [{k}] ({type(v).__name__}): {truncate_val(v)}")

    print(f"\n{'='*80}")
    print("SUMMARY OF SCHEMA")
    print(f"{'='*80}")
    if records:
        all_keys = set()
        for r in records:
            all_keys.update(r.keys())
        print(f"All observed keys across {len(records)} records: {sorted(list(all_keys))}")
        
        # Deep inspection of record 0
        r0 = records[0]
        print("\nDeep inspection of record 1:")
        for k, v in r0.items():
            print(f"\n--- Key: {k} (type: {type(v).__name__}) ---")
            if isinstance(v, (dict, list)):
                try:
                    print(json.dumps(v, indent=2, default=str)[:600])
                except Exception:
                    print(str(v)[:600])
            else:
                print(str(v)[:600])


if __name__ == "__main__":
    main()
