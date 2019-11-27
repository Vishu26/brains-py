'''Author: HC Ruiz Euler and Unai Alegre-Ibarra; 
DNPU based network of devices to solve complex tasks 25/10/2019
'''

import torch
import numpy as np
import torch.nn as nn
from bspyproc.utils.pytorch import TorchUtils
from bspyproc.processors.simulation.dopanet import DNPU


class DNPU_NET(nn.Module):
    def __init__(self, in_dict,
                 path=r'../Data/Models/checkpoint3000_02-07-23h47m.pt'):
        super().__init__()
        self.in_dict = in_dict
        self.conversion_offset = torch.tensor(-0.6)
        self.offset = self.init_offset(-0.35, 0.7)
        self.scale = self.init_scale(0.1, 1.5)

        self.input_node1 = DNPU(in_dict['input_node1'], path=path)
        self.input_node2 = DNPU(in_dict['input_node2'], path=path)
        self.bn1 = nn.BatchNorm1d(2, affine=False)

        self.output_node = DNPU(in_dict['output_node'], path=path)

    def init_offset(self, offset_min, offset_max):
        offset = offset_min + offset_max * np.random.rand(1, 2)
        offset = TorchUtils.get_tensor_from_numpy(offset)
        return nn.Parameter(offset)

    def init_scale(self, scale_min, scale_max):
        scale = scale_min + scale_max * np.random.rand(1)
        scale = TorchUtils.get_tensor_from_numpy(scale)
        return nn.Parameter(scale)

    def regularizer(self):
        control_penalty = self.input_node1.regularizer() \
            + self.input_node2.regularizer() \
            + self.output_node.regularizer()
        return control_penalty + self.offset_penalty() + self.scale_penalty()

    def offset_penalty(self):
        return torch.sum(torch.relu(self.offset_min - self.offset) + torch.relu(self.offset - self.offset_max))

    def scale_penalty(self):
        return torch.sum(torch.relu(self.scale_min - self.scale) + torch.relu(self.scale - self.scale_m))


if __name__ == "__main__":

    import matplotlib.pyplot as plt

    IN_DICT = {}
    IN_DICT['input_node1'] = [3, 4]
    IN_DICT['input_node2'] = [3, 4]
    IN_DICT['output_node'] = [3, 4]

    dnpu_net = DNPU_NET(IN_DICT)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    dnpu_net.to(device)

    nr_points = 7
    x = -1.2 + 1.8 * np.random.rand(nr_points, 2)
    x = TorchUtils.get_tensor_from_numpy(x)
    target = TorchUtils.get_tensor_from_numpy(
        300 * np.random.rand(nr_points, 1))
    loss = nn.MSELoss()
    optimizer = torch.optim.Adam([{'params': dnpu_net.parameters()}], lr=0.007)

    LOSS_LIST = []
    for eps in range(5000):

        optimizer.zero_grad()
        out = dnpu_net(x)
        if np.isnan(out.data.cpu().numpy()[0]):
            break
        LOSS = loss(out, target) + dnpu_net.regularizer()
        LOSS_LIST.append(LOSS.item())
        print(f'Epoch {eps} with training loss {LOSS_LIST[-1]}')
        LOSS.backward()
        optimizer.step()

    print(f'OUTPUT : \n {out.data.cpu()} \n TARGETS: \n {target.data.cpu()}')

    plt.figure()
    plt.plot(LOSS_LIST)
    plt.title("Loss per epoch")
    plt.show()
