import enum
import math
import sys

from scservo_sdk import PortHandler, PacketHandler, COMM_SUCCESS

class Register(enum.Enum):
    ID = 5
    MaxTorque = 16
    PositionCorrection = 31
    TorqueEnable = 40
    GoalPosition = 42
    TorqueLimit = 48
    WriteLock = 55
    PresentPosition = 56
    CurrentLoad = 60
    CurrentVoltage = 62
    CurrentTemperature = 63

multibyte_registers = {
    Register.MaxTorque,
    Register.PositionCorrection,
    Register.TorqueEnable,
    Register.GoalPosition,
    Register.TorqueLimit,
    Register.PresentPosition,
    Register.CurrentLoad,
}

class Client:
    def __init__(self, port: str):
        self.port_handler = PortHandler(port)
        # SCS uses big endian, but other lines use little endian. For some reason 0 means little endian and anything else means big
        # Right now support non-SCS only
        self.packet_handler = PacketHandler(0)
        self.connected = False

    def connect(self):
        self.port_handler.openPort()
        self.connected = True

    def disconnect(self):
        self.port_handler.closePort()
        self.connected = False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()

    def update_id(self, old_id: int, new_id: int):
        self.write_register(old_id, Register.WriteLock, 0)
        self.write_register(old_id, Register.ID, new_id)
        self.write_register(new_id, Register.WriteLock, 1)

    def zero_motor(self, motor_id: int):
        self.write_register(motor_id, Register.PositionCorrection, 0)
        pos = self.read_register(motor_id, Register.PresentPosition)

        new_offset = 0
        if pos <= 2047:
            new_offset = pos
        else:
            new_offset = 2048 + 4096 - pos

        self.write_register(motor_id, Register.WriteLock, 0)
        self.write_register(motor_id, Register.PositionCorrection, new_offset)
        self.write_register(motor_id, Register.WriteLock, 1)

    def enable(self, motor_id: int):
        self.write_register(motor_id, Register.TorqueEnable, 1)

    def disable(self, motor_id: int):
        self.write_register(motor_id, Register.TorqueEnable, 0)

    def enabled(self, motor_id: int) -> bool:
        return self.read_register(motor_id, Register.TorqueEnable) == 1

    def write_goal_position(self, motor_id: int, angle: float):
        if angle < 0 or angle > 2 * math.pi:
            raise ValueError('Goal position must be between 0 and 2*pi')
        ft_position = int(angle / (2 * math.pi) * 4096)
        self.write_register(motor_id, Register.GoalPosition, ft_position)

    def read_goal_position(self, motor_id: int) -> float:
        ft_position = self.read_register(motor_id, Register.GoalPosition)
        return float(ft_position) * (2 * math.pi) / 4096

    def read_present_position(self, motor_id: int) -> float:
        ft_position = self.read_register(motor_id, Register.PresentPosition)
        return float(ft_position) * (2 * math.pi) / 4096

    def read_torque_limit_percent(self, motor_id: int) -> float:
        return float(self.read_register(motor_id, Register.TorqueLimit)) / 1000

    def write_torque_limit_percent(self, motor_id: int, torque_limit: float):
        reg_value = int(torque_limit * 1000)
        self.write_register(motor_id, Register.TorqueLimit, reg_value)

    def read_load_percent(self, motor_id: int) -> float:
        val = self.read_register(motor_id, Register.CurrentLoad)
        if val > 1000:
            val -= 1000
        return float(val) / 1000

    def read_temp(self, motor_id: int) -> int:
        return self.read_register(motor_id, Register.CurrentTemperature)

    def read_register(self, motor_id: int, register):
        self._check_connected()
        if register in multibyte_registers:
            result, comm_result, error = self.packet_handler.read2ByteTxRx(self.port_handler, motor_id, register.value)
        else:
            result, comm_result, error = self.packet_handler.read1ByteTxRx(self.port_handler, motor_id, register.value)
        if comm_result != COMM_SUCCESS:
            raise ConnectionError(comm_result)
        elif error != 0:
            raise Exception(error)

        return result

    def write_register(self, motor_id: int, register, value):
        self._check_connected()
        if register in multibyte_registers:
            comm_result, error = self.packet_handler.write2ByteTxRx(self.port_handler, motor_id, register.value, value)
        else:
            comm_result, error = self.packet_handler.write1ByteTxRx(self.port_handler, motor_id, register.value, value)
        if comm_result != COMM_SUCCESS:
            raise ConnectionError(comm_result)
        elif error == 1:
            print('error: voltage', file=sys.stderr)
        elif error != 0:
            raise Exception(error)

    def _check_connected(self):
        if not self.connected:
            raise Exception("Client is not connected, call connect() first")