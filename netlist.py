import copy
import os
from typing import Union, List


class Device:

    pos_attributes = {'name', 'PLUS', 'MINUS', 'Model', 'S', 'D', 'G', 'B'}

    def set_attribute(self, attribute: str, value: str) -> None:
        self.__setattr__(attribute, value)

    def __repr__(self) -> str:
        info = [v if v.isalpha() or k in self.pos_attributes else f'{k}={v}' for k, v in self.__dict__.items()]
        return f"{type(self).__name__}: {' '.join(info)}"

    def __str__(self) -> str:
        return self.__repr__()


class Diode(Device):
    def __init__(self, name: str, plus: str, minus: str, model: str, **kwargs: str):
        self.name = name
        self.PLUS = plus
        self.MINUS = minus
        self.Model = model

        for k, v in kwargs.items():
            self.__setattr__(k, v)


class Transistor(Device):
    def __init__(self, name: str, source: str, drain: str, gate: str, base: str, model: str, **kwargs: str):
        self.name = name
        self.S = source
        self.D = drain
        self.G = gate
        self.B = base
        self.Model = model

        for k, v in kwargs.items():
            self.__setattr__(k, v)


class Cell:
    def __init__(self, name: str, description: str, equation: str, pin_order: List[str],
                 instances: List[Union[Diode, Transistor]]):
        self.name = name
        self.description = description
        self.equation = equation
        self.pin_order = pin_order
        self.instances = copy.deepcopy(instances)

    def get_pin_order(self) -> str:
        return ' '.join(self.pin_order)

    def set_pin_order(self, pin_order: str) -> None:
        self.pin_order = pin_order.split()

    def get_all_instances(self) -> str:
        return '\n'.join(map(str, self.instances))

    def get_instance(self, instance_name: str) -> Union[Diode, Transistor]:
        for instance in self.instances:
            if instance.name == instance_name:
                return instance

    def __repr__(self) -> str:
        return f'{self.name} (Description: {self.description}, Equation: {self.equation})'


class Netlist:
    def __init__(self):
        self.cell_list = []

    def read(self, path_to_file: Union[str, os.PathLike]) -> None:
        instances = []
        with open(path_to_file, 'r') as nl:
            lines = nl.readlines()
            for line in lines:
                if line.startswith('*'):
                    if line.find('Description') != -1:
                        description = line.split(':', maxsplit=1)[-1].strip()
                    elif line.find('Equation') != -1:
                        equation = line.split(':', maxsplit=1)[-1].strip()
                elif line.startswith('.subckt'):
                    cell_info = line.split()
                    cell_name = cell_info[1]
                    pin_order = cell_info[2:]
                elif line.startswith('M'):
                    instances.append(self.read_transistor(line))
                elif line.startswith('D'):
                    instances.append(self.read_diode(line))
                elif line.startswith('.ends'):
                    self.cell_list.append(Cell(cell_name, description, equation, pin_order, instances))
                    instances.clear()

    def write(self, path_to_file: Union[str, os.PathLike]) -> None:
        lines = []
        for cell in self.cell_list:
            lines.append(f'*      Description : {cell.description}\n')
            lines.append(f'*      Equation    : {cell.equation}\n')
            lines.append(f'.subckt {cell.name} {cell.get_pin_order()}\n')
            for device in cell.instances:
                lines.append(f'{str(device).split(":", maxsplit=1)[-1].strip()}\n')
            lines.append('.ends\n\n')
        with open(path_to_file, 'w') as nl:
            nl.writelines(lines)

    def get_cell(self, cell_name: str) -> Cell:
        for cell in self.cell_list:
            if cell.name == cell_name:
                return cell

    def get_all_cells(self) -> List[Cell]:
        return self.cell_list

    @staticmethod
    def read_transistor(line_with_transistor_params: str) -> Transistor:
        params = line_with_transistor_params.split()
        pos_params = params[:6]
        kw_params = {}
        for elem in params[6:]:
            k, v = elem.split('=')
            kw_params[k] = v
        return Transistor(*pos_params, **kw_params)

    @staticmethod
    def read_diode(line_with_diode_params: str) -> Diode:
        params = line_with_diode_params.split()
        pos_params = params[:4]
        kw_params = {}
        for elem in params[4:]:
            k, v = elem.split('=')
            kw_params[k] = v
        return Diode(*pos_params, **kw_params)


if __name__ == '__main__':
    net_obj = Netlist()
    net_obj.read('netlist_example.txt')
    cell = net_obj.get_cell('INV')
    print(cell.get_pin_order())
    cell.set_pin_order('vdd vss vbp vbn x a')
    print(cell.get_pin_order())
    print(cell.get_all_instances())
