import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/shouptick/Documents/4dof_manipulator_vision/install/vision_pkg'
