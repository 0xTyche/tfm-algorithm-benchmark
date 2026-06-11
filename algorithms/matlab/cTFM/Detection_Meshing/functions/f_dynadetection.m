%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_dynadetection is called by the cTFM mesh generator      %
%                                                           %
% This function thresholds the image at a value given by    %
% the user. The resulting binary image contains pixel       %
% islands of '1's surrounded by '0's. The calculation of    %
% the weighted centroids of the island's gray scale values  %
% gives the subpixel position of the quantum dots. These    %
% positions are returned.                                   %
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function [ybar2,xbar2]=f_dynadetection(img,thresh)
    intensity_thresh = thresh*mean(mean(img));
    bw = img > intensity_thresh;
    bw = imfill(bw, 'holes');
    [L,num] = bwlabel(bw);
    
    s = regionprops(L, 'PixelIdxList', 'PixelList');

    xbar = zeros(num,1);
    ybar = zeros(num,1);
     
    for k = 1:num
        idx = s(k).PixelIdxList;
        pixel_values = double(img(idx));
        sum_pixel_values = sum(pixel_values);
        x = s(k).PixelList(:, 1);
        y = s(k).PixelList(:, 2);
        xbar(k) = sum(x .* pixel_values) / sum_pixel_values;
        ybar(k) = sum(y .* pixel_values) / sum_pixel_values;
    end
    
    %--- below gives the exact same results
    xbar2 = zeros(num,1);
    ybar2 = zeros(num,1);
    
    c = regionprops(L,img, 'WeightedCentroid');
    for k = 1:num
        xbar2(k) = c(k).WeightedCentroid(1);
        ybar2(k) = c(k).WeightedCentroid(2);
    end
    
end