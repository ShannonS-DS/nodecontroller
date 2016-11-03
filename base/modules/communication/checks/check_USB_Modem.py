# Check that there is a "Wireless" or "Realtek" (LAN) device
# connected to the USB hub
def check():
	output = run_command(['lsusb'])
	for line in output:
		if (b"Wireless" in line) or \
			(b"Realtek" in line):
			return True, str(line)

	return False, 'None'