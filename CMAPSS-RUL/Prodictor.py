import sys
sys.path.append("..")
import torch.nn as nn
import math
import torch.nn.functional as F
import torch


class conv_bn(nn.Module):
    def __init__(self, input_dim, output_dim, kernel, activation = "relu"):
        super(conv_bn, self).__init__()
        self.kernel_size = kernel
        self.donwconv = nn.Conv1d(in_channels = input_dim, 
                                  out_channels = output_dim, 
                                  kernel_size  = kernel)
        self.activation = F.relu if activation == "relu" else F.gelu
        self.norm       = nn.BatchNorm1d(output_dim)
		
    def forward(self, x):	
        padding_size = int(self.kernel_size/2)
        paddding_x   = nn.functional.pad(x, 
                                         pad=(padding_size, padding_size),
                                         mode='replicate')
        enc_out = self.norm(self.activation(self.donwconv(paddding_x)))
        return enc_out
		
		
class FullPredictor(nn.Module):
    def __init__(self, d_model,input_length):
        super(FullPredictor, self).__init__()
	

        self.conv_bn1   =  conv_bn( input_dim    = d_model,
                                    output_dim   = int(d_model/2),
                                    kernel       = 3)
									
        self.conv_bn2   =  conv_bn( input_dim    = int(d_model/2),
                                    output_dim   = int(d_model/4),
                                    kernel       = 3)

        self.conv_bn3   =  conv_bn( input_dim    = int(d_model/4),
                                    output_dim   = 1,
                                    kernel       = 3)
									


        self.predict = nn.Linear(in_features=input_length, 
                                 out_features=input_length)
	
    def forward(self, x):
        # 这里的输入是encoder的输出，encoder保证输出的格式为 B L D D=dmoel
        x = x.permute(0, 2, 1)

        x = self.conv_bn1(x)
        x = self.conv_bn2(x)
        x = self.conv_bn3(x)

        x = x.permute(0,2,1).squeeze()
	

        # fully layer prediction 											  
        enc_out = self.predict(x) 
        return enc_out
		
		
class LinearPredictor(nn.Module):
    def __init__(self, d_model):
        super(LinearPredictor, self).__init__()
		
        self.conv_bn1   =  conv_bn( input_dim    = d_model,
                                    output_dim   = int(d_model/2),
                                    kernel       = 3)
									
        self.conv_bn2   =  conv_bn( input_dim    = int(d_model/2),
                                    output_dim   = int(d_model/4),
                                    kernel       = 3)

        self.conv_bn3   =  conv_bn( input_dim    = int(d_model/4),
                                    output_dim   = int(d_model/8),
                                    kernel       = 3)
		
		
		
        self.predict = nn.Linear(int(d_model/8),1, bias=True)	
		
    def forward(self, x):
        # 这里的输入是encoder的输出，encoder保证输出的格式为 B L D D=dmoel
        x = x.permute(0, 2, 1)

        x = self.conv_bn1(x)

        x = self.conv_bn2(x)

        x = self.conv_bn3(x)


        x = x.permute(0, 2, 1)  
        enc_out = self.predict(x).squeeze()
              
        return enc_out
		
		
class ConvPredictor(nn.Module):
    def __init__(self, d_model, pred_kernel = 5):
        super(ConvPredictor, self).__init__()
        self.pred_kernel = 5
	

        self.conv_bn1   =  conv_bn( input_dim    = d_model,
                                    output_dim   = int(d_model/2),
                                    kernel       = 3)
									
        self.conv_bn2   =  conv_bn( input_dim    = int(d_model/2),
                                    output_dim   = int(d_model/4),
                                    kernel       = 3)

        self.conv_bn3   =  conv_bn( input_dim    = int(d_model/4),
                                    output_dim   = int(d_model/8),
                                    kernel       = 3)
									


        self.predict = nn.Conv1d(in_channels = int(d_model/8),
                                 out_channels = 1,
                                 kernel_size  = self.pred_kernel)
	
    def forward(self, x):
        # 这里的输入是encoder的输出，encoder保证输出的格式为 B L D D=dmoel
        x = x.permute(0, 2, 1)

        x = self.conv_bn1(x)
        x = self.conv_bn2(x)
        x = self.conv_bn3(x)
            
        padding_size = int(self.pred_kernel/2)
        paddding_x  = nn.functional.pad(x,
                                        pad=(padding_size, padding_size),
                                        mode='replicate') 
  
					  
        
        enc_out = self.predict(paddding_x).permute(0,2,1).squeeze()
        return enc_out