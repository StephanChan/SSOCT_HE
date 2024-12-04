# SSOCT_HE
this is the control software for SSOCT_for_HE project at Sustech.
############################################################################################################ SOFTWARE STRUCTURE
using QThread of PYQT to do multi-threading control of data acquisition, scanning, data processing, display&saving
using Queue to organize threads
spectral domain data are stored in global memory, and memory location (pointers) are shared between threads using Queue
############################################################################################################ HARDWARE STRUCTURE
using swept source Aline trigger as trigger for digitizer, clock source can be external k-clock or internal clock 
using swept source Aline trigger as clock for Galvo&stage board, using digitizer output trigger as trigger for Galvo&stage board
scanning regime: X galvo scan in X dimension, Y stage scan in Y dimension. 
Stages are controlled with a single DIRECTIONAL digital signal (non-buffered) and an array of STEP digital signal (buffered)
this is the software framework:
![software frame](https://github.com/user-attachments/assets/962d2162-0599-4fcf-8886-57a50430deae)
This is the software timeline:
![software timeline](https://github.com/user-attachments/assets/c8a3ae85-6902-4988-984e-8a155be562bc)
