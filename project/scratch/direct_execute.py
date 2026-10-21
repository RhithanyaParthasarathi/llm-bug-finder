import json
import ast

def execute_repro_test(script_path, input_val):
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Split the file by the diff marker
    parts = content.split('# --- Post-diff Version (AI Modified) ---')
    pre_diff_code = parts[0]
    post_diff_code = parts[1]
    
    # Execute pre-diff
    pre_env = {}
    exec(pre_diff_code, pre_env)
    
    # Execute post-diff
    post_env = {}
    exec(post_diff_code, post_env)
    
    # Find the wrapper or target function name
    # The JSON has it but we can just use the known ones
    return pre_env, post_env

print("=== Independent Execution Verification ===")

# 1. broadinstitute__starrynight_01127134_transform
pre, post = execute_repro_test('project/results/benchmark/repro_broadinstitute__starrynight_01127134_transform.py', None)
print("\n[Test 1] broadinstitute__starrynight transform")
print("Input: ast='<any str>'")
print("Pre-diff output :", pre['transform_wrapper']('test'))
print("Post-diff output:", post['transform_wrapper']('test'))

# 2. tobypullan__CC_GH_Integration_229fa7e5_subtract_vectors
pre, post = execute_repro_test('project/results/benchmark/repro_tobypullan__CC_GH_Integration_229fa7e5_subtract_vectors.py', None)
print("\n[Test 2] tobypullan__CC_GH_Integration subtract_vectors")
print("Input: x='test', y='ing'")
print("Pre-diff output :", pre['subtract_vectors']('test', 'ing'))
try:
    print("Post-diff output:", post['subtract_vectors']('test', 'ing'))
except Exception as e:
    print("Post-diff output: Exception ->", type(e).__name__, str(e))
