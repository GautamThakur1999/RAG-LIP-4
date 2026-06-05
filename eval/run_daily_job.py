import subprocess
import sys
import os
import datetime

def run_script(script_path):
    print(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting {script_path}...")
    try:
        # Run the script using the current Python executable
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Success: {script_path}")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] FAILED: {script_path}")
        print("Output:", e.stdout)
        print("Error:", e.stderr)
        raise

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_file = os.path.join(base_dir, 'eval', 'daily_job.log')

    # Redirect stdout and stderr to the log file, while also keeping them on the console if running manually
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*50}\n")
        f.write(f"DAILY JOB STARTED AT {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*50}\n")

    # Define the sequence of scripts
    scripts_to_run = [
        os.path.join(base_dir, "src", "ingest", "fetch.py"),
        os.path.join(base_dir, "src", "ingest", "parse.py"),
        os.path.join(base_dir, "src", "ingest", "chunk.py"),
        os.path.join(base_dir, "src", "ingest", "build_index.py"),
        os.path.join(base_dir, "eval", "run_eval.py")
    ]

    for script in scripts_to_run:
        try:
            run_script(script)
        except Exception:
            print(f"Daily job aborted due to failure in {script}")
            sys.exit(1)

    print(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] DAILY JOB COMPLETED SUCCESSFULLY.")

if __name__ == "__main__":
    main()
