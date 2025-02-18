# Feetech

A more ergonomic library for controlling Feetech servos.

Install by running:

```
pip install -e .
```

Example usage:

```
import feetech
import time

client = feetech.Client('/dev/ttyACM0')
client.connect() # can also use `with feetech.Client('/dev/ttyACM0') as client:` to avoid needing to call connect/disconnect

motor_id = 1

# Torque enable servo 1
client.enable(motor_id)

# Read the current motor position in degrees
pos = client.read_present_posiiton(motor_id)

# Rotate the servo 15 degrees
client.write_goal_position(motor_id, pos + 15)

time.sleep(1)

new_pos = client.read_present_position(motor_id)
print(f'moved servo from {pos} to {new_pos} degrees')

client.disconnect()
```
