# Features

## Time domain features 
Window: 10s (short)
* mean_nni: Mean RR-interval on cleaned signal 
* median_nni: Median RR-interval on cleaned signal
* sdnn: Standard deviation of NN intervals on cleaned signal ?
* sdsd: Standard deviation of differences between adjacent RR-interval on cleaned signal ?
* nni_50: Number of interval differences of successive RR-intervals greater than 50ms on cleaned signal
* nni_20: Number of interval differences of successive RR-intervals greater than 20ms on cleaned signal
* pnni_50: Percentage of interval differences of successive RR-intervals greater than 50ms on cleaned signal
* pnni_20: Percentage of interval differences of successive RR-intervals greater than 20ms on cleaned signal
* range_nni: difference between max and min RR-interval on cleaned signal
* rmssd: Square root of the mean of the squared differences between adjacent RR-intervals
* cvsd: Coefficient of variation of successive differences equal to the rmssd divided by mean_nni
* cvnni: sdnn/mean_nni
* mean_hr: Mean of heart rate (1/nni)
* max_hr: Max of heart rate (1/nni)
* std_hr: Standard deviation of heart rate (1/nni)

## Frequency domain features
Window: 2m30s (large)
* lf: Variance (=Power) in HRV in the low frequency (0.04-0.15Hz)
* hf: Variance (=Power) in HRV in the low frequency (0.15-0.4Hz)
* vlf: Variance (=Power) in HRV in the low frequency (0.003-0.04Hz)
* lf_hf_ratio: lf/hf

## Non-linear domain features
Window: 60s (medium)
* sd1: largeur du nuage de Pointcarré ?
* sd2: hauteur du nuage de Pointcarré ?
* csi: Cardiac sympathetic index (~sd1/sd2) ???????
* cvi: Cardiac vagal index (~log10(sd1*sd2) ?????
* modified_csi: (~sd1^2/sd2) ????
* sampen: Sample entropy ???