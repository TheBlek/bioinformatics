import utils
import sys

# Read input from stdin
output = sys.stdin.read()

# Extract the percentage
percentage = utils.extract_mapped_percentage(output)

if percentage is None:
    print("Error: No mapped percentage found", file=sys.stderr)
    sys.exit(1)

if percentage < 90:
    print("Error: Mapped percentage si too low", file=sys.stderr)
    sys.exit(1)

print("Quality is fine")
