import copy


class Device:
    def set_attribute(self, attribute, value):
        self.__setattr__(attribute, value)

    def __repr__(self):
        info = [v if v.isalpha() or k == 'name' else f'{k}={v}' for k, v in self.__dict__.items()]
        return f"{type(self).__name__}: {' '.join(info)}"

    def __str__(self):
        return self.__repr__()


class Diode(Device):
    def __init__(self, name, plus, minus, model, **kwargs):
        self.name = name
        self.PLUS = plus
        self.MINUS = minus
        self.Model = model

        for k, v in kwargs.items():
            self.__setattr__(k, v)


class Transistor(Device):
    def __init__(self, name, source, drain, gate, base, model, **kwargs):
        self.name = name
        self.S = source
        self.D = drain
        self.G = gate
        self.B = base
        self.Model = model

        for k, v in kwargs.items():
            self.__setattr__(k, v)


class NetList:
    def __init__(self):
        self.cell_list = []

    def read(self, path_to_file):
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
                    _args, _kwargs = self.read_transistor(line)
                    instances.append(Transistor(*_args, **_kwargs))
                elif line.startswith('D'):
                    _args, _kwargs = self.read_diode(line)
                    instances.append(Diode(*_args, **_kwargs))
                elif line.startswith('.ends'):
                    self.cell_list.append(Cell(cell_name, description, equation, pin_order, instances))
                    instances.clear()

    def write(self, path_to_file):
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

    def get_cell(self, cell_name):
        for cell in self.cell_list:
            if cell.name == cell_name:
                return cell

    def get_all_cells(self):
        return self.cell_list

    @staticmethod
    def read_transistor(line_with_transistor_params):
        params = line_with_transistor_params.split()
        pos_params = params[:6]
        kw_params = {}
        for elem in params[6:]:
            k, v = elem.split('=')
            kw_params[k] = v
        return pos_params, kw_params

    @staticmethod
    def read_diode(line_with_diode_params):
        params = line_with_diode_params.split()
        pos_params = params[:4]
        kw_params = {}
        for elem in params[4:]:
            k, v = elem.split('=')
            kw_params[k] = v
        return pos_params, kw_params


class Cell:
    def __init__(self, name, description, equation, pin_order, instances):
        self.name = name
        self.description = description
        self.equation = equation
        self.pin_order = pin_order
        self.instances = copy.deepcopy(instances)

    def get_pin_order(self):
        return ' '.join(self.pin_order)

    def set_pin_order(self, pin_order):
        self.pin_order = pin_order.split()

    def get_all_instances(self):
        return '\n'.join(map(str, self.instances))

    def get_instance(self, instance_name):
        for instance in self.instances:
            if instance.name == instance_name:
                return instance

    def __repr__(self):
        return f'{self.name} (Description: {self.description}, Equation: {self.equation})'


if __name__ == '__main__':
    net_obj = NetList()
    net_obj.read('netlist_example.txt')
    cell = net_obj.get_cell('INV')
    print(cell.get_pin_order())
    cell.set_pin_order('vdd vss vbp vbn x a')
    print(cell.get_pin_order())
    # print(cell.get_all_instances())
    instance = cell.get_instance('MNA')
    print(instance)
    instance.set_attribute('S', 'newvdd')
    print(instance)
    net_obj.write('test_new_netlist.txt')
