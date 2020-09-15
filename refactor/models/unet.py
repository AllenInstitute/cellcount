import torch
import torch.nn as nn
import torch.optim as optim


def double_conv(in_channels, out_channels):
    '''Performs two successive convolution operations
    '''
    conv = nn.Sequential(
        nn.Conv2d(in_channels, out_channels, kernel_size=3),
        nn.ReLU(inplace=True),
        nn.Conv2d(out_channels, out_channels, kernel_size=3),
        nn.ReLU(inplace=True)
    )
    return conv


def crop_tensor(tensor, target_tensor):
    '''Crop the tensor xdim and ydim.
     - Assumes sizes are divisible by 2
     - Assumes tensor sizes are [batch,channels,xdim,ydim]
    '''
    tensor_size = tensor.size()[2]
    target_tensor_size = target_tensor.size()[2]
    delta = (tensor_size-target_tensor_size)//2
    target = tensor[:, :, delta:tensor_size-delta, delta:tensor_size-delta]
    return target


def dice_loss(input, target):
    '''Dice loss for segmentation problems'''
    smooth = 1.
    iflat = input.view(-1)
    tflat = target.view(-1)
    intersection = (iflat * tflat).sum()
    return 1 - ((2. * intersection + smooth) /
                (iflat.sum() + tflat.sum() + smooth))

def cross_entropy(input, target):
    criterion = nn.CrossEntropyLoss()



class UNet(nn.Module):
    def __init__(self):
        super(UNet, self).__init__()
        self.maxpool_2x2 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.down_conv_1 = double_conv(1, 16)
        self.down_conv_2 = double_conv(64, 128)
        self.down_conv_3 = double_conv(128, 256)
        self.down_conv_4 = double_conv(256, 512)
        self.down_conv_5 = double_conv(512, 1024)

        self.up_trans_1 = nn.ConvTranspose2d(1024, 512, kernel_size=2, stride=2)
        self.up_conv_1 = double_conv(1024, 512)

        self.up_trans_2 = nn.ConvTranspose2d(512, 256, kernel_size=2, stride=2)
        self.up_conv_2 = double_conv(512, 256)

        self.up_trans_3 = nn.ConvTranspose2d(256, 128, kernel_size=2, stride=2)
        self.up_conv_3 = double_conv(256, 128)

        self.up_trans_4 = nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2)
        self.up_conv_4 = double_conv(128, 64)

        self.out = nn.Conv2d(64, 2, kernel_size=1)
        return

    def forward(self, image):
        x1 = self.down_conv_1(image)
        print(x1.size())

        x2 = self.maxpool_2x2(x1)
        x2 = self.down_conv_2(x2)
        print(x2.size())

        x3 = self.maxpool_2x2(x2)
        x3 = self.down_conv_3(x3)
        print(x3.size())

        x4 = self.maxpool_2x2(x3)
        x4 = self.down_conv_4(x4)
        print(x4.size())

        x5 = self.maxpool_2x2(x4)
        x5 = self.down_conv_5(x5)
        print(x5.size())

        x6 = self.up_trans_1(x5)
        x4 = crop_tensor(tensor=x4, target_tensor=x6)
        x7 = self.up_conv_1(torch.cat(tensors=[x4, x6], dim=1))
        print(x7.size())
        x7 = self.up_trans_2(x7)

        x3 = crop_tensor(tensor=x3, target_tensor=x7)
        x8 = self.up_conv_2(torch.cat(tensors=[x3, x7], dim=1))
        print(x8.size())

        x8 = self.up_trans_3(x8)
        x2 = crop_tensor(tensor=x2, target_tensor=x8)
        x9 = self.up_conv_3(torch.cat(tensors=[x2, x8], dim=1))
        print(x9.size())

        x9 = self.up_trans_4(x9)
        x1 = crop_tensor(tensor=x1, target_tensor=x9)
        x10 = self.up_conv_4(torch.cat(tensors=[x1, x9], dim=1))
        print(x10.size())

        x = self.out(x10)
        print(x.size())
        return x


if __name__ == '__main__':
    image = torch.rand(size=(1, 1, 572, 572))
    unet = UNet()
    unet(image)

    
    # optimizer = optim.SGD(unet.parameters(), lr=0.001, momentum=0.9)


    # running_loss = 0.0
    # for i, data in enumerate(trainloader, 0):
    #     # get the inputs; data is a list of [inputs, labels]
    #     inputs, labels = data

    #     # zero the parameter gradients
    #     optimizer.zero_grad()

    #     # forward + backward + optimize
    #     outputs = unet(inputs)
    #     loss = cross_entropy(outputs, labels)
    #     loss.backward()
    #     optimizer.step()

    #     # print statistics
    #     running_loss += loss.item()
    #     if i % 2000 == 1999:    # print every 2000 mini-batches
    #         print('[%d, %5d] loss: %.3f' %
    #               (epoch + 1, i + 1, running_loss / 2000))
    #         running_loss = 0.0

    #     print('Finished Training')

    # return