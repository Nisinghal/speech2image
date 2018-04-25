#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 26 17:54:07 2018

@author: danny
"""

from costum_layers import RHN, attention
import torch
import torch.nn as nn

import time

# the network for embedding the vgg16 features
class img_encoder(nn.Module):
    def __init__(self):
        super(img_encoder, self).__init__()
        self.linear_transform = nn.Linear(4096,1024)
    
    def forward(self, input):
        x = self.linear_transform(input)
        #return nn.functional.normalize(x, p=2, dim=1)
        return x  
# audio encoder as described by Harwath and Glass(2016)
class Harwath_audio_encoder(nn.Module):
    def __init__(self):
        super(Harwath_audio_encoder, self).__init__()
        self.Conv1d_1 = nn.Conv1d(in_channels = 40, out_channels = 64, kernel_size = 5, 
                                 stride = 1, padding = 0, groups = 1)
        self.Pool1 = nn.MaxPool1d(kernel_size = 4, stride = 2, padding = 0, dilation = 1, 
                                  return_indices = False, ceil_mode = False)
        self.Conv1d_2 = nn.Conv1d(in_channels = 64, out_channels = 512, kernel_size = 25,
                                  stride = 1, padding = 0, groups = 1)
        self.Conv1d_3 = nn.Conv1d(in_channels = 512, out_channels = 1024, kernel_size = 25,
                                  stride = 1, padding = 0, groups = 1)
        self.Pool2 = nn.AdaptiveMaxPool1d(output_size = 1, return_indices=False)
        self.relu = nn.ReLU()

    def forward(self, input):
        x = self.relu(self.Pool1(self.Conv1d_1(input)))
        x = self.relu(self.Pool1(self.Conv1d_2(x)))
        x = self.relu(self.Pool2(self.Conv1d_3(x)))
        x = torch.squeeze(x)
        return nn.functional.normalize(x, p = 2, dim = 1)

class RCNN_audio_encoder(nn.Module):
    def __init__(self):
        super(RCNN_audio_encoder, self).__init__()
        self.Conv2d_1 = nn.Conv1d(in_channels = 40, out_channels = 64, kernel_size = 5, 
                                 stride = 1, padding = 2, groups = 1, bias = False)
        self.Pool1 = nn.MaxPool1d(kernel_size = 4, stride = 2, padding = 0, dilation = 1, 
                                  return_indices = False, ceil_mode = False)
        self.Conv1d_1 = nn.Conv1d(in_channels = 64, out_channels = 512, kernel_size = 25,
                                  stride = 1, padding = 12, groups = 1)
        self.Conv1d_2 = nn.Conv1d(in_channels = 512, out_channels = 1024, kernel_size = 25,
                                  stride = 1, padding = 12, groups = 1)
        self.Pool2 = nn.AdaptiveMaxPool1d(output_size = 1, return_indices=False)
        self.GRU = nn.GRU(1024, 1024, num_layers = 1, batch_first = True)
        self.att = attention(1024, 128)
        self.norm1 = nn.BatchNorm1d(64)
        self.norm2 = nn.BatchNorm1d(512)
        self.norm3 = nn.BatchNorm1d(1024)
    def forward(self, input):
        x = self.norm1(self.Conv2d_1(input))
        x = self.norm2(self.Conv1d_1(x))
        x = self.norm3(self.Conv1d_2(x))
        x = x.permute(0,2,1)
        x, hx = self.GRU(x)
        x = nn.functional.normalize(self.att(x), p=2, dim=1)
        return x

# Recurrent highway network audio encoder.
class RHN_audio_encoder(nn.Module):
    def __init__(self, batch_size):
        super(RHN_audio_encoder, self).__init__()
        self.Conv2d = nn.Conv2d(in_channels = 1, out_channels = 64, kernel_size = (40,6), 
                                 stride = (1,2), padding = 0, groups = 1)
        self.RHN = RHN(64, 1024, 2, batch_size)
        self.RHN_2 = RHN(1024, 1024, 2, batch_size)
        self.RHN_3 = RHN(1024, 1024, 2, batch_size)
        self.RHN_4 = RHN(1024, 1024, 2, batch_size)
        self.att = attention(1024, 128, 1024)
        
    def forward(self, input):
        x = self.Conv2d(input)
        x = x.squeeze().permute(2,0,1).contiguous()
        x = self.RHN(x)
        x = self.RHN_2(x)
        x = self.RHN_3(x)
        x = self.RHN_4(x)
        x = self.att(x)
        return x

# Recurrent highway network audio encoder.
class GRU_audio_encoder(nn.Module):
    def __init__(self):
        super(GRU_audio_encoder, self).__init__()
        self.Conv1d = nn.Conv1d(in_channels = 40, out_channels = 64, kernel_size = 6,
                                 stride = 2, padding = 0, groups = 1, bias = False)
        nn.init.xavier_uniform(self.Conv1d.weight.data)
        self.GRU = nn.GRU(64, 512, num_layers = 4, batch_first = True, bidirectional = True)
        self.att = attention(1024, 128)
    def forward(self, input):
        x = self.Conv1d(input)
        x = x.permute(0, 2, 1)
        x, hx = self.GRU(x)
        x = nn.functional.normalize(self.att(x), p=2, dim=1)
        return x


#start_time = time.time()
#gru = RCNN_audio_encoder()
#input = torch.autograd.Variable(torch.rand(8, 40, 1024))
#output = gru(input)

#time = time.time() - start_time
#print(time)
