#!/usr/bin/env python3
"""
Internal helper script to run Python code with cProfile profiling.
This is called by run_python.sh to avoid cProfile argument parsing issues.
"""

import sys
import cProfile
import pstats
import runpy
import os

if len(sys.argv) < 3:
    print("Usage: _run_with_profile.py <profile_file> <sort_by> <top_n> <python_args...>", file=sys.stderr)
    sys.exit(1)

profile_file = sys.argv[1]
sort_by = sys.argv[2]
top_n = int(sys.argv[3])
python_args = sys.argv[4:]

if not python_args:
    print("Error: No Python script or module provided", file=sys.stderr)
    sys.exit(1)

# Create profiler
profiler = cProfile.Profile()

try:
    # Run the code
    if python_args[0] == '-m':
        # Module mode
        module_name = python_args[1]
        module_args = python_args[2:]
        sys.argv = [module_name] + module_args
        profiler.enable()
        runpy.run_module(module_name, run_name='__main__')
        profiler.disable()
    else:
        # Script mode - convert to absolute path if relative
        script_path = python_args[0]
        if not os.path.isabs(script_path):
            script_path = os.path.abspath(script_path)
        script_args = python_args[1:]
        sys.argv = [script_path] + script_args
        profiler.enable()
        runpy.run_path(script_path, run_name='__main__')
        profiler.disable()
    
    exit_code = 0
except SystemExit as e:
    profiler.disable()
    exit_code = e.code if e.code is not None else 0
except Exception as e:
    profiler.disable()
    # Save profile even on error, then re-raise
    try:
        profiler.dump_stats(profile_file)
    except:
        pass
    raise

# Always save profile and print results
profiler.dump_stats(profile_file)

# Print top N results
print("")
print(f"Profile results (top {top_n} consumers, sorted by {sort_by}):")
print("=" * 60)
stats = pstats.Stats(profile_file)
stats.sort_stats(sort_by)
stats.print_stats(top_n)

# Print regex search method stats if it exists
# The function appears as: {method 'search' of 're.Pattern' objects}
print("")
print("=" * 60)
print("Regex Pattern Search Method Stats:")
print("=" * 60)
# Filter for functions containing 'search' and 're.Pattern' or just 'search' method
# pstats print_stats accepts a regex pattern
stats.print_stats('.*search.*|.*re\.Pattern.*')

print("")
print(f"Full profile saved to: {profile_file}")
print(f"To view full profile: python3 -m pstats {profile_file}")

sys.exit(exit_code)

