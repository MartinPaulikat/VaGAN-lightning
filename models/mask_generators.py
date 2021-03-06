import torch.nn as nn
import torch
from models.model_utils import (ACTIVATION,
                                deconv2d_bn_block,
                                conv2d_bn_block,
                                crop_and_concat,
                                conv2d_block,
                                conv3d_block,
                                Identity)


class UNet(nn.Module):
    '''
    portings for the models found in the reference reference's official repo
    https://github.com/baumgach/vagan-code
    '''
    def __init__(self, n_channels=61, nf=16, batch_norm=True, dimensions=2, activation=ACTIVATION):
        super(UNet, self).__init__()
        if dimensions == 2:
            conv_block = conv2d_bn_block if batch_norm else conv2d_block
        else:
            conv_block = conv3d_block
        max_pool = nn.MaxPool2d(2) if int(dimensions) is 2 else nn.MaxPool3d(2)
        act = activation

        self.down0 = nn.Sequential(
            conv_block(n_channels, nf, activation=act),
            conv_block(nf, nf, activation=act)
        )
        self.down1 = nn.Sequential(
            max_pool,
            conv_block(nf, 2*nf, activation=act),
            conv_block(2*nf, 2*nf, activation=act),
        )
        self.down2 = nn.Sequential(
            max_pool,
            conv_block(2*nf, 4*nf, activation=act),
            conv_block(4*nf, 4*nf, activation=act),
        )
        self.down3 = nn.Sequential(
            max_pool,
            conv_block(4*nf, 8*nf, activation=act),
            conv_block(8*nf, 8*nf, activation=act),
        )

        self.up3 = deconv2d_bn_block(8*nf, 4*nf, activation=act)

        self.conv5 = nn.Sequential(
            conv_block(8*nf, 4*nf, activation=act),
            conv_block(4*nf, 4*nf, activation=act),
        )
        self.up2 = deconv2d_bn_block(4*nf, 2*nf, activation=act)

        self.conv6 = nn.Sequential(
            conv_block(4*nf, 2*nf, activation=act),
            conv_block(2*nf, 2*nf, activation=act),
        )
        self.up1 = deconv2d_bn_block(2*nf, nf, activation=act)

        self.conv7 = nn.Sequential(
            conv_block(2*nf, nf, activation=act),
            conv_block(nf, n_channels, activation=Identity),
        )

        self.tanh = nn.Sequential(
            nn.Tanh()
        )

        self.sigmoid = nn.Sequential(
            nn.Sigmoid()
        )

    def forward(self, x, sigmoid=False):
        x0 = self.down0(x)
        x1 = self.down1(x0)
        x2 = self.down2(x1)
        x3 = self.down3(x2)

        xu3 = self.up3(x3)
        cat3 = crop_and_concat(xu3, x2)
        x5 = self.conv5(cat3)
        xu2 = self.up2(x5)
        cat2 = crop_and_concat(xu2, x1)
        x6 = self.conv6(cat2)
        xu1 = self.up1(x6)
        cat1 = crop_and_concat(xu1, x0)
        x7 = self.conv7(cat1)

        if sigmoid:
            x8 = self.sigmoid(torch.add(x7,x))
        else:
            x8 = self.tanh(x7)

        return x8