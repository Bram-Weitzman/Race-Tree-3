##Progress Bar
import sys

def print_progress(current, total, prefix='', suffix='', length=40):
    percent = f"{100 * (current / float(total)):.1f}"
    filled_len = int(length * current // total)
    bar = '█' * filled_len + '-' * (length - filled_len)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()

    if current == total:
        print()  # Move to next line

#✅ 2. Use It in a Loop
#Example usage during lap processing:
#

total_laps = 18  # however many laps you have

for lap_num in range(1, total_laps + 1):
    # Simulate processing
    print_progress(lap_num, total_laps, prefix='Progress', suffix=f'Lap {lap_num}/{total_laps}')
    # your code here like fetching or processing lap_data