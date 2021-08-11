import torch
from torchvision import datasets, transforms
import math
import numpy as np
from utils.utility_functions.arguments import Arguments


class MNISTTransform:
    @classmethod
    def train_transform(cls):
        return transforms.Compose([
           transforms.ToTensor(),
           transforms.Normalize((0.1307, ), (0.3081, ))
           ])

class EMNISTTransform:
    @classmethod
    def train_transform(cls):
        return transforms.Compose([transforms.Resize((28,28)),
                               transforms.ToTensor(),
                               transforms.Normalize((0.5,), (0.5,))])
class CIFAR10Transform:
    data_mean = (0.4914, 0.4822, 0.4465)
    data_stddev = (0.2023, 0.1994, 0.2010)

    @classmethod
    def train_transform(cls):

        return transforms.Compose(
                    [
                        transforms.RandomCrop(32, padding=4),
                        transforms.RandomHorizontalFlip(),
                        transforms.ToTensor(),
                        transforms.Normalize(CIFAR10Transform.data_mean, CIFAR10Transform.data_stddev),
                    ]
                )

    @classmethod
    def test_transform(cls):
        return transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(CIFAR10Transform.data_mean, CIFAR10Transform.data_stddev),
        ])


class CIFAR100Transform:
    data_mean = (0.5070751592371323, 0.48654887331495095, 0.4409178433670343)
    data_stddev = (0.2673342858792401, 0.2564384629170883, 0.27615047132568404)

    @classmethod
    def train_transform(cls):

        return transforms.Compose(
                    [
                        transforms.RandomCrop(32, padding=4),
                        transforms.RandomHorizontalFlip(),
                        transforms.ToTensor(),
                        transforms.Normalize(CIFAR100Transform.data_mean, CIFAR100Transform.data_stddev),
                    ]
                )

    @classmethod
    def test_transform(cls):
        return transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(CIFAR100Transform.data_mean, CIFAR100Transform.data_stddev),
        ])

def partition_noniid(dataset: torch.utils.data.Dataset,workers: int, percentage_iid: float,use_two_splits):
    perm = torch.randperm(len(dataset))
    iid_indices = perm[:int(len(dataset)*percentage_iid)]
    noniid_indices = perm[int(len(dataset)*percentage_iid):]
    targets = torch.tensor(dataset.targets).clone().detach()

    labels=torch.unique(targets)
    structured_noniiid_indices=[]
    for label in labels:
        indices = np.intersect1d( torch.squeeze((targets == label).nonzero()) , noniid_indices)
        structured_noniiid_indices.append(torch.from_numpy(indices))

    #if nshards == 2:
    #    all_indices=torch.cat(all_indices).view(2*workers,-1)
    #    all_indices=all_indices[torch.randperm(all_indices.size()[0])]
    #    all_indices=all_indices.view(workers,-1)
    structured_noniiid_indices=torch.cat(structured_noniiid_indices).view(workers,-1)
    if percentage_iid == 0:
        return [torch.utils.data.Subset(dataset, structured_noniiid_indices[i] ) for i in range(workers)]
    iid_indices=iid_indices.view(workers,-1)
    if use_two_splits == False:
        return [torch.utils.data.Subset(dataset, torch.cat((iid_indices[i],structured_noniiid_indices[i])) ) for i in range(workers)]
    else:
        return [[torch.utils.data.Subset(dataset, iid_indices[i] ), torch.utils.data.Subset(dataset, structured_noniiid_indices[i] ) ] for i in range(workers)]

def split_data(task: str, workers: int, percentage_iid: float, use_two_splits: bool):
    if task == "MNIST":
        dataset = datasets.MNIST(root=Arguments.data_home, train=True, download=True, transform=MNISTTransform.train_transform())
    elif task == "EMNIST":
        dataset = datasets.EMNIST(root=Arguments.data_home,split="balanced" ,train=True, download=True,transform=EMNISTTransform.train_transform())
    elif task == "CIFAR100":
        dataset = datasets.CIFAR100(root=Arguments.data_home, train=True, download=True,
                                   transform=CIFAR100Transform.train_transform())
    else :# task == "CIFAR10"
        dataset = datasets.CIFAR10(root=Arguments.data_home, train=True, download=True,
                                   transform=CIFAR10Transform.train_transform())

    if percentage_iid == 1:
        return torch.utils.data.random_split(dataset, [math.floor(len(dataset)/workers) for _ in range(workers)])
    elif percentage_iid == -1:
        return [dataset for _ in range(workers)]
    else:
        return partition_noniid(dataset,workers,percentage_iid,use_two_splits)

def get_validation_data(task: str):
    if task == "MNIST":
        dataset =  datasets.MNIST(root=Arguments.data_home, train=False, download=True, transform=MNISTTransform.train_transform())
    elif task == "EMNIST":
        dataset =  datasets.EMNIST(root=Arguments.data_home,split="balanced" ,train=False, download=True,transform=EMNISTTransform.train_transform())
    elif task == "CIFAR100":
        dataset = datasets.CIFAR100(root=Arguments.data_home, train=False, download=True, transform=CIFAR100Transform.test_transform())
    else:# task == "CIFAR10"
        dataset = datasets.CIFAR10(root=Arguments.data_home, train=False, download=True, transform=CIFAR10Transform.test_transform())
    return dataset