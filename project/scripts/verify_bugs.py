#!/usr/bin/env python3
"""
Verification script for 3 confirmed bugs found by the pipeline:
1. read_csv (AgentPack commit kym6464/clipboard-to-url@89c83dc3)
2. make_palindrome (HumanEval_10)
3. how_many_times (HumanEval_18)
"""
import hashlib


# --- Bug 1: read_csv ---
def hash_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()[:16]

def read_csv_old(value: str) -> tuple[bytes, str] | None:
    lines = value.strip().splitlines()
    assert len(lines) > 0, 'Expected non-empty CSV string'
    assert ',' in lines[0] or ';' in lines[0] or '\t' in lines[0], 'Expected comma, semicolon, or tab delimiter in header'
    content = value.encode()
    blob_name = f'{hash_bytes(content)}.csv'
    return (content, blob_name)

def read_csv_new(value: str) -> tuple[bytes, str] | None:
    lines = value.strip().splitlines()
    assert len(lines) >= 2, 'Expected at least 2 lines for CSV structure'
    delimiter = None
    for delim in [',', ';', '\t']:
        if delim in lines[0]:
            delimiter = delim
            break
    assert delimiter, 'Expected comma, semicolon, or tab delimiter in header'
    field_counts = []
    for line in lines[:min(5, len(lines))]:
        if not line.strip():
            continue
        field_count = line.count(delimiter) + 1
        field_counts.append(field_count)
    assert len(field_counts) >= 2, 'Expected at least 2 non-empty lines'
    assert len(set(field_counts)) == 1, 'Expected consistent field counts across lines'
    assert field_counts[0] >= 2, 'Expected at least 2 fields per line'
    content = value.encode()
    blob_name = f'{hash_bytes(content)}.csv'
    return (content, blob_name)


# --- Bug 2: make_palindrome ---
def is_palindrome(string: str) -> bool:
    return string == string[::-1]

def make_palindrome_old(string: str) -> str:
    if is_palindrome(string):
        return string
    for i in range(len(string)):
        if is_palindrome(string[i:]):
            return string + string[i-1::-1]

def make_palindrome_new(string: str) -> str:
    if is_palindrome(string):
        return string
    for i in range(len(string)-1, -1, -1):
        if is_palindrome(string[i:]):
            return string + string[:i][::-1]
    return string + string[:-1][::-1]


# --- Bug 3: how_many_times ---
def how_many_times_old(string: str, substring: str) -> int:
    occurences = 0
    for i in range(len(string)):
        if string[i:].startswith(substring):
            occurences += 1
    return occurences

def how_many_times_new(string: str, substring: str) -> int:
    count = 0
    if len(substring) == 0:
        return 0
    for i in range(len(string)-len(substring)+1):
        if string[i:i+len(substring)] == substring:
            count += 1
    return count


def run_tests():
    print("=" * 70)
    print("BUG 1: read_csv (AgentPack kym6464/clipboard-to-url@89c83dc3)")
    input1 = "user_id,username,email"
    print(f"Input: value = {input1!r} (valid single-line CSV header/record)")
    try:
        res_old = read_csv_old(input1)
        print(f"  Old version output: {res_old}")
    except Exception as e:
        print(f"  Old version raised: {type(e).__name__}: {e}")
    try:
        res_new = read_csv_new(input1)
        print(f"  New version output: {res_new}")
    except Exception as e:
        print(f"  New version raised: {type(e).__name__}: {e}")

    print("\n" + "=" * 70)
    print("BUG 2: make_palindrome (HumanEval_10)")
    input2 = "abac"
    print(f"Input: string = {input2!r}")
    res_old2 = make_palindrome_old(input2)
    res_new2 = make_palindrome_new(input2)
    print(f"  Old version (longest palindrome suffix 'aba' -> suffix 'c' at i=3 -> 'abacaba'): {res_old2!r}")
    print(f"  New version (searches in reverse, finds 'c' at i=3 first -> 'abacaba' vs 'abacaba'?): {res_new2!r}")
    input2_b = "xyxza"
    print(f"Input: string = {input2_b!r}")
    print(f"  Old version: {make_palindrome_old(input2_b)!r}")
    print(f"  New version: {make_palindrome_new(input2_b)!r}")

    print("\n" + "=" * 70)
    print("BUG 3: how_many_times (HumanEval_18)")
    input3 = ("banana", "")
    print(f"Input: string = {input3[0]!r}, substring = {input3[1]!r}")
    res_old3 = how_many_times_old(*input3)
    res_new3 = how_many_times_new(*input3)
    print(f"  Old version: {res_old3}")
    print(f"  New version: {res_new3}")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
