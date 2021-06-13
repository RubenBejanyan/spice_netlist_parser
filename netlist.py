import copy
import os
from typing import Union, List


class Device:

    positional_attributes = {'name', 'PLUS', 'MINUS', 'Model', 'S', 'D', 'G', 'B'}

    def set_attribute(self, attribute_name: str, attribute_value: str) -> None:

        if not isinstance(attribute_name, str):
            raise TypeError(f'Attribute name must be str, {type(attribute_name).__name__} given')
        if not isinstance(attribute_value, str):
            raise TypeError(f'Attribute value must be str, {type(attribute_value).__name__} given')
        if attribute_name not in self.__dict__.keys():
            raise AttributeError(f'{type(self).__name__} has no attribute "{attribute_name}"')

        self.__setattr__(attribute_name, attribute_value)

    def __repr__(self) -> str:
        info = [v if k in self.positional_attributes else f'{k}={v}' for k, v in self.__dict__.items()]
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

    def set_pin_order(self, new_pin_order: str) -> None:

        if not isinstance(new_pin_order, str):
            raise TypeError(f'Pin order must be str, {type(new_pin_order).__name__} given')

        new_pin_order = new_pin_order.split()

        # in this part I create valid_pins set where i collect all pins from cell devices,
        # because I think pin must exist at first
        valid_pins = set()
        for _instance in self.instances:
            for pin in _instance.__dict__:
                if pin in Device.positional_attributes.difference({'name', 'Model'}):
                    valid_pins.add(getattr(_instance, pin))

        if set(new_pin_order).issubset(valid_pins):
            self.pin_order = new_pin_order
        else:
            raise Exception(f'Pin(s) {set(new_pin_order).difference(valid_pins)} not exist')

    def get_all_instances(self) -> str:
        return '\n'.join(map(str, self.instances))

    def get_instance(self, instance_name: str) -> Union[Diode, Transistor]:

        if not isinstance(instance_name, str):
            raise TypeError(f'Instance name must be str, {type(instance_name).__name__} given')

        for _instance in self.instances:
            if _instance.name == instance_name:
                return _instance

        raise NameError(f'Cell "{self.name}" has no instance "{instance_name}". Choose from: '
                        f'{[getattr(_, "name") for _ in self.instances]}')

    def __repr__(self) -> str:
        return f'{self.name} (Description: {self.description}, Equation: {self.equation})'


class Netlist:

    def __init__(self):
        self.cell_list = []

    def read(self, path_to_file: Union[str, os.PathLike]) -> None:

        instances = []
        # this dict needed to check netlist text style, in every block I change value to True
        valid_spice_netlist = dict.fromkeys(['description', 'equation', 'subckt', 'instances'], False)

        with open(path_to_file, 'r') as nl:
            lines = nl.readlines()

            for line in lines:
                # this flag needed to check '.ends' at the end of the last cell
                finished = False

                if line.startswith('*'):
                    # here I am checking if subckt or instances is already True
                    # this means that last cell does not have '.ends' at the end
                    if valid_spice_netlist['subckt'] or valid_spice_netlist['instances']:
                        raise Exception(f'"{path_to_file}" file have other text style,'
                                        f' no ".ends" at the end of the cell "{cell_name}"')
                    if line.find('Description') != -1:
                        valid_spice_netlist['description'] = True
                        description = line.split(':', maxsplit=1)[-1].strip()
                    elif line.find('Equation') != -1:
                        valid_spice_netlist['equation'] = True
                        equation = line.split(':', maxsplit=1)[-1].strip()

                elif line.startswith('.subckt'):
                    valid_spice_netlist['subckt'] = True
                    cell_info = line.split()
                    cell_name = cell_info[1]
                    pin_order = cell_info[2:]

                elif line.startswith('M'):
                    valid_spice_netlist['instances'] = True
                    instances.append(self.read_transistor(line))

                elif line.startswith('D'):
                    valid_spice_netlist['instances'] = True
                    instances.append(self.read_diode(line))

                elif line.startswith('.ends'):
                    finished = True
                    if not all(valid_spice_netlist.values()):
                        raise Exception(f'"{path_to_file}" file have other text style,'
                                        f' please check {[k for k, v in valid_spice_netlist.items() if v == False]}')
                    self.cell_list.append(Cell(cell_name, description, equation, pin_order, instances))
                    # reset the values of instances and valid_spice_netlist in case if netlist has more then one cell
                    instances.clear()
                    valid_spice_netlist = {key: False for key in valid_spice_netlist}

                else:
                    if line != '\n':
                        raise Exception(f'"{path_to_file}" file have other text style,'
                                        f' please check line "{line.strip()}"')

            else:
                if not finished:
                    raise Exception(f'"{path_to_file}" file have other text style, no ".ends" at the end')

    def write(self, path_to_file: Union[str, os.PathLike]) -> None:
        lines = []

        for _cell in self.cell_list:
            lines.append(f'*      Description : {_cell.description}\n')
            lines.append(f'*      Equation    : {_cell.equation}\n')
            lines.append(f'.subckt {_cell.name} {_cell.get_pin_order()}\n')
            for device in _cell.instances:
                lines.append(f'{str(device).split(":", maxsplit=1)[-1].strip()}\n')
            lines.append('.ends\n\n')

        with open(path_to_file, 'w') as nl:
            nl.writelines(lines)

    def get_cell(self, cell_name: str) -> Cell:

        if not isinstance(cell_name, str):
            raise TypeError(f'Cell name must be str, {type(cell_name).__name__} given')

        for _cell in self.cell_list:
            if _cell.name == cell_name:
                return _cell

        raise NameError(f'Netlist has no cell "{cell_name}". Choose from: '
                        f'{[getattr(_, "name") for _ in self.cell_list]}')

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
    cell.set_pin_order('VSS VDD VBP VBN X A')
    print(cell.get_pin_order())
    # print(cell.get_all_instances())
    instance = cell.get_instance('MNA')
    print(instance)
    instance.set_attribute('S', 'new_vdd')
    print(instance)
    net_obj.write('test_new_netlist.txt')
